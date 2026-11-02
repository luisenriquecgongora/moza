"""
Unit tests for Argus DecisionEngine
"""

from pathlib import Path
import pytest
from moza.rules.decision_engine import DecisionEngine


def test_decision_engine_rules():
    configs_dir = Path(__file__).parent.parent / "configs" / "rules"
    engine = DecisionEngine(rules_config_paths=[
        str(configs_dir / "crowd_density.json"),
        str(configs_dir / "bar_safety.json")
    ])

    triggered_alerts = []
    def alert_handler(params, ctx):
        triggered_alerts.append(params)

    engine.register_action_handler("send_alert", alert_handler)

    # Test broken glass alert
    context = {
        "shatter_detected": True,
        "broken_glass_count": 1,
        "fall_detected": False,
        "knife_count": 0,
        "glass_count": 5,
        "empty_glass_count": 0,
        "person_count": 20,
        "zone_id": "bar",
        "trend": "stable",
        "hour": 23,
        "bottle_count": 2,
        "cup_count": 1,
        "wine_glass_count": 3,
        "total_beverages": 6,
        "total_hazards": 1,
        "phone_count": 2
    }

    triggered = engine.evaluate(context)
    assert any("broken_glass" in t for t in triggered)
    assert "BROKEN_GLASS_ALERT" in triggered_alerts
