"""
Hybrid RPAVH Agent Implementation

A practical Reflect-Plan-Act-Verify-Handoff agent that combines:
- Lightweight heuristic planning (fast, rule-based)
- Selective LLM usage (only for reflection and adaptation)
- Direct tool execution (no LLM intermediation)
- Smart error recovery with LLM assistance
"""

import asyncio
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, TypedDict, Annotated, Union, Callable, TYPE_CHECKING
from ..roles import AgentRole
from dataclasses import dataclass, field
from enum import Enum

from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from operator import add

from agenticflow.core.models import get_chat_model
from agenticflow.registries.tool_registry import ToolRegistry

if TYPE_CHECKING:
    from agenticflow.core.config import AgentConfig
from agenticflow.core.events import get_event_bus
from agenticflow.core.logging import get_component_logger


class ExecutionPhase(Enum):
    """Phases in the Hybrid RPAVH execution cycle."""
    REFLECT = "reflect"
    PLAN = "plan"
    ACT = "act"
    VERIFY = "verify"
    HANDOFF = "handoff"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ActionPlan:
    """Simple action plan with direct tool execution."""
    actions: List[Dict[str, Any]]
    strategy: str
    fallback_enabled: bool = True
    estimated_duration: float = 30.0


class HybridRPAVHState(TypedDict):
    """State for Hybrid RPAVH execution - simplified but effective."""
    # Input and Context
    messages: Annotated[List[BaseMessage], add]
    original_request: str
    thread_id: Optional[str]
    
    # Execution State
    current_phase: str
    attempt_number: int
    max_attempts: int
    
    # Lightweight Planning
    action_plan: Optional[Dict[str, Any]]
    pending_actions: List[Dict[str, Any]]
    completed_actions: List[Dict[str, Any]]
    current_result: Optional[Any]
    
    # Reflection and Adaptation (LLM-driven)
    needs_reflection: bool
    reflection_summary: Optional[str]
    adaptation_needed: bool
    
    # Results and Handoff
    verification_passed: bool
    requires_handoff: bool
    final_response: Optional[str]
    execution_complete: bool
    execution_success: bool


