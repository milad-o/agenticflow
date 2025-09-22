# AgenticFlow V2 Roadmap

This document tracks the phased plan and acceptance criteria for AgenticFlow V2. It mirrors the vision in v2_vision.md and v2_architecture.md while focusing execution on durable, non-disruptive foundations.

Updated: 2025-09-22

## Snapshot: current status

Completed
- Core orchestrator with durability, retries/backoff, rate-limits, circuit breaker
- Concurrency: global max_parallelism and per_agent_concurrency
- DebugInterface timelines and workflow/system diagrams (Mermaid, DOT, optional SVG)
- Security hooks (SecurityContext) and light task schema enforcement
- ToolAgent + built-in guarded tools (fs_read, http_fetch)
- Utility agents (Stats, Report, Scan, Summarize), GroupChatSupervisor
- Examples refactor: self-contained demos with data/ vs artifacts/ and uv-first runs
- Tests: 59 passing, 8 skipped (integration), provider-free defaults

In progress / next
- Class-based topology helpers (PipelineTopology, FanoutReduceTopology)
- Stronger JSON Schema validation and policy guardrails
- Remote/distributed workers (Redis Streams or NATS JetStream)
- HITL UX (approve/deny UI) and richer observability exporters
- Root-level Quickstart and focused how-to guides

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

## Phase 1: Foundation (Core Capabilities) — Completed

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

## Phase 2: Communication & Patterns — Completed (MVP patterns available)

Scope
- CommunicationBus interfaces (Message, publish/subscribe, request/response, broadcast)
- Adapters: InMemory (dev) and LocalWebSocket (dev) behind interfaces
- Interaction patterns: request/response and broadcast atop the bus
- Persistence hooks: optional append to EventStore for replay
- Reliability: CircuitBreaker utility and retry helpers
- Observability: optional OpenTelemetry exporter wiring; metrics counters for bus/orchestrator
- Security: standardize operation:resource naming; audit enrichment (trace/workflow IDs)

Acceptance criteria
- InMemory and LocalWebSocket adapters pass compliance tests (pub/sub, request/response)
- Backpressure hook invoked when subscriber count or queue size exceeds threshold
- Request/response supports timeout and propagates errors; correlation IDs consistent
- Broadcast delivers exactly once per subscriber
- If OTel enabled, spans export to Jaeger; otherwise Noop tracer is default

Backward-compat constraints
- Preserve Phase 1 contracts: Event types, FSM API, Orchestrator interfaces

---

## Phase 3: Supervisor & Advanced Observability — Completed (initial scope)

Scope
- Supervisor & Decomposition
  - LLM-powered TaskDecomposer (schema-guided, deterministic temperature), capability matching
  - Template registry for common workflows; validation and optimization step
- Advanced patterns
  - Negotiation and auction interaction patterns with convergence detection and fairness policies
  - Streaming communications with backpressure and flow control
- Deep Observability
  - Distributed tracing spans across agents/orchestrator/tools with context propagation over bus
  - Real-time Debug interface (event timeline per workflow/agent), event replay helpers
  - Metrics dashboards (tasks latency, failures, circuit states)

Acceptance criteria
- Supervisor: given a complex query, returns a multi-step workflow with dependencies and executes successfully with human-readable trace
- Patterns: negotiation/auction tests validate convergence under synthetic inputs
- Observability: spans export to Jaeger when enabled; debug interface can reconstruct task timelines from EventStore

---

## Phase 4: Validation, Policy, and Guardrails

Scope
- JSON Schema (optional dependency) for task parameter validation with helpful errors
- Policy guardrails: allow/deny by agent/task/tool; environment profiles (dev/test/prod)
- Enforced schema/guard checks pre-assignment; consistent error taxonomy

Acceptance
- Invalid task params are rejected with actionable messages
- Policy profiles toggle behavior without code changes

---

## Phase 5: Distributed Execution (Remote Workers)

Scope
- Bus-backed remote workers (Redis Streams or NATS JetStream) processing task_assigned events
- Leases, retries, backpressure, and graceful shutdown
- Transport abstraction to switch between in-memory and remote modes
- Observability: per-worker metrics, lag, and health

Acceptance
- Example workflow executes with remote workers; correctness and idempotence preserved
- Backpressure tests demonstrate bounded behavior under load

---

## Phase 6: UX, Quickstart, and Docs

Scope
- Root-level Quickstart (end-to-end run + diagrams via a single uv command)
- HITL approve/deny UI; resume from UI
- Enhanced observability exporters (OpenTelemetry, metrics dashboards)
- How-to guides: extend agents/tools, add remote workers, build topologies, security/policy

Acceptance
- Quickstart completes with diagrams; HITL UI demo flow works locally
- Docs cover developer extensibility and operations

---

- Performance tuning and load testing
- Security audit and sandboxing enforcement
- Documentation, examples, CI/CD & release automation

---

## Developer TODOs (near-term)

- Topology helpers (class-based)
  - Implement PipelineTopology and FanoutReduceTopology
  - Unit tests comparing outputs to function helpers
  - Docs update (UTILITIES.md) and brief example snippet
- Validation & policy
  - Integrate jsonschema (optional extra) and wire informative errors
  - Policy profiles with allow/deny lists by agent/task/tool
- Quickstart
  - Single-file quickstart.py at repo root; write diagrams to artifacts/
  - Add short section to README.md linking to examples and quickstart
- Remote workers MVP
  - Choose Redis Streams or NATS JetStream; implement transport and worker loop
  - Metrics and debug hooks; resilience tests

## Agent execution plan (internal)

1) Implement class-based topology helpers + tests + docs
2) Add Quickstart script + docs
3) Upgrade validation/policy (jsonschema optional extra)
4) Remote worker MVP (transport + worker CLI) with tests and diagrams
5) Optional: HITL UI stub and observability exporters

We will manage execution via the internal task list and mark completion at each milestone. See TODOs maintained during development for current status.

We will manage execution via the internal task list and mark completion at each milestone. See TODOs maintained during development for current status.
