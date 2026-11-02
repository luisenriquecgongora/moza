"""
Moza Core Domain Models.
Centralizes data transfer objects, typed telemetry contracts, and categories.
Ensures DRY (Don't Repeat Yourself) across perception, analytics, server, and client.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import time


class ObjectCategory(str, Enum):
    """Detection category classifications."""
    PERSON = "person"
    BEVERAGE = "beverage"
    HAZARD = "hazard"
    DEVICE = "device"


class GlassType(str, Enum):
    """Glassware vessel classifications."""
    COCKTAIL = "cocktail_glass"
    WINE = "wine_glass"
    TUMBLER = "tumbler"
    PINT = "pint_glass"
    BOTTLE = "bottle"


class FillState(str, Enum):
    """Liquid consumption levels."""
    FULL = "full"            # 80 - 100%
    CONSUMING = "consuming"  # 20 - 79%
    EMPTY = "empty"          # < 20%
    ABANDONED = "abandoned"  # Idle for > 15 minutes


@dataclass(frozen=True)
class BoundingBox:
    """Immutable 2D bounding box coordinates."""
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    label: str
    category: ObjectCategory

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    @property
    def center(self) -> Tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def as_tuple(self) -> Tuple[int, int, int, int, float, str]:
        return (self.x1, self.y1, self.x2, self.y2, self.confidence, self.label)


@dataclass
class DetectionResult:
    """Standardized output container from any BaseDetector."""
    people: List[Tuple[int, int, int, int, float]] = field(default_factory=list)
    beverages: List[Tuple[int, int, int, int, float, str]] = field(default_factory=list)
    hazards: List[Tuple[int, int, int, int, float, str]] = field(default_factory=list)
    devices: List[Tuple[int, int, int, int, float, str]] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)

    @property
    def person_count(self) -> int:
        return len(self.people)

    @property
    def beverage_count(self) -> int:
        return len(self.beverages)

    @property
    def hazard_count(self) -> int:
        return len(self.hazards)


@dataclass
class GlassDetection:
    """Glassware instance detection with volumetric state."""
    glass_type: GlassType
    bbox: Tuple[int, int, int, int]
    confidence: float
    fill_ratio: float               # 0.0 to 1.0
    fill_state: FillState
    beverage_hue: Optional[str] = None


@dataclass
class ShatterEvent:
    """Broken glass fracture incident data."""
    detected: bool
    confidence: float
    acoustic_score: float
    visual_score: float
    zone_id: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class MozaTelemetry:
    """
    Authoritative telemetry contract shared across server, client, and analytics.
    Single Source of Truth for live venue state.
    """
    status: str
    people_count: int
    bottle_count: int
    wine_glass_count: int
    total_beverages: int
    knife_count: int
    total_hazards: int
    broken_glass: bool
    trend: str = "stable"
    avg_count: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "people_count": self.people_count,
            "bottle_count": self.bottle_count,
            "wine_glass_count": self.wine_glass_count,
            "total_beverages": self.total_beverages,
            "knife_count": self.knife_count,
            "total_hazards": self.total_hazards,
            "broken_glass": self.broken_glass,
            "trend": self.trend,
            "avg_count": self.avg_count,
            "timestamp": self.timestamp
        }
