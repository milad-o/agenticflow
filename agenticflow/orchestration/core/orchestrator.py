from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from ..tasks.graph import TaskGraph, TaskNode
from ...core.events.event import AgenticEvent
from ...adapters.bus.memory import InMemoryEventBus
from ...adapters.store.memory import InMemoryEventStore
from ...agents.base.agent import Agent


@dataclass(frozen=True)
class WorkflowDefinition:
    tasks: List[TaskNode]


class Orchestrator:
    def __init__(self) -> None:
        self._active: Dict[str, TaskGraph] = {}
        self._agents: Dict[str, Agent] = {}
        self.event_bus = InMemoryEventBus()
        self.event_store = InMemoryEventStore()

    def register_agent(self, agent: Agent) -> None:
        self._agents[agent.agent_id] = agent

    async def execute_workflow(self, defn: WorkflowDefinition) -> str:
        # Build graph
        graph = TaskGraph()
        for t in defn.tasks:
            graph.add_task(t)
        workflow_id = f"wf-{len(self._active)+1}"
        self._active[workflow_id] = graph

        # Simple dependency-resolution loop (sequential)
        completed: Set[str] = set()
        remaining = set(graph.nodes.keys())

        while remaining:
            # find ready tasks
            ready = [
                graph.nodes[tid]
                for tid in list(remaining)
                if graph.nodes[tid].dependencies.issubset(completed)
            ]
            if not ready:
                raise RuntimeError(f"Deadlock or missing dependencies in workflow {workflow_id}")

            for task in ready:
                # Emit task_assigned
                assigned = AgenticEvent.create(
                    "task_assigned",
                    {
                        "workflow_id": workflow_id,
                        "task_id": task.task_id,
                        "agent_id": task.agent_id,
                        "task_type": task.task_type,
                        "params": dict(task.params),
                    },
                    trace_id=workflow_id,
                )
                await self.event_store.append(workflow_id, [assigned])
                await self.event_bus.publish(assigned)

                # Execute via agent
                agent = self._agents.get(task.agent_id)
                if not agent:
                    # Emit task_failed
                    failed = AgenticEvent.create(
                        "task_failed",
                        {"workflow_id": workflow_id, "task_id": task.task_id, "reason": "agent_not_found"},
                        trace_id=workflow_id,
                    )
                    await self.event_store.append(workflow_id, [failed])
                    await self.event_bus.publish(failed)
                    raise RuntimeError(f"Agent {task.agent_id} not found")

                try:
                    await agent.perform_task(task.task_type, task.params)
                    # Emit task_completed
                    completed_event = AgenticEvent.create(
                        "task_completed",
                        {"workflow_id": workflow_id, "task_id": task.task_id},
                        trace_id=workflow_id,
                    )
                    await self.event_store.append(workflow_id, [completed_event])
                    await self.event_bus.publish(completed_event)
                    completed.add(task.task_id)
                    remaining.remove(task.task_id)
                except Exception as e:
                    failed = AgenticEvent.create(
                        "task_failed",
                        {"workflow_id": workflow_id, "task_id": task.task_id, "error": str(e)},
                        trace_id=workflow_id,
                    )
                    await self.event_store.append(workflow_id, [failed])
                    await self.event_bus.publish(failed)
                    raise

        return workflow_id
