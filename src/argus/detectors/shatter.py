"""
Multimodal Broken Glass & Shatter Detection Engine.
Fuses high-frequency acoustic shockwave transients with optical specular shard scatter.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

from ..logger import logger


@dataclass
class ShatterEvent:
    """Broken glass incident data."""
    detected: bool
    confidence: float
    acoustic_score: float
    visual_score: float
    zone_id: str
    timestamp: float


class ShatterDetector:
    """
    Multimodal Broken Glass & Shatter Perception Engine.

    Theory:
    Brittle fractures release a distinctive acoustic impulse with an immediate rise-time (<2ms)
    concentrated between 3 kHz and 8 kHz, combined with visual high-frequency floor plane scatter.
    """

    def __init__(self, acoustic_weight: float = 0.55, visual_weight: float = 0.45, threshold: float = 0.65):
        self.acoustic_weight = acoustic_weight
        self.visual_weight = visual_weight
        self.threshold = threshold
        self.prev_frame_gray: Optional[np.ndarray] = None

    def evaluate_audio_frame(self, audio_chunk: np.ndarray, sample_rate: int = 44100) -> float:
        """
        Evaluate audio PCM chunk for brittle fracture frequency signature (3 kHz - 8 kHz).
        Returns acoustic shock score in range [0.0, 1.0].
        """
        if audio_chunk is None or len(audio_chunk) < 512:
            return 0.0

        try:
            from scipy.fft import rfft, rfftfreq
            fft_vals = np.abs(rfft(audio_chunk))
            freqs = rfftfreq(len(audio_chunk), 1.0 / sample_rate)

            # Mask frequencies between 3000 Hz and 8000 Hz
            shatter_band = (freqs >= 3000) & (freqs <= 8000)
            baseline_band = (freqs >= 200) & (freqs < 3000)

            shatter_energy = np.mean(fft_vals[shatter_band]) if np.any(shatter_band) else 0.0
            baseline_energy = np.mean(fft_vals[baseline_band]) if np.any(baseline_band) else 1e-5

            # Energy ratio with sigmoid normalization
            ratio = float(shatter_energy / (baseline_energy + 1e-4))
            score = 1.0 / (1.0 + np.exp(-(ratio - 2.5)))
            return float(np.clip(score, 0.0, 1.0))
        except Exception:
            return 0.0

    def evaluate_video_frame(self, frame_bgr: np.ndarray) -> float:
        """
        Evaluate visual frame difference and high-frequency specular glint scattering.
        Returns visual shatter score in range [0.0, 1.0].
        """
        import cv2

        if frame_bgr is None:
            return 0.0

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        if self.prev_frame_gray is None or self.prev_frame_gray.shape != gray.shape:
            self.prev_frame_gray = gray
            return 0.0

        # Frame difference
        diff = cv2.absdiff(self.prev_frame_gray, gray)
        self.prev_frame_gray = gray

        # Specular glint threshold (bright flash from reflections on scattering shards)
        _, thresh = cv2.threshold(diff, 60, 255, cv2.THRESH_BINARY)
        non_zero_ratio = float(np.count_nonzero(thresh) / (thresh.shape[0] * thresh.shape[1]))

        # High sudden delta localized to floor indicates sudden drop/shatter
        visual_score = float(np.clip(non_zero_ratio * 15.0, 0.0, 1.0))
        return visual_score

    def evaluate(
        self,
        frame_bgr: Optional[np.ndarray] = None,
        audio_chunk: Optional[np.ndarray] = None,
        sample_rate: int = 44100,
        zone_id: str = "main",
        timestamp: float = 0.0
    ) -> ShatterEvent:
        """
        Dual-modality evaluation fusion.
        """
        a_score = self.evaluate_audio_frame(audio_chunk, sample_rate) if audio_chunk is not None else 0.0
        v_score = self.evaluate_video_frame(frame_bgr) if frame_bgr is not None else 0.0

        # Late-fusion score
        if audio_chunk is not None and frame_bgr is not None:
            fusion_score = (self.acoustic_weight * a_score) + (self.visual_weight * v_score)
        elif frame_bgr is not None:
            fusion_score = v_score
        else:
            fusion_score = a_score

        is_shatter = bool(fusion_score >= self.threshold)
        if is_shatter:
            logger.warning(f"🚨 GLASS SHATTER DETECTED in '{zone_id}'! Conf={fusion_score:.2f} (Audio={a_score:.2f}, Visual={v_score:.2f})")

        return ShatterEvent(
            detected=is_shatter,
            confidence=fusion_score,
            acoustic_score=a_score,
            visual_score=v_score,
            zone_id=zone_id,
            timestamp=timestamp
        )
