"""
Multi-class object detection using YOLO or MediaPipe.
Detects people, beverages (bottles, cups, wine glasses), hazards (knives), and devices.
"""

from typing import Dict, List, Optional, Tuple, Any

from ..core.interfaces import BaseDetector
from ..core.models import ObjectCategory
from ..logger import logger

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


# Standard COCO class mappings (Class ID -> (Class Label, Category))
COCO_MAPPINGS: Dict[int, Tuple[str, ObjectCategory]] = {
    0: ("person", ObjectCategory.PERSON),
    39: ("bottle", ObjectCategory.BEVERAGE),
    41: ("cup", ObjectCategory.BEVERAGE),
    43: ("knife", ObjectCategory.HAZARD),
    46: ("wine glass", ObjectCategory.BEVERAGE),
    67: ("cell phone", ObjectCategory.DEVICE),
    73: ("laptop", ObjectCategory.DEVICE),
}

# Category colors for bounding box overlays (BGR format)
CATEGORY_COLORS: Dict[ObjectCategory, Tuple[int, int, int]] = {
    ObjectCategory.PERSON: (255, 255, 0),     # Cyan
    ObjectCategory.BEVERAGE: (255, 119, 0),   # Ocean Blue
    ObjectCategory.HAZARD: (0, 0, 255),       # Crimson Red - ALERT
    ObjectCategory.DEVICE: (0, 255, 255),     # Yellow
}


class PersonDetector(BaseDetector):
    """
    Multi-class object detection suite supporting YOLO and MediaPipe.
    Implements BaseDetector abstract interface.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.35,
        use_yolo: bool = True,
        detect_objects: bool = True,
        model_name: str = "yolov8n.pt"
    ):
        self.confidence_threshold = confidence_threshold
        self.use_yolo = use_yolo and YOLO_AVAILABLE
        self.detect_objects = detect_objects and self.use_yolo
        self.model_name = model_name
        self.model = None
        self.mp_pose = None

        if self.use_yolo:
            self._init_yolo()
        elif MEDIAPIPE_AVAILABLE:
            self._init_mediapipe()
        else:
            logger.warning("Neither YOLO nor MediaPipe is available. Running in dummy detector mode.")

    def _init_yolo(self) -> None:
        """Initialize Ultralytics YOLO model."""
        try:
            self.model = YOLO(self.model_name)
            logger.success(f"YOLO initialized ({self.model_name}) with conf={self.confidence_threshold}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}. Falling back to MediaPipe.")
            self.use_yolo = False
            if MEDIAPIPE_AVAILABLE:
                self._init_mediapipe()

    def _init_mediapipe(self) -> None:
        """Initialize MediaPipe Pose detection."""
        try:
            self.mp_pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=self.confidence_threshold
            )
            logger.success("MediaPipe Pose initialized (people-only mode)")
        except Exception as e:
            logger.error(f"Failed to load MediaPipe Pose: {e}")

    def detect(self, frame) -> Dict[str, Any]:
        """
        Execute detection on frame.

        Returns:
            Dictionary with category lists and specific counts:
            {
                'people': [(x1, y1, x2, y2, conf), ...],
                'beverages': [(x1, y1, x2, y2, conf, label), ...],
                'hazards': [...],
                'devices': [...],
                'counts': {'person': n, 'bottle': n, 'wine glass': n, ...}
            }
        """
        results: Dict[str, Any] = {
            "people": [],
            "beverages": [],
            "hazards": [],
            "devices": [],
            "counts": {}
        }

        if frame is None:
            return results

        if self.use_yolo and self.model is not None:
            return self._detect_yolo(frame)
        elif self.mp_pose is not None:
            return self._detect_mediapipe(frame)

        return results

    def _detect_yolo(self, frame) -> Dict[str, Any]:
        """Inference with YOLO."""
        res = {
            "people": [],
            "beverages": [],
            "hazards": [],
            "devices": [],
            "counts": {}
        }

        # Run inference
        predictions = self.model(frame, conf=self.confidence_threshold, verbose=False)
        if not predictions:
            return res

        boxes = predictions[0].boxes
        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            coords = tuple(map(int, box.xyxy[0].tolist()))

            if cls_id in COCO_MAPPINGS:
                label, category = COCO_MAPPINGS[cls_id]
                res["counts"][label] = res["counts"].get(label, 0) + 1

                item = (coords[0], coords[1], coords[2], coords[3], conf, label)
                if category == ObjectCategory.PERSON:
                    res["people"].append((coords[0], coords[1], coords[2], coords[3], conf))
                elif category == ObjectCategory.BEVERAGE and self.detect_objects:
                    res["beverages"].append(item)
                elif category == ObjectCategory.HAZARD and self.detect_objects:
                    res["hazards"].append(item)
                elif category == ObjectCategory.DEVICE and self.detect_objects:
                    res["devices"].append(item)

        return res

    def _detect_mediapipe(self, frame) -> Dict[str, Any]:
        """Inference with MediaPipe Pose."""
        import cv2
        res = {
            "people": [],
            "beverages": [],
            "hazards": [],
            "devices": [],
            "counts": {}
        }

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pose_results = self.mp_pose.process(rgb_frame)

        if pose_results and pose_results.pose_landmarks:
            h, w = frame.shape[:2]
            landmarks = pose_results.pose_landmarks.landmark
            xs = [int(lm.x * w) for lm in landmarks if lm.visibility > self.confidence_threshold]
            ys = [int(lm.y * h) for lm in landmarks if lm.visibility > self.confidence_threshold]

            if xs and ys:
                x1, x2 = max(0, min(xs)), min(w, max(xs))
                y1, y2 = max(0, min(ys)), min(h, max(ys))
                res["people"].append((x1, y1, x2, y2, 0.9))
                res["counts"]["person"] = 1

        return res

    def draw_boxes(self, frame, detections: Dict[str, Any]) -> None:
        """Render colored bounding boxes and labels onto frame."""
        import cv2

        # Draw people
        for person in detections.get("people", []):
            x1, y1, x2, y2, conf = person[:5]
            color = CATEGORY_COLORS[ObjectCategory.PERSON]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"Person {conf:.2f}", (x1, max(20, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Draw other categories
        for cat, items in [("beverages", detections.get("beverages", [])),
                          ("hazards", detections.get("hazards", [])),
                          ("devices", detections.get("devices", []))]:
            for item in items:
                x1, y1, x2, y2, conf, label = item
                color = CATEGORY_COLORS[ObjectCategory.HAZARD if cat == "hazards" else (
                    ObjectCategory.BEVERAGE if cat == "beverages" else ObjectCategory.DEVICE)]
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, max(20, y1 - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
