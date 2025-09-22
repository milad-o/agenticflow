from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence

from .core.orchestrator import WorkflowDefinition
from .tasks.graph import TaskNode


@dataclass(frozen=True)
class PipelineStage:
    task_id: str
    agent_id: str
    task_type: str
    params: dict


def pipeline(stages: Sequence[PipelineStage]) -> WorkflowDefinition:
    tasks: List[TaskNode] = []
    prev_id: str | None = None
    for st in stages:
        deps = {prev_id} if prev_id else set()
        tasks.append(TaskNode(task_id=st.task_id, agent_id=st.agent_id, task_type=st.task_type, params=dict(st.params), dependencies=deps))
        prev_id = st.task_id
    return WorkflowDefinition(tasks=tasks)


class PipelineTopology:
    """OOP helper for building linear pipelines.

    Example:
        stages = [
            PipelineStage("read", "reader", "fs_read", {"path": "README.md"}),
            PipelineStage("stats", "processor", "compute_stats", {"path": "README.md"}),
        ]
        wf = PipelineTopology(stages).build()
    """

    def __init__(self, stages: Sequence[PipelineStage] | None = None) -> None:
        self._stages: List[PipelineStage] = list(stages or [])

    def add(self, stage: PipelineStage) -> "PipelineTopology":
        self._stages.append(stage)
        return self

    def extend(self, stages: Sequence[PipelineStage]) -> "PipelineTopology":
        self._stages.extend(stages)
        return self

    @property
    def stages(self) -> List[PipelineStage]:
        return list(self._stages)

    def build(self) -> WorkflowDefinition:
        return pipeline(self._stages)


def fanout_reduce(
    *,
    fanout_tasks: Sequence[TaskNode],
    reduce_task: TaskNode,
) -> WorkflowDefinition:
    # ensure reduce_task depends on all fanout task_ids
    deps = set(reduce_task.dependencies)
    deps.update(t.task_id for t in fanout_tasks)
    red = TaskNode(
        task_id=reduce_task.task_id,
        agent_id=reduce_task.agent_id,
        task_type=reduce_task.task_type,
        params=dict(reduce_task.params),
        dependencies=deps,
        retries=reduce_task.retries,
        timeout_seconds=reduce_task.timeout_seconds,
    )
    return WorkflowDefinition(tasks=list(fanout_tasks) + [red])


class FanoutReduceTopology:
    """OOP helper for fanout + reduce workflows.

    Example:
        wf = FanoutReduceTopology(fanout=[...], reduce=reduce_node).build()
    """

    def __init__(self, *, fanout: Sequence[TaskNode] | None = None, reduce: TaskNode | None = None) -> None:  # noqa: A002
        self._fanout: List[TaskNode] = list(fanout or [])
        self._reduce: TaskNode | None = reduce

    def add_fanout(self, node: TaskNode) -> "FanoutReduceTopology":
        self._fanout.append(node)
        return self

    def set_reduce(self, node: TaskNode) -> "FanoutReduceTopology":
        self._reduce = node
        return self

    @property
    def fanout(self) -> List[TaskNode]:
        return list(self._fanout)

    @property
    def reduce(self) -> TaskNode | None:
        return self._reduce

    def build(self) -> WorkflowDefinition:
        if self._reduce is None:
            return WorkflowDefinition(tasks=list(self._fanout))
        return fanout_reduce(fanout_tasks=self._fanout, reduce_task=self._reduce)
