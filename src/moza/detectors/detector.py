"""
Multi-class object detection using YOLOX (ONNX Runtime) or MediaPipe.
Detects people, beverages (bottles, cups, wine glasses), hazards (knives), and devices.

YOLOX (https://github.com/Megvii-BaseDetection/YOLOX) is licensed under Apache-2.0
and runs here through ONNX Runtime (MIT). No AGPL code or weights are used.
"""

import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np

from ..core.interfaces import BaseDetector
from ..core.models import ObjectCategory
from ..logger import logger

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

try:
    import onnxruntime as ort
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# Official Apache-2.0 YOLOX ONNX exports (COCO, 80 classes)
YOLOX_RELEASE_URL = "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/{name}"
DEFAULT_MODEL_NAME = os.environ.get("MOZA_MODEL", "yolox_s.onnx")
DEFAULT_MODEL_DIR = Path(os.environ.get("MOZA_MODEL_DIR", "models"))
NMS_IOU_THRESHOLD = 0.45


def ensure_model(model_name: str = DEFAULT_MODEL_NAME, model_dir: Path = DEFAULT_MODEL_DIR) -> Path:
    """Return a local path to the YOLOX ONNX model, downloading it on first use."""
    path = Path(model_name)
    if path.is_file():
        return path
    path = Path(model_dir) / path.name
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        url = YOLOX_RELEASE_URL.format(name=path.name)
        logger.info(f"Downloading YOLOX model {path.name} from {url}")
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(path)
    return path


class YoloxOnnx:
    """Minimal YOLOX inference wrapper on ONNX Runtime (mirrors the official YOLOX ONNX demo)."""

    def __init__(self, model_path: Path):
        providers = [p for p in ("CUDAExecutionProvider", "DmlExecutionProvider", "CPUExecutionProvider")
                     if p in ort.get_available_providers()]
        self.session = ort.InferenceSession(str(model_path), providers=providers)
        inp = self.session.get_inputs()[0]
        self.input_name = inp.name
        self.input_h, self.input_w = int(inp.shape[2]), int(inp.shape[3])
        self.grids, self.strides = self._make_grids(self.input_h, self.input_w)

    @staticmethod
    def _make_grids(h: int, w: int, strides=(8, 16, 32)) -> Tuple[np.ndarray, np.ndarray]:
        grids, expanded = [], []
        for s in strides:
            hs, ws = h // s, w // s
            xv, yv = np.meshgrid(np.arange(ws), np.arange(hs))
            grid = np.stack((xv, yv), 2).reshape(-1, 2)
            grids.append(grid)
            expanded.append(np.full((grid.shape[0], 1), s))
        return np.concatenate(grids).astype(np.float32), np.concatenate(expanded).astype(np.float32)

    def _preprocess(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        import cv2
        h, w = frame.shape[:2]
        ratio = min(self.input_h / h, self.input_w / w)
        resized = cv2.resize(frame, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_LINEAR)
        padded = np.full((self.input_h, self.input_w, 3), 114, dtype=np.uint8)
        padded[: resized.shape[0], : resized.shape[1]] = resized
        blob = padded.transpose(2, 0, 1)[None].astype(np.float32)
        return np.ascontiguousarray(blob), ratio

    def __call__(self, frame: np.ndarray, conf: float) -> List[Tuple[Tuple[int, int, int, int], float, int]]:
        """Run inference. Returns [((x1, y1, x2, y2), score, class_id), ...] in frame coordinates."""
        import cv2
        blob, ratio = self._preprocess(frame)
        out = self.session.run(None, {self.input_name: blob})[0][0]

        xy = (out[:, :2] + self.grids) * self.strides
        wh = np.exp(out[:, 2:4]) * self.strides
        cls_scores = out[:, 5:] * out[:, 4:5]
        cls_ids = cls_scores.argmax(1)
        scores = cls_scores[np.arange(len(cls_ids)), cls_ids]

        keep = scores >= conf
        if not keep.any():
            return []
        xy, wh, scores, cls_ids = xy[keep] / ratio, wh[keep] / ratio, scores[keep], cls_ids[keep]
        boxes_xywh = np.concatenate([xy - wh / 2, wh], axis=1)

        h, w = frame.shape[:2]
        detections = []
        for cid in np.unique(cls_ids):
            idx = np.where(cls_ids == cid)[0]
            kept = cv2.dnn.NMSBoxes(boxes_xywh[idx].tolist(), scores[idx].tolist(), conf, NMS_IOU_THRESHOLD)
            for k in np.array(kept).flatten():
                i = idx[int(k)]
                x, y, bw, bh = boxes_xywh[i]
                x1, y1 = max(0, int(x)), max(0, int(y))
                x2, y2 = min(w, int(x + bw)), min(h, int(y + bh))
                detections.append(((x1, y1, x2, y2), float(scores[i]), int(cid)))
        return detections


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
    Multi-class object detection suite supporting YOLOX (ONNX Runtime) and MediaPipe.
    Implements BaseDetector abstract interface.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.35,
        use_yolo: bool = True,
        detect_objects: bool = True,
        model_name: str = DEFAULT_MODEL_NAME
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
        """Initialize YOLOX ONNX model (Apache-2.0)."""
        try:
            self.model = YoloxOnnx(ensure_model(self.model_name))
            logger.success(f"YOLOX initialized ({self.model_name}) with conf={self.confidence_threshold}")
        except Exception as e:
            logger.error(f"Failed to load YOLOX model: {e}. Falling back to MediaPipe.")
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
        """Inference with YOLOX."""
        res = {
            "people": [],
            "beverages": [],
            "hazards": [],
            "devices": [],
            "counts": {}
        }

        # Run inference
        for coords, conf, cls_id in self.model(frame, conf=self.confidence_threshold):
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
