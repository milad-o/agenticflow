import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent


class OK(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


class Boom(Agent):
    async def perform_task(self, task_type, params):
        raise RuntimeError("nope")


@pytest.mark.asyncio
async def test_workflow_completed_event_emitted_when_enabled():
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(OK("a1"))

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="a1", task_type="x"),
    ])

    wf_id = await orch.execute_workflow(wf)

    events = await orch.event_store.replay(wf_id)
    types = [e.event_type for e in events]
    assert types == ["workflow_started", "task_assigned", "task_completed", "workflow_completed"]


@pytest.mark.asyncio
async def test_workflow_failed_event_emitted_before_raise():
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(Boom("a1"))

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="a1", task_type="x", retries=0),
    ])

    with pytest.raises(Exception):
        await orch.execute_workflow(wf)

    # get wf id from started event
    wf_id = None
    async for ev in orch.event_store.query_all():
        if ev.event_type == "workflow_started":
            wf_id = ev.payload.get("workflow_id")
    assert wf_id

    events = await orch.event_store.replay(wf_id)
    types = [e.event_type for e in events]
    # Expect failure emitted after task_failed
    assert types == ["workflow_started", "task_assigned", "task_failed", "workflow_failed"]
