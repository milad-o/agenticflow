"""
Enhanced Agent Implementation for AgenticFlow

This is the main Agent class that replaces both the legacy Agent and HybridRPAVHAgent.
It provides a clean, pluggable LangGraph architecture with intelligent execution patterns.

Key Features:
- Pluggable LangGraph execution graphs
- Intelligent RPAVH (Reflect-Plan-Act-Verify-Handoff) pattern by default
- Component-aware logging and diagnostics
- Hierarchical tool/resource resolution
- Event-driven architecture with lifecycle management
"""

import asyncio
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, TypedDict, Annotated, Union, Callable, TYPE_CHECKING
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
from agenticflow.core.logging import get_component_logger

if TYPE_CHECKING:
    from agenticflow.core.config import AgentConfig
from agenticflow.core.events import get_event_bus


class ExecutionPhase(Enum):
    """Phases in agent execution cycle."""
    INITIALIZE = "initialize"
    REFLECT = "reflect"
    PLAN = "plan"
    ACT = "act"
    VERIFY = "verify"
    HANDOFF = "handoff"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ActionPlan:
    """Simple action plan for direct tool execution."""
    actions: List[Dict[str, Any]]
    strategy: str
    fallback_enabled: bool = True
    estimated_duration: float = 30.0


class AgentState(TypedDict):
    """State for agent execution - comprehensive but clean."""
    # Input and Context
    messages: Annotated[List[BaseMessage], add]
    original_request: str
    thread_id: Optional[str]

    # Execution State
    current_phase: str
    attempt_number: int
    max_attempts: int

    # Planning and Actions
    action_plan: Optional[Dict[str, Any]]
    pending_actions: List[Dict[str, Any]]
    completed_actions: List[Dict[str, Any]]
    current_result: Optional[Any]

    # Reflection and Adaptation
    needs_reflection: bool
    reflection_summary: Optional[str]
    adaptation_needed: bool

    # Results and Handoff
    verification_passed: bool
    requires_handoff: bool
    final_response: Optional[str]
    execution_complete: bool
    execution_success: bool


