from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse, HTMLResponse

from agenticflow.observability.debug import DebugInterface
from agenticflow.observability.graph import mermaid_with_status
from agenticflow.observability.viz import reconstruct_workflow_definition, derive_agents_and_types
from agenticflow.observability.system_viz import mermaid_system
from agenticflow.orchestration.core.orchestrator import Orchestrator


def build_app(orchestrator: Orchestrator) -> FastAPI:
    app = FastAPI(title="AgenticFlow UI", version="0.1")
    dbg = DebugInterface(event_store=orchestrator.event_store)

    @app.get("/")
    async def index() -> HTMLResponse:
        return HTMLResponse(
            """
            <html>
            <head><title>AgenticFlow UI</title></head>
            <body>
              <h1>AgenticFlow UI</h1>
              <p>Use /api/summaries to list workflows.</p>
              <ul>
                <li><a href="/api/summaries">/api/summaries</a></li>
              </ul>
            </body></html>
            """
        )

    @app.get("/api/summaries")
    async def api_summaries(limit: int = 50, status: Optional[str] = None) -> JSONResponse:
        sums = await dbg.list_workflow_summaries(limit=limit, status=status)
        out = [
            {
                "workflow_id": s.workflow_id,
                "status": s.status,
                "duration_s": s.duration_s,
                "last_event": s.last_event,
            }
            for s in sums
        ]
        return JSONResponse(out)

    @app.get("/api/workflows/{wid}/mermaid")
    async def api_mermaid(wid: str) -> PlainTextResponse:
        wf_def = await reconstruct_workflow_definition(dbg, wid)
        summary = await dbg.get_workflow_summary(wid)
        mmd = mermaid_with_status(wf_def, summary)
        if not mmd:
            raise HTTPException(404, "not_found")
        return PlainTextResponse(mmd, media_type="text/plain; charset=utf-8")

    @app.get("/api/workflows/{wid}/system")
    async def api_system(wid: str) -> PlainTextResponse:
        wf_def = await reconstruct_workflow_definition(dbg, wid)
        agents, task_types = derive_agents_and_types(wf_def)
        mmd = mermaid_system(agents, tools_by_agent={}, task_types_by_agent=task_types)
        return PlainTextResponse(mmd, media_type="text/plain; charset=utf-8")

    @app.get("/api/workflows/{wid}/events")
    async def api_events(wid: str) -> JSONResponse:
        evs = await dbg.event_store.replay(wid)
        out = [
            {
                "ts": e.ts,
                "event_type": e.event_type,
                "payload": e.payload,
            }
            for e in evs
        ]
        return JSONResponse(out)

    @app.get("/api/workflows/{wid}/events/stream")
    async def api_events_stream(wid: str, poll_ms: int = 1000) -> StreamingResponse:
        async def gen() -> AsyncGenerator[bytes, None]:
            last_len = 0
            while True:
                evs = await dbg.event_store.replay(wid)
                if len(evs) > last_len:
                    new = evs[last_len:]
                    last_len = len(evs)
                    for e in new:
                        line = f"event: {e.event_type}\ndata: { { 'ts': e.ts, 'payload': e.payload } }\n\n"
                        yield line.encode("utf-8")
                await asyncio.sleep(max(0.05, poll_ms / 1000.0))
        return StreamingResponse(gen(), media_type="text/event-stream")

    return app