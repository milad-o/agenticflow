import pytest
import asyncio

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent


class SlowOK(Agent):
    async def perform_task(self, task_type, params):
        await asyncio.sleep(0.05)
        return {"ok": True}


class Boom(Agent):
    async def perform_task(self, task_type, params):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_max_duration_timeout_emits_and_stops():
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(SlowOK("a1"))
    orch.register_agent(SlowOK("a2"))

    wf = WorkflowDefinition(
        tasks=[
            TaskNode(task_id="t1", agent_id="a1", task_type="x"),
            TaskNode(task_id="t2", agent_id="a2", task_type="y", dependencies={"t1"}),
        ],
        max_duration_seconds=0,  # practically immediate timeout
    )

    wf_id = await orch.execute_workflow(wf)
    events = await orch.event_store.replay(wf_id)
    types = [e.event_type for e in events]
    # Started, then likely assigned or timeout first depending on timing, but must include workflow_timed_out
    assert "workflow_timed_out" in types


@pytest.mark.asyncio
async def test_compensation_on_failure_when_enabled():
    class CompAgent(Agent):
        def __init__(self, agent_id):
            super().__init__(agent_id)
            self.compensated = False

        async def perform_task(self, task_type, params):
            return {"ok": True}

        async def compensate_task(self, task_type, params, result=None):
            self.compensated = True
            return {"undone": True}

    comp = CompAgent("a1")
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(comp)
    orch.register_agent(Boom("boom"))

    wf = WorkflowDefinition(
        tasks=[
            TaskNode(task_id="t1", agent_id="a1", task_type="x", enable_compensation=True),
            TaskNode(task_id="t2", agent_id="boom", task_type="y", dependencies={"t1"}),
        ],
        enable_compensation=True,
    )

    with pytest.raises(Exception):
        await orch.execute_workflow(wf)

    assert comp.compensated is True
    events = await orch.event_store.replay(orch.get_last_workflow_id())
    types = [e.event_type for e in events]
    assert "task_compensated" in types
