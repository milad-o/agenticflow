# AgenticFlow

Fast, practical multi-agent orchestration built on LangGraph. AgenticFlow gives you:
- A minimal Flow container with an Orchestrator meta-graph
- Lightweight, tool-first agents (Hybrid RPAVH) with direct tool execution
- LLM‑first reporting (with a deterministic baseline fallback)
- Pandas-based analytics for large CSVs via chunked processing
- Strong observability with human-readable transcripts

Status: Developer Preview — stable for demos and experimentation.

## Highlights
- Orchestrator (LangGraph): Plan → DAG → assign → execute with parallelism and retries
- Agents (Hybrid RPAVH): Reflect (LLM if needed) → Plan (heuristic) → Act (tools) → Verify → Complete
- Tools: Filesystem, search, streaming reads, CSV merge/validate, pandas chunked aggregation
- Reporting: LLM-first synthesis with a safe fallback baseline
- Observability: Quiet console + full transcript saved to `logs/`
- Privacy: No external telemetry by default; only local logs are written

## Quick Start
Prerequisites
- Python 3.10+
- uv (recommended) or pip

Install
- `uv venv`
- `uv pip install -e .`

Try it now (auto LLM detection)
- `uv run examples/csv_merge_demo.py`

Outputs
- Reports: written to `examples/artifact`
- Transcripts: saved to `logs/`
- Inputs: demos read from `examples/data`

## Examples
All demos read inputs from `examples/data` and write generated reports to `examples/artifact`.

- Human Filesystem/Report
  - `uv run examples/hybrid_human_demo.py`
  - Discovers SSIS `.dtsx` files under `examples/data/ssis`, reads content, and writes an executive-ready report.

- CSV Merge Planning
  - `uv run examples/csv_merge_demo.py`
  - Finds CSVs under `examples/data/csv`, inspects headers and samples, and asks the reporter (LLM) to propose a merge plan:
    - inferred join keys
    - join type (inner/left/right)
    - column mappings/renames
    - missing/type handling
    - sample SQL and pandas code snippets

- Huge CSV Analysis (Pandas)
  - `uv run examples/huge_csv_analysis_demo.py`
  - Validates a large CSV under `examples/data/huge` and computes average `size` per `category` using chunked pandas.
  - Note: a small synthetic dataset is auto-generated if the big file is missing, so the demo always runs.

## LLM Providers (optional)
AgenticFlow examples default to auto-detecting an available LLM. To pin a provider, set its environment variable(s):

- Groq
  - `export GROQ_API_KEY=...`
- OpenAI
  - `export OPENAI_API_KEY=...`
- Azure OpenAI
  - `export AZURE_OPENAI_API_KEY=...`
  - `export AZURE_OPENAI_ENDPOINT=...`
  - (optionally) `export AZURE_OPENAI_DEPLOYMENT=...`
- Anthropic
  - `export ANTHROPIC_API_KEY=...`
- Ollama (local)
  - Install and run Ollama locally; examples can use it automatically when available

## Architecture Overview
- Flow: creates registries, reporter, and orchestrator; starts/stops runs.
- Orchestrator: LLM-backed planner (optional) → atomic task splitter → capability‑aware routing → task lifecycle → streaming/chunked execution.
- Agents: Hybrid RPAVH (Reflect/Plan/Act/Verify/Handoff). Direct tool execution with minimal LLM use in non‑reporting phases.
- Tools: Thin registry; adopt per agent to keep capabilities precise (filesystem, search, CSV, streaming).

## Development
- Tests: `uv run -m pytest -q`
- Lint/format: `ruff`, `black` (optional; see pyproject.toml)
- Providers: Examples also support auto-detection via `get_easy_llm("auto")`.

## Notes
- Reporting is LLM-first, with a deterministic baseline fallback; if the LLM fails, a baseline report still gets written.
- Pandas chunk aggregation is the default for large CSV analytics.

## License
MIT
