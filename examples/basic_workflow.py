import asyncio

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.base.agent import Agent


class AnalystAgent(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


class ReporterAgent(Agent):
    async def perform_task(self, task_type, params):
        return {"ok": True}


async def main() -> None:
    orch = Orchestrator()
    orch.register_agent(AnalystAgent("analyst"))
    orch.register_agent(ReporterAgent("reporter"))

    wf = WorkflowDefinition(tasks=[
        TaskNode(task_id="analyze_data", agent_id="analyst", task_type="analyze"),
        TaskNode(task_id="generate_report", agent_id="reporter", task_type="report", dependencies={"analyze_data"}),
    ])
    wf_id = await orch.execute_workflow(wf)
    print(f"Started workflow: {wf_id}")


if __name__ == "__main__":
    asyncio.run(main())
