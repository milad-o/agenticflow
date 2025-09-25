# AgenticFlow

Fast, practical multi-agent orchestration built on LangGraph. AgenticFlow gives you:
- A minimal Flow container with an Orchestrator meta-graph
- Lightweight, tool-first agents (Hybrid RPAVH) with direct tool execution
- Intelligent reporting (LLM-only) for high-quality outputs
- Pandas-based analytics for large CSVs with chunked processing
- Strong observability with a human-readable execution transcript

Status: Developer Preview — stable for demos and experimentation.

## Key Features
- Orchestrator (LangGraph): Plan → DAG → assign → execute with parallelism and retries
- Agents (Hybrid RPAVH): Reflect (LLM if needed) → Plan (heuristic) → Act (tools) → Verify → Complete
- Tools: Filesystem, search, streaming reads, CSV merge/validate, pandas chunked aggregation
- Intelligent Reporting: Strict LLM-only (no heuristic fallback)
- Observability: Minimal console logs + full transcript saved to `logs/`
- Safe defaults: LangSmith telemetry disabled by default; secrets loaded from `.env`

## Requirements
- Python 3.10+
- uv (recommended) or pip
- Groq account + `GROQ_API_KEY` for LLM-generated reports (or configure another provider)

## Quick Start
1) Create a virtual environment and install
   - `uv venv`
   - `uv pip install -e .`
2) Configure LLM (Groq)
   - `export AGENTICFLOW_LLM_PROVIDER=groq`
   - `export GROQ_API_KEY=...`
3) Run the demos
   - Human filesystem/report demo: `uv run examples/hybrid_human_demo.py`
   - CSV merge planning demo: `uv run examples/csv_merge_demo.py`
   - Huge CSV analysis (pandas) demo: `uv run examples/huge_csv_analysis_demo.py`

Each demo prints a report path and a transcript path on completion.

## Demos
### 1) Human Filesystem/Report Demo
- Discovers SSIS `.dtsx` files, reads content, and writes an executive-ready report via the Reporting agent (LLM-only).
- Minimal console noise; see the full transcript under `logs/`.

### 2) CSV Merge Demo
- Finds CSVs under `examples/data/csv`, inspects headers and samples, and asks the reporter (LLM) to propose a merge plan:
  - inferred join keys
  - join type (inner/left/right)
  - column mappings/renames
  - missing/type handling
  - sample SQL and pandas code snippets

### 3) Huge CSV Analysis Demo (Pandas)
- Validates a large CSV (`examples/data/huge/products-1000000.csv`).
- Computes the average `size` per `category` using pandas with chunked reads.
- Injects factual aggregates into the Reporting agent prompt for a high-quality LLM report.

## Configuration
- Set `AGENTICFLOW_LLM_PROVIDER=groq` and `GROQ_API_KEY` in your shell or `.env`.
- LangSmith telemetry is disabled by default. To enable (optional), add to `.env`:
  - `LANGCHAIN_TRACING_V2=true`
  - `LANGSMITH_TRACING=true`
  - `LANGSMITH_API_KEY=...`

## Architecture Overview
- Flow: creates registries, reporter, and orchestrator; starts/stops runs.
- Orchestrator: LLM-backed planner (optional) → atomic task splitter → capability-aware routing → task lifecycle → streaming/chunked execution.
- Agents: Hybrid RPAVH (Reflect/Plan/Act/Verify/Handoff). Direct tool execution with minimal LLM use in non-reporting phases.
- Tools: Thin registry; adopt per-agent to keep capabilities precise.

## Development
- Tests: `uv run -m pytest -q`
- Lint/format: `ruff`, `black` (optional; see pyproject.toml)
- Local provider: You can wire a different provider via `AGENTICFLOW_LLM_PROVIDER`.

## Notes
- Reporting is strict LLM-only. If the LLM fails or returns empty content, the write step fails and retries (no heuristic fallback).
- Pandas analytics is the default for large CSV aggregation. Redundant aggregators were removed from the public API.

## License
MIT
