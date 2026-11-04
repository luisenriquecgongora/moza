"""Rule actions reach the executor, and webhooks never block the vision loop."""

import threading
import time

from moza.actions import executor as executor_module
from moza.actions.executor import ActionExecutor
from moza.rules.decision_engine import DecisionEngine
from services.moza_server.main import register_action_handlers


def test_webhook_is_sent_off_the_calling_thread(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    sent = []

    def slow_post(self, payload):
        started.set()
        release.wait(5)
        sent.append(payload)

    monkeypatch.setattr(ActionExecutor, "_post_webhook", slow_post)
    ex = ActionExecutor(webhook_url="https://hooks.example/alert")
    t0 = time.monotonic()
    ex.send_alert("BROKEN_GLASS_ALERT", {"zone_id": "main"})
    assert time.monotonic() - t0 < 0.5
    assert started.wait(2)
    release.set()
    for _ in range(50):
        if sent:
            break
        time.sleep(0.02)
    assert sent[0]["alert"] == "BROKEN_GLASS_ALERT"


def test_non_http_webhook_url_is_refused(monkeypatch):
    calls = []
    monkeypatch.setattr(executor_module.threading, "Thread", lambda *a, **k: calls.append(k))
    ActionExecutor(webhook_url="file:///etc/passwd").send_alert("X", {})
    assert calls == []


def test_server_routes_rule_actions_to_executor(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(
        '{"rules": [{"id": "glass", "condition": "shatter_detected", "cooldown_seconds": 0,'
        ' "actions": ["send_alert:BROKEN_GLASS_ALERT", "notify_staff:clean", "log_event:hazard"]}]}',
        encoding="utf-8",
    )
    engine = DecisionEngine(rules_config_paths=[str(path)])
    calls = []

    class Recorder(ActionExecutor):
        def dispatch(self, action_type, params, context):
            calls.append((action_type, params))

    register_action_handlers(engine, Recorder())
    engine.evaluate({"shatter_detected": True})
    assert calls == [("send_alert", "BROKEN_GLASS_ALERT"), ("notify_staff", "clean"), ("log_event", "hazard")]
