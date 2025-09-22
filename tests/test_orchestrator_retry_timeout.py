import asyncio
import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent


class FlakyAgent(Agent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.count = 0

    async def perform_task(self, task_type, params):
        self.count += 1
        if self.count == 1:
            raise RuntimeError("flaky once")
        return {"ok": True}


class SlowAgent(Agent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.count = 0

    async def perform_task(self, task_type, params):
        self.count += 1
        if self.count == 1:
            await asyncio.sleep(0.2)
        return {"ok": True}


@pytest.mark.asyncio
async def test_orchestrator_retries_then_succeeds():
    orch = Orchestrator()
    flaky = FlakyAgent("flaky")
    orch.register_agent(flaky)

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="flaky", task_type="x", retries=1, timeout_seconds=1),
    ])

    wf_id = await orch.execute_workflow(wf)

    # Ensure the flaky ran twice
    assert flaky.count == 2


@pytest.mark.asyncio
async def test_orchestrator_timeout_then_retries():
    orch = Orchestrator()
    slow = SlowAgent("slow")
    orch.register_agent(slow)

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="slow", task_type="x", retries=1, timeout_seconds=0.05),
    ])

    # First run will timeout; second should succeed
    wf_id = await orch.execute_workflow(wf)
    assert slow.count == 2
