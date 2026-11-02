"""
Argus Server: Production FastAPI & WebSocket Telemetry Streaming Daemon.
Runs edge perception in background worker and exposes real-time telemetry over WebSockets and REST.
"""

import asyncio
import json
import threading
import time
from typing import Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from argus.capture.camera import CameraManager
from argus.detectors.detector import PersonDetector
from argus.detectors.shatter import ShatterDetector
from argus.analytics.engine import AnalyticsEngine
from argus.rules.decision_engine import DecisionEngine
from argus.logger import logger

app = FastAPI(
    title="Argus Vision Server",
    description="Real-Time Edge Vision & Venue Spatial Intelligence Daemon",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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


def background_vision_worker(camera_source: int = 0, confidence: float = 0.35):
    """Continuous edge detection loop running in background thread."""
    global latest_telemetry

    try:
        camera = CameraManager(source=camera_source, resolution=(1280, 720))
        detector = PersonDetector(confidence_threshold=confidence, use_yolo=True, detect_objects=True)
        shatter_detector = ShatterDetector()
        analytics = AnalyticsEngine(db_path="data/metrics.db")
        decision_engine = DecisionEngine()

        camera.start()
        logger.info("Argus background vision worker running...")

        last_log = time.time()

        while True:
            frame = camera.get_frame(timeout=0.1)
            if frame is None:
                time.sleep(0.01)
                continue

            detections = detector.detect(frame)
            shatter_event = shatter_detector.evaluate(frame_bgr=frame)

            people = len(detections.get("people", []))
            counts = detections.get("counts", {})

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
    return {"status": "healthy", "service": "argus-server", "version": "0.1.0"}


@app.get("/metrics/current")
async def get_current_metrics():
    return latest_telemetry


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await hub.connect(websocket)
    try:
        while True:
            # Keep socket open and receive any client control commands
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await hub.disconnect(websocket)


def main():
    uvicorn.run("services.argus_server.main:app", host="0.0.0.0", port=8100, reload=False)


if __name__ == "__main__":
    main()
