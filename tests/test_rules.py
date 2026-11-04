"""
Unit tests for Argus DecisionEngine
"""

import json
from pathlib import Path
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


CONFIGS_DIR = Path(__file__).parent.parent / "configs" / "rules"
DISABLED_UNTIL_DETECTOR = {"slip_fall_incident", "abandoned_cocktail_glasses"}


def test_every_shipped_rule_loads():
    """A rule using a value the server does not provide would never fire; catch it here."""
    engine = DecisionEngine(rules_config_paths=[str(p) for p in sorted(CONFIGS_DIR.glob("*.json"))])
    assert set(engine.skipped_rules) == DISABLED_UNTIL_DETECTOR
    assert all(reason == "disabled" for reason in engine.skipped_rules.values())


def _engine_with(tmp_path, rules):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"rules": rules}), encoding="utf-8")
    return DecisionEngine(rules_config_paths=[str(path)])


def test_rule_with_unknown_name_is_skipped(tmp_path):
    engine = _engine_with(tmp_path, [
        {"id": "typo", "condition": "persn_count > 1", "actions": []},
        {"id": "ok", "condition": "person_count > 1 and trend == 'increasing'", "actions": []},
    ])
    assert [r.id for r in engine.rules] == ["ok"]
    assert "persn_count" in engine.skipped_rules["typo"]


def test_disabled_and_invalid_rules_are_skipped(tmp_path):
    engine = _engine_with(tmp_path, [
        {"id": "off", "condition": "person_count > 1", "enabled": False, "actions": []},
        {"id": "broken", "condition": "person_count >", "actions": []},
    ])
    assert engine.rules == []
    assert engine.skipped_rules["off"] == "disabled"
    assert engine.skipped_rules["broken"].startswith("invalid condition")


def test_hour_rule_fires_only_late(tmp_path):
    engine = _engine_with(tmp_path, [
        {"id": "late", "condition": "person_count < 5 and hour >= 23", "cooldown_seconds": 0, "actions": ["log_event:late"]},
    ])
    assert engine.evaluate({"person_count": 2, "hour": 22}) == []
    assert engine.evaluate({"person_count": 2, "hour": 23}) == ["late:log_event:late"]


def test_eval_builtins_are_not_reachable(tmp_path):
    """Conditions run in simpleeval, never Python eval."""
    engine = _engine_with(tmp_path, [
        {"id": "x", "condition": "person_count.__class__ == 1", "cooldown_seconds": 0, "actions": ["log_event:x"]},
    ])
    assert engine.evaluate({"person_count": 1}) == []
