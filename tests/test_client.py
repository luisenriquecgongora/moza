"""
Unit tests for MozaClient data parsing
"""

from moza_client.client import MozaTelemetry


def test_telemetry_instantiation():
    t = MozaTelemetry(
        status="running",
        people_count=18,
        bottle_count=5,
        wine_glass_count=4,
        total_beverages=9,
        knife_count=0,
        total_hazards=0,
        broken_glass=False,
        trend="increasing",
        timestamp=1700000000.0
    )

    assert t.people_count == 18
    assert t.total_beverages == 9
    assert t.broken_glass is False
    assert t.trend == "increasing"
