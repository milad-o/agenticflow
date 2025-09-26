"""
Flow - Main Orchestration Class

Implements the Flow-Supervisor-Planner-Workers architecture using LangGraph.
"""
import asyncio
from typing import Dict, Any, Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
import os

from ..teams import SupervisorAgent, TeamState, TeamGraph


class Flow:
    """Main orchestration class for hierarchical agent teams."""

    def __init__(self, llm: Optional[BaseChatModel] = None):
        # Setup LLM (default to OpenAI if API key available)
        if llm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
            else:
                raise ValueError("LLM required. Provide llm parameter or set OPENAI_API_KEY")

        self.llm = llm

        # Worker agents
        self.workers: Dict[str, Any] = {}

        # Team components (created when first worker is added)
        self.supervisor: Optional[SupervisorAgent] = None
        self.team_graph: Optional[TeamGraph] = None

    def add_worker(self, name: str, worker: Any) -> "Flow":
        """Add a specialized worker agent to the team."""
        self.workers[name] = worker

        # Create/update supervisor and team graph
        self._setup_team()

        print(f"✅ Added {name} worker to hierarchical team")
        return self

    def remove_worker(self, name: str) -> "Flow":
        """Remove a worker from the team."""
        if name in self.workers:
            del self.workers[name]
            self._setup_team()
            print(f"❌ Removed {name} worker from team")
        return self

    def list_workers(self) -> List[str]:
        """List all worker names."""
        return list(self.workers.keys())

    def _setup_team(self) -> None:
        """Setup supervisor and team graph with current workers."""
        if not self.workers:
            self.supervisor = None
            self.team_graph = None
            return

        # Create supervisor with current workers
        self.supervisor = SupervisorAgent(self.llm, self.workers)

        # Create team coordination graph
        self.team_graph = TeamGraph(self.supervisor)

    async def execute(self, task: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task using the hierarchical team."""

        if not self.team_graph:
            raise ValueError("No workers added to the team. Use add_worker() first.")

        print(f"🚀 Executing hierarchical team task: {task}")
        print(f"   Team: {', '.join(self.workers.keys())}")

        # Execute using team graph
        final_state = await self.team_graph.execute_team_task(task, config)

        # Return results
        result = {
            "success": final_state.is_complete and not final_state.error_message,
            "task": final_state.current_task,
            "workers_used": final_state.completed_workers,
            "messages": final_state.messages,
            "results": final_state.worker_results,
            "error": final_state.error_message,
            "summary": final_state.get_summary()
        }

        # Print summary
        if result["success"]:
            print(f"✅ Task completed successfully!")
            print(f"   Workers used: {', '.join(final_state.completed_workers)}")
        else:
            print(f"❌ Task failed: {final_state.error_message}")

        return result

    def describe_team(self) -> Dict[str, Any]:
        """Describe the current team configuration."""
        if not self.supervisor:
            return {"workers": [], "capabilities": {}}

        return {
            "workers": list(self.workers.keys()),
            "capabilities": self.supervisor.worker_capabilities,
            "supervisor_active": self.supervisor is not None,
            "llm_model": getattr(self.llm, 'model_name', 'unknown')
        }

    # Convenience methods
    async def arun(self, task: str) -> Dict[str, Any]:
        """Alias for execute()"""
        return await self.execute(task)

    def run(self, task: str) -> Dict[str, Any]:
        """Synchronous version of execute()"""
        return asyncio.run(self.execute(task))