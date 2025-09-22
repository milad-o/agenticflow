import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent
from agenticflow.observability.debug import DebugInterface


class A1(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


class A2(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


@pytest.mark.asyncio
async def test_debug_timelines_workflow_and_agent():
    orch = Orchestrator()
    orch.register_agent(A1("analyst"))
    orch.register_agent(A2("reporter"))

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="analyst", task_type="analyze"),
        TaskNode(task_id="t2", agent_id="reporter", task_type="report", dependencies={"t1"}),
    ])

    wf_id = await orch.execute_workflow(wf)

    dbg = DebugInterface(event_store=orch.event_store)
    w_events = await dbg.get_workflow_timeline(wf_id)
    a_events = await dbg.get_agent_timeline("analyst")

    assert [e.event_type for e in w_events] == [
        "task_assigned", "task_completed", "task_assigned", "task_completed"
    ]
    assert [e.event_type for e in a_events] == ["task_assigned", "task_completed"]
