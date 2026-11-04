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
| `docs/ARCHITECTURE.md` | Colored map of the parts, one frame through the server, server vs CLI, and what is not connected yet. Start here |
| `.agents/skills/` | Task playbooks for any coding agent (`SKILL.md` format): `add-detector`, `add-rule`, `review-change`. Read the matching one before starting such a task. Add new skills here only; `.claude/skills/<name>` is a symlink to each (Claude Code reads only that folder), and `verify.py` checks the links. |

### 7. Commands
- Install: `pip install -e ".[dev,server]"`
- Server: `python -m services.moza_server.main` (port 8100)
- Desktop UI: `cd apps/desktop && yarn install && yarn dev`

### 8. Gotchas
- New implementations should subclass the interfaces in `core/interfaces.py`; `GlasswareDetector` and `ShatterDetector` do not yet.
- The YOLOX model downloads on first use into `models/` (gitignored); override with `MOZA_MODEL` / `MOZA_MODEL_DIR`. Tests must not depend on it.
- The server URL `127.0.0.1:8100` is hard-coded in several desktop files (`grep -rn 8100 apps/desktop/src`); change them together.
- The server binds `127.0.0.1` by default because the video stream shows people on camera. Network access is opt-in: `--host 0.0.0.0` or `MOZA_HOST`. The Docker image binds `0.0.0.0` on purpose (container port mapping needs it). Browser access is limited to the desktop app origins in `ALLOWED_ORIGINS` (`services/moza_server/main.py`), for HTTP and the WebSocket; add a web dashboard with `MOZA_ALLOWED_ORIGINS`.
- Rules only see the values in `CONTEXT_KEYS` (`src/moza/rules/decision_engine.py`), which the server context must match; rules using anything else are skipped at load. Triggered `send_alert` / `notify_staff` / `log_event` actions go to `ActionExecutor`, which posts to `MOZA_WEBHOOK_URL` when set.
- Ruff rules are pinned in `pyproject.toml`; there is no mypy gate yet.

### 9. Never
- Never commit camera recordings, `data/`, `models/`, or face crops: they are personal data.
- Never read, print or commit `.env` files or API keys.
- Never force-push or rewrite published history.

### 10. Supporting another coding agent
Instructions live only in this file and skills only in `.agents/skills/`; every agent tool gets them from there.
- **Tool reads `AGENTS.md` and `.agents/skills/`** (Codex, OpenCode, Cursor, Copilot, Antigravity): nothing to do.
- **Tool reads only its own files** (like Claude Code: `CLAUDE.md`, `.claude/skills/`):
  1. Add a one-line pointer file to `AGENTS.md` in the tool's format (see `CLAUDE.md`).
  2. Add its skills folder to `SKILL_MIRRORS` in `scripts/verify.py`, then run `python scripts/verify.py --only skills --fix` to create the symlinks.
  3. Confirm the tool sees the skills: ask it to list its available skills (e.g. `opencode debug skill`, `codex exec`, `claude -p`, `agy -p`).
- Never copy a skill into a tool's folder; link it, so there is one copy to keep current.

### 11. Documentation & Traceability
Code changes arrive faster than people can read them, so a person must be able to follow every change from the docs and the history alone.
- **Explain visually:** describe structure and flows with text plus a colored Mermaid diagram (GitHub renders it) and a legend for the colors; use the palette in `docs/ARCHITECTURE.md`. Write for an engineer new to the repo: define terms and say why, not only what.
- **Keep the map current:** `docs/ARCHITECTURE.md` shows the repo's parts and how data flows between them. A change that adds, removes or rewires a part updates that diagram in the same pull request.
- **Explain every pull request:** what changed and why, how it was verified, and, when a structure or flow changed, a small diagram of the new shape.
- **One intent per commit:** someone reading the history commit by commit must be able to tell what each one did and why (see section 4).
