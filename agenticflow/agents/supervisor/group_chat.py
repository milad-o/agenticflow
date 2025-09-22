from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ...orchestration.core.orchestrator import WorkflowDefinition
from ...orchestration.tasks.graph import TaskNode


@dataclass(frozen=True)
class GroupChatSupervisor:
    """Builds a static multi-round group chat workflow across local agents.

    This produces a DAG where each message is a task assigned to its agent_id
    with task_type (default: "chat"). Each message depends on all prior messages,
    ensuring a deterministic order among rounds while allowing per-round parallelism
    if desired (by customizing dependencies later).
    """

    agent_task_type: str = "chat"

    def build_workflow(self, *, participants: List[str], rounds: int, topic: str) -> WorkflowDefinition:
        if rounds <= 0 or not participants:
            return WorkflowDefinition(tasks=[])
        tasks: List[TaskNode] = []
        prior_ids: List[str] = []
        for r in range(1, rounds + 1):
            for idx, agent_id in enumerate(participants):
                tid = f"round{r}_{agent_id}_{idx}"
                node = TaskNode(
                    task_id=tid,
                    agent_id=agent_id,
                    task_type=self.agent_task_type,
                    params={"topic": topic, "round": r, "speaker": agent_id},
                    dependencies=set(prior_ids),
                )
                tasks.append(node)
                prior_ids.append(tid)
        return WorkflowDefinition(tasks=tasks)