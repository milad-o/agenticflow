from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from agenticflow.orchestration.core.orchestrator import Orchestrator
from agenticflow.adapters.store.sqlite import SQLiteEventStore
from agenticflow.ui.server import build_app


if __name__ == "__main__":
    # Default to the sales workflow DB so users see something
    db_path = os.environ.get("AGENTICFLOW_UI_DB", str(Path("examples/02_sales_workflow/persistent.sqlite3")))
    es = SQLiteEventStore(db_path)
    orch = Orchestrator(event_store=es, emit_workflow_started=True, emit_workflow_lifecycle=True)
    app = build_app(orch)
    # Run
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")))