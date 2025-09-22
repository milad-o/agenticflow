import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent
from agenticflow.security.policy import PolicyGuard


class OK(Agent):
    async def perform_task(self, t, p):
        return {"ok": True}


@pytest.mark.asyncio
async def test_policy_guard_denies_disallowed_task():
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(OK("a"))
    orch.set_policy_guard(PolicyGuard(allow_agent_tasks={"a": ["x"]}))

    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a", task_type="y", params={})])
    with pytest.raises(Exception):
        await orch.execute_workflow(wf)


@pytest.mark.asyncio
async def test_policy_guard_allows_allowed_task():
    orch = Orchestrator()
    orch.register_agent(OK("a"))
    orch.set_policy_guard(PolicyGuard(allow_agent_tasks={"a": ["x"]}))

    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a", task_type="x", params={})])
    wid = await orch.execute_workflow(wf)
    assert wid