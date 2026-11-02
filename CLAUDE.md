# Argus Development Guide & Engineering Contract

### Quick Commands
- Run test suite: `pytest tests/`
- Run fast unit tests: `pytest tests/unit/`
- Start streaming server: `python -m services.argus_server.main`
- Run standalone detection CLI: `python -m argus.cli --camera 0 --models people,beverages,hazards`
- Check types: `mypy src/argus`
- Lint code: `ruff check src/argus`

### Monorepo Architecture
- `src/argus`: Core Python computer vision and spatial analytics engine.
- `services/argus_server`: Standalone FastAPI / WebSocket server for edge deployment.
- `clients/python/argus_client`: Featherweight Python client SDK with zero heavy CV dependencies for `takient/robot_host`.
- `configs/rules`: JSON operational and venue safety rules.

See `AGENTS.md` for conventional commit format and strict PR change invariant manifests.
