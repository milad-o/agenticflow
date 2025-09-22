import asyncio
import tempfile
from pathlib import Path

import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.adapters.store.sqlite import SQLiteEventStore


class DummyAgent:
    agent_id = "a"
    async def perform_task(self, t, p):
        return None


@pytest.mark.asyncio
async def test_collision_same_process_active_set():
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(DummyAgent())
    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a", task_type="noop", params={})])

    wid = await orch.execute_workflow(wf, workflow_id="dup-x")
    assert wid == "dup-x"

    with pytest.raises(ValueError):
        await orch.execute_workflow(wf, workflow_id="dup-x")


@pytest.mark.asyncio
async def test_collision_across_processes_with_sqlite(tmp_path: Path):
    db_path = tmp_path / "events.sqlite3"
    store = SQLiteEventStore(db_path)

    # First process
    orch1 = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True, event_store=store)
    orch1.register_agent(DummyAgent())
    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a", task_type="noop", params={})])
    wid = await orch1.execute_workflow(wf, workflow_id="dup-sqlite")
    assert wid == "dup-sqlite"

    # Second process using the same DB
    store2 = SQLiteEventStore(db_path)
    orch2 = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True, event_store=store2)
    orch2.register_agent(DummyAgent())

    with pytest.raises(ValueError):
        await orch2.execute_workflow(wf, workflow_id="dup-sqlite")