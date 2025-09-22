from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .core.orchestrator import Orchestrator, WorkflowDefinition
from ..observability.debug import DebugInterface, WorkflowSummary


@dataclass
class WorkflowService:
    orchestrator: Orchestrator

    def __post_init__(self) -> None:
        self._debug = DebugInterface(event_store=self.orchestrator.event_store)

    async def start(self, defn: WorkflowDefinition, *, workflow_id: Optional[str] = None) -> str:
        return await self.orchestrator.execute_workflow(defn, workflow_id=workflow_id)

    async def resume(self, workflow_id: str) -> str:
        return await self.orchestrator.resume_workflow(workflow_id)

    async def cancel(self, workflow_id: str, *, reason: str = "user_cancelled") -> None:
        await self.orchestrator.cancel_workflow(workflow_id, reason=reason)

    async def list_workflows(self, limit: Optional[int] = None, status: Optional[str] = None) -> List[str]:
        return await self._debug.list_workflows(limit=limit, status=status)

    async def summaries(self, limit: Optional[int] = None, status: Optional[str] = None) -> List[WorkflowSummary]:
        return await self._debug.list_workflow_summaries(limit=limit, status=status)

    def last_workflow_id(self) -> Optional[str]:
        return self.orchestrator.get_last_workflow_id()
