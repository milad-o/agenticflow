from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from ..base.agent import Agent
from ...orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from ...orchestration.tasks.graph import TaskNode


class TaskDecomposer:
    async def decompose(self, query: str, context: Dict[str, Any]) -> WorkflowDefinition:  # pragma: no cover (interface)
        raise NotImplementedError


class NoopTaskDecomposer(TaskDecomposer):
    def __init__(self, default_agent_id: str = "worker") -> None:
        self.default_agent_id = default_agent_id

    async def decompose(self, query: str, context: Dict[str, Any]) -> WorkflowDefinition:
        # Minimal decomposition: single task routed to default agent
        task = TaskNode(task_id="t1", agent_id=self.default_agent_id, task_type="noop", params={"query": query})
        return WorkflowDefinition(tasks=[task])


@dataclass
class SupervisorAgent(Agent):
    orchestrator: Orchestrator
    decomposer: TaskDecomposer

    async def handle_user_query(self, query: str, user_context: Dict[str, Any] | None = None) -> str:
        user_context = user_context or {}
        wf_def = await self.decomposer.decompose(query, user_context)
        wf_id = await self.orchestrator.execute_workflow(wf_def)
        return wf_id
