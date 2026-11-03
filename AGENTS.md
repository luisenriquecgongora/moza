# Engineering Standards & Observability Contract

### 1. Pre-Change Invariant Manifest
Before executing code modifications touching more than one file, output a compact change manifest table:

| Target File / Module | Nature of Change | Breaking / Invariant Impact |
| :--- | :--- | :--- |
| `path/to/file` | `[refactor / feat / fix / rename]` | `None / Exposes new method / Renames prop` |

Do not output narrative summaries, conversational setups, or ad-hoc diagrams.

### 2. Diff Noise & Spurious Edit Invariants
- **No Unsolicited Formatting:** Do NOT reformat, re-indent, or adjust comments on lines unrelated to your assigned task. Leave untouched code exactly as it is.
- **Import Hygiene:** Do not randomly shuffle or re-order existing import statements unless adding or removing an active dependency.
- **Isolate Mass Renames:** If a task requires renaming an identifier across multiple files, isolate that rename into a dedicated `refactor(<scope>): rename X to Y` commit with ZERO other logic changes.

### 3. Conventional Commit Standards
All commits must follow:
`<type>(<scope>): <short imperative subject under 50 chars>`

- **Allowed Types:** `feat`, `fix`, `refactor`, `perf`, `chore`, `test`, `docs`, `build`, `ci` (add `model`, `data`, `eval`, `exp` for ML pipelines).
- **Allowed Scopes:** [`core`, `capture`, `detectors`, `analytics`, `rules`, `audio`, `spatial`, `privacy`, `storage`, `server`, `client`, `config`, `deps`, `docs`, `tests`]
- **Rule:** Never mention AI, LLMs, or prompt tools in commit messages.

### 4. Commit Granularity & Invariants
- **Atomic Commits:** Do not bundle refactorings, feature code, and config tweaks into a single commit.
- **Commit Sequence:**
  1. `refactor(<scope>): ...` (Structural prep or renames only)
  2. `feat(<scope>): ...` or `fix(<scope>): ...` (Logic changes)
  3. `test(<scope>): ...` (Specs/tests)
- **Blast-Radius Cap:** A single commit must not exceed 5 staged files (excluding lockfiles/documentation).
- **Bisect Safety:** Every individual commit must compile and pass tests.

### 5. Definition of Done
- Run `python scripts/verify.py` before reporting a task complete. It runs exactly what CI runs: ruff, the test suite, the desktop typecheck, and a secret scan when `gitleaks` is installed. Skipped checks are listed; "NOT COMPLETE" means you are not done.
- Narrow it while iterating: `--only python`, `--only desktop`, `--only secrets`.
- Python: uses `.venv` when present, otherwise the current interpreter; set `VERIFY_PYTHON` to override (e.g. in a git worktree).
- A task that changes behavior adds or updates a test in `tests/`.

### 6. Repository Map
| Path | What lives there |
| :--- | :--- |
| `src/moza/core/` | `interfaces.py` (abstract `BaseFrameSource`, `BaseDetector`, `BaseActionChannel`, `BaseMetricsSink`) and `models.py` |
| `src/moza/capture/` | `CameraManager` (webcam, RTSP, file) and segment recorder |
| `src/moza/detectors/` | `PersonDetector` (YOLOX ONNX / MediaPipe), `GlasswareDetector`, `ShatterDetector` |
| `src/moza/analytics/` | `AnalyticsEngine`: SQLite metrics sink |
| `src/moza/rules/` | `DecisionEngine`: evaluates `configs/rules/*.json` |
| `src/moza/actions/` | `ActionExecutor`: webhook and alert channels |
| `src/moza/privacy/` | Face anonymizer |
| `src/moza/cli.py` | Standalone detection loop: `python -m moza.cli --source 0 --confidence 0.35` |
| `services/moza_server/` | FastAPI server on port 8100: `/health`, `/metrics/current`, `/config`, `/stream/video`, WebSocket `/ws/telemetry` |
| `clients/python/moza_client/` | Lightweight client SDK with no CV dependencies (used by takient `robot_host`) |
| `apps/desktop/` | Tauri + React desktop studio |

### 7. Commands
- Install: `pip install -e ".[dev,server]"`
- Server: `python -m services.moza_server.main` (port 8100)
- Desktop UI: `cd apps/desktop && yarn install && yarn dev`

### 8. Gotchas
- New implementations should subclass the interfaces in `core/interfaces.py`; `GlasswareDetector` and `ShatterDetector` do not yet.
- The YOLOX model downloads on first use into `models/` (gitignored); override with `MOZA_MODEL` / `MOZA_MODEL_DIR`. Tests must not depend on it.
- The server URL `127.0.0.1:8100` is hard-coded in several desktop files (`grep -rn 8100 apps/desktop/src`); change them together.
- The server binds `0.0.0.0`, so the video stream is reachable from the local network.
- Ruff rules are pinned in `pyproject.toml`; there is no mypy gate yet.

### 9. Never
- Never commit camera recordings, `data/`, `models/`, or face crops: they are personal data.
- Never read, print or commit `.env` files or API keys.
- Never force-push or rewrite published history.
