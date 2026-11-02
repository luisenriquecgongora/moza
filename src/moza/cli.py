"""
Moza Standalone Interactive CLI.
Run detection directly on webcam or RTSP stream with OpenCV display.
"""

import argparse
import time
import cv2

from .capture.camera import CameraManager
from .detectors.detector import PersonDetector
from .detectors.glassware import GlasswareDetector
from .detectors.shatter import ShatterDetector
from .analytics.engine import AnalyticsEngine
from .logger import logger


def main():
    parser = argparse.ArgumentParser(description="Moza Edge Vision & Venue Intelligence CLI")
    parser.add_argument("--source", default=0, help="Camera index (0, 1) or RTSP URL or video file")
    parser.add_argument("--resolution", default="1280x720", help="Resolution WxH (default: 1280x720)")
    parser.add_argument("--confidence", type=float, default=0.35, help="Confidence threshold (default: 0.35)")
    parser.add_argument("--yolo", action="store_true", default=True, help="Use YOLO detector")
    parser.add_argument("--no-multiclass", action="store_true", help="Disable multi-class beverage/hazard detection")
    parser.add_argument("--db", default="data/metrics.db", help="Path to metrics SQLite database")
    args = parser.parse_args()

    # Parse resolution
    try:
        w, h = map(int, args.resolution.lower().split("x"))
    except ValueError:
        w, h = 1280, 720

    # Parse source
    source = int(args.source) if str(args.source).isdigit() else str(args.source)

    logger.info("👁️ Starting Moza Edge Vision System")
    camera = CameraManager(source=source, resolution=(w, h))
    detector = PersonDetector(
        confidence_threshold=args.confidence,
        use_yolo=args.yolo,
        detect_objects=not args.no_multiclass
    )
    glass_detector = GlasswareDetector(confidence_threshold=args.confidence)
    shatter_detector = ShatterDetector()
    analytics = AnalyticsEngine(db_path=args.db)

    camera.start()
    last_log_time = time.time()
    last_stats_time = time.time()

    try:
        while True:
            frame = camera.get_frame(timeout=0.1)
            if frame is None:
                time.sleep(0.01)
                continue

            # Run multi-class detection
            detections = detector.detect(frame)
            people_count = len(detections.get("people", []))
            counts = detections.get("counts", {})

            # Check shatter visual delta
            shatter_event = shatter_detector.evaluate(frame_bgr=frame)

            # Draw bounding boxes
            detector.draw_boxes(frame, detections)

            # Log to SQLite every 1 second
            now = time.time()
            if now - last_log_time >= 1.0:
                analytics.log_detection(
                    zone_id="main",
                    person_count=people_count,
                    bounding_boxes=detections.get("people", []),
                    object_counts=counts,
                    broken_glass=shatter_event.detected
                )
                last_log_time = now

            # Print terminal stats every 3 seconds
            if now - last_stats_time >= 3.0:
                metrics = analytics.get_current_metrics("main")
                logger.info(
                    f"📊 Intel: People={metrics['current_count']} (avg={metrics['avg_count']:.1f}, trend={metrics['trend']}) | "
                    f"Bottles={metrics['bottle_count']}, Glasses={metrics['wine_glass_count']}, "
                    f"Hazards={metrics['total_hazards']}"
                )
                last_stats_time = now

            # Show GUI window
            cv2.imshow("Moza Vision Engine - Press 'q' to exit", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("User requested exit.")
                break

    finally:
        camera.stop()
        cv2.destroyAllWindows()
        logger.info("Moza CLI shutdown complete.")


if __name__ == "__main__":
    main()
