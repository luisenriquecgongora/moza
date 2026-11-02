"""
Unit tests for Moza AnalyticsEngine
"""

import os
import tempfile
import pytest
from moza.analytics.engine import AnalyticsEngine


def test_analytics_logging_and_metrics():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_metrics.db")
        engine = AnalyticsEngine(db_path=db_path, window_minutes=5)

        # Log detections
        engine.log_detection(
            zone_id="bar",
            person_count=12,
            object_counts={"bottle": 4, "wine glass": 3, "knife": 0},
            broken_glass=False
        )

        metrics = engine.get_current_metrics("bar")
        assert metrics["current_count"] == 12
        assert metrics["bottle_count"] == 4
        assert metrics["wine_glass_count"] == 3
        assert metrics["total_beverages"] == 7
        assert metrics["broken_glass_detected"] is False
        assert metrics["trend"] == "stable"


def test_analytics_broken_glass_alert():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_metrics.db")
        engine = AnalyticsEngine(db_path=db_path, window_minutes=5)

        engine.log_detection(
            zone_id="dance_floor",
            person_count=45,
            object_counts={"bottle": 2},
            broken_glass=True
        )

        metrics = engine.get_current_metrics("dance_floor")
        assert metrics["current_count"] == 45
        assert metrics["broken_glass_detected"] is True
        assert metrics["total_hazards"] == 1