class Agent:
    """
    Enhanced Agent class with pluggable LangGraph architecture.

    This is the main agent implementation that provides:
    - Intelligent RPAVH execution pattern by default
    - Pluggable custom LangGraph graphs
    - Component-aware logging and diagnostics
    - Hierarchical tool and resource resolution
    - Event-driven lifecycle management
    """

    def __init__(
        self,
        model: BaseChatModel,  # Required LLM instance
        tools: Optional[List[BaseTool]] = None,
        name: str = "agent",  # Required name
        checkpointer: Optional[Any] = None,
        static_resources: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3,
        use_llm_reflection: bool = True,
        use_llm_verification: bool = False,
        custom_graph: Optional[StateGraph] = None,
        config: Optional["AgentConfig"] = None,  # Optional for advanced config
    ):
        """
        Initialize the Agent with required LLM instance.

        Args:
            model: Required LLM model instance (BaseChatModel)
            tools: List of available tools
            name: Agent name
            checkpointer: State checkpointer for persistence
            static_resources: Static resources available to the agent
            max_attempts: Maximum retry attempts for failed operations
            use_llm_reflection: Whether to use LLM for reflection phase
            use_llm_verification: Whether to use LLM for verification phase
            custom_graph: Optional custom LangGraph to replace default RPAVH pattern
            config: Optional advanced configuration object
        """
        # Build config if needed (for compatibility)
        if config is None:
            from agenticflow.core.config import AgentConfig
            config = AgentConfig(name=name, model="user_provided", temperature=0.1)

        self.config = config
        self.name = name  # Use the required name parameter

        # Core components - LLM is required
        self.tools: List[BaseTool] = list(tools or [])
        self.model = model  # Required parameter, no fallback
        self.checkpointer = checkpointer or MemorySaver()
        self.static_resources: Dict[str, Any] = dict(static_resources or {})

        # Execution Configuration
        self.max_attempts = max_attempts
        self.use_llm_reflection = use_llm_reflection
        self.use_llm_verification = use_llm_verification

        # Tool Registry and Flow Reference
        self.tool_registry = ToolRegistry()
        self._flow_ref: Optional[Any] = None

        # Register tools in registry
        for tool in self.tools:
            self.tool_registry.register_tool_instance(tool)

        # Event Bus Integration
        try:
            self.event_bus = get_event_bus()
        except Exception:
            self.event_bus = None

        # Component-aware logger
        self.logger = get_component_logger(self.name, "agent")

        # Build the execution graph (pluggable)
        if custom_graph:
            self.graph = custom_graph
            self.logger.info("Using custom execution graph")
        else:
            self.graph = self._build_default_graph()
            self.logger.info("Using default RPAVH execution graph")

        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)

        # Coordination callbacks
        self.handoff_callback: Optional[Callable] = None

        self.logger.info("Agent initialized", tools=len(self.tools),
                        llm_reflection=self.use_llm_reflection,
                        llm_verification=self.use_llm_verification)

    def set_custom_graph(self, custom_graph: StateGraph) -> "Agent":
        """Replace the execution graph with a custom one."""
        self.graph = custom_graph
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
        self.logger.info("Updated to custom execution graph")
        return self

    def _build_default_graph(self) -> StateGraph:
        """Build the default RPAVH (Reflect-Plan-Act-Verify-Handoff) graph."""
        graph = StateGraph(AgentState)

        # Core phases
        graph.add_node("initialize", self._initialize)
        graph.add_node("reflect", self._reflect)
        graph.add_node("plan", self._plan)
        graph.add_node("act", self._act)
        graph.add_node("verify", self._verify)
        graph.add_node("complete", self._complete)
        graph.add_node("handle_failure", self._handle_failure)

        # Flow
        graph.add_edge(START, "initialize")
        graph.add_edge("initialize", "reflect")

        # Conditional routing
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

    async def _initialize(self, state: AgentState) -> Dict[str, Any]:
        """Initialize the agent state for execution."""
        self.logger.user_progress("Initializing agent")
        self.logger.debug("Agent: Initializing")

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

    async def _reflect(self, state: AgentState) -> Dict[str, Any]:
        """Reflect on the request and determine approach."""
        attempt = state["attempt_number"]
        needs_llm = state.get("needs_reflection", False)

        if needs_llm:
            self.logger.user_info("Analyzing request and planning approach...")
        else:
            self.logger.user_progress("Quick assessment", step=attempt)

        self.logger.debug("Agent: Reflection", attempt=attempt, needs_llm=needs_llm)

        # Quick reflection for first attempt
        if attempt == 1 and not needs_llm:
            return {
                "reflection_summary": f"Processing request: {state['original_request'][:100]}",
                "adaptation_needed": False,
                "current_phase": ExecutionPhase.PLAN.value
            }

        # LLM reflection for failures or when explicitly needed
        if needs_llm:
            try:
                reflection_prompt = f"""
                Request: {state['original_request']}
                Attempt: {attempt}
                Previous failures: {len(state.get('completed_actions', []))}

                Reflect on this request and determine the best approach.
                Available tools: {[t.name for t in self.tools]}
                """

                messages = [HumanMessage(content=reflection_prompt)]
                response = await self.model.ainvoke(messages)

                return {
                    "reflection_summary": response.content,
                    "adaptation_needed": attempt > 1,
                    "current_phase": ExecutionPhase.PLAN.value
                }
            except Exception as e:
                self.logger.warning("LLM reflection failed, using fallback", error=str(e))

        # Fallback reflection
        return {
            "reflection_summary": f"Direct execution approach for: {state['original_request'][:100]}",
            "adaptation_needed": attempt > 1,
            "current_phase": ExecutionPhase.PLAN.value
        }

    async def _plan(self, state: AgentState) -> Dict[str, Any]:
        """Create an action plan using heuristics or LLM."""
        self.logger.user_info("Planning actions...")
        self.logger.debug("Agent: Planning")

        request = state["original_request"]

        # Simple heuristic planning (fast and predictable)
        planned_actions = self._create_heuristic_plan(request)

        if planned_actions:
            plan = ActionPlan(
                actions=planned_actions,
                strategy="heuristic_rule_based",
                fallback_enabled=True
            )

            self.logger.user_info(f"Created plan with {len(planned_actions)} actions")
            self.logger.debug("Agent: Plan created", actions=len(planned_actions))

            return {
                "action_plan": {
                    "actions": plan.actions,
                    "strategy": plan.strategy,
                    "fallback_enabled": plan.fallback_enabled
                },
                "pending_actions": planned_actions,
                "current_phase": ExecutionPhase.ACT.value
            }

        # No plan could be created
        return {
            "action_plan": None,
            "pending_actions": [],
            "current_phase": ExecutionPhase.FAILED.value
        }

    def _create_heuristic_plan(self, request: str) -> List[Dict[str, Any]]:
        """Create a simple action plan using heuristics."""
        # This is a simplified planning logic
        # In practice, this would be more sophisticated

        request_lower = request.lower()
        actions = []

        # File system operations
        if any(word in request_lower for word in ["find", "search", "locate", "csv", "files"]):
            if any(t.name in ["find_files", "find_csv_files"] for t in self.tools):
                actions.append({
                    "id": "find_files_action",
                    "tool": "find_files" if any(t.name == "find_files" for t in self.tools) else "find_csv_files",
                    "depends_on": None
                })

        # Reading operations
        if any(word in request_lower for word in ["read", "analyze", "inspect", "sample"]):
            if any(t.name in ["read_text_fast", "read_csv_sample"] for t in self.tools):
                actions.append({
                    "id": "read_content_action",
                    "tool": "read_text_fast" if any(t.name == "read_text_fast" for t in self.tools) else "read_csv_sample",
                    "depends_on": None
                })

        # Writing/reporting operations
        if any(word in request_lower for word in ["write", "report", "generate", "create"]):
            if any(t.name in ["write_text_atomic"] for t in self.tools):
                actions.append({
                    "id": "write_report_action",
                    "tool": "write_text_atomic",
                    "depends_on": None
                })

        return actions

    async def _act(self, state: AgentState) -> Dict[str, Any]:
        """Execute planned actions directly."""
        pending = len(state["pending_actions"])
        self.logger.user_progress(f"Executing {pending} actions")
        self.logger.debug("Agent: Executing actions")

        completed = []
        current_result = None

        for action in state["pending_actions"]:
            try:
                tool_name = action["tool"]
                self.logger.user_info(f"Using {tool_name}...")
                self.logger.debug("Agent: Executing tool", tool=tool_name)

                # Find and execute tool
                tool = next((t for t in self.tools if t.name == tool_name), None)
                if not tool:
                    raise ValueError(f"Tool {tool_name} not found")

                # Simple parameter inference (in practice, this would be more sophisticated)
                tool_input = self._infer_tool_parameters(action, state["original_request"])

                # Execute tool
                result = await tool.ainvoke(tool_input) if hasattr(tool, 'ainvoke') else tool.invoke(tool_input)
                current_result = result

                completed.append({
                    **action,
                    "result": str(result)[:500],  # Truncate for storage
                    "status": "completed",
                    "timestamp": time.time()
                })

                self.logger.debug("Agent: Action completed", action_id=action["id"])

            except Exception as e:
                self.logger.user_error(f"Action failed: {tool_name}")
                self.logger.error("Agent: Action failed", action_id=action.get("id"), error=str(e))

                completed.append({
                    **action,
                    "result": None,
                    "error": str(e),
                    "status": "failed",
                    "timestamp": time.time()
                })

        # Determine next phase
        failed_actions = [a for a in completed if a.get("status") == "failed"]

        if failed_actions and state["attempt_number"] < self.max_attempts:
            next_phase = ExecutionPhase.REFLECT.value
        elif current_result:
            next_phase = ExecutionPhase.VERIFY.value
        else:
            next_phase = ExecutionPhase.COMPLETE.value

        return {
            "completed_actions": completed,
            "current_result": current_result,
            "current_phase": next_phase
        }

    def _infer_tool_parameters(self, action: Dict[str, Any], request: str) -> Dict[str, Any]:
        """Infer tool parameters from action and request."""
        tool_name = action["tool"]

        # Simple parameter inference based on tool type
        if tool_name in ["find_files", "find_csv_files"]:
            return {"root_path": "examples/data", "file_glob": "*.csv"}
        elif tool_name == "read_text_fast":
            return {"path": "examples/data/csv/customers.csv"}
        elif tool_name == "read_csv_sample":
            return {"file_path": "examples/data/csv/customers.csv", "limit": 5}
        elif tool_name == "write_text_atomic":
            return {
                "path": "examples/artifact/report.md",
                "content": f"# Analysis Report\n\nRequest: {request}\n\nAnalysis results will be populated here."
            }

        return {}

    async def _verify(self, state: AgentState) -> Dict[str, Any]:
        """Verify the execution results."""
        self.logger.user_progress("Verifying results")
        self.logger.debug("Agent: Verification")

        # Fast heuristic verification by default
        result = state.get("current_result")

        if not result:
            return {
                "verification_passed": False,
                "current_phase": ExecutionPhase.FAILED.value
            }

        # Simple verification heuristics
        result_str = str(result).lower()
        success_indicators = ["success", "completed", "found", "created", "written"]
        failure_indicators = ["error", "failed", "not found", "exception"]

        has_success = any(indicator in result_str for indicator in success_indicators)
        has_failure = any(indicator in result_str for indicator in failure_indicators)

        verification_passed = has_success and not has_failure

        # Optional LLM verification for complex cases
        if self.use_llm_verification and not verification_passed:
            try:
                verify_prompt = f"""
                Original request: {state['original_request']}
                Execution result: {result}

                Does this result successfully address the original request? Answer with YES or NO and brief explanation.
                """

                messages = [HumanMessage(content=verify_prompt)]
                response = await self.model.ainvoke(messages)
                verification_passed = "yes" in response.content.lower()

            except Exception as e:
                self.logger.warning("LLM verification failed, using heuristic result", error=str(e))

        return {
            "verification_passed": verification_passed,
            "current_phase": ExecutionPhase.COMPLETE.value if verification_passed else ExecutionPhase.FAILED.value
        }

    async def _complete(self, state: AgentState) -> Dict[str, Any]:
        """Complete the execution successfully."""
        success = state.get("verification_passed", False)

        self.logger.user_success("Task completed" if success else "Task completed with issues")
        self.logger.debug("Agent: Completion", success=success)

        # Prepare final response
        result = state.get("current_result", "")
        final_response = str(result) if result else "Task completed"

        return {
            "final_response": final_response,
            "execution_complete": True,
            "execution_success": success,
            "current_phase": ExecutionPhase.COMPLETE.value
        }

    async def _handle_failure(self, state: AgentState) -> Dict[str, Any]:
        """Handle execution failure."""
        self.logger.user_error("Task failed, analyzing issue...")
        self.logger.error("Agent: Handling failure")

        # Prepare failure response
        errors = []
        for action in state.get("completed_actions", []):
            if action.get("error"):
                errors.append(f"{action['tool']}: {action['error']}")

        failure_summary = f"Execution failed. Errors: {'; '.join(errors)}" if errors else "Execution failed"

        return {
            "final_response": failure_summary,
            "execution_complete": True,
            "execution_success": False,
            "current_phase": ExecutionPhase.FAILED.value
        }

    # Conditional routing methods
    def _after_reflect(self, state: AgentState) -> str:
        """Determine next step after reflection."""
        if state.get("adaptation_needed") and state["attempt_number"] >= self.max_attempts:
            return "failed"
        return "plan"

    def _after_act(self, state: AgentState) -> str:
        """Determine next step after action."""
        if state.get("current_result"):
            return "verify"
        elif state["attempt_number"] < self.max_attempts:
            return "reflect"
        else:
            return "failed"

    def _after_verify(self, state: AgentState) -> str:
        """Determine next step after verification."""
        if state.get("verification_passed"):
            return "complete"
        elif state["attempt_number"] < self.max_attempts:
            return "reflect"
        else:
            return "failed"

    # Tool and resource management (same as before)
    def add_tools(self, tools: List[BaseTool]) -> None:
        """Add tools and update registry."""
        new_tools = []
        existing = {t.name for t in self.tools}
        for tool in tools:
            if tool.name not in existing:
                new_tools.append(tool)
                self.tools.append(tool)
                self.tool_registry.register_tool_instance(tool)

        if new_tools:
            self.logger.info("Agent tools added", new_tools=len(new_tools))

    def adopt_flow_tools(self, flow, names: List[str] = None) -> "Agent":
        """Adopt tools from flow registry."""
        self._flow_ref = flow

        if names:
            tools_to_add = []
            for name in names:
                try:
                    tool = flow.tool_registry.get_tool(name)
                    tools_to_add.append(tool)
                except Exception as e:
                    self.logger.warning(f"Could not adopt tool {name}: {e}")

            if tools_to_add:
                self.add_tools(tools_to_add)
                self.logger.info("Agent adopted flow tools", adopted_count=len(tools_to_add))

        return self

    def list_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]

    # Main execution methods
    async def arun(
        self,
        message: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Run the agent asynchronously."""
        self.logger.user_progress(f"Starting task: {message[:50]}...")
        self.logger.info("Agent starting", request_preview=message[:100])

        config = {"configurable": {"thread_id": thread_id or "default"}}

        try:
            # Register agent in thread-local storage to avoid serialization
            thread_id_actual = thread_id or "default"
            try:
                from agenticflow.agent.strategies.enhanced_rpavh_agent import set_agent_for_thread
                set_agent_for_thread(thread_id_actual, self)
            except ImportError:
                pass  # Enhanced RPAVH not available, continue without agent reference
            
            # Initialize state - only include serializable data
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "original_request": message,
                "thread_id": thread_id_actual,
                "tools_available": [tool.name for tool in self.tools],  # Only tool names, not objects
                "static_resources": getattr(self, 'static_resources', {}),
                "agent_name": self.name
            }
            
            # Agent state initialized successfully

            # Execute the graph
            final_state = None
            async for chunk in self.compiled_graph.astream(initial_state, config=config):
                # Track the final state
                final_state = chunk

            # Extract results - handle both standard and enhanced graph nodes
            if final_state and "complete" in final_state:
                result = final_state["complete"]
                return {
                    "agent_name": self.name,
                    "message": result.get("final_response", ""),
                    "success": result.get("execution_success", False),
                    "actions_completed": len(result.get("completed_actions", [])),
                    "metadata": result.get("metadata", {}),
                    "data": result.get("handoff_data", {})
                }
            elif final_state and "handoff" in final_state:  # Enhanced graph completion
                result = final_state["handoff"]
                return {
                    "agent_name": self.name,
                    "message": result.get("final_response", "Enhanced task completed"),
                    "success": result.get("execution_success", False),
                    "metadata": {"execution_complete": result.get("execution_complete", False)},
                    "data": result.get("handoff_data", {})
                }
            elif final_state and "handle_failure" in final_state:
                result = final_state["handle_failure"]
                return {
                    "agent_name": self.name,
                    "message": result.get("final_response", "Task failed"),
                    "success": False,
                    "error": "Execution failed"
                }
            else:
                return {
                    "agent_name": self.name,
                    "message": "Task completed",
                    "success": True
                }

        except Exception as e:
            self.logger.user_error(f"Agent execution failed: {str(e)}")
            self.logger.error("Agent execution failed", error=str(e))
            return {
                "agent_name": self.name,
                "message": f"Agent execution failed: {str(e)}",
                "success": False,
                "error": str(e)
            }
        finally:
            # Cleanup thread-local agent reference
            try:
                from agenticflow.agent.strategies.enhanced_rpavh_agent import clear_agent_for_thread
                clear_agent_for_thread(thread_id_actual)
            except ImportError:
                pass  # Enhanced RPAVH not available

    def run(self, message: str, thread_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Synchronous wrapper for arun."""
        return asyncio.run(self.arun(message, thread_id, **kwargs))

    # State management
    def get_state(self, thread_id: str = "default") -> Dict[str, Any]:
        """Get the current state of the agent conversation."""
        config = {"configurable": {"thread_id": thread_id}}
        return self.compiled_graph.get_state(config)

    def update_state(
        self,
        values: Dict[str, Any],
        thread_id: str = "default",
        as_node: Optional[str] = None
    ) -> None:
        """Update the agent's state."""
        config = {"configurable": {"thread_id": thread_id}}
        self.compiled_graph.update_state(config, values, as_node)

    # Properties for compatibility
    @property
    def description(self) -> str:
        """Get agent description."""
        return self.config.description or f"Agent with {len(self.tools)} tools"