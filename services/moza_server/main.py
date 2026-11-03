"""
Moza Server: Production FastAPI & WebSocket Telemetry Streaming Daemon.
Runs edge perception in background worker and exposes real-time telemetry over WebSockets and REST.
"""

import argparse
import asyncio
import os
import threading
import time
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import cv2

from moza.capture.camera import CameraManager
from moza.detectors.detector import PersonDetector
from moza.detectors.shatter import ShatterDetector
from moza.analytics.engine import AnalyticsEngine
from moza.rules.decision_engine import DecisionEngine
from moza.privacy.anonymizer import FaceAnonymizer
from moza.logger import logger

app = FastAPI(
    title="Moza Vision Server",
    description="Real-Time Edge Vision & Venue Spatial Intelligence Daemon",
    version="0.1.0"
)

# Browser pages allowed to call this server: the desktop app (Tauri 2 serves it from
# http://tauri.localhost on Windows, tauri://localhost on macOS/Linux) and its Vite
# dev server. Any other website open on this machine must not read the camera
# telemetry or change the config. Non-browser clients send no Origin and are
# unaffected. Add origins with MOZA_ALLOWED_ORIGINS (comma-separated).
ALLOWED_ORIGINS = [
    "http://tauri.localhost",
    "tauri://localhost",
    "http://localhost:3302",
    "http://127.0.0.1:3302",
] + [o.strip() for o in os.environ.get("MOZA_ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TelemetryHub:
    """Manages active WebSocket subscriber connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        async with self.lock:
            dead_connections = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)
            for dead in dead_connections:
                self.active_connections.remove(dead)


hub = TelemetryHub()
latest_telemetry: Dict[str, Any] = {
    "status": "idle",
    "people_count": 0,
    "bottle_count": 0,
    "wine_glass_count": 0,
    "total_beverages": 0,
    "knife_count": 0,
    "total_hazards": 0,
    "broken_glass": False,
    "trend": "stable",
    "timestamp": time.time()
}
latest_jpeg_frame: Optional[bytes] = None
active_config: Dict[str, Any] = {
    "confidence": 0.35,
    "anonymize_faces": True,
    "source": 0
}


class ConfigPayload(BaseModel):
    confidence: Optional[float] = None
    anonymize_faces: Optional[bool] = None
    source: Optional[Union[int, str]] = None


def background_vision_worker():
    """Continuous edge detection loop running in background thread."""
    global latest_telemetry, latest_jpeg_frame

    try:
        camera = CameraManager(source=active_config["source"], resolution=(1280, 720))
        detector = PersonDetector(confidence_threshold=active_config["confidence"], use_yolo=True, detect_objects=True)
        shatter_detector = ShatterDetector()
        anonymizer = FaceAnonymizer()
        analytics = AnalyticsEngine(db_path="data/metrics.db")
        decision_engine = DecisionEngine()

        camera.start()
        logger.info("Moza background vision worker running...")

        last_log = time.time()

        while True:
            frame = camera.get_frame(timeout=0.1)
            if frame is None:
                time.sleep(0.01)
                continue

            # Update detector threshold dynamically if config changed
            if detector.confidence_threshold != active_config["confidence"]:
                detector.confidence_threshold = active_config["confidence"]

            detections = detector.detect(frame)
            shatter_event = shatter_detector.evaluate(frame_bgr=frame)

            people = len(detections.get("people", []))
            counts = detections.get("counts", {})

            # Draw visualization bounding boxes
            detector.draw_boxes(frame, detections)

            # Apply zero-PII face obfuscation if enabled
            if active_config.get("anonymize_faces", True):
                anonymizer.anonymize(frame)

            # Encode frame to JPEG for local webview streaming
            ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
            if ret:
                latest_jpeg_frame = jpeg.tobytes()

            now = time.time()
            if now - last_log >= 1.0:
                analytics.log_detection(
                    zone_id="main",
                    person_count=people,
                    object_counts=counts,
                    broken_glass=shatter_event.detected
                )
                metrics = analytics.get_current_metrics("main")

                # Evaluate decision rules
                context = {
                    "person_count": people,
                    "bottle_count": counts.get("bottle", 0),
                    "wine_glass_count": counts.get("wine glass", 0),
                    "knife_count": counts.get("knife", 0),
                    "shatter_detected": shatter_event.detected,
                    "broken_glass_count": 1 if shatter_event.detected else 0,
                    "zone_id": "main",
                    "trend": metrics["trend"]
                }
                decision_engine.evaluate(context)

                # Update live telemetry state
                latest_telemetry = {
                    "status": "running",
                    "people_count": people,
                    "bottle_count": counts.get("bottle", 0),
                    "wine_glass_count": counts.get("wine glass", 0),
                    "total_beverages": metrics["total_beverages"],
                    "knife_count": counts.get("knife", 0),
                    "total_hazards": metrics["total_hazards"],
                    "broken_glass": shatter_event.detected,
                    "trend": metrics["trend"],
                    "avg_count": metrics["avg_count"],
                    "timestamp": now
                }
                last_log = now

    except Exception as e:
        logger.error(f"Vision worker crashed: {e}")


@app.on_event("startup")
async def on_startup():
    # Start vision worker in separate daemon thread
    thread = threading.Thread(target=background_vision_worker, daemon=True)
    thread.start()

    # Periodic telemetry broadcast loop
    async def broadcast_loop():
        while True:
            await asyncio.sleep(1.0)
            if hub.active_connections:
                await hub.broadcast(latest_telemetry)

    asyncio.create_task(broadcast_loop())


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "moza-server", "version": "0.1.0"}


@app.get("/metrics/current")
async def get_current_metrics():
    return latest_telemetry


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    # Browsers do not apply CORS to WebSockets, so check the Origin here.
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in ALLOWED_ORIGINS:
        await websocket.close(code=1008)  # policy violation
        return
    await hub.connect(websocket)
    try:
        while True:
            # Keep socket open and receive any client control commands
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await hub.disconnect(websocket)


@app.get("/config")
async def get_config():
    return active_config


@app.post("/config")
async def update_config(payload: ConfigPayload):
    if payload.confidence is not None:
        active_config["confidence"] = max(0.1, min(0.95, payload.confidence))
    if payload.anonymize_faces is not None:
        active_config["anonymize_faces"] = payload.anonymize_faces
    if payload.source is not None:
        if isinstance(payload.source, str) and payload.source.isdigit():
            active_config["source"] = int(payload.source)
        else:
            active_config["source"] = payload.source
    logger.info(f"Updated live config: {active_config}")
    return {"status": "updated", "config": active_config}


def _mjpeg_stream_generator():
    """100% Local MJPEG frame generator streaming directly to desktop app."""
    while True:
        if latest_jpeg_frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + latest_jpeg_frame + b'\r\n')
        time.sleep(0.033)  # ~30 FPS


@app.get("/stream/video")
async def stream_video():
    """Streams live annotated video to Moza Desktop Studio over local loopback."""
    return StreamingResponse(
        _mjpeg_stream_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def main(argv: Optional[List[str]] = None):
    # Loopback by default: the video stream and telemetry show people on camera.
    # Serving other machines is opt-in (--host 0.0.0.0 or MOZA_HOST); the Docker image does so.
    parser = argparse.ArgumentParser(description="Moza vision server")
    parser.add_argument("--host", default=os.environ.get("MOZA_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MOZA_PORT", "8100")))
    args = parser.parse_args(argv)
    if args.host not in LOOPBACK_HOSTS:
        logger.warning(
            f"Serving on {args.host}:{args.port}: the live video stream and telemetry "
            "are reachable from other machines on this network."
        )
    uvicorn.run("services.moza_server.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
