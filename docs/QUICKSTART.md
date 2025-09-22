# Quickstart

This is the shortest path to seeing AgenticFlow run end-to-end with diagrams.

Prereqs
- Python 3.11+
- uv (https://github.com/astral-sh/uv)

Install
```bash
uv sync --dev
```

Run the Quickstart
```bash
uv run python quickstart.py
```
This writes diagrams under artifacts/quickstart/.

Run tests (excluding integrations)
```bash
PYTHONPATH=. uv run pytest -q --ignore=tests/integration
```

Explore examples
- See examples/README.md for a tour. All examples follow data/ vs artifacts/ convention and provide a single demo.py entry.
