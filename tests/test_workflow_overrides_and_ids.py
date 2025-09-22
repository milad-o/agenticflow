import asyncio
import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent
from agenticflow.observability.debug import DebugInterface


class Flaky(Agent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.count = 0

    async def perform_task(self, task_type, params):
        self.count += 1
        if self.count == 1:
            raise RuntimeError("first fails")
        return {"ok": True}


class OK(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


@pytest.mark.asyncio
async def test_task_level_backoff_overrides_workflow_and_default(monkeypatch):
    # Capture sleeps
    sleeps = []

    async def fake_sleep(duration):
        sleeps.append(duration)
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    # Orchestrator defaults would be 0.2, workflow override 0.05, task override 0.01
    orch = Orchestrator(retry_backoff_base=0.2)
    flaky = Flaky("a1")
    orch.register_agent(flaky)

    wf = WorkflowDefinition(
        tasks=[
            TaskNode(
                task_id="t1",
                agent_id="a1",
                task_type="x",
                retries=1,
                timeout_seconds=1,
                retry_backoff_base=0.01,  # task-level override used
            ),
        ],
        retry_backoff_base=0.05,  # workflow-level override (ignored due to task-level)
    )

    await orch.execute_workflow(wf)
    assert len(sleeps) == 1
    assert 0.009 <= sleeps[0] <= 0.011


@pytest.mark.asyncio
async def test_custom_workflow_id_and_last_id():
    orch = Orchestrator(emit_workflow_started=True)
    orch.register_agent(OK("a1"))

    custom_id = "wf-custom-123"
    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a1", task_type="x")])
    wf_id = await orch.execute_workflow(wf, workflow_id=custom_id)
    assert wf_id == custom_id
    assert orch.get_last_workflow_id() == custom_id

    # Ensure events use the custom id
    events = await orch.event_store.replay(custom_id)
    assert events[0].payload.get("workflow_id") == custom_id


@pytest.mark.asyncio
async def test_debug_list_workflows_returns_created_ids():
    orch = Orchestrator(emit_workflow_started=True)
    orch.register_agent(OK("a1"))

    wf1 = await orch.execute_workflow(WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a1", task_type="x")]))
    wf2 = await orch.execute_workflow(WorkflowDefinition(tasks=[TaskNode(task_id="t2", agent_id="a1", task_type="y")]))

    dbg = DebugInterface(event_store=orch.event_store)
    ids = await dbg.list_workflows()
    # Should contain both
    assert wf1 in ids and wf2 in ids
    # limit should return most recent
    assert dbg is not None
    recent = await dbg.list_workflows(limit=1)
    assert recent == [wf2]
