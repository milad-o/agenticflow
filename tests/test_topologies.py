from agenticflow.orchestration.topologies import pipeline, PipelineStage, fanout_reduce
from agenticflow.orchestration.core.orchestrator import WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode


def test_pipeline_topology_basic():
    stages = [
        PipelineStage(task_id="s1", agent_id="a1", task_type="x", params={}),
        PipelineStage(task_id="s2", agent_id="a2", task_type="y", params={}),
        PipelineStage(task_id="s3", agent_id="a3", task_type="z", params={}),
    ]
    wf = pipeline(stages)
    assert isinstance(wf, WorkflowDefinition)
    # s2 depends on s1, s3 on s2
    t = {t.task_id: t for t in wf.tasks}
    assert t["s2"].dependencies == {"s1"}
    assert t["s3"].dependencies == {"s2"}


def test_fanout_reduce_topology():
    f1 = TaskNode(task_id="f1", agent_id="a", task_type="x", params={})
    f2 = TaskNode(task_id="f2", agent_id="a", task_type="x", params={})
    red = TaskNode(task_id="join", agent_id="b", task_type="r", params={}, dependencies=set())
    wf = fanout_reduce(fanout_tasks=[f1, f2], reduce_task=red)
    t = {t.task_id: t for t in wf.tasks}
    assert t["join"].dependencies == {"f1", "f2"}
