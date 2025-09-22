import asyncio
from pathlib import Path

import pytest

from agenticflow.adapters.store.sqlite import SQLiteEventStore
from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.service import WorkflowService
from agenticflow.orchestration.tasks.graph import TaskNode


class FailingAgent:
    agent_id = "flaky"
    async def perform_task(self, t, p):
        raise RuntimeError("fail once")


class GoodAgent:
    agent_id = "flaky"
    async def perform_task(self, t, p):
        return {"ok": True}


@pytest.mark.asyncio
async def test_workflow_service_resume_across_processes(tmp_path: Path):
    db = tmp_path / "events.sqlite3"

    # Process 1: start and fail
    store1 = SQLiteEventStore(db)
    orch1 = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True, event_store=store1)
    orch1.register_agent(FailingAgent())
    svc1 = WorkflowService(orch1)
    wf = WorkflowDefinition(tasks=[TaskNode(task_id="work", agent_id="flaky", task_type="do", params={}, retries=0)])
    with pytest.raises(RuntimeError):
        await svc1.start(wf, workflow_id="svc-demo-1")

    # Process 2: resume successfully
    store2 = SQLiteEventStore(db)
    orch2 = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True, event_store=store2)
    orch2.register_agent(GoodAgent())
    svc2 = WorkflowService(orch2)
    rid = await svc2.resume("svc-demo-1")
    assert rid == "svc-demo-1"

    sums = await svc2.summaries()
    found = [s for s in sums if s.workflow_id == "svc-demo-1"]
    assert found and found[0].status == "completed"