---
name: add-detector
description: Add a new visual or audio detector to Moza (people, objects, glassware, hazards, falls, sounds) or change an existing one, and wire it into the detection loop. Use when asked to detect something new in the camera or audio feed, or to change detection logic or thresholds.
---

# Add or change a detector

## Where things live

| What | Where |
|---|---|
| Interfaces to implement | `src/moza/core/interfaces.py` (`BaseDetector.detect(frame) -> Dict[str, Any]`) |
| Detectors | `src/moza/detectors/` (`detector.py` = `PersonDetector`, `glassware.py`, `shatter.py`) |
| Event models | `src/moza/core/models.py` |
| Loops that run detectors | `src/moza/cli.py` (standalone) and `background_vision_worker` in `services/moza_server/main.py` |
| Rules that react to results | `configs/rules/*.json` (see the `add-rule` skill) |

## Contract

- **Subclass `BaseDetector`** for frame detectors. `detect(frame)` takes a BGR `np.ndarray` and returns the
  category dict used by `PersonDetector`: `people`, `beverages`, `hazards`, `devices` as lists of
  `(x1, y1, x2, y2, conf[, label])`, plus `counts: {label: n}`. Return empty lists, never `None`.
- **Degrade, do not crash**: if an optional dependency (ONNX model, scipy, MediaPipe) is missing, log once
  and return empty results, like `ShatterDetector` does without scipy.
- **Models download on first use** into `models/` (gitignored, `MOZA_MODEL` / `MOZA_MODEL_DIR`).
  Tests must not depend on a model or a camera: build synthetic frames with numpy.
- **Privacy**: never write frames, crops or faces to disk from a detector; recording is the capture
  layer's job and is opt-in.
- Known debt: `GlasswareDetector` and `ShatterDetector` do not subclass the interfaces yet, and
  `GlasswareDetector` is constructed in `cli.py` but not called. Prefer fixing that over copying it.

## Wiring a new detector into the loops

Both loops must change together, or the CLI and the server behave differently:
1. Construct it next to `PersonDetector` in `cli.py` and in `background_vision_worker`.
2. Call it per frame in both loops.
3. Server only: add its results to the `context` dict passed to `decision_engine.evaluate(context)`
   (the CLI does not run rules). Rules can only use keys that appear in that dict.

## Tests

Add `tests/test_<detector>.py` with synthetic inputs that should and should not trigger it
(see `tests/test_shatter.py` and `tests/test_glassware.py`).

## Done when

`python scripts/verify.py` passes (ruff, tests, desktop typecheck).
