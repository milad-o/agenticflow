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


class TaskGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, TaskNode] = {}

    def add_task(self, node: TaskNode) -> None:
        self.nodes[node.task_id] = node
