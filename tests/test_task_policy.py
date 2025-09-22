import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.security.policy import TaskSchemaRegistry
from agenticflow.agents.base.agent import Agent


class Noop(Agent):
    async def perform_task(self, t, p):
        return {"ok": True}


@pytest.mark.asyncio
async def test_task_schema_validation_blocks_invalid():
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(Noop("a"))
    # require param 'foo'
    reg = TaskSchemaRegistry(schemas={"a:x": {"type": "object", "required": ["foo"]}})
    orch.set_task_schema_registry(reg)

    wf = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a", task_type="x", params={})])
    with pytest.raises(Exception):
        await orch.execute_workflow(wf)
