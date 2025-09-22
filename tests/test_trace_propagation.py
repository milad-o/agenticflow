import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent


class OkAgent(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


class FlakyAgent(Agent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.count = 0

    async def perform_task(self, task_type, params):
        self.count += 1
        if self.count == 1:
            raise RuntimeError("flaky once")
        return {"ok": True}


@pytest.mark.asyncio
async def test_events_include_correlation_id_and_trace_id():
    orch = Orchestrator()
    orch.register_agent(OkAgent("a1"))

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="a1", task_type="x"),
    ])

    wf_id = await orch.execute_workflow(wf)
    events = await orch.event_store.replay(wf_id)

    # Must include assigned and completed
    types = [e.event_type for e in events]
    assert types == ["task_assigned", "task_completed"]

    assigned, completed = events

    # trace_id should be workflow_id
    assert assigned.trace_id == wf_id
    assert completed.trace_id == wf_id

    # correlation_id should be present in payloads and be identical for the same task attempt
    ac = assigned.payload.get("correlation_id")
    cc = completed.payload.get("correlation_id")
    assert isinstance(ac, str) and ac
    assert isinstance(cc, str) and cc
    assert ac == cc

    # correlation_id should contain workflow and task id for debuggability
    assert "t1" in ac
    assert wf_id in ac


@pytest.mark.asyncio
async def test_correlation_id_changes_between_attempts_and_matches_within_attempt():
    orch = Orchestrator()
    flaky = FlakyAgent("flaky")
    orch.register_agent(flaky)

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="flaky", task_type="x", retries=1, timeout_seconds=1),
    ])

    wf_id = await orch.execute_workflow(wf)
    events = await orch.event_store.replay(wf_id)

    # Expect: assigned(fail), failed, assigned(succeed), completed
    types = [e.event_type for e in events]
    assert types == ["task_assigned", "task_failed", "task_assigned", "task_completed"]

    a1, f1, a2, c2 = events
    # trace id consistent
    for e in events:
        assert e.trace_id == wf_id

    # correlation ids present
    c1 = a1.payload.get("correlation_id")
    c1f = f1.payload.get("correlation_id")
    c2a = a2.payload.get("correlation_id")
    c2c = c2.payload.get("correlation_id")

    assert c1 and c1f and c2a and c2c
    # First attempt correlation ids match between assigned and failed
    assert c1 == c1f
    # Second attempt correlation ids match between assigned and completed
    assert c2a == c2c
    # Attempts should have different correlation ids
    assert c1 != c2a
