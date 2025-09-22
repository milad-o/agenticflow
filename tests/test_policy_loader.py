import json
from pathlib import Path

import pytest

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent
from examples.utils.policy_loader import load_policy


class OK(Agent):
    async def perform_task(self, t, p):
        return {"ok": True}


@pytest.mark.asyncio
async def test_load_policy_from_json_and_apply(tmp_path: Path):
    # Create a simple JSON policy file
    policy_obj = {
        "schemas": {
            "a:x": {
                "type": "object",
                "properties": {"foo": {"type": "number"}},
                "required": ["foo"],
            }
        },
        "policy": {
            "allow_agent_tasks": {"a": ["x"]},
            "default_allow": False,
        },
    }
    p = tmp_path / "policy.json"
    p.write_text(json.dumps(policy_obj))

    loaded = load_policy(p)
    orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
    orch.register_agent(OK("a"))
    if loaded.schema:
        orch.set_task_schema_registry(loaded.schema)
    if loaded.guard:
        orch.set_policy_guard(loaded.guard)

    # Missing required 'foo' should be rejected by schema
    wf_bad = WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id="a", task_type="x", params={})])
    with pytest.raises(Exception):
        await orch.execute_workflow(wf_bad)

    # Providing foo should pass
    wf_ok = WorkflowDefinition(tasks=[TaskNode(task_id="t2", agent_id="a", task_type="x", params={"foo": 1})])
    wid = await orch.execute_workflow(wf_ok)
    assert wid
