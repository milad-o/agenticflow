"""
Team Coordination Graph

LangGraph-based coordination for Supervisor-Workers architecture.
"""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .team_state import TeamState
from .supervisor import SupervisorAgent


class TeamGraph:
    """Coordinates the Supervisor-Workers architecture using LangGraph."""

    def __init__(self, supervisor: SupervisorAgent):
        self.supervisor = supervisor
        self.checkpointer = MemorySaver()

        # Build the coordination graph
        self.graph = self._build_coordination_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)

    def _build_coordination_graph(self) -> StateGraph:
        """Build the Supervisor-Workers coordination graph."""

        def supervisor_node(state: TeamState) -> TeamState:
            """Supervisor coordination node."""
            import asyncio
            return asyncio.run(self.supervisor.coordinate_task(state))

        def should_continue(state: TeamState) -> Literal["supervisor", "__end__"]:
            """Decide whether to continue or end."""
            if state.is_complete or state.error_message:
                return "__end__"
            return "supervisor"

        # Build the graph
        workflow = StateGraph(TeamState)

        # Add supervisor node
        workflow.add_node("supervisor", supervisor_node)

        # Add edges
        workflow.add_edge(START, "supervisor")

        # Conditional routing - keep going until complete
        workflow.add_conditional_edges(
            "supervisor",
            should_continue,
            {
                "supervisor": "supervisor",
                "__end__": END
            }
        )

        return workflow

    async def execute_team_task(self, task: str, config: Dict[str, Any] = None) -> TeamState:
        """Execute a task using the hierarchical team."""

        # Initialize state
        initial_state = TeamState(
            current_task=task,
            messages=[{"role": "user", "content": task}]
        )

        # Execute the coordination graph
        config = config or {"configurable": {"thread_id": "team_execution"}}

        final_state = await self.compiled_graph.ainvoke(
            initial_state.dict(),
            config=config
        )

        return TeamState(**final_state)