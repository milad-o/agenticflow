from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional

from ..base.agent import Agent
from ...core.events.event import AgenticEvent
from ...core.events.store import EventStore


class ApprovalGateAgent(Agent):
    """Human-in-the-loop gate that requests approval and waits for approval event.

    Required params:
      - workflow_id: str (stream id to write/read events)
      - token: str (optional; auto-generated if missing)
      - timeout_seconds: int (optional; default 300)
    """

    def __init__(self, agent_id: str, event_store: EventStore) -> None:
        super().__init__(agent_id)
        self.event_store = event_store

    async def perform_task(self, task_type: str, params: Dict[str, Any]):
        if task_type != "approval_gate":
            return {"ok": False}
        workflow_id = params.get("workflow_id")
        if not workflow_id:
            return {"ok": False, "error": "missing_workflow_id"}
        token = params.get("token") or f"tok-{uuid.uuid4()}"
        timeout = int(params.get("timeout_seconds", 300))
        # Emit review_requested
        ev = AgenticEvent.create(
            "review_requested",
            {"workflow_id": workflow_id, "token": token, "agent_id": self.agent_id},
            trace_id=workflow_id,
        )
        await self.event_store.append(workflow_id, [ev])
        # Wait for review_approved
        start = asyncio.get_event_loop().time()
        while True:
            events = await self.event_store.replay(workflow_id)
            for e in events[::-1]:
                if e.event_type == "review_approved" and (e.payload or {}).get("token") == token:
                    return {"ok": True, "approved": True, "token": token}
                if e.event_type == "review_denied" and (e.payload or {}).get("token") == token:
                    return {"ok": True, "approved": False, "token": token}
            if asyncio.get_event_loop().time() - start > timeout:
                return {"ok": False, "error": "approval_timeout", "token": token}
            await asyncio.sleep(1.0)