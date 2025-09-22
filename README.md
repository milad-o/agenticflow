# AgenticFlow V2 (Phase 1)

Minimal, stable foundation for the next-generation, event-driven, FSM-based multi-agent framework. This repository has been reset to a clean scaffold to implement Phase 1 without legacy coupling.

## Goals (Phase 1)
- Event-sourced core: immutable events, persistent store, replay
- Agent FSM core: explicit transitions, deterministic behavior
- Orchestrator MVP: DAG execution with retries/timeouts
- Security skeleton: basic authorization + audit logging
- Observability hooks: structured logs, tracer/metrics facades
- Solid DX: pytest + asyncio, ruff/black/mypy, examples

## Quickstart
```bash
# Install dependencies (dev included) with uv
uv sync --dev

# Run the Quickstart (writes artifacts/quickstart/*)
uv run python quickstart.py
```

## Dev Quickstart
```bash
# Run tests (excluding integrations by default)
PYTHONPATH=. uv run pytest -q --ignore=tests/integration
```

## Examples

All examples are self-contained (one demo.py each) and follow a data/ vs artifacts/ split. See examples/README.md for full details and commands.

- 01_file_qna — provider-free by default
  ```bash
  AGENTICFLOW_LLM_PROVIDER=noop uv run python examples/01_file_qna/demo.py
  ```
- 02_sales_workflow — CSV analysis + report
  ```bash
  uv run python examples/02_sales_workflow/demo.py
  ```
- 03_group_chat — multi-round local chat + diagrams
  ```bash
  uv run python examples/03_group_chat/demo.py --participants analyst reporter --rounds 2 --topic "Plan Q2" --store sqlite --outdir examples/03_group_chat/artifacts
  ```
- 04_tools_pipeline — ToolAgent + stats + report
  ```bash
  uv run python examples/04_tools_pipeline/demo.py
  ```
- 05_local_docs — scan and summarize local files
  ```bash
  uv run python examples/05_local_docs/demo.py
  ```

## Development providers (LLM + Embeddings)

This repo includes optional adapters for development:
- LLM: Groq (default), Azure OpenAI
- Embeddings: Ollama (default, local), Hugging Face (local CPU/GPU)

Install the extras you need:
```bash
uv sync --extra dev --extra llm-groq --extra embed-ollama
# Optionally add Azure, HF, MCP SDK
uv sync --extra llm-azure --extra embed-hf --extra mcp
```

Set your environment (e.g., from .env).
```bash
# Groq (primary)
export GROQ_API_KEY=your_key
export GROQ_MODEL=llama-3.1-8b-instant
# Optional: Azure OpenAI
# export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
# export AZURE_OPENAI_API_KEY=your_key
# export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
# export AZURE_OPENAI_API_VERSION=2024-02-15-preview
# Ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_EMBED_MODEL=nomic-embed-text
# Optional Azure
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_API_KEY=your_key
export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

Run the dev demos:
```bash
# Health check for Groq + Ollama
uv run python examples/utils/health_check.py

# LLM + Embedding quick check
uv run python examples/dev_llm_embed_demo.py

# Supervisor with LLM decomposer (uses env-driven LLM provider)
uv run python examples/supervisor_llm_demo.py

# Optional: Groq integration test (skips if GROQ_API_KEY missing)
uv run pytest tests/integration/test_groq_integration.py -q
```

### Observability: Logging and Metrics

- Logging
  - By default, logs are structured JSON (override with AGENTICFLOW_LOG_FORMAT=text)
  - Level via AGENTICFLOW_LOG_LEVEL (e.g., INFO, DEBUG)
- Metrics
  - Enable Prometheus exporter by setting AGENTICFLOW_METRICS=prometheus and optionally AGENTICFLOW_PROM_PORT (default 8000)

### Communication Bus PoC (Redis and NATS)

RedisBus and NatsBus are minimal PoC adapters intended for development/testing.
They’re optional and only active if you install their clients and run local servers.

- RedisBus
  - Install client: uv add redis
  - Start server: brew services start redis OR docker run -p 6379:6379 redis:7-alpine
  - Run demo: uv run python examples/bus_correlation_demo.py

- NatsBus
  - Install client: uv add nats-py
  - Start server: docker run -p 4222:4222 nats:2-alpine

Tests will automatically skip Redis/NATS integration tests if servers or clients are not available.

Optional: load capabilities from YAML for demos

Makefile shortcuts
```bash
# Install dev + Groq + Ollama extras
make sync-groq-ollama

# Run tests
make test

# Health check
make health

# Supervisor CLI (provide query and caps file)
make supervisor-cli QUERY="Analyze sales.csv then generate a report" CAPS=examples/capabilities/example_caps.yaml

# Config-driven demo (set CONFIG to YAML/JSON config path)
make demo-config CONFIG=examples/config/supervisor_demo.yaml

# Realistic sales analysis demo (reads a CSV and produces a summary)
make demo-realistic
```
```bash
# Sample capabilities file
cat examples/capabilities/example_caps.yaml

# In your demo code, load registry:
# from examples.utils.capabilities_loader import load_registry_from_file
# reg = load_registry_from_file("examples/capabilities/example_caps.yaml")
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

## Documentation
- Quickstart: docs/QUICKSTART.md
- Usage Guide: docs/USAGE.md
- Utilities Overview: docs/UTILITIES.md
- Security & Policy: docs/SECURITY_POLICY.md
- Extended API Reference: docs/API_REFERENCE.md
- Roadmap: docs/ROADMAP.md

## Roadmap
See ROADMAP.md for phased plan, deliverables, and acceptance criteria.

## License
MIT. See LICENSE.
