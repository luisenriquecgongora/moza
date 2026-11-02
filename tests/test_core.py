"""
Unit tests for Moza Core interfaces, models, and SOLID contracts
"""

import numpy as np
import pytest
from moza.core.models import (
    BoundingBox,
    ObjectCategory,
    DetectionResult,
    MozaTelemetry,
)
from moza.core.interfaces import BaseDetector, BaseFrameSource


class DummyMockDetector(BaseDetector):
    """Verifies that custom detectors can implement BaseDetector without modification."""
    def detect(self, frame: np.ndarray):
        return {
            "people": [(10, 10, 50, 100, 0.95)],
            "beverages": [],
            "hazards": [],
            "devices": [],
            "counts": {"person": 1}
        }


def test_bounding_box_geometry():
    bbox = BoundingBox(
        x1=10, y1=20, x2=50, y2=80,
        confidence=0.88, label="wine glass",
        category=ObjectCategory.BEVERAGE
    )
    assert bbox.width == 40
    assert bbox.height == 60
    assert bbox.center == (30, 50)
    assert bbox.as_tuple() == (10, 20, 50, 80, 0.88, "wine glass")


def test_custom_detector_liskov_substitution():
    detector: BaseDetector = DummyMockDetector()
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    res = detector.detect(frame)
    assert len(res["people"]) == 1
    assert res["counts"]["person"] == 1


def test_telemetry_serialization():
    t = MozaTelemetry(
        status="running",
        people_count=15,
        bottle_count=3,
        wine_glass_count=2,
        total_beverages=5,
        knife_count=0,
        total_hazards=0,
        broken_glass=False,
        trend="stable",
        avg_count=14.2
    )
    d = t.to_dict()
    assert d["people_count"] == 15
    assert d["total_beverages"] == 5
    assert d["avg_count"] == 14.2
