import pytest

from agenticflow.agents.base.agent import Agent
from agenticflow.agents.supervisor.base import SupervisorAgent, NoopTaskDecomposer
from agenticflow.orchestration.core.orchestrator import Orchestrator


class WorkerAgent(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


@pytest.mark.asyncio
async def test_supervisor_noop_decomposition_executes():
    orch = Orchestrator()
    # Register default worker agent expected by NoopTaskDecomposer
    orch.register_agent(WorkerAgent("worker"))

    sup = SupervisorAgent("super", orchestrator=orch, decomposer=NoopTaskDecomposer(default_agent_id="worker"))
    wf_id = await sup.handle_user_query("hello")

    events = await orch.event_store.replay(wf_id)
    types = [e.event_type for e in events]
    assert types == ["task_assigned", "task_completed"]
