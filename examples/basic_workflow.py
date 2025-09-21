import asyncio

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode


async def main() -> None:
    orch = Orchestrator()
    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="analyze_data", agent_id="analyst", task_type="analyze"),
        TaskNode(task_id="generate_report", agent_id="reporter", task_type="report", dependencies={"analyze_data"}),
    ])
    wf_id = await orch.execute_workflow(wf)
    print(f"Started workflow: {wf_id}")


if __name__ == "__main__":
    asyncio.run(main())
