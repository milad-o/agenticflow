import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent
from agenticflow.observability.debug import DebugInterface


class A(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


@pytest.mark.asyncio
async def test_debug_filters_and_summary():
    orch = Orchestrator()
    orch.register_agent(A("a1"))
    orch.register_agent(A("a2"))

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="a1", task_type="x"),
        TaskNode(task_id="t2", agent_id="a2", task_type="y", dependencies={"t1"}),
    ])

    wf_id = await orch.execute_workflow(wf)

    dbg = DebugInterface(event_store=orch.event_store)

    # Filter only completed events
    completed = await dbg.get_workflow_timeline(wf_id, event_types=["task_completed"])
    assert len(completed) == 2
    assert all(e.event_type == "task_completed" for e in completed)

    summary = await dbg.get_workflow_summary(wf_id)
    assert summary.workflow_id == wf_id
    assert summary.event_counts.get("task_assigned") == 2
    assert summary.event_counts.get("task_completed") == 2
    assert summary.unique_tasks == 2
    assert summary.unique_agents == 2
    assert summary.duration_s is not None
