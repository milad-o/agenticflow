import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent


class NoopAgent(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


@pytest.mark.asyncio
async def test_workflow_event_sequence_in_order():
    orch = Orchestrator()
    orch.register_agent(NoopAgent("a1"))
    orch.register_agent(NoopAgent("a2"))

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="a1", task_type="x"),
        TaskNode(task_id="t2", agent_id="a2", task_type="y", dependencies={"t1"}),
    ])

    wf_id = await orch.execute_workflow(wf)

    events = await orch.event_store.replay(wf_id)
    types = [e.event_type for e in events]

    assert types == [
        "task_assigned", "task_completed",  # t1
        "task_assigned", "task_completed",  # t2
    ]
