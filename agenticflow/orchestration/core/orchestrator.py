from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from ..tasks.graph import TaskGraph, TaskNode


@dataclass(frozen=True)
class WorkflowDefinition:
    tasks: List[TaskNode]


class Orchestrator:
    def __init__(self) -> None:
        self._active: Dict[str, TaskGraph] = {}

    async def execute_workflow(self, defn: WorkflowDefinition) -> str:
        # TODO: Implement DAG execution with retries/timeouts in Phase 1
        _ = defn
        workflow_id = "wf-placeholder"
        self._active[workflow_id] = TaskGraph()
        return workflow_id
