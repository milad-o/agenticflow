# Contributing to AgenticFlow V2

## Dev setup
- Python 3.11+
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e ".[dev]"`

## Commands
- Lint/format: `ruff check .` and `black .`
- Type-check: `mypy agenticflow`
- Tests: `pytest -q`

## Guidelines
- Favor composition over inheritance
- Keep public contracts stable; avoid breaking changes within a phase
- Add tests with new interfaces; prefer async-friendly designs
