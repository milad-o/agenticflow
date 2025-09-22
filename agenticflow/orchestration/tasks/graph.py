from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass(frozen=True)
class TaskNode:
    task_id: str
    agent_id: str
    task_type: str
    params: Dict[str, object] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    retries: int = 0
    timeout_seconds: int = 30
    # Optional per-task retry policy overrides
    retry_backoff_base: float | None = None
    retry_jitter: float | None = None
    retry_max_backoff: float | None = None
    # Compensation support
    enable_compensation: bool = False
    compensation_params: Dict[str, object] = field(default_factory=dict)


class TaskGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, TaskNode] = {}

    def add_task(self, node: TaskNode) -> None:
        self.nodes[node.task_id] = node
