"""
Action Executor: Dispatches automated actions triggered by DecisionEngine.
Handles webhooks, staff alerts, and third-party system integrations.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import urllib.request

from ..core.interfaces import BaseActionChannel
from ..logger import logger


class ActionExecutor(BaseActionChannel):
    """
    Executes automated actions triggered by decision rules.
    Implements BaseActionChannel interface.
    """

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self.action_history = []

    def dispatch(self, action_type: str, params: str, context: Dict[str, Any]) -> None:
        """Route action to appropriate handler method."""
        if action_type == "notify_staff":
            self.notify_staff(params, context)
        elif action_type == "send_alert":
            self.send_alert(params, context)
        else:
            self.log_event(f"{action_type}:{params}", context)

    def notify_staff(self, params: str, context: Dict[str, Any]) -> None:
        """Send operational alert to staff via webhook or log."""
        payload = {
            "type": "staff_alert",
            "message": params,
            "zone": context.get("zone_id", "main"),
            "person_count": context.get("person_count", 0),
            "timestamp": datetime.now().isoformat()
        }
        logger.warning(f"📢 STAFF ALERT: {params} | Zone: {payload['zone']} | Count: {payload['person_count']}")
        self._send_webhook(payload)

    def send_alert(self, params: str, context: Dict[str, Any]) -> None:
        """High-priority safety alert (broken glass, slip/fall, security hazard)."""
        payload = {
            "type": "emergency_alert",
            "alert": params,
            "zone": context.get("zone_id", "main"),
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"🚨 CRITICAL ALERT: {params} | Zone: {payload['zone']}")
        self._send_webhook(payload)

    def log_event(self, params: str, context: Dict[str, Any]) -> None:
        """Log event for telemetry history."""
        logger.info(f"📝 Telemetry Event: {params} in zone {context.get('zone_id')}")

    def _send_webhook(self, payload: Dict[str, Any]) -> None:
        """Post payload to webhook URL if configured."""
        if not self.webhook_url:
            return

        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                pass
        except Exception as e:
            logger.debug(f"Webhook dispatch failed: {e}")
