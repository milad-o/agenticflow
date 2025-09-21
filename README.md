# AgenticFlow V2 (Phase 1)

Minimal, stable foundation for the next-generation, event-driven, FSM-based multi-agent framework. This repository has been reset to a clean scaffold to implement Phase 1 without legacy coupling.

## Goals (Phase 1)
- Event-sourced core: immutable events, persistent store, replay
- Agent FSM core: explicit transitions, deterministic behavior
- Orchestrator MVP: DAG execution with retries/timeouts
- Security skeleton: basic authorization + audit logging
- Observability hooks: structured logs, tracer/metrics facades
- Solid DX: pytest + asyncio, ruff/black/mypy, examples

## Quickstart (dev)
```bash
# Create venv and install (editable)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest -q

# Run the example
python examples/basic_workflow.py
```

## Repository Layout (scaffold)
```
agenticflow/
  core/
    events/      # AgenticEvent, EventStore, EventBus (interfaces)
    types/       # Result/identifier types
    exceptions/  # Base exceptions
  agents/
    base/        # Agent base
    state/       # FSM machinery
  tools/
    base/        # Tool + registry interfaces
  orchestration/
    core/        # Orchestrator MVP
    tasks/       # Task graph
  security/      # SecurityContext + audit
  observability/ # Tracing/metrics facades
adapters/
  bus/           # In-memory bus adapter
  store/         # SQLite event store adapter
examples/
  basic_workflow.py
```

## Roadmap
See ROADMAP.md for phased plan, deliverables, and acceptance criteria.

## License
MIT. See LICENSE.
