"""
Rule-based decision engine with priority queue and cooldown.
Evaluates conditions safely and dispatches actions without spam.
"""

import ast
import json
import os
from typing import List, Dict, Callable, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from simpleeval import SimpleEval

from ..logger import logger

# Names the server puts in the context it evaluates rules against
# (background_vision_worker in services/moza_server/main.py). Keep the two in sync.
CONTEXT_KEYS = frozenset({
    "person_count", "bottle_count", "wine_glass_count", "knife_count",
    "shatter_detected", "broken_glass_count", "zone_id", "trend",
})
_LITERAL_NAMES = {"True", "False", "None"}


def condition_names(condition: str) -> set:
    """Variable names a rule condition reads."""
    tree = ast.parse(condition, mode="eval")
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} - _LITERAL_NAMES


@dataclass
class Rule:
    """Rule definition with priority and cooldown."""
    id: str
    condition: str
    actions: List[str]
    priority: int = 1
    cooldown_seconds: int = 300


class DecisionEngine:
    """
    Rule-based operational decision engine.
    Evaluates venue conditions against JSON rulesets.
    """

    def __init__(self, rules_config_paths: Optional[List[str]] = None, known_names=CONTEXT_KEYS):
        self.rules_config_paths = rules_config_paths or ["configs/rules/crowd_density.json", "configs/rules/bar_safety.json"]
        self.known_names = frozenset(known_names)
        self.skipped_rules: Dict[str, str] = {}
        self.rules: List[Rule] = []
        self.action_handlers: Dict[str, Callable] = {}
        self.last_triggered: Dict[str, datetime] = {}
        self.evaluator = SimpleEval()

        self._load_all_rules()

    def _load_all_rules(self) -> None:
        """Load rules from all configured paths."""
        self.rules = []
        for path in self.rules_config_paths:
            if os.path.exists(path):
                self._load_rules_file(path)
            else:
                logger.debug(f"Rule file not found (skipped): {path}")

        # Sort by priority (highest priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"Loaded {len(self.rules)} active rules into DecisionEngine")

    def _load_rules_file(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for r in data.get("rules", []):
                reason = self._skip_reason(r)
                if reason:
                    self.skipped_rules[r["id"]] = reason
                    logger.warning(f"Rule [{r['id']}] skipped: {reason}")
                    continue
                self.rules.append(Rule(
                    id=r["id"],
                    condition=r["condition"],
                    actions=r.get("actions", []),
                    priority=r.get("priority", 1),
                    cooldown_seconds=r.get("cooldown_seconds", 300)
                ))
        except Exception as e:
            logger.error(f"Error loading rule file {path}: {e}")

    def _skip_reason(self, rule: Dict[str, Any]) -> Optional[str]:
        """Why a rule cannot run (disabled, unparsable, or reads names the context lacks), else None."""
        if rule.get("enabled", True) is False:
            return "disabled"
        try:
            names = condition_names(rule["condition"])
        except SyntaxError as e:
            return f"invalid condition: {e.msg}"
        unknown = sorted(names - self.known_names)
        if unknown:
            return f"uses values the server does not provide: {', '.join(unknown)}"
        return None

    def register_action_handler(self, action_type: str, handler: Callable) -> None:
        """Register callback for action prefix (e.g., 'notify_staff', 'send_alert')."""
        self.action_handlers[action_type] = handler

    def evaluate(self, context: Dict[str, Any]) -> List[str]:
        """
        Evaluate context against all rules.
        Dispatches matched actions if cooled down.
        Returns list of triggered action identifiers.
        """
        triggered_actions = []
        now = datetime.now()

        # Update evaluator variables
        self.evaluator.names = context

        for rule in self.rules:
            # Check cooldown
            last_time = self.last_triggered.get(rule.id)
            if last_time and (now - last_time).total_seconds() < rule.cooldown_seconds:
                continue

            try:
                result = self.evaluator.eval(rule.condition)
                if result:
                    self.last_triggered[rule.id] = now
                    logger.info(f"⚡ Rule Triggered: [{rule.id}] (Priority {rule.priority})")

                    for action_str in rule.actions:
                        triggered_actions.append(f"{rule.id}:{action_str}")
                        self._dispatch_action(action_str, context)
            except Exception as e:
                logger.error(f"Failed to evaluate rule [{rule.id}]: {e}")

        return triggered_actions

    def _dispatch_action(self, action_str: str, context: Dict[str, Any]) -> None:
        """Dispatch action string (e.g. 'send_alert:BROKEN_GLASS_ALERT') to registered handler."""
        parts = action_str.split(":", 1)
        action_type = parts[0]
        params = parts[1] if len(parts) > 1 else ""

        handler = self.action_handlers.get(action_type)
        if handler:
            try:
                handler(params, context)
            except Exception as e:
                logger.error(f"Action handler error for {action_type}: {e}")
        else:
            logger.debug(f"Action logged (no explicit handler): {action_str}")
