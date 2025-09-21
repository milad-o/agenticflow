# Changelog

All notable changes to this project will be documented in this file.

## v0.1.0a0 — Phase 1 foundation

Initial V2 foundation with stable core contracts and working scaffold.

Highlights
- Event system
  - AgenticEvent (immutable, trace fields)
  - EventStore interface with InMemory and SQLite adapters (persistence + replay)
  - EventBus interface with InMemory adapter
- Orchestrator
  - Executes DAGs in dependency order
  - Retries and timeouts per task; idempotent completion
  - Emits task_assigned / task_failed / task_completed with attempt metadata
- Agents & FSM
  - Agent base with explicit FSM and invalid transition handling
  - Default transitions: idle→processing, processing→idle/error, error→idle
- Tools & Security
  - SecureTool + ToolRegistry.invoke with SecurityContext authorization
  - Audit logs for granted/denied and success
  - Built-in EchoTool for tests
- Observability
  - No-op tracer compatible facade and simple Metrics stub
- Dev Experience
  - uv-based workflow (uv sync, uv run)
  - Tests (pytest + asyncio + property-style checks where applicable)
  - Pre-commit config (black, ruff), CONTRIBUTING, ROADMAP, README

Breaking changes
- Repo reset from v1: legacy code, tests, and docs were archived via tag/branch (v1-archive, v1-legacy) and removed from main.

Upgrade notes
- Use uv for environment management:
  - `uv sync --extra dev`
  - `uv run pytest -q`
  - `uv run python examples/basic_workflow.py`

Next (Phase 2)
- Communication bus (WebSocket/Redis), basic interaction patterns
- Tracing exporters, metrics integration, supervisor agent scaffolding
- Provider adapters for LLM/embeddings/vector and RAG template
