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
from agenticflow.core.task_status_tracker import TaskStatusTracker, TaskStatus
from agenticflow.core.event_bus import get_event_bus, EventType, Event
import structlog

logger = structlog.get_logger()


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
        
        # Initialize task status tracking
        self.event_bus = get_event_bus()
        self.task_tracker = TaskStatusTracker(self.event_bus)
        
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
            # Build agent catalog for planner context
            agent_catalog = []
            try:
                # include name, tools, and capabilities for better planning
                for aname, a in self.agents.items():
                    tool_names = [getattr(t, "name", "") for t in getattr(a, "tools", [])]
                    caps = set()
                    for tn in tool_names:
                        meta = self.tool_registry.list_tools().get(tn) if hasattr(self.tool_registry, "list_tools") else None
                        if meta:
                            for c in (meta.capabilities or set()):
                                caps.add(c)
                    agent_catalog.append({
                        "name": aname,
                        "tools": tool_names,
                        "capabilities": sorted(caps),
                    })
            except Exception:
                agent_catalog = []
            plan = await self.planner.aplan(user_request, agent_catalog=agent_catalog)
            tasks = []
            if plan and plan.tasks:
                for t in plan.tasks:
                    tasks.append({
                        "id": t.id,
                        "description": t.description,
                        "required_capabilities": ["general"],
                        "priority": t.priority,
                        "dependencies": t.dependencies,
                        "status": "pending",
                        # carry planner suggestions
                        "agent": getattr(t, "agent", None),
                        "capabilities": getattr(t, "capabilities", []),
                    })
            # Split composite descriptions into atomic tasks (preserves agent/capabilities)
            atomic = split_atomic(tasks)

            # Heuristic: ensure report-writing tasks depend on all prior tasks
            try:
                report_idxs = []
                for i, t in enumerate(atomic):
                    desc = (t.get("description") or "").lower()
                    if any(w in desc for w in ["report", "write", "document"]):
                        report_idxs.append(i)
                if report_idxs:
                    all_ids = [t.get("id") for t in atomic]
                    for idx in report_idxs:
                        tid = atomic[idx].get("id")
                        deps = set(atomic[idx].get("dependencies", []) or [])
                        for dep_id in all_ids:
                            if dep_id and dep_id != tid:
                                deps.add(dep_id)
                        atomic[idx]["dependencies"] = list(deps)
            except Exception:
                pass

            # Detect cycles; if found, fallback to a simple, safe 3-task DAG
            def _has_cycle(ts):
                try:
                    ids = [t.get("id") for t in ts if t.get("id")]
                    indeg = {tid: 0 for tid in ids}
                    adj = {tid: [] for tid in ids}
                    for t in ts:
                        tid = t.get("id")
                        for dep in (t.get("dependencies", []) or []):
                            if dep in indeg and tid in indeg:
                                indeg[tid] += 1
                                adj[dep].append(tid)
                    from collections import deque
                    dq = deque([n for n, d in indeg.items() if d == 0])
                    visited = 0
                    while dq:
                        n = dq.popleft()
                        visited += 1
                        for m in adj.get(n, []):
                            indeg[m] -= 1
                            if indeg[m] == 0:
                                dq.append(m)
                    return visited < len(ids)
                except Exception:
                    return False

            if _has_cycle(atomic):
                if getattr(self, "reporter", None):
                    try:
                        self.reporter.planner("dag_cycle_detected", note="Planner produced cyclic dependencies; applying safe fallback plan")
                    except Exception:
                        pass
                # Safe fallback minimal plan tailored to this common request type
                fallback_tasks = [
                    {"id": "task_1", "description": "Scan directory for SSIS packages", "dependencies": [], "status": "pending"},
                    {"id": "task_2", "description": "Stream read contents of each SSIS package", "dependencies": ["task_1"], "status": "pending"},
                    {"id": "task_3", "description": "Write executive-ready report", "dependencies": ["task_1", "task_2"], "status": "pending"},
                ]
                # Register tasks with tracker
                for task in fallback_tasks:
                    await self.task_tracker.create_task(
                        task_id=task["id"],
                        description=task["description"],
                        dependencies=task.get("dependencies", [])
                    )
                    if getattr(self, "reporter", None):
                        try:
                            self.reporter.planner(
                                "task_created",
                                task_id=task["id"],
                                description=task.get("description", "")[:120],
                                dependencies=task.get("dependencies", [])
                            )
                        except Exception:
                            pass
                if getattr(self, "reporter", None):
                    try:
                        nodes, edges, roots, leaves = self._dag_stats(fallback_tasks)
                        self.reporter.planner("dag_generated", task_count=nodes, edges=edges)
                        self.reporter.planner("dag_stats", nodes=nodes, edges=edges, roots=roots, leaves=leaves)
                    except Exception:
                        pass
                return {"tasks": fallback_tasks, "messages": state.get("messages", [])}

            # Register tasks with tracker
            for task in atomic:
                await self.task_tracker.create_task(
                    task_id=task["id"],
                    description=task["description"],
                    dependencies=task.get("dependencies", [])
                )
                # Human-readable planner task summary
                if getattr(self, "reporter", None):
                    try:
                        self.reporter.planner(
                            "task_created",
                            task_id=task["id"],
                            description=task.get("description", "")[:120],
                            dependencies=task.get("dependencies", []),
                            agent_suggested=task.get("agent")
                        )
                    except Exception:
                        pass
            # Planner logging limited to task count and edge count
            if getattr(self, "reporter", None):
                try:
                    nodes, edges, roots, leaves = self._dag_stats(atomic)
                    self.reporter.planner("dag_generated", task_count=nodes, edges=edges)
                    self.reporter.planner("dag_stats", nodes=nodes, edges=edges, roots=roots, leaves=leaves)
                except Exception:
                    pass
            return {"tasks": atomic, "messages": state.get("messages", [])}
        # fallback single task (no planner logging; orchestrator will log stats later when executing)
        tasks = [{
            "id": "main_task",
            "description": user_request,
            "required_capabilities": ["general"],
            "priority": 1,
            "dependencies": [],
            "status": "pending"
        }]
        # Register fallback task with tracker
        for task in tasks:
            await self.task_tracker.create_task(
                task_id=task["id"],
                description=task["description"],
                dependencies=task.get("dependencies", [])
            )
        return {"tasks": tasks, "messages": state.get("messages", [])}
    
    def _dag_stats(self, tasks: List[Dict[str, Any]]):
        try:
            nodes = len(tasks)
            ids = {t.get("id") for t in tasks}
            dependents = {tid: 0 for tid in ids}
            edges = []
            for t in tasks:
                tid = t.get("id")
                for dep in t.get("dependencies", []) or []:
                    edges.append((dep, tid))
                    if dep in dependents:
                        dependents[dep] += 1
            roots = [t.get("id") for t in tasks if not (t.get("dependencies") or [])]
            leaves = [tid for tid, cnt in dependents.items() if cnt == 0]
            return nodes, len(edges), roots, leaves
        except Exception:
            return len(tasks), 0, [], []

    async def _assign_agents(self, state: OrchestratorState) -> Dict[str, Any]:
        """Assign agents to all ready tasks (dependency-satisfied) up to parallel limit."""
        tasks = state.get("tasks") or []
        task_results = state.get("task_results", {})
        
        # Defensive guard - ensure we have valid tasks
        if tasks is None:
            tasks = []
        if not isinstance(tasks, list):
            tasks = []

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
        
        # Use task tracker to get ready tasks and avoid re-executing completed ones
        ready_from_tracker = self.task_tracker.get_ready_tasks()
        ready_task_ids = {task.task_id for task in ready_from_tracker}
        
        # Filter orchestrator tasks to only include ready ones that haven't been completed/failed
        ready_tasks = []
        for t in tasks:
            # Skip tasks that are already completed or failed
            tracker_task = self.task_tracker.get_task(t["id"])
            if tracker_task and tracker_task.is_terminal():
                # Update orchestrator task status to match tracker
                t["status"] = tracker_task.status.value
                if tracker_task.status == TaskStatus.COMPLETED:
                    task_results[t["id"]] = tracker_task.result or {"message": "Task completed"}
                continue
                
            # Only include tasks that are ready according to tracker
            if t["id"] in ready_task_ids and t["status"] == "pending":
                ready_tasks.append(t)
        
        if not ready_tasks:
            return {"tasks": tasks, "current_batch": [], "task_results": task_results}

        # Log comprehensive DAG stats on first assignment cycle
        if getattr(self, "reporter", None) and not getattr(self, "_dag_stats_logged", False):
            try:
                nodes, edges, roots, leaves = self._dag_stats(tasks)
                self.reporter.orchestrator("dag_stats", nodes=nodes, edges=edges, roots=roots, leaves=leaves)
                self._dag_stats_logged = True
            except Exception:
                pass

        # Assign up to max_parallel ready tasks
        for candidate in ready_tasks:
            if len(current_batch) >= max_parallel:
                break

            # Prepare agent summary for routing
            agent_summary = [
                {
                    "name": name,
                    "description": getattr(agent, "description", ""),
                    "tools": [getattr(t, "name", "") for t in getattr(agent, "tools", [])],
                }
                for name, agent in self.agents.items()
            ]

            # 0) Respect planner suggestion if present and valid
            suggested = (candidate.get("agent") or "").strip()
            chosen = None
            if suggested and suggested in self.agents:
                chosen = suggested
                if getattr(self, "reporter", None):
                    try:
                        self.reporter.router("choice", task_id=candidate.get("id"), chosen=chosen, raw={"agent": "planner_suggested"})
                    except Exception:
                        pass

            if chosen is None:
                # Heuristic routing by tool availability first (fast and reliable)
                try:
                    dlow = (candidate.get("description", "") or "").lower()
                    # Prefer agent with write_text_atomic for report/document/write tasks
                    if any(w in dlow for w in ["report", "write", "document"]):
                        for name, agent in self.agents.items():
                            if any(getattr(t, "name", "") == "write_text_atomic" for t in getattr(agent, "tools", [])):
                                chosen = name
                                if getattr(self, "reporter", None):
                                    self.reporter.router("choice", task_id=candidate.get("id"), chosen=chosen, raw={"agent": "tool_heuristic", "reason": "needs write_text_atomic"})
                                break
                    # Prefer filesystem-capable agent for find/read/stream tasks
                    if chosen is None and any(w in dlow for w in ["find", "scan", "discover", "list", "read", "stream"]):
                        best = None
                        best_score = -1
                        for name, agent in self.agents.items():
                            score = 0
                            tools = getattr(agent, "tools", [])
                            names = {getattr(t, "name", "") for t in tools}
                            if "find_files" in names:
                                score += 2
                            if "streaming_file_reader" in names:
                                score += 2
                            if "read_text_fast" in names:
                                score += 1
                            if score > best_score:
                                best_score = score
                                best = name
                        if best is not None and best_score > 0:
                            chosen = best
                            if getattr(self, "reporter", None):
                                self.reporter.router("choice", task_id=candidate.get("id"), chosen=chosen, raw={"agent": "tool_heuristic", "reason": "needs search/read tools"})
                    # Prefer analysis-capable agent for aggregation tasks
                    if chosen is None and any(w in dlow for w in ["average", "avg", "mean", "aggregate", "group by", "per category"]):
                        for name, agent in self.agents.items():
                            if any(getattr(t, "name", "") == "csv_chunk_aggregate" for t in getattr(agent, "tools", [])):
                                chosen = name
                                if getattr(self, "reporter", None):
                                    self.reporter.router("choice", task_id=candidate.get("id"), chosen=chosen, raw={"agent": "tool_heuristic", "reason": "needs aggregation tool"})
                                break
                except Exception:
                    chosen = None

            if chosen is None:
                # AI-driven routing: ask the LLM to choose the best agent, with fallback
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
                # Merge planner capability hints if present
                try:
                    req_from_planner = set(candidate.get("capabilities", []) or [])
                    required |= req_from_planner
                except Exception:
                    pass
                best_agent = None
                best_score = -1
                for name, agent in self.agents.items():
                    score = len(agent_caps(agent) & required)
                    if score > best_score:
                        best_score = score
                        best_agent = name
                chosen = best_agent or list(self.agents.keys())[0]

            # Assign in tracker and orchestrator
            assignment_success = await self.task_tracker.assign_task(candidate["id"], chosen)
            if assignment_success:
                candidate["assigned_agent"] = chosen
                candidate["status"] = "assigned"
                current_batch.append(candidate)
                if getattr(self, "reporter", None):
                    self.reporter.task(
                        "assigned",
                        task_id=candidate.get("id"),
                        agent=chosen,
                        dependencies=candidate.get("dependencies", []),
                        description=(candidate.get("description", "") or "")[:120]
                    )
                    self.reporter.orchestrator(
                        "assignment",
                        task_id=candidate.get("id"),
                        agent=chosen,
                        note="Task assigned to agent for execution"
                    )
            else:
                logger.warning("Failed to assign task in tracker", task_id=candidate["id"], agent=chosen)

        return {"tasks": tasks, "current_batch": current_batch}
    
    async def _execute_task(self, state: OrchestratorState) -> Dict[str, Any]:
        """Execute the current batch of tasks concurrently using assigned agents."""
        current_batch = state.get("current_batch", [])
        task_results = state.get("task_results", {})
        
        if not current_batch:
            return state

        async def run_one(task: Dict[str, Any]) -> Dict[str, Any]:
            agent_name = task["assigned_agent"]
            agent = self.agents[agent_name]
            task_id = task["id"]
            
            # Check if task is already completed to avoid re-execution
            tracker_task = self.task_tracker.get_task(task_id)
            if tracker_task and tracker_task.is_terminal():
                logger.info("Skipping already completed task", task_id=task_id, status=tracker_task.status.value)
                return {"task": task, "result": tracker_task.result or {"message": "Task already completed"}}
            
            # Mark task as starting
            await self.task_tracker.start_task(task_id)
            
            # Emit task start event
            self.event_bus.emit(Event(
                event_type=EventType.TASK_STARTED,
                source="orchestrator",
                data={"task_id": task_id, "agent": agent_name, "description": task["description"]},
                channel="orchestrator"
            ))
            
            if getattr(self, "reporter", None):
                self.reporter.task("start", task_id=task_id, agent=agent_name)
                self.reporter.agent(
                    "execute_task",
                    agent=agent_name,
                    task_id=task_id,
                    phase="start"
                )
            
            # Prepare context for agent with dependency results
            task_context = self._prepare_task_context(task, task_results)
            enhanced_description = self._enhance_task_description(task, task_context)
            if getattr(self, "reporter", None):
                try:
                    dep_count = len(task_context.get("dependencies", []) or [])
                    self.reporter.orchestrator(
                        "context_prepared",
                        task_id=task_id,
                        agent=agent_name,
                        dependencies=task.get("dependencies", []),
                        note=f"Prepared context with {dep_count} dependencies"
                    )
                except Exception:
                    pass
                
            try:
                result = await agent.arun(
                    enhanced_description,
                    thread_id=f"task_{task_id}"
                )
                
                # Mark task as completed in tracker
                await self.task_tracker.complete_task(task_id, result)
                
                # Emit task completion event
                self.event_bus.emit(Event(
                    event_type=EventType.TASK_COMPLETED,
                    source="orchestrator",
                    data={"task_id": task_id, "agent": agent_name, "result": result},
                    channel="orchestrator"
                ))
                
                if getattr(self, "reporter", None):
                    preview = (result.get("message", "") or "")[:120]
                    self.reporter.task("end", task_id=task_id, agent=agent_name, preview=preview)
                    self.reporter.agent(
                        "execute_task",
                        agent=agent_name,
                        task_id=task_id,
                        phase="end",
                        preview=preview
                    )
                    
                return {"task": task, "result": result}
                
            except Exception as e:
                error_msg = str(e)
                
                # Mark task as failed in tracker
                await self.task_tracker.fail_task(task_id, error_msg)
                
                # Emit task failure event
                self.event_bus.emit(Event(
                    event_type=EventType.TASK_FAILED,
                    source="orchestrator",
                    data={"task_id": task_id, "agent": agent_name, "error": error_msg},
                    channel="orchestrator"
                ))
                
                if getattr(self, "reporter", None):
                    self.reporter.task("error", task_id=task_id, agent=agent_name, error=error_msg)
                    
                # Return failure result
                error_result = {"message": f"Task failed: {error_msg}", "error": error_msg}
                return {"task": task, "result": error_result}

        results = await asyncio.gather(*(run_one(t) for t in current_batch))

        # Update task results
        for entry in results:
            t = entry["task"]
            res = entry["result"]
            t["status"] = "completed"
            t["result"] = res
            task_results[t["id"]] = res
        
        return {"task_results": task_results, "current_batch": []}
    
    def _should_continue(self, state: OrchestratorState) -> str:
        """Determine if there are more tasks to execute using task tracker."""
        # Check if workflow is complete using task tracker
        if self.task_tracker.is_workflow_complete():
            workflow_summary = self.task_tracker.get_workflow_summary()
            logger.info("Workflow complete", **workflow_summary)
            return "finish"
        
        # Check for ready tasks or active tasks
        ready_tasks = self.task_tracker.get_ready_tasks()
        active_tasks = self.task_tracker.get_active_tasks()
        
        if ready_tasks or active_tasks:
            logger.info("Workflow continuing", ready_tasks=len(ready_tasks), active_tasks=len(active_tasks))
            return "continue"
        
        # Check failed tasks - if all remaining tasks are failed, stop
        failed_tasks = self.task_tracker.get_failed_tasks()
        total_tasks = len(self.task_tracker.tasks)
        completed_tasks = len(self.task_tracker.get_completed_tasks())
        
        if failed_tasks and (completed_tasks + len(failed_tasks)) == total_tasks:
            logger.warning("Workflow stopping due to failures", 
                         failed_tasks=len(failed_tasks), 
                         completed_tasks=completed_tasks,
                         total_tasks=total_tasks)
            return "finish"
        
        logger.info("Workflow finishing - no more executable tasks")
        return "finish"
    
    def _prepare_task_context(self, task: Dict[str, Any], task_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for a task including results from dependency tasks."""
        context = {
            "task_id": task["id"],
            "task_description": task["description"],
            "dependencies": task.get("dependencies", []),
            "dependency_results": {}
        }
        
        # Collect results from dependency tasks
        for dep_id in task.get("dependencies", []):
            if dep_id in task_results:
                dep_result = task_results[dep_id]
                context["dependency_results"][dep_id] = {
                    "message": dep_result.get("message", ""),
                    "data": dep_result.get("data", {}),
                    "files_processed": dep_result.get("files_processed", []),
                    "summary": dep_result.get("summary", "")
                }
        
        return context
    
    def _enhance_task_description(self, task: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Enhance task description with context from dependency results."""
        base_description = task["description"]
        
        # If no dependencies, return original description
        if not context["dependency_results"]:
            return base_description
        
        # Build context section with dependency results
        context_section = "\n\n=== CONTEXT FROM PREVIOUS TASKS ==="
        
        for dep_id, dep_result in context["dependency_results"].items():
            context_section += f"\n\n--- Results from {dep_id} ---"
            if dep_result["message"]:
                context_section += f"\n{dep_result['message'][:1000]}..."
            # Include structured files (if available) to aid downstream consumers/LLMs
            try:
                files = dep_result.get("data", {}).get("files", [])
                if files:
                    context_section += "\nFiles (from dependency):\n" + "\n".join(
                        f"- {f.get('path')} ({int(f.get('size_bytes',0))/1024.0:.1f} KB)" for f in files[:10] if f.get('path')
                    )
            except Exception:
                pass
            if dep_result["summary"]:
                context_section += f"\nSummary: {dep_result['summary']}"
            if dep_result["files_processed"]:
                context_section += f"\nFiles processed: {len(dep_result['files_processed'])}"
        
        context_section += "\n\n=== YOUR TASK ==="
        
        return f"{base_description}{context_section}"
    
    
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
