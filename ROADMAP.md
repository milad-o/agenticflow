# AgenticFlow V2 Roadmap

This document tracks the phased plan and acceptance criteria for AgenticFlow V2. It mirrors the vision in v2_vision.md and v2_architecture.md while focusing execution on durable, non-disruptive foundations.

---

## Phase 0: Repo Reset and Scaffold (This PR)

Deliverables
- Archive v1 state: tag `v1-archive`, branch `v1-legacy`
- Remove legacy code: src/, tests/, examples/, docs/
- Replace top-level metadata: new README.md and pyproject.toml
- Create v2 scaffold directories (see README)
- Add this ROADMAP.md

Exit checks
- `git tag -l v1-archive` exists, `git branch -l v1-legacy` exists
- Repo contains only v2 scaffold + LICENSE + .gitignore + vision docs

---

## Phase 1: Foundation (Core Capabilities)

Objective: Ship a minimal, production-credible core that locks in public contracts and directory layout, enabling non-disruptive evolution.

Scope
1) Event system
- Contracts: AgenticEvent (immutable), EventStore (append/read/query/replay), EventBus (publish/subscribe)
- Impl: InMemory EventBus; InMemory + SQLite EventStore (SQLAlchemy)

2) Agent FSM core
- Contracts: Agent base (handle_event), StateMachine (transitions/guards)
- Impl: Minimal FSM, ToolRegistry interface

3) Orchestrator MVP
- Contracts: TaskDefinition (frozen), TaskGraph, Orchestrator.execute_workflow()
- Impl: Single-process DAG executor with retries/timeouts; emits task events

4) Security skeleton
- Contracts: SecurityContext.authorize(op:resource), AuditLogger
- Impl: In-memory RBAC; stdout/file audit; EncryptedMemory interface placeholder

5) Observability hooks
- Contracts: get_tracer(name), Metrics facade
- Impl: No-op tracer (OTel-compatible API), structlog logger

6) DX
- pytest + pytest-asyncio + hypothesis
- ruff, black, mypy; pre-commit
- Example: examples/basic_workflow.py (two-agent, single-dependency DAG)

Acceptance criteria
- EventStore replay determinism (property test)
- Backend swap via config (in-mem <-> SQLite) without code changes
- Orchestrator executes a small DAG; emits task_assigned/completed/failed
- Security: denied tool invocation is blocked and audited
- Observability: logs include workflow_id/trace_id/agent_id correlators

---

## Phase 2: Communication & Patterns

- Multi-protocol CommunicationBus (WebSockets/Redis)
- Basic interaction patterns (request/response, broadcast)
- Message persistence/replay; circuit breakers/retries
- Metrics collection framework

Backward-compat constraints
- Preserve Phase 1 contracts: Event types, FSM API, Orchestrator interfaces

---

## Phase 3: Supervisor & Advanced Observability

- SupervisorAgent with LLM-based task decomposition
- Advanced patterns (negotiation, auction)
- OpenTelemetry exporters + Jaeger; Debug interface

---

## Phase 4: Production Hardening

- Performance tuning and load testing
- Security audit and sandboxing enforcement
- Documentation, examples, CI/CD & release automation

---

## Tracking

We will manage execution via the internal task list and mark completion at each milestone. See TODOs maintained during development for current status.
