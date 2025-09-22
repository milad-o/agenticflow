# AgenticFlow v2.0.0a1 (alpha)

This release delivers a ready-to-use core with validation/policy guardrails, mid-task streaming events, OOP topology helpers, examples reorganization, a Quickstart, and a minimal Web UI—plus optional MCP integration hooks.

## Highlights
- Validation & Policy (local)
  - TaskSchemaRegistry enforced pre-assignment (jsonschema if installed; required-only fallback with actionable hints).
  - PolicyGuard (allow/deny per agent:task), also enforced pre-assignment.
  - Dev policy loader (YAML/JSON) + sample profiles for deny-by-default hardening.
- Mid-task events (streaming-friendly)
  - Tools can emit mid-task progress via `emit_progress(kind, data)`.
  - Orchestrator publishes `task_progress` events.
- Topologies (OOP)
  - `PipelineTopology` and `FanoutReduceTopology` with tests; function helpers remain (`pipeline`, `fanout_reduce`).
- Examples reorganization (self-contained)
  - Each demo has a single entrypoint (demo.py) and a `data/` vs `artifacts/` split.
  - New/updated examples:
    - 04_tools_pipeline (FSReadTool + Stats + Report)
    - 05_local_docs (Scan + Summarize)
    - 06_mcp_demo (Tavily/Open‑Meteo MCP scaffolding; result artifacts; optional SDK usage)
- Quickstart
  - `quickstart.py` runs a minimal pipeline with diagrams into `artifacts/quickstart/`.
- Minimal Web UI (optional)
  - FastAPI app to browse summaries, diagrams, event logs, and SSE stream of new events.
- Hardening
  - FSReadTool: root allowlist + extension allowlist.
  - HttpFetchTool: HTTPS-only option, content-type allowlist, content-length/max_bytes caps, sanitized errors.
  - Reduced httpx log noise (default WARNING) to avoid leaking URLs in logs.
- Documentation
  - Quickstart (`docs/QUICKSTART.md`)
  - Usage Guide (`docs/USAGE.md`)
  - Extended API Reference (`docs/API_REFERENCE.md`)
  - Security & Policy (`docs/SECURITY_POLICY.md`)
  - Utilities (`docs/UTILITIES.md`)
  - Roadmap updated (`docs/ROADMAP.md`)

## Breaking changes
- Examples were moved/standardized to self-contained folders with a single `demo.py` per example. Old root-level example scripts were retired.

## Upgrade notes
- Web UI extras:
  - `uv sync --extra ui`
- MCP SDK-based tools (optional):
  - `uv sync --extra mcp`

## Install and Quickstart
- Install:
  - `uv sync --dev`
- Run Quickstart:
  - `uv run python quickstart.py`
- Run tests (excluding integrations):
  - `PYTHONPATH=. uv run pytest -q --ignore=tests/integration`

## Examples
- Tools pipeline:
  - `uv run python examples/04_tools_pipeline/demo.py`
- Local docs summary:
  - `uv run python examples/05_local_docs/demo.py`
- MCP demo (optional; writes artifacts even with minimal HTTP fallback):
  - `export TAVILY_API_KEY=…` (for Tavily MCP)
  - `uv sync --extra mcp` (to prefer official SDK tools)
  - `AGENTICFLOW_LOG_LEVEL=WARNING uv run python examples/06_mcp_demo/demo.py`

## Web UI (optional)
- Install UI extras:
  - `uv sync --extra ui`
- Start server:
  - `AGENTICFLOW_LOG_LEVEL=WARNING uv run python examples/webui/run_server.py`
- Browse:
  - http://127.0.0.1:8000
- Endpoints:
  - `/api/summaries`, `/api/workflows/{wid}/mermaid`, `/system`, `/events`, `/events/stream` (SSE)

## Links
- Quickstart: `docs/QUICKSTART.md`
- Usage guide: `docs/USAGE.md`
- API reference: `docs/API_REFERENCE.md`
- Security & Policy: `docs/SECURITY_POLICY.md`
- Roadmap: `docs/ROADMAP.md`
