# Changelog

## 2.0.0a1 (2025-09-22)

Highlights
- Validation & Policy (local): TaskSchemaRegistry enforced pre-assignment (jsonschema when available; fallback with helpful hints), PolicyGuard (allow/deny per agent:task), dev policy loader (YAML/JSON) + sample profiles
- Mid-task events: tools can emit progress; orchestrator publishes task_progress events (streaming-friendly)
- Topologies: class-based PipelineTopology and FanoutReduceTopology with tests; function helpers remain
- Examples reorg: each demo self-contained (demo.py + data/ vs artifacts/); added Tools Pipeline, Local Docs, MCP demo scaffolding
- Quickstart: root script that runs a minimal pipeline and renders diagrams (artifacts/quickstart)
- Web UI (optional): minimal FastAPI server to browse summaries, diagrams, events, plus SSE stream
- MCP (optional): preferred SDK integration hooks (mcp/fastmcp), fallback hardened HTTP/SSE tools; demo writes server responses to artifacts
- Hardening: FSReadTool (extensions), HttpFetchTool (HTTPS-only option, content-type/size caps), sanitized error handling and log noise reduction
- Docs: Quickstart, Usage, extended API Reference, Security & Policy (with troubleshooting), Utilities; Roadmap updated

Breaking changes
- Examples were moved to self-contained folders, and root-level example scripts removed in favor of demo.py per example

Upgrade notes
- Install UI or MCP extras if needed:
  - `uv sync --extra ui` (Web UI)
  - `uv sync --extra mcp` (MCP SDK-based tools)

---

# Changelog

All notable changes to this project will be documented in this file.

## v0.3.0a0 — Phase 3 scaffolding (Decomposition, Patterns, Debugging)

Highlights
- Decomposition & Capabilities
  - LLMTaskDecomposer: parses JSON plans from LLM output and maps capabilities to agents via CapabilityMatcher
  - CapabilityMatcher and DictCapabilityMatcher for simple capability→agent routing
- Advanced Patterns
  - Negotiation: deterministic numeric negotiation with delta-based convergence and aggregation
  - Auction: second-price (Vickrey) auction helper with winner/price output
- Debugging & Summaries
  - DebugInterface filters (event_types, since/until) for workflow/agent timelines
  - WorkflowSummary: event counts, unique tasks/agents, start/end timestamps, duration
  - Orchestrator events now include agent_id (and task_type for completed) for better introspection
- Tests: full coverage for decomposer, patterns, debug filters/summary

## v0.2.0a0 — Phase 2 alpha (Communication, Reliability, Supervisor, Observability)

Highlights
- Communication
  - CommunicationBus interfaces and Message type (topic, type, payload, correlation_id, reply_to)
  - Adapters: InMemory and LocalWebSocket (server/client), both support publish/subscribe and request/response
  - Request/Response pattern helpers (rpc_call, register_rpc_handler) with correlation preservation
- Reliability
  - CircuitBreaker utility (CLOSED/OPEN/HALF_OPEN) with failure thresholds and recovery timeout
  - Optional integration in ToolRegistry.invoke
- Supervisor scaffolding
  - SupervisorAgent interface and NoopTaskDecomposer (single-task workflow generation)
- Observability (optional exporters)
  - Env-toggled OpenTelemetry tracer wiring (console or OTLP), fallback to Noop by default
  - Env-toggled Prometheus metrics HTTP server (no-op if library absent)
- Tests & DX
  - WebSocket adapter tests (broadcast, request/response)
  - Pattern, reliability, supervisor, and optional observability tests
  - uv-based workflow remains default (uv sync, uv run)

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
