import asyncio
from pathlib import Path

import pytest

from agenticflow.agents.tool_agent import ToolAgent
from agenticflow.agents.tools.builtin import FSReadTool
from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode


class AllowAllSecurity:
    principal = "tester"
    async def authorize(self, action: str, resource: str):
        return True


@pytest.mark.asyncio
async def test_tool_agent_fs_read(tmp_path: Path):
    p = tmp_path / "hello.txt"
    p.write_text("hello world")
    tool = FSReadTool(roots=[str(tmp_path)])
    agent = ToolAgent("reader", tools={tool.name: tool}, security=AllowAllSecurity())

    orch = Orchestrator()
    orch.register_agent(agent)
    wf = WorkflowDefinition(tasks=[TaskNode(task_id="read", agent_id="reader", task_type="http_fetch", params={"tool": "fs_read", "path": str(p)})])
    wid = await orch.execute_workflow(wf)
    assert wid
