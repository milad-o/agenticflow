# AgenticFlow Web UI (minimal)

A minimal FastAPI UI to inspect workflows stored in the event store.

Install UI extras:
```bash
uv sync --extra ui
```

Run the server (defaults to examples/02_sales_workflow/persistent.sqlite3):
```bash
uv run python examples/webui/run_server.py
```

Configure database (optional):
```bash
export AGENTICFLOW_UI_DB=examples/01_file_qna/events.sqlite3
uv run python examples/webui/run_server.py
```

Endpoints:
- GET / — landing page
- GET /api/summaries — list workflows (status, duration)
- GET /api/workflows/{wid}/mermaid — Mermaid workflow diagram with status
- GET /api/workflows/{wid}/system — Mermaid system diagram (agents + task types)
- GET /api/workflows/{wid}/events — full event timeline
- GET /api/workflows/{wid}/events/stream — SSE stream of new events (polling-based)