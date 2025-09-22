import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent
from agenticflow.observability.debug import DebugInterface
from agenticflow.observability.progress import emit_progress


class ProgressAgent(Agent):
    async def perform_task(self, t, p):
        # Emit mid-task progress events
        for i in range(3):
            await emit_progress("tick", {"i": i})
        return {"ok": True}


@pytest.mark.asyncio
async def test_task_progress_events_emitted():
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(ProgressAgent("p"))
    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t", agent_id="p", task_type="run", params={})])
    wid = await orch.execute_workflow(wf)

    dbg = DebugInterface(event_store=orch.event_store)
    events = await dbg.event_store.replay(wid)
    kinds = [e.payload.get("kind") for e in events if e.event_type == "task_progress"]
    assert kinds == ["tick", "tick", "tick"]
