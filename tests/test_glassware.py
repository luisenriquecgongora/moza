"""
Unit tests for GlasswareDetector and fill-level logic
"""

import numpy as np
import pytest
from moza.detectors.glassware import GlasswareDetector, FillState, GlassType


def test_glassware_detector_synthetic_roi():
    detector = GlasswareDetector()

    # Synthetic ROI: 100x50 BGR image
    # Top 30% background (dark), bottom 70% liquid (amber/whiskey)
    roi_full = np.zeros((100, 50, 3), dtype=np.uint8)
    roi_full[30:, :] = [20, 150, 220]  # Amber / orange liquid

    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[50:150, 50:100] = roi_full

    detection = detector.analyze_vessel(frame, (50, 50, 100, 150), label="cocktail_glass")

    assert detection.confidence > 0.0
    assert detection.fill_ratio > 0.0
    assert detection.fill_state in [FillState.FULL, FillState.CONSUMING]
