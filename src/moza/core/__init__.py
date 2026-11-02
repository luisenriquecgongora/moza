"""
Moza Core Package: Models and Interfaces
"""

from .models import (
    ObjectCategory,
    GlassType,
    FillState,
    BoundingBox,
    DetectionResult,
    GlassDetection,
    ShatterEvent,
    MozaTelemetry,
)
from .interfaces import (
    BaseFrameSource,
    BaseDetector,
    BaseActionChannel,
    BaseMetricsSink,
)

__all__ = [
    "ObjectCategory",
    "GlassType",
    "FillState",
    "BoundingBox",
    "DetectionResult",
    "GlassDetection",
    "ShatterEvent",
    "MozaTelemetry",
    "BaseFrameSource",
    "BaseDetector",
    "BaseActionChannel",
    "BaseMetricsSink",
]
