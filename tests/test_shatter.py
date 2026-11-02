"""
Unit tests for ShatterDetector
"""

import numpy as np
import pytest
from argus.detectors.shatter import ShatterDetector


def test_shatter_detector_audio_impulse():
    detector = ShatterDetector()

    # Generate synthetic 5000 Hz tone (within 3 kHz - 8 kHz fracture frequency band)
    sample_rate = 44100
    t = np.linspace(0, 0.1, int(sample_rate * 0.1), endpoint=False)
    high_freq_tone = (0.9 * np.sin(2 * np.pi * 5000 * t)).astype(np.float32)

    score_high = detector.evaluate_audio_frame(high_freq_tone, sample_rate)
    assert score_high > 0.0

    # Low frequency 100 Hz tone (outside fracture band)
    low_freq_tone = (0.9 * np.sin(2 * np.pi * 100 * t)).astype(np.float32)
    score_low = detector.evaluate_audio_frame(low_freq_tone, sample_rate)
    assert score_high > score_low


def test_shatter_detector_visual_delta():
    detector = ShatterDetector()

    frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
    frame2 = np.full((100, 100, 3), 200, dtype=np.uint8)

    # First frame initializes
    detector.evaluate_video_frame(frame1)
    # Sudden large brightness shift simulates scattered shard glint
    v_score = detector.evaluate_video_frame(frame2)
    assert v_score > 0.5
