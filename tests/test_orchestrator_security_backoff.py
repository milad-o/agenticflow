import asyncio
import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent
from agenticflow.security.context import SecurityContext
from agenticflow.core.exceptions.base import SecurityError


class OK(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


class Flaky(Agent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.count = 0

    async def perform_task(self, task_type, params):
        self.count += 1
        if self.count == 1:
            raise RuntimeError("first fails")
        return {"ok": True}


@pytest.mark.asyncio
async def test_orchestrator_security_denied_emits_event_and_raises():
    sec = SecurityContext(principal="u1", permissions={})
    orch = Orchestrator(security=sec, emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(OK("a1"))

    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a1", task_type="x")])

    with pytest.raises(SecurityError):
        await orch.execute_workflow(wf)

    # find workflow id
    wf_id = None
    async for ev in orch.event_store.query_all():
        if ev.event_type == "workflow_started":
            wf_id = ev.payload.get("workflow_id")
    assert wf_id

    events = await orch.event_store.replay(wf_id)
    types = [e.event_type for e in events]
    assert types[0] == "workflow_started"
    assert "task_authorization_denied" in types
    # No task_assigned should occur
    assert "task_assigned" not in types
    # Lifecycle failure is emitted
    assert "workflow_failed" in types


@pytest.mark.asyncio
async def test_orchestrator_security_authorized_emits_event_then_assigns():
    sec = SecurityContext(principal="u1", permissions={"assign:task:a1:x": True})
    orch = Orchestrator(security=sec, emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(OK("a1"))

    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a1", task_type="x")])
    wf_id = await orch.execute_workflow(wf)

    events = await orch.event_store.replay(wf_id)
    types = [e.event_type for e in events]
    # Ensure authorized precedes assigned
    assert types[:2] == ["workflow_started", "task_authorized"]
    assert "task_assigned" in types and "task_completed" in types
    assert types[-1] == "workflow_completed"


@pytest.mark.asyncio
async def test_retry_backoff_with_jitter(monkeypatch):
    # Capture sleeps
    sleeps = []

    async def fake_sleep(duration):
        sleeps.append(duration)
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    orch = Orchestrator(retry_backoff_base=0.1, retry_jitter=0.0)
    flaky = Flaky("a1")
    orch.register_agent(flaky)

    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a1", task_type="x", retries=1, timeout_seconds=1)])
    await orch.execute_workflow(wf)

    # Expect one sleep ~0.1s before retry
    assert len(sleeps) == 1
    assert 0.09 <= sleeps[0] <= 0.11
