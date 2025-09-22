import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent
from agenticflow.adapters.store.memory import InMemoryEventStore


class OK(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


class AlwaysFail(Agent):
    async def perform_task(self, task_type, params):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_resume_completes_remaining_tasks():
    store = InMemoryEventStore()

    # First run: second task fails without retries -> workflow raises
    orch1 = Orchestrator(event_store=store, emit_workflow_started=True)
    orch1.register_agent(OK("a1"))
    orch1.register_agent(AlwaysFail("a2"))

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="t1", agent_id="a1", task_type="x"),
        TaskNode(task_id="t2", agent_id="a2", task_type="y", dependencies={"t1"}, retries=0),
    ])

    with pytest.raises(Exception):
        await orch1.execute_workflow(wf)

    # Discover workflow id from workflow_started
    wf_id = None
    async for ev in store.query_all():
        if ev.event_type == "workflow_started":
            wf_id = ev.payload.get("workflow_id")
    assert wf_id, "workflow_id not found in events"

    # Resume with a successful agent for t2
    orch2 = Orchestrator(event_store=store, emit_workflow_started=True)
    orch2.register_agent(OK("a1"))
    orch2.register_agent(OK("a2"))

    # Resume the discovered workflow id
    rid = await orch2.resume_workflow(wf_id)
    assert rid == wf_id

    events = await store.replay(wf_id)
    types = [e.event_type for e in events]

    # Expect: workflow_started, t1 assigned+completed, t2 assigned+failed, then t2 assigned+completed after resume
    assert types == [
        "workflow_started",
        "task_assigned", "task_completed",
        "task_assigned", "task_failed",
        "task_assigned", "task_completed",
    ]

    # Attempt continuity for t2
    t2_events = [e for e in events if e.payload.get("task_id") == "t2" and e.event_type != "workflow_started"]
    # First two are assigned+failed (attempt 0), next two assigned+completed (attempt 1)
    # Compare correlation_id suffix
    cids = [e.payload.get("correlation_id") for e in t2_events]
    assert all(cids)
    first_attempt = cids[0].split(":")[-1]
    second_attempt = cids[2].split(":")[-1]
    assert first_attempt != second_attempt
