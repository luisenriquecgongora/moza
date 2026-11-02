"""
Moza Core Interfaces and Protocols.
Defines abstract contracts enforcing SOLID principles:
- Interface Segregation Principle (ISP): Small, role-specific interfaces.
- Dependency Inversion Principle (DIP): High-level modules depend on abstractions.
- Open/Closed Principle (OCP): New detectors or channels extend without modifying existing code.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import numpy as np

from .models import DetectionResult, MozaTelemetry


class BaseFrameSource(ABC):
    """Abstract interface for video frame acquisition (cameras, RTSP, video files)."""

    @abstractmethod
    def start(self) -> None:
        """Initialize and start background acquisition."""
        pass

    @abstractmethod
    def get_frame(self, timeout: float = 0.5) -> Optional[np.ndarray]:
        """Retrieve most recent video frame."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Release underlying hardware or network stream."""
        pass


class BaseDetector(ABC):
    """Abstract interface for visual inference engines (YOLO, MediaPipe, ONNX, Mock)."""

    @abstractmethod
    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Execute object detection on a BGR video frame.

        Returns:
            Dictionary with category keys ('people', 'beverages', 'hazards', 'devices', 'counts')
        """
        pass


class BaseActionChannel(ABC):
    """Abstract interface for notification and alert sinks (Webhooks, MQTT, Slack, Overlays)."""

    @abstractmethod
    def dispatch(self, action_type: str, params: str, context: Dict[str, Any]) -> None:
        """Dispatch action to external sink."""
        pass


class BaseMetricsSink(ABC):
    """Abstract interface for time-series persistence (SQLite, DuckDB, TimescaleDB, Cloud)."""

    @abstractmethod
    def log_detection(
        self,
        zone_id: str,
        person_count: int,
        object_counts: Optional[Dict[str, int]] = None,
        broken_glass: bool = False
    ) -> None:
        pass

    @abstractmethod
    def get_current_metrics(self, zone_id: str) -> Dict[str, Any]:
        pass
