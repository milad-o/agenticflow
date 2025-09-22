import pytest

from agenticflow.orchestration.core.orchestrator import WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.orchestration.topologies import (
    PipelineStage,
    pipeline,
    fanout_reduce,
    PipelineTopology,
    FanoutReduceTopology,
)


def tasks_to_tuples(wf: WorkflowDefinition):
    return sorted(
        (
            t.task_id,
            t.agent_id,
            t.task_type,
            tuple(sorted(t.dependencies)),
            tuple(sorted(t.params.items())),
        )
        for t in wf.tasks
    )


def test_pipeline_topology_matches_function():
    stages = [
        PipelineStage("t1", "a1", "x", {"p": 1}),
        PipelineStage("t2", "a2", "y", {"q": 2}),
        PipelineStage("t3", "a3", "z", {}),
    ]
    wf_func = pipeline(stages)
    wf_oop = PipelineTopology(stages).build()
    assert tasks_to_tuples(wf_oop) == tasks_to_tuples(wf_func)


def test_fanout_reduce_topology_matches_function():
    f1 = TaskNode(task_id="f1", agent_id="a1", task_type="x", params={})
    f2 = TaskNode(task_id="f2", agent_id="a2", task_type="y", params={})
    red = TaskNode(task_id="r", agent_id="ar", task_type="reduce", params={}, dependencies={"pre"})
    wf_func = fanout_reduce(fanout_tasks=[f1, f2], reduce_task=red)
    wf_oop = FanoutReduceTopology(fanout=[f1, f2], reduce=red).build()
    assert tasks_to_tuples(wf_oop) == tasks_to_tuples(wf_func)
