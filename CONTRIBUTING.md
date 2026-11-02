# Contributing to Moza

Thank you for contributing to Moza, the open-source real-time vision, cocktail perception, and venue spatial intelligence engine.

## Commit Standards
Every commit must adhere to [Conventional Commits](https://www.conventionalcommits.org/):
`type(scope): subject`

Allowed types:
`feat`, `fix`, `refactor`, `perf`, `chore`, `test`, `docs`, `build`, `ci`, `model`, `data`, `eval`, `exp`

Allowed scopes:
`core`, `capture`, `detectors`, `analytics`, `rules`, `audio`, `spatial`, `privacy`, `storage`, `server`, `client`, `config`, `deps`, `docs`, `tests`

Maximum 5 staged files per atomic commit. See `AGENTS.md` for full requirements.

## Development Setup
```bash
# Clone the repository
git clone https://github.com/luisenriquecgongora/moza.git
cd moza

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install editable package with dev dependencies
pip install -e ".[dev]"
```
