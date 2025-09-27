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
        """Main coordination logic with friendly conversation and intelligent routing."""

        # If task is complete, provide friendly completion message
        if state.is_complete:
            return state

        # First interaction - provide greeting and understanding
        if state.execution_count == 0:
            greeting_response = await self._provide_friendly_greeting(state)
            state.add_message("supervisor", greeting_response)

        # Safety check - limit total executions to prevent infinite loops
        if state.execution_count >= 10:
            state.mark_complete()
            completion_message = await self._provide_completion_summary(state)
            state.add_message("supervisor", completion_message)
            return state

        # Increment execution counter
        state.execution_count += 1

        # Check if we should route to a worker or provide conversational response
        routing_decision = await self._decide_routing_strategy(state)

        if routing_decision["action"] == "CONVERSATION":
            # Provide conversational response without tool calling
            conversational_response = await self._provide_conversational_response(state)
            state.add_message("supervisor", conversational_response)
            state.mark_complete()
            return state

        elif routing_decision["action"] == "ROUTE_TO_WORKER":
            next_worker = routing_decision["worker"]

            # Provide friendly explanation of what we're doing
            explanation = await self._explain_worker_routing(state, next_worker)
            state.add_message("supervisor", explanation)

            # Execute worker task
            try:
                worker = self.workers[next_worker]
                worker_task = await self._create_worker_task(state, next_worker)
                result = await self._execute_worker(worker, worker_task)

                # Store result and provide friendly summary
                state.set_worker_result(next_worker, result)
                summary = await self._summarize_worker_result(next_worker, result)
                state.add_message("supervisor", summary)

                # Update context for next iteration
                state.update_context(f"{next_worker}_completed", True)

            except Exception as e:
                error_message = await self._handle_worker_error(next_worker, str(e))
                state.add_message("supervisor", error_message)
                state.mark_error(f"Worker {next_worker} failed: {str(e)}")

        elif routing_decision["action"] == "FINISH":
            state.mark_complete()
            completion_message = await self._provide_completion_summary(state)
            state.add_message("supervisor", completion_message)

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

    async def _provide_friendly_greeting(self, state: TeamState) -> str:
        """Provide a friendly greeting and understanding of the user's request."""
        prompt = f"""You are a friendly AI assistant managing a team of specialized agents.

The user has asked: "{state.current_task}"

Provide a warm, helpful greeting that:
1. Acknowledges their request
2. Shows understanding of what they want to accomplish
3. Explains that you'll coordinate with your team of specialists to help them
4. Keeps it conversational and friendly

Be concise but welcoming. Don't start working yet - just greet them and show you understand."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

    async def _decide_routing_strategy(self, state: TeamState) -> Dict[str, str]:
        """Decide whether to have a conversation or route to workers."""
        prompt = f"""You are a friendly supervisor deciding how to handle a user request.

USER REQUEST: "{state.current_task}"

AVAILABLE SPECIALIST AGENTS:
{self._format_workers_for_llm(list(self.workers.keys()))}

CURRENT PROGRESS:
{self._format_results_for_llm(state.worker_results)}

Decide the best approach:

1. CONVERSATION - If the request is:
   - A greeting (hello, hi, how are you)
   - A question about capabilities ("what can you do?")
   - A general chat or thanks
   - Asking for help or information

2. ROUTE_TO_WORKER - If the request needs actual work:
   - File operations, code execution, data processing, etc.
   - Choose the most appropriate specialist agent

3. FINISH - If the work is complete and user just needs a summary

Respond with ONLY one of:
- "CONVERSATION"
- "ROUTE_TO_WORKER:agent_name"
- "FINISH"

Current analysis shows the request is asking for: practical work that needs specialist agents."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        decision = response.content.strip()

        if decision == "CONVERSATION":
            return {"action": "CONVERSATION"}
        elif decision == "FINISH":
            return {"action": "FINISH"}
        elif decision.startswith("ROUTE_TO_WORKER:"):
            worker = decision.split(":", 1)[1].strip()
            return {"action": "ROUTE_TO_WORKER", "worker": worker}
        else:
            # Default to conversation for safety
            return {"action": "CONVERSATION"}

    async def _provide_conversational_response(self, state: TeamState) -> str:
        """Provide a conversational response without tool calling."""
        prompt = f"""You are a friendly AI assistant. The user said: "{state.current_task}"

This appears to be a conversational message rather than a task requiring specialist agents.

Provide a helpful, friendly response that:
- Directly addresses their message
- Offers information about your capabilities if they ask
- Suggests how you could help them with practical tasks
- Keeps the tone warm and conversational

Available specialists you can coordinate: Python execution, file operations, database work, data processing, web scraping, ETL pipelines."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

    async def _explain_worker_routing(self, state: TeamState, worker_name: str) -> str:
        """Explain what we're doing when routing to a worker."""
        worker_caps = ', '.join(self.worker_capabilities.get(worker_name, ['general tasks']))

        prompt = f"""You are explaining to the user what you're doing next.

USER REQUEST: "{state.current_task}"
SPECIALIST BEING USED: {worker_name} (specializes in: {worker_caps})

Write a brief, friendly message explaining:
- You understand their request
- Which specialist you're asking to help
- What that specialist is good at

Keep it conversational and reassuring. Examples:
"I'll have my file operations specialist take a look at that for you..."
"Let me ask my Python expert to help with that code..."
"I'm connecting you with my database specialist who can handle that..."
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

    async def _summarize_worker_result(self, worker_name: str, result: Any) -> str:
        """Provide a friendly summary of what the worker accomplished."""
        prompt = f"""A specialist agent just completed work. Provide a friendly summary for the user.

SPECIALIST: {worker_name}
RESULT: {str(result)[:500]}

Write a conversational summary that:
- Explains what was accomplished in plain language
- Highlights key outcomes or findings
- Maintains a helpful, positive tone
- Avoids technical jargon unless necessary

Keep it concise but informative."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

    async def _handle_worker_error(self, worker_name: str, error: str) -> str:
        """Handle worker errors with friendly explanation."""
        prompt = f"""A specialist encountered an issue. Explain this to the user in a helpful way.

SPECIALIST: {worker_name}
ERROR: {error}

Write a friendly message that:
- Acknowledges the issue without being alarming
- Explains what went wrong in simple terms
- Suggests what they might try instead or how to fix it
- Maintains a supportive, problem-solving tone"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

    async def _provide_completion_summary(self, state: TeamState) -> str:
        """Provide a friendly completion summary."""
        prompt = f"""Provide a friendly completion summary for the user.

ORIGINAL REQUEST: "{state.current_task}"
WORK COMPLETED:
{self._format_results_for_llm(state.worker_results)}

Write a warm, helpful summary that:
- Confirms what was accomplished
- Highlights key results or outcomes
- Thanks them for using the system
- Offers help with anything else they might need

Keep it conversational and positive."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()