class HybridRPAVHAgent:
    """
    Hybrid RPAVH Agent - Fast, practical, and reliable.
    
    Key Principles:
    - Rule-based planning (fast, predictable)
    - LLM for reflection and adaptation only
    - Direct tool execution (no LLM intermediation)
    - Smart error recovery with minimal overhead
    """
    
    def __init__(
        self,
        config: Optional["AgentConfig"] = None,
        tools: Optional[List[BaseTool]] = None,
        model: Optional[BaseChatModel] = None,
        checkpointer: Optional[Any] = None,
        static_resources: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3,
        use_llm_reflection: bool = True,
        use_llm_verification: bool = False,  # Keep lightweight by default
        # Convenience parameters
        name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        # Build config if needed
        if config is None:
            cfg_name = name or "hybrid_rpavh_agent"
            cfg_model = model_name or "llama3.2:latest"
            cfg_temp = temperature if temperature is not None else 0.1
            from agenticflow.core.config import AgentConfig
            config = AgentConfig(name=cfg_name, model=cfg_model, temperature=cfg_temp)
        
        self.config = config
        self.name = config.name
        
        # Core components
        self.tools: List[BaseTool] = list(tools or [])
        self.model = model or get_chat_model(model_name=config.model, temperature=config.temperature)
        self.checkpointer = checkpointer or MemorySaver()
        self.static_resources: Dict[str, Any] = dict(static_resources or {})
        
        # Hybrid Configuration
        self.max_attempts = max_attempts
        self.use_llm_reflection = use_llm_reflection
        self.use_llm_verification = use_llm_verification
        
        # Tool Registry and Flow Reference
        self.tool_registry = ToolRegistry()
        self._flow_ref: Optional[Any] = None
        
        # Register tools in registry
        for tool in self.tools:
            self.tool_registry.register_tool_instance(tool)
        
        # Event Bus Integration (simplified)
        try:
            self.event_bus = get_event_bus()
        except Exception:
            self.event_bus = None

        # Component-aware logger
        self.logger = get_component_logger(self.name, "agent")

        # Build the Hybrid RPAVH graph
        self.graph = self._build_hybrid_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)

        # Coordination callbacks
        self.handoff_callback: Optional[Callable] = None

        self.logger.info("Hybrid RPAVH Agent initialized", tools=len(self.tools),
                        llm_reflection=self.use_llm_reflection, llm_verification=self.use_llm_verification)
    
    def _build_hybrid_graph(self) -> StateGraph:
        """Build the streamlined Hybrid RPAVH graph."""
        graph = StateGraph(HybridRPAVHState)
        
        # Streamlined phases
        graph.add_node("initialize", self._initialize)
        graph.add_node("reflect", self._reflect)
        graph.add_node("plan", self._plan_heuristic)  # Rule-based planning
        graph.add_node("act", self._act_direct)       # Direct tool execution
        graph.add_node("verify", self._verify_fast)   # Quick verification
        graph.add_node("complete", self._complete)
        graph.add_node("handle_failure", self._handle_failure)
        
        # Streamlined flow
        graph.add_edge(START, "initialize")
        graph.add_edge("initialize", "reflect")
        
        # Simple conditional logic
        graph.add_conditional_edges(
            "reflect",
            self._after_reflect,
            {"plan": "plan", "complete": "complete", "failed": "handle_failure"}
        )
        
        graph.add_edge("plan", "act")
        
        graph.add_conditional_edges(
            "act",
            self._after_act,
            {"verify": "verify", "reflect": "reflect", "complete": "complete", "failed": "handle_failure"}
        )
        
        graph.add_conditional_edges(
            "verify",
            self._after_verify,
            {"complete": "complete", "reflect": "reflect", "failed": "handle_failure"}
        )
        
        # Terminal states
        graph.add_edge("complete", END)
        graph.add_edge("handle_failure", END)
        
        return graph
    
    async def _initialize(self, state: HybridRPAVHState) -> Dict[str, Any]:
        """Quick initialization without heavy LLM processing."""
        self.logger.user_progress("Initializing agent")
        self.logger.debug("Hybrid RPAVH: Initializing")
        try:
            if hasattr(self, "reporter") and self.reporter:
                self.reporter.agent("phase", agent=self.name, phase="initialize")
        except Exception:
            pass
        
        return {
            "current_phase": ExecutionPhase.REFLECT.value,
            "attempt_number": 1,
            "max_attempts": self.max_attempts,
            "action_plan": None,
            "pending_actions": [],
            "completed_actions": [],
            "needs_reflection": self.use_llm_reflection,
            "reflection_summary": None,
            "adaptation_needed": False,
            "verification_passed": False,
            "requires_handoff": False,
            "execution_complete": False,
            "execution_success": False
        }
    
    async def _reflect(self, state: HybridRPAVHState) -> Dict[str, Any]:
        """Smart reflection - LLM only when needed or on failures."""
        attempt = state["attempt_number"]
        needs_llm = state.get("needs_reflection", False)

        if needs_llm:
            self.logger.user_info("Analyzing request and planning approach...")
        else:
            self.logger.user_progress("Quick assessment", step=attempt)

        self.logger.debug("Hybrid RPAVH: Reflection", attempt=attempt, needs_llm=needs_llm)
        try:
            if hasattr(self, "reporter") and self.reporter:
                self.reporter.agent("phase", agent=self.name, phase="reflect", attempt=attempt)
        except Exception:
            pass
        
        # Quick reflection for first attempt
        if state["attempt_number"] == 1 and not state.get("needs_reflection", False):
            return {
                "reflection_summary": f"Processing request: {state['original_request'][:100]}",
                "adaptation_needed": False,
                "current_phase": ExecutionPhase.PLAN.value
            }
        
        # LLM reflection for failures or when explicitly needed
        if self.use_llm_reflection and (state["attempt_number"] > 1 or state.get("needs_reflection", False)):
            try:
                reflection_prompt = f"""Quick reflection on current situation:

REQUEST: {state['original_request']}
ATTEMPT: {state['attempt_number']}/{state['max_attempts']}
COMPLETED ACTIONS: {len(state.get('completed_actions', []))}

Briefly analyze what needs to be done and any issues to avoid. Respond in 2-3 sentences only.
"""
                
                response = await asyncio.wait_for(
                    self.model.ainvoke([HumanMessage(content=reflection_prompt)]),
                    timeout=10.0  # Quick timeout
                )
                
                reflection_summary = response.content[:500]  # Keep it short
                
                return {
                    "reflection_summary": reflection_summary,
                    "adaptation_needed": "fail" in reflection_summary.lower() or "error" in reflection_summary.lower(),
                    "current_phase": ExecutionPhase.PLAN.value
                }
                
            except Exception as e:
                self.logger.warning("LLM reflection failed, using fallback", error=str(e))
                return {
                    "reflection_summary": f"Fallback reflection: Continue processing request (attempt {state['attempt_number']})",
                    "adaptation_needed": state["attempt_number"] > 1,
                    "current_phase": ExecutionPhase.PLAN.value
                }
        
        # No reflection needed
        return {
            "reflection_summary": "Proceeding with task execution",
            "adaptation_needed": False,
            "current_phase": ExecutionPhase.PLAN.value
        }
    
    async def _plan_heuristic(self, state: HybridRPAVHState) -> Dict[str, Any]:
        """Fast, rule-based planning - no LLM needed."""
        self.logger.user_info("Planning actions...")
        self.logger.debug("Hybrid RPAVH: Heuristic planning")
        try:
            if hasattr(self, "reporter") and self.reporter:
                self.reporter.agent("phase", agent=self.name, phase="plan")
        except Exception:
            pass

        request = state["original_request"].lower()
        available_tools = [tool.name for tool in self.tools]

        self.logger.debug("Planning details", request_preview=request[:100],
                   available_tools=available_tools,
                   static_resources=getattr(self, 'static_resources', {}))

        # Check what actions have already been completed
        completed_actions = state.get("completed_actions", [])
        completed_action_ids = {action.get("id") for action in completed_actions}

        # Rule-based action planning
        planned_actions = []
        
        # File discovery or existence validation
        csv_path_in_text = None
        try:
            for token in request.split():
                if token.lower().endswith(".csv"):
                    csv_path_in_text = token.strip("'\" ")
                    break
        except Exception:
            csv_path_in_text = None
        needs_validation = any(w in request for w in ["validate", "exist", "exists", "accessible", "access"]) or csv_path_in_text is not None
        if needs_validation and "file_stat" in available_tools:
            planned_actions.append({
                "id": "file_stat_action",
                "tool": "file_stat",
                "parameters": {"path": csv_path_in_text or (self.static_resources.get("csv_path") if hasattr(self, 'static_resources') else "")},
                "description": "Validate file existence and metadata",
                "expected_result": "file_metadata"
            })
        # File discovery patterns (enhanced matching)
        elif (any(pattern in request for pattern in ["find", "discover", "list", "search", "files", "ssis", "packages", "analyze"]) 
            or "ssis" in request or "dtsx" in request):
            if "find_files" in available_tools:
                # Extract file patterns
                # Prefer static resources; fall back to defaults and request hints
                file_pattern = self.static_resources.get("file_pattern", "*.dtsx") if hasattr(self, 'static_resources') else "*.dtsx"
                if "*.csv" in request:
                    file_pattern = "*.csv"
                elif "*.xml" in request:
                    file_pattern = "*.xml"
                elif "*.json" in request:
                    file_pattern = "*.json"
                elif "*.txt" in request:
                    file_pattern = "*.txt"
                
                # Extract search path with fallback to static resources
                search_path = self.static_resources.get("search_root", "data/ssis") if hasattr(self, 'static_resources') else "data/ssis"
                
                # Override with request-specific paths (avoid generic 'examples' override that breaks subdir roots)
                if "current" in request or "here" in request:
                    search_path = "."
                
                planned_actions.append({
                    "id": "find_files_action",
                    "tool": "find_files",
                    "parameters": {
                        "file_glob": file_pattern,
                        "root_path": search_path
                    },
                    "description": f"Find files matching {file_pattern} in {search_path}",
                    "expected_result": "list_of_files"
                })
        
        # File reading patterns
        if any(pattern in request for pattern in ["read", "analyze", "content", "examine"]):
            if "read_text_fast" in available_tools:
                # Depend on find only if we actually planned a find action
                depends = "find_files_action" if any(a.get("id") == "find_files_action" for a in planned_actions) else None
                planned_actions.append({
                    "id": "read_files_action",
                    "tool": "read_text_fast",
                    "parameters": {},  # Will be populated dynamically
                    "description": "Read discovered file contents",
                    "expected_result": "file_contents",
                    "depends_on": depends
                })
        
        # CSV aggregation patterns (analysis)
        if any(pattern in request for pattern in ["average", "avg", "mean", "group by", "per category", "aggregate"]):
            tool_choice = None
            if "pandas_chunk_aggregate" in available_tools:
                tool_choice = "pandas_chunk_aggregate"
            elif "csv_chunk_aggregate" in available_tools:
                tool_choice = "csv_chunk_aggregate"
            if tool_choice:
                # extract path and column hints
                csv_path = None
                group_by = None
                value_col = None
                # try to pull from static resources
                if hasattr(self, 'static_resources'):
                    csv_path = self.static_resources.get("csv_path")
                    group_by = self.static_resources.get("group_by")
                    value_col = self.static_resources.get("value_column")
                # naive parse of a .csv path from request
                try:
                    for token in request.split():
                        if token.lower().endswith(".csv"):
                            csv_path = token.strip("'\" ")
                            break
                except Exception:
                    pass
                action = {
                    "id": "csv_aggregate_action",
                    "tool": tool_choice,
                    "parameters": {
                        **({"path": csv_path} if csv_path else {}),
                        **({"group_by": group_by} if group_by else {}),
                        **({"value_column": value_col} if value_col else {}),
                    },
                    "description": "Compute mean per category from large CSV",
                    "expected_result": "grouped_averages"
                }
                planned_actions.append(action)

        # Report generation patterns
        if any(pattern in request for pattern in ["report", "generate", "create", "write", "document"]):
            # Only reporter agents are allowed to write reports
            if (getattr(self.config, "role", None) == AgentRole.REPORTER) and ("write_text_atomic" in available_tools):
                report_filename = "analysis_report.md"
                if hasattr(self, 'static_resources') and "report_filename" in self.static_resources:
                    report_filename = self.static_resources["report_filename"]
                
                # Ensure we have at least one discovery step before writing if tools are available
                has_find = any(a.get("id") == "find_files_action" for a in planned_actions)
                if not has_find and "find_files" in available_tools:
                    search_path = self.static_resources.get("search_root", "data/ssis") if hasattr(self, 'static_resources') else "data/ssis"
                    fp = self.static_resources.get("file_pattern", "*.dtsx") if hasattr(self, 'static_resources') else "*.dtsx"
                    planned_actions.append({
                        "id": "find_files_action",
                        "tool": "find_files",
                        "parameters": {
                            "file_glob": fp,
                            "root_path": search_path
                        },
                        "description": f"Find files matching {fp} in {search_path}",
                        "expected_result": "list_of_files"
                    })
                
                planned_actions.append({
                    "id": "write_report_action",
                    "tool": "write_text_atomic",
                    "parameters": {
                        "path": report_filename
                        # content will be added dynamically
                    },
                    "description": f"Generate report: {report_filename}",
                    "expected_result": "report_created",
                    "depends_on": (
                        "read_files_action" if any(a.get("id") == "read_files_action" for a in planned_actions)
                        else ("find_files_action" if any(a.get("id") == "find_files_action" for a in planned_actions) else None)
                    )
                })
        
        # Fallback: choose a safe and meaningful default
        if not planned_actions:
            if "file_stat" in available_tools and (csv_path_in_text or (hasattr(self, 'static_resources') and self.static_resources.get("csv_path"))):
                planned_actions.append({
                    "id": "file_stat_action",
                    "tool": "file_stat",
                    "parameters": {"path": csv_path_in_text or self.static_resources.get("csv_path")},
                    "description": "Validate file existence and metadata",
                    "expected_result": "file_metadata"
                })
            elif "find_files" in available_tools:
                fp = self.static_resources.get("file_pattern", "*.dtsx") if hasattr(self, 'static_resources') else "*.dtsx"
                search_path = self.static_resources.get("search_root", ".") if hasattr(self, 'static_resources') else "."
                planned_actions.append({
                    "id": "find_files_action",
                    "tool": "find_files",
                    "parameters": {"file_glob": fp, "root_path": search_path},
                    "description": f"Find files matching {fp} in {search_path}",
                    "expected_result": "list_of_files"
                })
            elif available_tools:
                planned_actions.append({
                    "id": "generic_action",
                    "tool": available_tools[0],
                    "parameters": {},
                    "description": f"Execute using {available_tools[0]}",
                    "expected_result": "task_result"
                })
        
        # Create action plan
        action_plan = {
            "strategy": "heuristic_rule_based",
            "total_actions": len(planned_actions),
            "estimated_duration": len(planned_actions) * 5.0,  # 5 seconds per action
            "uses_llm": False,
            "created_at": time.time()
        }
        
        self.logger.user_info(f"Created plan with {len(planned_actions)} actions")
        self.logger.debug("Hybrid RPAVH: Plan created", actions=len(planned_actions), 
                   strategy=action_plan["strategy"])
        # Remove actions that have already been completed
        filtered_actions = []
        for action in planned_actions:
            action_id = action.get("id")
            if action_id not in completed_action_ids:
                filtered_actions.append(action)
            else:
                self.logger.debug(f"Skipping already completed action: {action_id}")

        try:
            plan_summary = [
                {"id": a.get("id"), "tool": a.get("tool"), "depends_on": a.get("depends_on")}
                for a in filtered_actions
            ]
            self.logger.debug("Hybrid RPAVH: Plan summary", actions=plan_summary)
        except Exception:
            pass

        return {
            "action_plan": action_plan,
            "pending_actions": filtered_actions,
            "current_phase": ExecutionPhase.ACT.value
        }
    
    async def _act_direct(self, state: HybridRPAVHState) -> Dict[str, Any]:
        """Direct tool execution - fast and reliable."""
        pending_count = len(state["pending_actions"])
        self.logger.user_progress(f"Executing {pending_count} actions")
        self.logger.debug("Hybrid RPAVH: Direct action execution",
                   pending=len(state.get("pending_actions", [])))
        try:
            if hasattr(self, "reporter") and self.reporter:
                self.reporter.agent("phase", agent=self.name, phase="act", pending=len(state.get("pending_actions", [])))
        except Exception:
            pass
        
        pending_actions = list(state.get("pending_actions", []))
        completed_actions = list(state.get("completed_actions", []))
        current_result = None
        execution_errors = []

        # If no pending actions, consider this a success if we have completed any work
        if not pending_actions:
            success = len(completed_actions) > 0
            self.logger.user_info("No pending actions - task appears complete")
            return {
                "completed_actions": completed_actions,
                "current_result": state.get("current_result"),
                "current_phase": ExecutionPhase.VERIFY.value,
                "needs_reflection": False,
            }

        # Execute actions until no further progress can be made
        while True:
            progress_made = False
            for action in pending_actions:
                if action.get("status") == "completed":
                    continue
                
                # Check dependencies (support single id or list of ids)
                depends_on = action.get("depends_on")
                if depends_on:
                    if isinstance(depends_on, (list, tuple, set)):
                        dependency_completed = all(
                            any(a["id"] == dep and a.get("status") == "completed" for a in completed_actions)
                            for dep in depends_on
                        )
                    else:
                        dependency_completed = any(
                            a["id"] == depends_on and a.get("status") == "completed" 
                            for a in completed_actions
                        )
                    if not dependency_completed:
                        continue  # Skip this action for now
                
                action_start = time.time()
                tool_name = action.get("tool", "")
                
                try:
                    # Find tool
                    tool = next((t for t in self.tools if t.name == tool_name), None)
                    if not tool:
                        raise ValueError(f"Tool '{tool_name}' not available")
                    
                    # Prepare parameters
                    params = dict(action.get("parameters", {}))
                    
                    # Path fallback adjustments for filesystem tools
                    if tool_name == "find_files":
                        rp = params.get("root_path")
                        if rp and not os.path.isabs(rp) and not os.path.isdir(rp):
                            alt = os.path.join("examples", rp)
                            if os.path.isdir(alt):
                                params["root_path"] = alt
                    
                    # Dynamic parameter population
                    if tool_name == "read_text_fast" and "path" not in params:
                        # Get file from previous find_files result or static csv_path
                        find_result = next((a.get("result") for a in completed_actions 
                                          if a.get("id") == "find_files_action"), None)
                        if find_result:
                            # Normalize result from find_files (dict with 'files')
                            file_list = []
                            if isinstance(find_result, dict) and 'files' in find_result:
                                file_list = [f.get('path') for f in find_result.get('files', [])]
                            elif isinstance(find_result, list):
                                file_list = find_result
                            if file_list:
                                params["path"] = file_list[0]  # Read first file
                        elif hasattr(self, 'static_resources') and self.static_resources.get("csv_path"):
                            params["path"] = self.static_resources.get("csv_path")
                    
                    elif tool_name == "write_text_atomic" and not params.get("content"):
                        # Ensure path param exists
                        if "path" not in params:
                            params["path"] = self.static_resources.get("report_filename", "analysis_report.md")

                        # Collect data from previous actions for a richer report
                        files_info = []  # list of {path, size_bytes}
                        content_snippets = []  # list of strings
                        aggregates = []  # list of aggregate results
                        # Collect aggregates from dependency tasks if available (via tracker)
                        try:
                            if hasattr(self, "_flow_ref") and self._flow_ref and hasattr(self._flow_ref, "orchestrator") and state.get("thread_id"):
                                thread_id = state.get("thread_id") or ""
                                current_task_id = thread_id.split("task_", 1)[-1]
                                tracker = getattr(self._flow_ref.orchestrator, "task_tracker", None)
                                if tracker:
                                    current = tracker.get_task(current_task_id)
                                    dep_ids = (current.dependencies if current else []) or []
                                    for dep_id in dep_ids:
                                        dep_task = tracker.get_task(dep_id)
                                        dep_res = getattr(dep_task, "result", None) if dep_task else None
                                        if isinstance(dep_res, dict):
                                            data = dep_res.get("data", {})
                                            if isinstance(data, dict):
                                                if data.get("groups"):
                                                    aggregates.append(data)
                        except Exception:
                            pass

                        # 1) From this agent's completed actions (if any)
                        for prev_action in completed_actions:
                            res = prev_action.get("result")
                            if isinstance(res, dict) and res.get("files"):
                                # Gather file info from find_files
                                for f in res.get("files", [])[: self.static_resources.get("max_files_to_include", 10)]:
                                    files_info.append({
                                        "path": f.get("path"),
                                        "size_bytes": int(f.get("size_bytes", 0) or 0),
                                    })
                            elif isinstance(res, str) and prev_action.get("tool") == "read_text_fast":
                                content_snippets.append(res)
                            elif isinstance(res, dict) and prev_action.get("tool") == "streaming_file_reader" and res.get("chunks"):
                                # Use previews from streaming chunks
                                try:
                                    for ch in res.get("chunks", [])[:3]:
                                        prev = ch.get("preview") or ""
                                        if prev:
                                            content_snippets.append(prev)
                                except Exception:
                                    pass
                            elif isinstance(res, dict) and prev_action.get("tool") in ("csv_chunk_aggregate", "pandas_chunk_aggregate") and res.get("groups"):
                                aggregates.append(res)

                        # 2) Augment with dependency results from orchestrator (if Flow reference is available)
                        try:
                            if hasattr(self, "_flow_ref") and self._flow_ref and hasattr(self._flow_ref, "orchestrator") and state.get("thread_id"):
                                thread_id = state.get("thread_id") or ""
                                # Thread IDs are formatted as 'task_<task_id>' by the orchestrator
                                current_task_id = thread_id.split("task_", 1)[-1]
                                tracker = getattr(self._flow_ref.orchestrator, "task_tracker", None)
                                if tracker:
                                    current = tracker.get_task(current_task_id)
                                    dep_ids = (current.dependencies if current else []) or []
                                    for dep_id in dep_ids:
                                        dep_task = tracker.get_task(dep_id)
                                        dep_res = getattr(dep_task, "result", None) if dep_task else None
                                        if isinstance(dep_res, dict):
                                            data = dep_res.get("data", {})
                                            # files
                                            for f in (data.get("files", []) or [])[: self.static_resources.get("max_files_to_include", 10)]:
                                                info = {
                                                    "path": f.get("path"),
                                                    "size_bytes": int(f.get("size_bytes", 0) or 0),
                                                }
                                                if info["path"] and info not in files_info:
                                                    files_info.append(info)
                                            # sample snippets
                                            for s in (data.get("samples", []) or [])[:3]:
                                                if isinstance(s, str):
                                                    content_snippets.append(s)
                        except Exception:
                            pass


                        # Optionally ask LLM to synthesize a richer report
                        use_llm = self.static_resources.get("use_llm_for_report")
                        if use_llm is None:
                            use_llm = True
                        if use_llm:
                            try:
                                max_chars = self.static_resources.get("content_limits", {}).get("max_file_content_chars", 1000)
                                samples = []
                                for s in content_snippets[:3]:
                                    samples.append(s[:max_chars])
                                files_table = "\n".join(
                                    f"- {Path(f['path']).name} ({int(f.get('size_bytes',0))/1024.0:.1f} KB)" for f in files_info[:10] if f.get('path')
                                )
                                # Determine content type (CSV/SSIS/files) for a contextual prompt
                                try:
                                    exts = set()
                                    for f in files_info:
                                        try:
                                            exts.add(Path(f.get("path", "")).suffix.lower())
                                        except Exception:
                                            pass
                                except Exception:
                                    exts = set()
                                if exts and all(e == ".csv" for e in exts):
                                    content_type = "CSV files"
                                elif exts and all(e == ".dtsx" for e in exts):
                                    content_type = "SSIS packages"
                                else:
                                    content_type = "files"

                                extra_guidance = ""
                                if content_type == "CSV files":
                                    extra_guidance = (
                                        "For CSV files, infer schemas from headers and propose a merge strategy: likely join keys, join type (inner/left/right/full), "
                                        "column mappings/renames, handling of missing values and type mismatches, and a brief step-by-step plan. Include a short example "
                                        "(SQL JOIN or pandas merge) using the inferred keys.\n\n"
                                    )

                                # Compose aggregate summary for LLM if available
                                agg_text = ""
                                try:
                                    if aggregates:
                                        agg = aggregates[0]
                                        lines = [
                                            f"Aggregations: mean of '{agg.get('value_column','value')}' grouped by '{agg.get('group_by','group')}'.",
                                            f"Rows processed: {agg.get('row_count',0)}, unique groups: {agg.get('unique_groups',0)}.",
                                            "Top groups by count:",
                                        ]
                                        for g in agg.get('groups', [])[:10]:
                                            lines.append(f"- {g.get('group','')}: count={int(g.get('count',0))}, average={float(g.get('average',0.0)):.4f}")
                                        agg_text = "\n".join(lines)
                                except Exception:
                                    agg_text = ""
                                prompt = (
                                    "You are a senior data integration analyst. Draft a comprehensive, professional markdown report "
                                    f"based on the provided {content_type} and file metadata. Include the sections: Executive Summary, "
                                    "Data Overview, Detailed Analysis, Key Findings, and Conclusion. Be concise but substantive.\n\n"
                                    f"Files:\n{files_table}\n\n"
                                    + (f"Aggregates summary:\n{agg_text}\n\n" if agg_text else "")
                                    + ("Content samples (truncated):\n\n" + "\n\n".join(f"Sample {i+1}:\n\n{sample}" for i, sample in enumerate(samples)) + "\n\n" if samples else "")
                                    + extra_guidance +
                                    "Write in clear markdown without backticks around the whole report."
                                )
                                llm_resp = await asyncio.wait_for(self.model.ainvoke([HumanMessage(content=prompt)]), timeout=60.0)
                                llm_text = llm_resp.content if hasattr(llm_resp, "content") else str(llm_resp)
                                if llm_text and isinstance(llm_text, str) and len(llm_text.strip()) > 0:
                                    params["content"] = llm_text
                                else:
                                    raise RuntimeError("LLM report generation returned empty content")
                            except Exception as e:
                                raise
                        else:
                            raise RuntimeError("use_llm_for_report is False but LLM-only reporting is enforced")
                    
                    
                    # Execute tool via ainvoke with param dict
                    tool_input = params if params else {}
                    self.logger.user_info(f"Using {tool_name}...")
                    self.logger.debug("Hybrid RPAVH: Executing tool", tool=tool_name, params=tool_input)
                    try:
                        if hasattr(self, "reporter") and self.reporter:
                            pv = {k: v for k, v in tool_input.items() if k in ("path", "root_path", "file_glob")}
                            self.reporter.agent("tool_execute", agent=self.name, tool=tool_name, params_preview=pv)
                    except Exception:
                        pass
                    result = await tool.ainvoke(tool_input)
                    
                    # Record success
                    action["result"] = result
                    action["status"] = "completed"
                    action["execution_time"] = time.time() - action_start
                    current_result = result
                    completed_actions.append(action)

                    # Expand dynamic follow-up actions based on results (e.g., read all found files)
                    try:
                        if tool_name == "find_files" and isinstance(result, dict) and result.get("files") and not action.get("expanded"):
                            max_reads = self.static_resources.get("max_files_to_include", 10)
                            existing_ids = {a.get("id") for a in pending_actions} | {a.get("id") for a in completed_actions}
                            count = 0
                            new_read_ids = []

                            # Determine available reading tools
                            tool_names = {t.name for t in self.tools}
                            stream_available = "streaming_file_reader" in tool_names
                            stream_threshold_kb = int(self.static_resources.get("stream_threshold_kb", 256))

                            for f in result.get("files", []):
                                path = f.get("path")
                                if not path:
                                    continue
                                rid = f"read_file_{os.path.basename(path)}"
                                if rid in existing_ids:
                                    continue
                                size_bytes = int(f.get("size_bytes", 0) or 0)
                                # Choose streaming for larger files when available
                                if stream_available and size_bytes > (stream_threshold_kb * 1024):
                                    read_action = {
                                        "id": rid,
                                        "tool": "streaming_file_reader",
                                        "parameters": {
                                            "file_path": path,
                                            "chunk_size_kb": int(self.static_resources.get("chunk_size_kb", 128)),
                                            "max_chunks": int(self.static_resources.get("max_stream_chunks", 8)),
                                        },
                                        "description": f"Stream file content: {os.path.basename(path)}",
                                        "expected_result": "file_chunks",
                                        "depends_on": action.get("id")
                                    }
                                else:
                                    read_action = {
                                        "id": rid,
                                        "tool": "read_text_fast",
                                        "parameters": {"path": path},
                                        "description": f"Read file content: {os.path.basename(path)}",
                                        "expected_result": "file_content",
                                        "depends_on": action.get("id")
                                    }
                                pending_actions.append(read_action)
                                new_read_ids.append(rid)
                                existing_ids.add(rid)
                                count += 1
                                if count >= max_reads:
                                    break

                            # Make write action wait for all read actions
                            write_action = next((a for a in pending_actions if a.get("id") == "write_report_action" and a.get("status") != "completed"), None)
                            if write_action and new_read_ids:
                                write_action["depends_on"] = new_read_ids
                            action["expanded"] = True
                            try:
                                if hasattr(self, "reporter") and self.reporter:
                                    self.reporter.agent("expanded_actions", agent=self.name, count=count, base_action=action.get("id"))
                            except Exception:
                                pass
                    except Exception:
                        pass
                    
                    self.logger.debug("Hybrid RPAVH: Action completed", action_id=action["id"], 
                               tool=tool_name, duration=action["execution_time"]) 
                    try:
                        if hasattr(self, "reporter") and self.reporter:
                            self.reporter.agent("action_completed", agent=self.name, action_id=action.get("id"), tool=tool_name)
                    except Exception:
                        pass
                    
                except Exception as e:
                    error_msg = str(e)
                    self.logger.user_error(f"Action failed: {tool_name}")
                    self.logger.error("Hybrid RPAVH: Action failed", action_id=action.get("id"), 
                               tool=tool_name, error=error_msg)
                    
                    action["status"] = "failed"
                    action["error"] = error_msg
                    action["execution_time"] = time.time() - action_start
                    execution_errors.append(f"Action {action.get('id')} failed: {error_msg}")
            if not progress_made:
                break
        
        # Update state
        success = len(execution_errors) == 0
        next_phase = ExecutionPhase.VERIFY.value if success else ExecutionPhase.REFLECT.value
        
        if not success and state["attempt_number"] >= state["max_attempts"]:
            next_phase = ExecutionPhase.FAILED.value
        
        updates = {
            "completed_actions": completed_actions,
            "current_result": current_result,
            "current_phase": next_phase,
            "needs_reflection": not success,  # Only reflect on failures
        }
        
        if not success:
            updates["attempt_number"] = state["attempt_number"] + 1
        
        return updates
    
    async def _verify_fast(self, state: HybridRPAVHState) -> Dict[str, Any]:
        """Fast verification - minimal LLM usage."""
        self.logger.user_progress("Verifying results")
        self.logger.debug("Hybrid RPAVH: Fast verification")
        try:
            if hasattr(self, "reporter") and self.reporter:
                self.reporter.agent("phase", agent=self.name, phase="verify")
        except Exception:
            pass
        
        completed_actions = state.get("completed_actions", [])
        current_result = state.get("current_result")
        
        # Simple heuristic verification
        verification_passed = (
            len(completed_actions) > 0 and
            not any(action.get("status") == "failed" for action in completed_actions)
        )

        # Only fail verification if there are INCOMPLETE write actions
        try:
            pending_actions = state.get("pending_actions", [])
            incomplete_writes = [a for a in pending_actions
                               if a.get("tool") == "write_text_atomic" and a.get("status") != "completed"]
            if incomplete_writes:
                verification_passed = False
                self.logger.debug(f"Verification failed: {len(incomplete_writes)} incomplete write actions")
            else:
                self.logger.debug(f"Verification passed: {len(completed_actions)} completed actions, no incomplete writes")
        except Exception as e:
            self.logger.warning(f"Verification check failed: {e}")
            pass
        
        # Optional LLM verification for complex cases
        if not verification_passed and self.use_llm_verification:
            try:
                verify_prompt = f"""Quick verification: Does this result address the request adequately?

REQUEST: {state['original_request']}
RESULT: {str(current_result)[:200]}
ACTIONS: {len(completed_actions)} completed

Answer with just: YES or NO, followed by a brief reason.
"""
                
                response = await asyncio.wait_for(
                    self.model.ainvoke([HumanMessage(content=verify_prompt)]),
                    timeout=8.0
                )
                
                verification_passed = response.content.strip().upper().startswith("YES")
                
            except Exception as e:
                self.logger.warning("LLM verification failed, using heuristic result", error=str(e))
        
        next_phase = ExecutionPhase.COMPLETE.value if verification_passed else ExecutionPhase.REFLECT.value
        
        return {
            "verification_passed": verification_passed,
            "current_phase": next_phase,
            "needs_reflection": not verification_passed
        }
    
    async def _complete(self, state: HybridRPAVHState) -> Dict[str, Any]:
        """Complete execution with results summary."""
        success = state.get("verification_passed", False)
        self.logger.user_success("Task completed" if success else "Task failed")
        self.logger.debug("Hybrid RPAVH: Completion", 
                   success=state.get("verification_passed", False))
        try:
            if hasattr(self, "reporter") and self.reporter:
                self.reporter.agent("phase", agent=self.name, phase="complete", success=state.get("verification_passed", False))
        except Exception:
            pass
        
        completed_actions = state.get("completed_actions", [])
        current_result = state.get("current_result")
        
        # Build concise final response
        if current_result:
            if isinstance(current_result, dict) and "message" in current_result:
                final_response = current_result["message"]
            elif isinstance(current_result, str):
                final_response = current_result
            else:
                final_response = str(current_result)
        else:
            # Summarize actions
            final_response = f"Completed {len(completed_actions)} actions for: {state['original_request'][:100]}"

        # Construct lightweight structured handoff data for downstream tasks
        files_info: List[Dict[str, Any]] = []
        content_snippets: List[str] = []
        aggregates: List[Dict[str, Any]] = []
        try:
            for prev_action in completed_actions:
                res = prev_action.get("result")
                if isinstance(res, dict) and res.get("files"):
                    for f in res.get("files", [])[: self.static_resources.get("max_files_to_include", 10)]:
                        files_info.append({
                            "path": f.get("path"),
                            "size_bytes": int(f.get("size_bytes", 0) or 0),
                        })
                elif isinstance(res, str) and prev_action.get("tool") == "read_text_fast":
                    content_snippets.append(res)
                elif isinstance(res, dict) and prev_action.get("tool") == "streaming_file_reader" and res.get("chunks"):
                    try:
                        for ch in res.get("chunks", [])[:3]:
                            prev = ch.get("preview") or ""
                            if prev:
                                content_snippets.append(prev)
                    except Exception:
                        pass
        except Exception:
            pass

        execution_success = (
            state.get("verification_passed", True) and
            len(completed_actions) > 0 and
            current_result is not None
        )
        
        return {
            "final_response": final_response,
            "execution_complete": True,
            "execution_success": execution_success,
            "current_phase": ExecutionPhase.COMPLETE.value,
            # Structured data for orchestrator context passing
            "handoff_data": {
                "files": files_info,
                "samples": content_snippets[:3],
                "aggregates": aggregates[:1] if aggregates else [],
            }
        }
    
    async def _handle_failure(self, state: HybridRPAVHState) -> Dict[str, Any]:
        """Handle failures with concise reporting."""
        self.logger.user_error("Task failed, analyzing issue...")
        self.logger.error("Hybrid RPAVH: Handling failure")
        try:
            if hasattr(self, "reporter") and self.reporter:
                self.reporter.agent("phase", agent=self.name, phase="failed")
        except Exception:
            pass
        
        failure_msg = f"Task failed after {state['attempt_number']} attempts: {state['original_request'][:100]}"
        
        return {
            "final_response": failure_msg,
            "execution_complete": True,
            "execution_success": False,
            "current_phase": ExecutionPhase.FAILED.value
        }
    
    # Transition logic
    def _after_reflect(self, state: HybridRPAVHState) -> str:
        if state["attempt_number"] > state["max_attempts"]:
            return "failed"
        return "plan"
    
    def _after_act(self, state: HybridRPAVHState) -> str:
        if state.get("needs_reflection", False):
            if state["attempt_number"] >= state["max_attempts"]:
                return "failed"
            return "reflect"
        return "verify"
    
    def _after_verify(self, state: HybridRPAVHState) -> str:
        if state.get("verification_passed", False):
            return "complete"
        if state["attempt_number"] >= state["max_attempts"]:
            return "failed"
        # If write action exists but not completed, try another cycle
        try:
            pending = state.get("pending_actions", [])
            if any((a.get("tool") == "write_text_atomic") and (a.get("status") != "completed") for a in pending):
                return "reflect"
        except Exception:
            pass
        # Default: complete if we have made any progress
        if len(state.get("completed_actions", [])) > 0:
            return "complete"
        return "reflect"
    
    # Public interface
    async def arun(
        self,
        message: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute Hybrid RPAVH cycle - fast and reliable."""
        self.logger.user_progress(f"Starting task: {message[:50]}...")
        self.logger.info("Hybrid RPAVH Agent starting", request_preview=message[:100])
        
        initial_state = HybridRPAVHState(
            messages=[HumanMessage(content=message)],
            original_request=message,
            thread_id=thread_id,
            current_phase=ExecutionPhase.REFLECT.value,
            attempt_number=1,
            max_attempts=self.max_attempts,
            action_plan=None,
            pending_actions=[],
            completed_actions=[],
            current_result=None,
            needs_reflection=False,
            reflection_summary=None,
            adaptation_needed=False,
            verification_passed=False,
            requires_handoff=False,
            final_response=None,
            execution_complete=False,
            execution_success=False
        )
        
        config = {"configurable": {"thread_id": thread_id or f"hybrid_{self.name}"}}
        
        try:
            final_state = await self.compiled_graph.ainvoke(initial_state, config=config, **kwargs)
            
            # Build structured data for downstream consumers (e.g., orchestrator context)
            data_block = {}
            try:
                # Prefer explicit handoff data if provided by _complete
                handoff = final_state.get("handoff_data") or {}
                if isinstance(handoff, dict):
                    data_block.update(handoff)
            except Exception:
                pass
            try:
                # As a fallback, synthesize minimal file list from completed actions
                if not data_block.get("files"):
                    files = []
                    for act in final_state.get("completed_actions", []) or []:
                        res = act.get("result")
                        if isinstance(res, dict) and res.get("files"):
                            for f in res.get("files", [])[:10]:
                                files.append({"path": f.get("path"), "size_bytes": int(f.get("size_bytes", 0) or 0)})
                    if files:
                        data_block["files"] = files
            except Exception:
                pass
            
            return {
                "message": final_state.get("final_response", "Task completed"),
                "success": final_state.get("execution_success", False),
                "attempts": final_state.get("attempt_number", 1),
                "actions_completed": len(final_state.get("completed_actions", [])),
                "verification_passed": final_state.get("verification_passed", False),
                "data": data_block,
                "metadata": {
                    "strategy": "hybrid_rpavh",
                    "phase": final_state.get("current_phase"),
                    "used_llm_reflection": self.use_llm_reflection,
                    "used_llm_verification": self.use_llm_verification
                }
            }
            
        except Exception as e:
            self.logger.user_error(f"Agent execution failed: {str(e)}")
            self.logger.error("Hybrid RPAVH Agent execution failed", error=str(e))
            return {
                "message": f"Agent execution failed: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    def run(self, message: str, thread_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Synchronous wrapper for arun."""
        return asyncio.run(self.arun(message, thread_id, **kwargs))
    
    # Tool management (same as before)
    def set_tools(self, tools: List[BaseTool]) -> None:
        """Replace tools and update registry."""
        self.tools = list(tools)
        self.tool_registry = ToolRegistry()
        for tool in self.tools:
            self.tool_registry.register_tool_instance(tool)
        self.logger.info("Hybrid RPAVH Agent tools updated", tool_count=len(tools))
    
    def add_tools(self, tools: List[BaseTool]) -> None:
        """Add tools (deduplicate by name)."""
        existing_names = {t.name for t in self.tools}
        new_tools = [t for t in tools if t.name not in existing_names]
        
        for tool in new_tools:
            self.tools.append(tool)
            self.tool_registry.register_tool_instance(tool)
        
        self.logger.info("Hybrid RPAVH Agent tools added", new_tools=len(new_tools))
    
    def list_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
    
    def set_flow_reference(self, flow_ref: Any) -> None:
        """Set reference to parent Flow for tool resolution."""
        self._flow_ref = flow_ref
    
    def adopt_flow_tools(self, flow: Any, names: Optional[List[str]] = None) -> None:
        """Adopt tools from a Flow instance."""
        if hasattr(flow, 'tool_registry'):
            available_tools = flow.tool_registry.list_tools()
            tools_to_add = []
            
            for tool_name, _ in available_tools.items():
                if names is None or tool_name in names:
                    try:
                        tool_instance = flow.tool_registry.get_tool(tool_name)
                        if tool_instance:
                            tools_to_add.append(tool_instance)
                    except Exception:
                        pass
            
            if tools_to_add:
                self.add_tools(tools_to_add)
                self.logger.info("Hybrid RPAVH Agent adopted flow tools", 
                          adopted_count=len(tools_to_add))
