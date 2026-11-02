# Moza Development Guide & Engineering Contract

### Quick Commands
- Run test suite: `pytest tests/`
- Run fast unit tests: `pytest tests/unit/`
- Start streaming server: `python -m services.moza_server.main`
- Run standalone detection CLI: `python -m moza.cli --source 0 --confidence 0.35`
- Check types: `mypy src/moza`
- Lint code: `ruff check src/moza`

### Monorepo Architecture
- `src/moza`: Core Python computer vision and spatial analytics engine.
- `services/moza_server`: Standalone FastAPI / WebSocket server for edge deployment.
- `clients/python/moza_client`: Featherweight Python client SDK with zero heavy CV dependencies for `takient/robot_host`.
- `configs/rules`: JSON operational and venue safety rules.

See `AGENTS.md` for conventional commit format and strict PR change invariant manifests.
