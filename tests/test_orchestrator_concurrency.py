import asyncio
import time
from pathlib import Path

import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent


class SleepAgent(Agent):
    def __init__(self, agent_id: str, delay: float):
        super().__init__(agent_id)
        self.delay = delay

    async def perform_task(self, task_type, params):
        await asyncio.sleep(self.delay)
        return {"ok": True}


@pytest.mark.asyncio
async def test_parallel_execution_reduces_time():
    orch = Orchestrator(max_parallelism=2)
    orch.register_agent(SleepAgent("a", 0.5))
    orch.register_agent(SleepAgent("b", 0.5))
    tasks = [
        TaskNode(task_id="t1", agent_id="a", task_type="do", params={}),
        TaskNode(task_id="t2", agent_id="b", task_type="do", params={}),
    ]
    wf = WorkflowDefinition(tasks=tasks)
    t0 = time.perf_counter()
    await orch.execute_workflow(wf)
    dt = time.perf_counter() - t0
    assert dt < 0.9, f"expected <0.9s, got {dt}"  # parallel ~0.5s


@pytest.mark.asyncio
async def test_per_agent_concurrency_limits_serialization():
    orch = Orchestrator(max_parallelism=2, per_agent_concurrency=1)
    orch.register_agent(SleepAgent("a", 0.5))
    tasks = [
        TaskNode(task_id="t1", agent_id="a", task_type="do", params={}),
        TaskNode(task_id="t2", agent_id="a", task_type="do", params={}),
    ]
    wf = WorkflowDefinition(tasks=tasks)
    t0 = time.perf_counter()
    await orch.execute_workflow(wf)
    dt = time.perf_counter() - t0
    assert dt >= 0.95, f"expected ~1.0s serialized, got {dt}"
