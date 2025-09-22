import asyncio
import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent


class Boom(Agent):
    async def perform_task(self, task_type, params):
        raise RuntimeError("boom")


class OK(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


@pytest.mark.asyncio
async def test_circuit_breaker_opens_and_blocks():
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True, circuit_failure_threshold=1, circuit_reset_seconds=60)
    boom = Boom("bad")
    orch.register_agent(boom)

    wf1 = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="bad", task_type="x", retries=0)])
    with pytest.raises(Exception):
        await orch.execute_workflow(wf1)

    # After first failure, circuit should open
    # Next workflow should be blocked due to open circuit
    wf2 = WorkflowDefinition(tasks=[TaskNode(task_id="t2", agent_id="bad", task_type="y")])
    with pytest.raises(Exception):
        await orch.execute_workflow(wf2)

    events = await orch.event_store.replay(orch.get_last_workflow_id())
    types = [e.event_type for e in events]
    assert "circuit_open" in types or "task_circuit_blocked" in types


@pytest.mark.asyncio
async def test_rate_limiting_emits_throttle_event(monkeypatch):
    sleeps = []

    async def fake_sleep(d):
        sleeps.append(d)
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    orch = Orchestrator(emit_workflow_started=True, default_agent_qps=1.0)
    ok = OK("a1")
    orch.register_agent(ok)

    # Two tasks for same agent without dependency; second should be throttled
    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="a1", task_type="x"),
        TaskNode(task_id="t2", agent_id="a1", task_type="y"),
    ])
    wf_id = await orch.execute_workflow(wf)

    events = await orch.event_store.replay(wf_id)
    types = [e.event_type for e in events]
    assert "agent_throttled" in types or len(sleeps) >= 1
