from agenticflow.orchestration.core.orchestrator import WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.observability.graph import mermaid_from_definition


def test_mermaid_basic():
    tasks = [
        TaskNode(task_id="a", agent_id="x", task_type="do", params={}),
        TaskNode(task_id="b", agent_id="y", task_type="do", params={}, dependencies={"a"}),
    ]
    m = mermaid_from_definition(WorkflowDefinition(tasks=tasks))
    assert "flowchart TD" in m
    assert "a --> b" in m
