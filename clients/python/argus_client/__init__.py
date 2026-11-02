"""
Argus Featherweight Client SDK
Lightweight integration library with ZERO heavy computer vision dependencies.
"""

from .client import ArgusClient, ArgusTelemetry
from .reporter import OccupancyReporter

__all__ = [
    "ArgusClient",
    "ArgusTelemetry",
    "OccupancyReporter",
]
