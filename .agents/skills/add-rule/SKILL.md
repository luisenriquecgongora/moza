---
name: add-rule
description: Add or change a Moza decision rule (a JSON condition plus actions such as alerts) in configs/rules, or add an action handler. Use when asked to alert, notify or log when the venue reaches some condition (crowding, broken glass, knives, trends).
---

# Add or change a decision rule

Rules are JSON, evaluated by `DecisionEngine` (`src/moza/rules/decision_engine.py`) on every processed
frame of the **server** loop (`background_vision_worker` in `services/moza_server/main.py`).
The standalone CLI does not run rules.

## Rule format (`configs/rules/*.json`)

```json
{
  "id": "crowd_over_capacity",
  "description": "More than 40 people in the main zone",
  "condition": "person_count > 40",
  "priority": 8,
  "cooldown_seconds": 60,
  "actions": ["send_alert:CROWD_ALERT", "log_event:over_capacity"]
}
```

- `condition` is an expression evaluated with `simpleeval` against the context dict.
- `actions` are `"<type>:<params>"`; each is dispatched to the handler registered for `<type>`.
- `cooldown_seconds` stops a rule from firing again for that long after it triggers.
- `"enabled": false` (with a `disabled_reason`) keeps a rule in the file without loading it, e.g. until a
  detector provides the value it needs.

## Context keys a condition can use

Only what the server puts in `context` before `decision_engine.evaluate(context)`:
`person_count`, `bottle_count`, `wine_glass_count`, `knife_count`, `shatter_detected`,
`broken_glass_count`, `zone_id` (always `"main"` for now), `trend`, `hour`, `total_beverages`,
`glass_count`. They are listed in `CONTEXT_KEYS` in `decision_engine.py`.

A rule using any other name is skipped when loaded, with a warning, and `tests/test_rules.py` fails for
shipped rules. To use a new value, add it to the server context **and** to `CONTEXT_KEYS` (see the
`add-detector` skill).

## Actions

The server routes `send_alert`, `notify_staff` and `log_event` to `ActionExecutor`
(`src/moza/actions/executor.py`), which logs them and posts JSON to `MOZA_WEBHOOK_URL` when set (in a
background thread, so the vision loop never waits). Other action types (`api_update`, `overlay_update`,
`playlist_control`) have no handler and only reach the debug log. A new type needs a branch in
`ActionExecutor.dispatch` and its name in `ACTION_TYPES` in `services/moza_server/main.py`.
Handlers that call out must never send frames or images.

## New rule files

`DecisionEngine` loads a fixed list: `configs/rules/crowd_density.json` and `configs/rules/bar_safety.json`,
relative to the working directory. A new file must be added to that default list.

## Rules for rules

- Never evaluate conditions with Python `eval`; they run in `simpleeval`, a required dependency.
- Add a test in `tests/test_rules.py` with a context that should and one that should not trigger the rule.

## Done when

`python scripts/verify.py` passes.
