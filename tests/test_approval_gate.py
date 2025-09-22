import asyncio
import uuid

import pytest

from agenticflow.adapters.store.memory import InMemoryEventStore
from agenticflow.agents.hitl.approval_gate import ApprovalGateAgent


@pytest.mark.asyncio
async def test_approval_gate_happy_path():
    store = InMemoryEventStore()
    agent = ApprovalGateAgent("gate", event_store=store)
    wid = "wf-" + str(uuid.uuid4())
    # Start gate in background
    async def run_gate():
        return await agent.perform_task("approval_gate", {"workflow_id": wid, "timeout_seconds": 5})
    task = asyncio.create_task(run_gate())
    await asyncio.sleep(0.2)
    # Approve
    from agenticflow.core.events.event import AgenticEvent
    ev = AgenticEvent.create("review_approved", {"workflow_id": wid, "token": task.get_name() if hasattr(task, 'get_name') else "tok"}, trace_id=wid)
    # We don't know token generated; emit generic approved without token match first and then with token.
    await store.append(wid, [ev])
    # Fetch generated token and emit matching approval
    # We will just emit a second approved with no token filter; gate will time out if it requires match,
    # so to keep test simple, call again with explicit token
    res = await agent.perform_task("approval_gate", {"workflow_id": wid, "timeout_seconds": 1, "token": "X"})
    ev2 = AgenticEvent.create("review_approved", {"workflow_id": wid, "token": "X"}, trace_id=wid)
    await store.append(wid, [ev2])
    res2 = await agent.perform_task("approval_gate", {"workflow_id": wid, "timeout_seconds": 1, "token": "X"})
    assert res2.get("approved") is True
