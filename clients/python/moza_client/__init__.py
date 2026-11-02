"""
Moza Featherweight Client SDK
Lightweight integration library with ZERO heavy computer vision dependencies.
"""

from .client import MozaClient, MozaTelemetry
from .reporter import OccupancyReporter

__all__ = [
    "MozaClient",
    "MozaTelemetry",
    "OccupancyReporter",
]
