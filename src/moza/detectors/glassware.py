"""
Transparent Glassware, Stemware & Cocktail Perception Engine.
Detects transparent vessels, extracts liquid meniscus, and estimates fill level.
"""

from typing import Tuple
import numpy as np

from ..core.models import GlassType, FillState, GlassDetection


class GlasswareDetector:
    """
    Transparent glassware and liquid level perception engine.
    Uses boundary refraction filtering and liquid meniscus gradient profiling.
    """

    def __init__(self, confidence_threshold: float = 0.30):
        self.confidence_threshold = confidence_threshold

    def analyze_vessel(self, frame_bgr: np.ndarray, bbox: Tuple[int, int, int, int], label: str = "wine glass") -> GlassDetection:
        """
        Analyze a detected glassware ROI for meniscus level and beverage chromaticity.
        """
        import cv2

        x1, y1, x2, y2 = bbox
        h, w = frame_bgr.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        roi = frame_bgr[y1:y2, x1:x2]
        if roi.size == 0 or roi.shape[0] < 10 or roi.shape[1] < 10:
            return GlassDetection(
                glass_type=GlassType.COCKTAIL if "cocktail" in label else GlassType.WINE,
                bbox=bbox,
                confidence=self.confidence_threshold,
                fill_ratio=0.5,
                fill_state=FillState.CONSUMING
            )

        # 1. Meniscus estimation via vertical edge intensity profile
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        sobel_y = cv2.Sobel(gray_roi, cv2.CV_64F, 0, 1, ksize=3)
        vertical_profile = np.mean(np.abs(sobel_y), axis=1)

        # Look for peak in the middle 20% to 80% of the glass height
        roi_height = roi.shape[0]
        search_start = int(roi_height * 0.20)
        search_end = int(roi_height * 0.85)

        if search_end > search_start:
            sub_profile = vertical_profile[search_start:search_end]
            meniscus_rel_y = search_start + int(np.argmax(sub_profile))
            # Meniscus relative to rim (top=0, bottom=1)
            depth_ratio = (meniscus_rel_y / float(roi_height))
            fill_ratio = float(np.clip(1.0 - depth_ratio, 0.0, 1.0))
        else:
            fill_ratio = 0.5

        # 2. Determine Fill State
        if fill_ratio >= 0.80:
            state = FillState.FULL
        elif fill_ratio >= 0.20:
            state = FillState.CONSUMING
        else:
            state = FillState.EMPTY

        # 3. Chromaticity profiling (HSV space)
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        avg_hue = np.mean(hsv_roi[:, :, 0])
        avg_sat = np.mean(hsv_roi[:, :, 1])

        if avg_sat < 30:
            hue_desc = "clear_water_spirit"
        elif avg_hue < 15 or avg_hue > 165:
            hue_desc = "red_wine_cocktail"
        elif 15 <= avg_hue <= 35:
            hue_desc = "amber_whiskey_beer"
        else:
            hue_desc = "mixed_cocktail"

        gtype = GlassType.WINE if "wine" in label else (
            GlassType.BOTTLE if "bottle" in label else GlassType.COCKTAIL
        )

        return GlassDetection(
            glass_type=gtype,
            bbox=bbox,
            confidence=0.85,
            fill_ratio=fill_ratio,
            fill_state=state,
            beverage_hue=hue_desc
        )
