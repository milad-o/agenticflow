"""
Supervisor Agent

Coordinates worker agents based on LangGraph hierarchical patterns.
"""
import asyncio
from typing import Dict, List, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .team_state import TeamState


class SupervisorAgent:
    """Supervisor agent that coordinates worker agents."""

    def __init__(self, llm: BaseChatModel, workers: Dict[str, Any]):
        self.llm = llm
        self.workers = workers
        self.worker_capabilities = self._analyze_worker_capabilities()

    def _analyze_worker_capabilities(self) -> Dict[str, List[str]]:
        """Analyze capabilities of each worker agent."""
        capabilities = {}
        for name, worker in self.workers.items():
            # Extract capabilities from worker
            if hasattr(worker, 'capabilities'):
                capabilities[name] = worker.capabilities
            elif hasattr(worker, 'skills'):
                capabilities[name] = worker.skills
            else:
                # Default capabilities based on name
                if 'file' in name.lower():
                    capabilities[name] = ['file_operations', 'data_discovery']
                elif 'report' in name.lower():
                    capabilities[name] = ['report_generation', 'content_creation']
                elif 'analysis' in name.lower():
                    capabilities[name] = ['data_analysis', 'computation']
                else:
                    capabilities[name] = ['general_tasks']

        return capabilities

    async def coordinate_task(self, state: TeamState) -> TeamState:
        """Main coordination logic - decide which worker should handle the task."""

        # If task is complete, do nothing
        if state.is_complete:
            return state

        # Safety check - limit total executions to prevent infinite loops
        if state.execution_count >= 10:
            state.mark_complete()
            state.add_message("supervisor", f"Task completed after {state.execution_count} worker executions")
            return state

        # Increment execution counter
        state.execution_count += 1

        # Determine next worker
        next_worker = await self._select_next_worker(state)

        if next_worker == "FINISH":
            state.mark_complete()
            return state

        if next_worker not in self.workers:
            state.mark_error(f"Unknown worker: {next_worker}")
            return state

        # Execute worker task
        try:
            worker = self.workers[next_worker]

            # Create worker-specific task
            worker_task = await self._create_worker_task(state, next_worker)

            # Execute worker
            result = await self._execute_worker(worker, worker_task)

            # Store result
            state.set_worker_result(next_worker, result)
            state.add_message(next_worker, f"Completed: {str(result)[:100]}...")

            # Update context for next iteration
            state.update_context(f"{next_worker}_completed", True)

        except Exception as e:
            state.mark_error(f"Worker {next_worker} failed: {str(e)}")

        return state

    async def _select_next_worker(self, state: TeamState) -> str:
        """Use LLM to intelligently select the next worker."""

        # Create selection prompt
        worker_list = list(self.workers.keys())
        completed = state.completed_workers

        prompt = f"""You are a supervisor coordinating a team of specialized agents.

TASK: {state.current_task}

ALL AVAILABLE WORKERS:
{self._format_workers_for_llm(worker_list)}

WORKERS THAT HAVE BEEN USED: {completed}

WORKER RESULTS SO FAR:
{self._format_results_for_llm(state.worker_results)}

DECISION CRITERIA:
- If the filesystem worker failed to find files, try a different search approach or move to analysis with available data
- If you have successfully found files, next step should be analysis
- If you have analysis results, next step should be reporting
- If you have all three (files found, analysis done, report created), respond "FINISH"
- If a worker keeps failing with the same error, try a different worker
- The task is: "{state.current_task}" - break it into steps: find -> analyze -> report

Based on what has been completed successfully and what still needs to be done:
Respond with ONLY: "FINISH" or one worker name ({', '.join(worker_list)})"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        # Parse response
        selected = response.content.strip().upper()

        # Validate selection
        if selected == "FINISH":
            return "FINISH"

        # Find matching worker (case insensitive)
        for worker in worker_list:
            if worker.upper() == selected:
                return worker

        # Fallback to first worker if selection is invalid
        return worker_list[0] if worker_list else "FINISH"

    def _format_workers_for_llm(self, workers: List[str]) -> str:
        """Format worker information for LLM selection."""
        formatted = []
        for worker in workers:
            caps = self.worker_capabilities.get(worker, ['general_tasks'])
            formatted.append(f"- {worker}: {', '.join(caps)}")
        return '\n'.join(formatted)

    def _format_results_for_llm(self, results: Dict[str, Any]) -> str:
        """Format worker results for LLM context."""
        if not results:
            return "None yet"

        formatted = []
        for worker, result in results.items():
            result_str = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
            formatted.append(f"- {worker}: {result_str}")
        return '\n'.join(formatted)

    async def _create_worker_task(self, state: TeamState, worker_name: str) -> str:
        """Create a specific task for the worker based on current state."""

        # Use LLM to create worker-specific task
        prompt = f"""Create a specific task for the {worker_name} worker.

ORIGINAL TASK: {state.current_task}

WORKER CAPABILITIES: {', '.join(self.worker_capabilities.get(worker_name, []))}

COMPLETED WORK:
{self._format_results_for_llm(state.worker_results)}

Create a clear, specific task for {worker_name} that contributes to the overall goal.
Be concise and actionable."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

    async def _execute_worker(self, worker: Any, task: str) -> Any:
        """Execute a worker with the given task."""

        # Different execution patterns based on worker type
        if hasattr(worker, 'arun'):
            # LangChain agent-style execution
            return await worker.arun(task)
        elif hasattr(worker, 'execute'):
            # Custom execute method
            if asyncio.iscoroutinefunction(worker.execute):
                return await worker.execute(task)
            else:
                return worker.execute(task)
        elif callable(worker):
            # Direct callable
            if asyncio.iscoroutinefunction(worker):
                return await worker(task)
            else:
                return worker(task)
        else:
            # Fallback
            return f"Worker {type(worker).__name__} executed task: {task}"