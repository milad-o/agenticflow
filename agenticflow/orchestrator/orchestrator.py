"""Orchestrator implementation for AgenticFlow."""

import asyncio
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage
import json
from agenticflow.core.models import get_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, create_react_agent
from operator import add

from agenticflow.core.config import OrchestratorConfig
from agenticflow.agent.agent import Agent
from agenticflow.registry.tool_registry import ToolRegistry
from agenticflow.orchestrator.delegate_tool import DelegateTool
from agenticflow.orchestrator.orchestrator_tools import CreateFileTool, ListDirectoryTool
from agenticflow.planner.planner import Planner, Plan
from agenticflow.planner.splitter import split_atomic
from agenticflow.orchestrator.capability_extractor import CapabilityExtractor


class OrchestratorState(TypedDict):
    """State for the orchestrator graph."""
    messages: Annotated[List[Any], add]  # Conversation history
    user_request: str  # Original user request
    tasks: List[Dict[str, Any]]  # Decomposed tasks
    task_results: Dict[str, Any]  # Results from completed tasks
    current_batch: List[Dict[str, Any]]  # Batch of tasks being executed
    final_response: str  # Final orchestrated response


class Orchestrator:
    """Meta-graph orchestrator for task decomposition and agent coordination."""
    
    def __init__(
        self,
        config: OrchestratorConfig,
        agents: Dict[str, Agent],
        tool_registry: ToolRegistry,
        checkpointer: Optional[Any] = None,
        planner: Optional[Planner] = None,
        capability_extractor: Optional[CapabilityExtractor] = None,
    ):
        self.config = config
        self.agents = agents
        self.tool_registry = tool_registry
        self.checkpointer = checkpointer or MemorySaver()
        self.planner = planner
        self.capability_extractor = capability_extractor
        self.reporter = None  # set by Flow after creation
        self.run_id = None
        
        # Create the LLM for orchestration
        self.llm = get_chat_model(model_name=config.model, temperature=config.temperature)
        
        # Build the classic orchestrator graph
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)

        # Build an agent interface (special agent) that can delegate via tool calls
        self._agent_tools = [
            DelegateTool(self.agents),
            CreateFileTool(self.agents),
            ListDirectoryTool(self.agents),
        ]
        self._agent_iface = create_react_agent(
            model=self.llm, tools=self._agent_tools, checkpointer=self.checkpointer
        )
    
    def _build_graph(self) -> StateGraph:
        """Build the orchestrator state graph."""
        graph = StateGraph(OrchestratorState)
        
        # Add nodes
        graph.add_node("analyze_request", self._analyze_request)
        graph.add_node("decompose_tasks", self._decompose_tasks)
        graph.add_node("assign_agents", self._assign_agents)
        graph.add_node("execute_task", self._execute_task)
        graph.add_node("synthesize_response", self._synthesize_response)
        
        # Add edges
        graph.add_edge(START, "analyze_request")
        graph.add_edge("analyze_request", "decompose_tasks")
        graph.add_edge("decompose_tasks", "assign_agents")
        graph.add_edge("assign_agents", "execute_task")
        
        # Conditional edge for task execution
        graph.add_conditional_edges(
            "execute_task",
            self._should_continue,
            {
                "continue": "assign_agents",
                "finish": "synthesize_response"
            }
        )
        
        graph.add_edge("synthesize_response", END)
        
        return graph
    
    async def _analyze_request(self, state: OrchestratorState) -> Dict[str, Any]:
        """Fast path: skip LLM analysis for speed."""
        user_request = state["user_request"]
        analysis = {
            "intent": "execute-request",
            "capabilities": ["general"],
            "complexity": "simple",
            "notes": "fast-path analysis (no LLM)"
        }
        return {"messages": [], "analysis": analysis}
    
    async def _decompose_tasks(self, state: OrchestratorState) -> Dict[str, Any]:
        """Decompose the request using Planner if present; otherwise a single task."""
        user_request = state["user_request"]
        if self.planner:
            plan = await self.planner.aplan(user_request)
            if getattr(self, "reporter", None):
                try:
                    self.reporter.planner("dag_generated", task_count=len(plan.tasks))
                except Exception:
                    pass
            tasks = []
            for t in plan.tasks:
                tasks.append({
                    "id": t.id,
                    "description": t.description,
                    "required_capabilities": ["general"],
                    "priority": t.priority,
                    "dependencies": t.dependencies,
                    "status": "pending"
                })
            # Split composite descriptions into atomic tasks (generic, no hardcoding)
            atomic = split_atomic(tasks)
            if getattr(self, "reporter", None) and len(atomic) != len(tasks):
                try:
                    self.reporter.planner("split", before=len(tasks), after=len(atomic))
                except Exception:
                    pass
            return {"tasks": atomic, "messages": state.get("messages", [])}
        # fallback single task
        tasks = [{
            "id": "main_task",
            "description": user_request,
            "required_capabilities": ["general"],
            "priority": 1,
            "dependencies": [],
            "status": "pending"
        }]
        return {"tasks": tasks, "messages": state.get("messages", [])}
    
    async def _assign_agents(self, state: OrchestratorState) -> Dict[str, Any]:
        """Assign agents to all ready tasks (dependency-satisfied) up to parallel limit."""
        tasks = state["tasks"]
        task_results = state.get("task_results", {})

        # Strong guard
        if not self.agents:
            raise RuntimeError("No agents available during orchestration. Aborting run.")

        max_parallel = getattr(self.config, "max_parallel_tasks", 3) or 1
        current_batch: List[Dict[str, Any]] = []
        
        # Helper: infer required capabilities from description/field
        def infer_caps(desc: str, req_caps: Optional[list] = None) -> set:
            caps = set((req_caps or []))
            d = desc.lower()
            if any(w in d for w in ["mkdir", "list ", "ls", "shell", "bash", "chmod", "pwd"]):
                caps.add("shell")
            if any(w in d for w in ["write", "create file", "append", ".csv", ".txt"]):
                caps.add("file_write")
            if any(w in d for w in ["read", "open", "print file"]):
                caps.add("file_read")
            if not caps:
                caps.add("general")
            return caps
        
        # Helper: capabilities of an agent based on its tools
        def agent_caps(agent: Agent) -> set:
            caps = set()
            try:
                tools = getattr(agent, "tools", [])
                for t in tools:
                    name = getattr(t, "name", "")
                    if name == "shell":
                        caps.add("shell")
                    if name in ("write_file",):
                        caps.add("file_write")
                    if name in ("read_file",):
                        caps.add("file_read")
                    if name in ("list_dir", "list_directory"):
                        caps.add("dir_walk")
                    if name in ("regex_search_dir", "regex_search_file", "find_files"):
                        caps.add("search")
                    if name in ("dir_tree",):
                        caps.add("dir_walk")
                    if name in ("file_stat",):
                        caps.add("file_meta")
                # tags on config
                try:
                    for tag in getattr(agent, "config", {}).tags:
                        caps.add(tag)
                except Exception:
                    pass
            except Exception:
                pass
            if not caps:
                caps.add("general")
            return caps
        
        # Dependencies satisfied predicate
        def deps_satisfied(task: dict) -> bool:
            deps = task.get("dependencies", []) or []
            return all(dep in task_results for dep in deps)
        
        # Collect all ready tasks (dependencies satisfied) that are pending
        ready_tasks = [t for t in tasks if t["status"] == "pending" and deps_satisfied(t)]
        if not ready_tasks:
            return {"tasks": tasks, "current_batch": []}

        # Assign up to max_parallel ready tasks
        for candidate in ready_tasks:
            if len(current_batch) >= max_parallel:
                break
            # AI-driven routing: ask the LLM to choose the best agent, with fallback
            agent_summary = [
                {
                    "name": name,
                    "description": getattr(agent, "description", ""),
                    "tools": [getattr(t, "name", "") for t in getattr(agent, "tools", [])],
                }
                for name, agent in self.agents.items()
            ]
            # Capability extraction (LLM) for traceability
            extracted_caps = None
            if getattr(self, "capability_extractor", None):
                try:
                    extracted_caps = await self.capability_extractor.aextract(candidate.get("description", ""), agent_summary)
                    if getattr(self, "reporter", None):
                        self.reporter.router("capabilities", task_id=candidate.get("id"), extracted=extracted_caps)
                except Exception:
                    extracted_caps = None
            # Tool hints pass: enrich description with available tool names
            all_tool_names = sorted({n for _, a in self.agents.items() for n in [getattr(t, "name", "") for t in getattr(a, "tools", [])] if n})
            tool_hints = f"Tool hints: Use these tools when applicable: {', '.join(all_tool_names)}."
            candidate["description"] = f"{candidate.get('description','')}\n\n{tool_hints}"

            route_prompt = f"""
Select the best agent to execute the following task.
Return STRICT JSON: {{"agent": "<name>", "reason": "..."}}
Task: {candidate.get("description", "")}
Agents: {json.dumps(agent_summary)}
Capabilities: {json.dumps(extracted_caps or {})}
Rules:
- Pick one agent name from Agents list.
- No extra text, only valid JSON.
"""
            try:
                rsp = await self.llm.ainvoke([HumanMessage(content=route_prompt)])
                data = json.loads(rsp.content) if isinstance(rsp.content, str) else {}
                chosen = data.get("agent")
                if getattr(self, "reporter", None):
                    self.reporter.router("choice", task_id=candidate.get("id"), chosen=chosen, raw=data)
            except Exception:
                chosen = None
            if not chosen or chosen not in self.agents:
                # fallback to heuristic
                required = infer_caps(candidate.get("description", ""), candidate.get("required_capabilities"))
                best_agent = None
                best_score = -1
                for name, agent in self.agents.items():
                    score = len(agent_caps(agent) & required)
                    if score > best_score:
                        best_score = score
                        best_agent = name
                chosen = best_agent or list(self.agents.keys())[0]

            # Assign
            candidate["assigned_agent"] = chosen
            candidate["status"] = "assigned"
            current_batch.append(candidate)
            if getattr(self, "reporter", None):
                self.reporter.task("assigned", task_id=candidate.get("id"), agent=chosen)

        return {"tasks": tasks, "current_batch": current_batch}
    
    async def _execute_task(self, state: OrchestratorState) -> Dict[str, Any]:
        """Execute the current batch of tasks concurrently using assigned agents."""
        current_batch = state.get("current_batch", [])
        if not current_batch:
            return state

        async def run_one(task: Dict[str, Any]) -> Dict[str, Any]:
            agent_name = task["assigned_agent"]
            agent = self.agents[agent_name]
            if getattr(self, "reporter", None):
                self.reporter.task("start", task_id=task["id"], agent=agent_name)
            result = await agent.arun(
                task["description"],
                thread_id=f"task_{task['id']}"
            )
            if getattr(self, "reporter", None):
                preview = (result.get("message", "") or "")[:120]
                self.reporter.task("end", task_id=task["id"], agent=agent_name, preview=preview)
            return {"task": task, "result": result}

        results = await asyncio.gather(*(run_one(t) for t in current_batch))

        task_results = state.get("task_results", {})
        # Update tasks
        for entry in results:
            t = entry["task"]
            res = entry["result"]
            t["status"] = "completed"
            t["result"] = res
            task_results[t["id"]] = res
        state["current_batch"] = []

        return {"task_results": task_results, "current_batch": []}
    
    def _should_continue(self, state: OrchestratorState) -> str:
        """Determine if there are more tasks to execute."""
        tasks = state["tasks"]
        # Continue if any task is pending or assigned
        for task in tasks:
            if task.get("status") in ("pending", "assigned"):
                return "continue"
        return "finish"
    
    async def _synthesize_response(self, state: OrchestratorState) -> Dict[str, Any]:
        """Synthesize the final response from all task results."""
        task_results = state.get("task_results", {})
        user_request = state["user_request"]
        
        if not task_results:
            final_response = "I wasn't able to complete any tasks for your request."
        else:
            # For MVP, just return the first result
            first_result = list(task_results.values())[0]
            final_response = first_result.get("message", "Task completed successfully.")
        if getattr(self, "reporter", None):
            self.reporter.orchestrator("synthesized", final_preview=final_response[:160])
        
        return {"final_response": final_response}
    
    async def arun(
        self,
        user_request: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Run the orchestrator asynchronously."""
        if not self.agents:
            raise ValueError("No agents available for orchestration. Ensure at least one Agent is registered before running.")
        config = {"configurable": {"thread_id": thread_id or "default"}}
        
        initial_state = OrchestratorState(
            messages=[],
            user_request=user_request,
            tasks=[],
            task_results={},
            current_batch=[],
            final_response=""
        )
        
        final_state = await self.compiled_graph.ainvoke(initial_state, config=config, **kwargs)
        
        return {
            "request": user_request,
            "final_response": final_state.get("final_response", ""),
            "task_results": final_state.get("task_results", {}),
            "tasks": final_state.get("tasks", [])
        }
    async def astream(
        self,
        user_request: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ):
        """Stream orchestrator execution."""
        if not self.agents:
            raise ValueError("No agents available for orchestration. Ensure at least one Agent is registered before running.")
        config = {"configurable": {"thread_id": thread_id or "default"}}
        
        initial_state = OrchestratorState(
            messages=[],
            user_request=user_request,
            tasks=[],
            task_results={},
            current_task=None,
            final_response=""
        )
        
        async for chunk in self.compiled_graph.astream(initial_state, config=config, **kwargs):
            yield chunk
    def run(self, user_request: str, thread_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Synchronous wrapper for arun."""
        return asyncio.run(self.arun(user_request, thread_id, **kwargs))

    # Orchestrator as an Agent (special agent)
    async def aagent_run(self, message: str, thread_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        if not self.agents:
            raise ValueError("No agents available for delegation.")
        config = {"configurable": {"thread_id": thread_id or "orchestrator-agent"}}
        # Let the agent interface decide via tool calls
        final_message = None
        async for chunk in self._agent_iface.astream({"messages": [("human", message)]}, config=config, **kwargs):
            if "agent" in chunk:
                final_message = chunk["agent"]["messages"][-1]
        return {
            "message": getattr(final_message, "content", "") if final_message else "",
            "tool_calls": getattr(final_message, "tool_calls", []) if final_message else []
        }

    def agent_run(self, message: str, thread_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return asyncio.run(self.aagent_run(message, thread_id, **kwargs))
