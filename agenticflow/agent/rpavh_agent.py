"""
Reflect-Plan-Act-Verify-Handoff (RPAVH) Agent Implementation

A sophisticated LangGraph-based agent that replaces the basic React pattern with:
- Self-reflection and error analysis
- Strategic planning with failure recovery
- Deliberate action execution with retry logic  
- Result verification and quality checks
- Intelligent task handoff coordination
- Persistent memory and learning from failures
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, TypedDict, Annotated, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from operator import add

from agenticflow.core.config import AgentConfig
from agenticflow.core.models import get_chat_model
from agenticflow.registry.tool_registry import ToolRegistry
from agenticflow.core.event_bus import EventEmitter, EventType, Event, get_event_bus
import structlog

logger = structlog.get_logger()


class ExecutionPhase(Enum):
    """Phases in the RPAVH execution cycle."""
    REFLECT = "reflect"
    PLAN = "plan"  
    ACT = "act"
    VERIFY = "verify"
    HANDOFF = "handoff"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class MemoryEntry:
    """Represents a memory entry for learning and context."""
    timestamp: float
    phase: ExecutionPhase
    content: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttemptRecord:
    """Records an execution attempt for failure analysis."""
    attempt_number: int
    timestamp: float
    phase: ExecutionPhase
    action_taken: str
    tool_used: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


class RPAVHState(TypedDict):
    """State for the RPAVH agent execution."""
    # Input and Context
    messages: Annotated[List[BaseMessage], add]
    original_request: str
    thread_id: Optional[str]
    
    # Execution State
    current_phase: str  # ExecutionPhase value
    attempt_number: int
    max_attempts: int
    
    # Memory and Learning
    memory: List[Dict[str, Any]]  # Serialized MemoryEntry objects
    attempt_history: List[Dict[str, Any]]  # Serialized AttemptRecord objects
    
    # Planning and Reflection
    current_plan: Optional[Dict[str, Any]]
    reflection_notes: List[str]
    identified_issues: List[str]
    
    # Action and Results
    pending_actions: List[Dict[str, Any]]
    completed_actions: List[Dict[str, Any]]
    current_result: Optional[Any]
    verification_passed: bool
    
    # Handoff and Coordination  
    requires_handoff: bool
    handoff_target: Optional[str]
    handoff_context: Optional[Dict[str, Any]]
    
    # Final State
    final_response: Optional[str]
    execution_complete: bool
    execution_success: bool


class RPAVHAgent:
    """
    Reflect-Plan-Act-Verify-Handoff Agent with sophisticated self-correction.
    
    This agent implements a five-phase execution cycle:
    1. REFLECT: Analyze current situation and past failures
    2. PLAN: Create strategic action plan with fallbacks  
    3. ACT: Execute planned actions with retry logic
    4. VERIFY: Validate results and check quality
    5. HANDOFF: Coordinate with other agents when needed
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tools: Optional[List[BaseTool]] = None,
        model: Optional[BaseChatModel] = None,
        checkpointer: Optional[Any] = None,
        static_resources: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3,
        reflection_enabled: bool = True,
        verification_enabled: bool = True,
        handoff_enabled: bool = True,
        # Convenience parameters
        name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        # Build config if needed
        if config is None:
            cfg_name = name or "rpavh_agent"
            cfg_model = model_name or "llama3.2:latest"
            cfg_temp = temperature if temperature is not None else 0.1
            config = AgentConfig(name=cfg_name, model=cfg_model, temperature=cfg_temp)
        
        self.config = config
        self.name = config.name
        
        # Core components
        self.tools: List[BaseTool] = list(tools or [])
        self.model = model or get_chat_model(model_name=config.model, temperature=config.temperature)
        self.checkpointer = checkpointer or MemorySaver()
        self.static_resources: Dict[str, Any] = dict(static_resources or {})
        
        # RPAVH Configuration
        self.max_attempts = max_attempts
        self.reflection_enabled = reflection_enabled
        self.verification_enabled = verification_enabled
        self.handoff_enabled = handoff_enabled
        
        # Tool Registry and Flow Reference
        self.tool_registry = ToolRegistry()
        self._flow_ref: Optional[Any] = None
        
        # Register tools in registry
        for tool in self.tools:
            self.tool_registry.register_tool_instance(tool)
        
        # Event Bus Integration
        self.event_bus = get_event_bus()
        self._event_emitter = EventEmitter(self.event_bus)
        
        # Build the RPAVH graph
        self.graph = self._build_rpavh_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
        
        # Coordination callbacks (set by orchestrator)
        self.handoff_callback: Optional[Callable] = None
        self.agent_registry_callback: Optional[Callable] = None
        
        logger.info("RPAVH Agent initialized", name=self.name, tools=len(self.tools), 
                   max_attempts=self.max_attempts)
    
    def _build_rpavh_graph(self) -> StateGraph:
        """Build the sophisticated RPAVH state graph."""
        graph = StateGraph(RPAVHState)
        
        # Core RPAVH phases
        graph.add_node("initialize", self._initialize)
        graph.add_node("reflect", self._reflect)
        graph.add_node("plan", self._plan)
        graph.add_node("act", self._act)
        graph.add_node("verify", self._verify)
        graph.add_node("handoff", self._handoff)
        graph.add_node("complete", self._complete)
        graph.add_node("handle_failure", self._handle_failure)
        
        # Entry point
        graph.add_edge(START, "initialize")
        
        # Main execution flow
        graph.add_edge("initialize", "reflect")
        
        # Conditional transitions from reflect
        graph.add_conditional_edges(
            "reflect",
            self._after_reflect,
            {
                "plan": "plan",
                "retry_previous": "act",  # Skip planning if retrying
                "handoff": "handoff",
                "complete": "complete"
            }
        )
        
        # Plan to Act
        graph.add_edge("plan", "act")
        
        # Conditional transitions from act
        graph.add_conditional_edges(
            "act", 
            self._after_act,
            {
                "verify": "verify",
                "reflect": "reflect",  # Back to reflection on failure
                "handoff": "handoff",
                "complete": "complete",
                "failed": "handle_failure"
            }
        )
        
        # Conditional transitions from verify
        graph.add_conditional_edges(
            "verify",
            self._after_verify, 
            {
                "complete": "complete",
                "reflect": "reflect",  # Re-reflect if verification failed
                "handoff": "handoff",
                "failed": "handle_failure"
            }
        )
        
        # Handoff outcomes
        graph.add_conditional_edges(
            "handoff",
            self._after_handoff,
            {
                "complete": "complete",
                "reflect": "reflect",  # Continue processing after handoff
                "failed": "handle_failure"
            }
        )
        
        # Terminal states
        graph.add_edge("complete", END)
        graph.add_edge("handle_failure", END)
        
        return graph
    
    async def _initialize(self, state: RPAVHState) -> Dict[str, Any]:
        """Initialize the execution state and load context."""
        logger.info("RPAVH: Initializing", agent=self.name, request_preview=state["original_request"][:100])
        
        # Setup initial state
        updates = {
            "current_phase": ExecutionPhase.REFLECT.value,
            "attempt_number": 1,
            "max_attempts": self.max_attempts,
            "memory": [],
            "attempt_history": [],
            "reflection_notes": [],
            "identified_issues": [],
            "pending_actions": [],
            "completed_actions": [],
            "verification_passed": False,
            "requires_handoff": False,
            "execution_complete": False,
            "execution_success": False
        }
        
        # Add initialization to memory
        memory_entry = MemoryEntry(
            timestamp=time.time(),
            phase=ExecutionPhase.REFLECT,
            content=f"Initialized RPAVH execution for: {state['original_request'][:200]}",
            success=True,
            metadata={"tools_available": len(self.tools), "resources": list(self.static_resources.keys())}
        )
        
        updates["memory"] = [self._serialize_memory(memory_entry)]
        
        # Emit initialization event
        self._emit_phase_event(ExecutionPhase.REFLECT, "initialized", {
            "request": state["original_request"],
            "tools_count": len(self.tools)
        })
        
        return updates
    
    async def _reflect(self, state: RPAVHState) -> Dict[str, Any]:
        """Reflect on current situation, past failures, and available resources."""
        logger.info("RPAVH: Reflection phase", agent=self.name, attempt=state["attempt_number"])
        
        attempt_start = time.time()
        
        # Build reflection context
        reflection_context = self._build_reflection_context(state)
        
        reflection_prompt = f"""
🔍 REFLECTION PHASE - Analyze Current Situation

CURRENT REQUEST: {state['original_request']}

CONTEXT:
- Attempt: {state['attempt_number']}/{state['max_attempts']}
- Phase: {state['current_phase']}
- Previous attempts: {len(state.get('attempt_history', []))}

{reflection_context}

AVAILABLE TOOLS: {[tool.name for tool in self.tools]}
STATIC RESOURCES: {list(self.static_resources.keys())}

REFLECTION TASKS:
1. Analyze the request and identify what needs to be accomplished
2. Review any past failures and learn from them  
3. Identify potential issues or challenges
4. Assess available tools and resources
5. Determine if this task requires handoff to another agent

Provide your reflection in JSON format:
{{
    "understanding": "Clear description of what needs to be done",
    "past_issues": ["List of issues from previous attempts"],
    "potential_challenges": ["Anticipated challenges or risks"], 
    "resource_assessment": "Assessment of available tools/resources",
    "handoff_needed": false,
    "handoff_reason": "Why handoff is needed (if applicable)",
    "confidence_level": "high/medium/low",
    "reflection_notes": ["Key insights from this reflection"]
}}
"""

        try:
            response = await self.model.ainvoke([HumanMessage(content=reflection_prompt)])
            reflection_data = self._parse_json_response(response.content)
            
            # Update state with reflection results
            updates = {
                "reflection_notes": reflection_data.get("reflection_notes", []),
                "identified_issues": reflection_data.get("potential_challenges", []),
                "requires_handoff": reflection_data.get("handoff_needed", False),
                "current_phase": ExecutionPhase.PLAN.value
            }
            
            if reflection_data.get("handoff_needed"):
                updates["handoff_context"] = {
                    "reason": reflection_data.get("handoff_reason", ""),
                    "understanding": reflection_data.get("understanding", ""),
                    "challenges": reflection_data.get("potential_challenges", [])
                }
            
            # Record reflection in memory
            memory_entry = MemoryEntry(
                timestamp=time.time(),
                phase=ExecutionPhase.REFLECT,
                content=f"Reflection: {reflection_data.get('understanding', '')}",
                success=True,
                metadata={
                    "confidence": reflection_data.get("confidence_level", "medium"),
                    "issues_identified": len(reflection_data.get("potential_challenges", [])),
                    "handoff_needed": reflection_data.get("handoff_needed", False)
                }
            )
            updates["memory"] = state.get("memory", []) + [self._serialize_memory(memory_entry)]
            
            # Record attempt
            attempt = AttemptRecord(
                attempt_number=state["attempt_number"],
                timestamp=attempt_start,
                phase=ExecutionPhase.REFLECT,
                action_taken="reflection_analysis",
                result=reflection_data,
                duration_seconds=time.time() - attempt_start
            )
            updates["attempt_history"] = state.get("attempt_history", []) + [self._serialize_attempt(attempt)]
            
            self._emit_phase_event(ExecutionPhase.REFLECT, "completed", {
                "confidence": reflection_data.get("confidence_level"),
                "issues_count": len(reflection_data.get("potential_challenges", [])),
                "handoff_needed": reflection_data.get("handoff_needed", False)
            })
            
            return updates
            
        except Exception as e:
            logger.error("RPAVH: Reflection failed", agent=self.name, error=str(e))
            
            # Record failure
            attempt = AttemptRecord(
                attempt_number=state["attempt_number"],
                timestamp=attempt_start,
                phase=ExecutionPhase.REFLECT,
                action_taken="reflection_analysis",
                error=str(e),
                duration_seconds=time.time() - attempt_start
            )
            
            return {
                "attempt_history": state.get("attempt_history", []) + [self._serialize_attempt(attempt)],
                "identified_issues": state.get("identified_issues", []) + [f"Reflection failure: {str(e)}"],
                "current_phase": ExecutionPhase.PLAN.value  # Continue to planning despite reflection failure
            }
    
    async def _plan(self, state: RPAVHState) -> Dict[str, Any]:
        """Create a strategic action plan with fallback options."""
        logger.info("RPAVH: Planning phase", agent=self.name, attempt=state["attempt_number"])
        
        attempt_start = time.time()
        
        planning_prompt = f"""
📋 PLANNING PHASE - Create Action Strategy

CURRENT REQUEST: {state['original_request']}

REFLECTION INSIGHTS:
- Notes: {state.get('reflection_notes', [])}
- Identified Issues: {state.get('identified_issues', [])}
- Attempt: {state['attempt_number']}/{state['max_attempts']}

AVAILABLE TOOLS: {[tool.name for tool in self.tools]}
STATIC RESOURCES: {list(self.static_resources.keys())}

PLANNING REQUIREMENTS:
1. Break down the request into specific, actionable steps
2. Choose appropriate tools for each step
3. Plan fallback strategies for likely failure points
4. Consider order dependencies between actions
5. Plan verification steps to check results

Provide your plan in JSON format:
{{
    "strategy": "Overall approach description",
    "primary_actions": [
        {{
            "step": 1,
            "action": "Description of action",
            "tool": "tool_name",
            "parameters": {{"param": "value"}},
            "expected_outcome": "What this should achieve",
            "fallback_strategy": "What to do if this fails"
        }}
    ],
    "verification_plan": "How to verify successful completion",
    "success_criteria": ["List of criteria that indicate success"],
    "risk_mitigation": ["Strategies to handle potential issues"]
}}
"""

        try:
            response = await self.model.ainvoke([HumanMessage(content=planning_prompt)])
            plan_data = self._parse_json_response(response.content)
            
            # Create structured plan
            structured_plan = {
                "strategy": plan_data.get("strategy", ""),
                "actions": plan_data.get("primary_actions", []),
                "verification": plan_data.get("verification_plan", ""),
                "success_criteria": plan_data.get("success_criteria", []),
                "risks": plan_data.get("risk_mitigation", []),
                "created_at": time.time()
            }
            
            # Convert planned actions to pending actions
            pending_actions = []
            for action in plan_data.get("primary_actions", []):
                pending_actions.append({
                    "id": f"action_{action.get('step', len(pending_actions) + 1)}",
                    "description": action.get("action", ""),
                    "tool": action.get("tool", ""),
                    "parameters": action.get("parameters", {}),
                    "expected_outcome": action.get("expected_outcome", ""),
                    "fallback": action.get("fallback_strategy", ""),
                    "status": "pending"
                })
            
            updates = {
                "current_plan": structured_plan,
                "pending_actions": pending_actions,
                "current_phase": ExecutionPhase.ACT.value
            }
            
            # Record planning in memory
            memory_entry = MemoryEntry(
                timestamp=time.time(),
                phase=ExecutionPhase.PLAN,
                content=f"Strategy: {plan_data.get('strategy', '')}",
                success=True,
                metadata={
                    "actions_count": len(pending_actions),
                    "risks_identified": len(plan_data.get("risk_mitigation", [])),
                    "has_verification": bool(plan_data.get("verification_plan"))
                }
            )
            updates["memory"] = state.get("memory", []) + [self._serialize_memory(memory_entry)]
            
            # Record attempt
            attempt = AttemptRecord(
                attempt_number=state["attempt_number"],
                timestamp=attempt_start,
                phase=ExecutionPhase.PLAN,
                action_taken="strategic_planning",
                result=structured_plan,
                duration_seconds=time.time() - attempt_start
            )
            updates["attempt_history"] = state.get("attempt_history", []) + [self._serialize_attempt(attempt)]
            
            self._emit_phase_event(ExecutionPhase.PLAN, "completed", {
                "actions_planned": len(pending_actions),
                "has_fallbacks": any("fallback" in action for action in pending_actions),
                "strategy": plan_data.get("strategy", "")[:100]
            })
            
            return updates
            
        except Exception as e:
            logger.error("RPAVH: Planning failed", agent=self.name, error=str(e))
            
            # Create minimal fallback plan
            fallback_actions = [{
                "id": "fallback_action",
                "description": f"Execute request: {state['original_request']}",
                "tool": self.tools[0].name if self.tools else "manual",
                "parameters": {},
                "expected_outcome": "Complete the requested task",
                "fallback": "Manual completion or error handling",
                "status": "pending"
            }]
            
            return {
                "current_plan": {"strategy": "Fallback execution", "actions": fallback_actions, "created_at": time.time()},
                "pending_actions": fallback_actions,
                "current_phase": ExecutionPhase.ACT.value,
                "identified_issues": state.get("identified_issues", []) + [f"Planning failure: {str(e)}"]
            }
    
    async def _act(self, state: RPAVHState) -> Dict[str, Any]:
        """Execute planned actions with retry logic and error handling."""
        logger.info("RPAVH: Action phase", agent=self.name, 
                   pending_actions=len(state.get("pending_actions", [])))
        
        attempt_start = time.time()
        pending_actions = list(state.get("pending_actions", []))
        completed_actions = list(state.get("completed_actions", []))
        current_result = None
        execution_errors = []
        
        # Execute each pending action
        for action in pending_actions:
            if action.get("status") == "completed":
                continue
                
            action_start = time.time()
            logger.info("RPAVH: Executing action", action_id=action.get("id"), 
                       tool=action.get("tool"))
            
            try:
                # Find and execute tool
                tool_name = action.get("tool", "")
                tool_params = action.get("parameters", {})
                
                # Execute tool if available
                if tool_name and tool_name in [t.name for t in self.tools]:
                    tool = next(t for t in self.tools if t.name == tool_name)
                    
                    # Convert parameters if needed
                    if isinstance(tool_params, dict):
                        result = await tool.arun(**tool_params)
                    else:
                        result = await tool.arun(tool_params)
                    
                    action["result"] = result
                    action["status"] = "completed"
                    action["execution_time"] = time.time() - action_start
                    current_result = result
                    
                    # Record successful action
                    attempt = AttemptRecord(
                        attempt_number=state["attempt_number"],
                        timestamp=action_start,
                        phase=ExecutionPhase.ACT,
                        action_taken=action.get("description", ""),
                        tool_used=tool_name,
                        result=result,
                        duration_seconds=time.time() - action_start
                    )
                    
                    completed_actions.append(action)
                    
                    self._emit_phase_event(ExecutionPhase.ACT, "action_completed", {
                        "action_id": action.get("id"),
                        "tool_used": tool_name,
                        "success": True
                    })
                    
                else:
                    # Tool not available - try LLM reasoning
                    reasoning_prompt = f"""
Execute this action using reasoning and available context:

ACTION: {action.get('description', '')}
EXPECTED OUTCOME: {action.get('expected_outcome', '')}
AVAILABLE TOOLS: {[t.name for t in self.tools]}
CONTEXT: {state['original_request']}

If you cannot execute this directly, provide a reasoned response or recommendation.
"""
                    
                    response = await self.model.ainvoke([HumanMessage(content=reasoning_prompt)])
                    result = {"message": response.content, "type": "reasoning"}
                    
                    action["result"] = result
                    action["status"] = "completed_reasoning"
                    action["execution_time"] = time.time() - action_start
                    current_result = result
                    
                    completed_actions.append(action)
                    
            except Exception as e:
                error_msg = str(e)
                logger.error("RPAVH: Action failed", action_id=action.get("id"), error=error_msg)
                
                execution_errors.append(f"Action {action.get('id')} failed: {error_msg}")
                
                # Try fallback strategy
                fallback = action.get("fallback", "")
                if fallback:
                    try:
                        # Execute fallback (simplified reasoning)
                        fallback_prompt = f"""
Primary action failed: {error_msg}
Fallback strategy: {fallback}
Original request: {state['original_request']}

Execute the fallback approach:
"""
                        response = await self.model.ainvoke([HumanMessage(content=fallback_prompt)])
                        fallback_result = {"message": response.content, "type": "fallback", "original_error": error_msg}
                        
                        action["result"] = fallback_result
                        action["status"] = "completed_fallback"
                        action["error"] = error_msg
                        action["execution_time"] = time.time() - action_start
                        current_result = fallback_result
                        
                        completed_actions.append(action)
                        
                        self._emit_phase_event(ExecutionPhase.ACT, "fallback_executed", {
                            "action_id": action.get("id"),
                            "original_error": error_msg,
                            "fallback_used": True
                        })
                        
                    except Exception as fallback_error:
                        action["status"] = "failed"
                        action["error"] = f"Primary: {error_msg}, Fallback: {str(fallback_error)}"
                        execution_errors.append(f"Action {action.get('id')} and fallback both failed")
                else:
                    action["status"] = "failed"
                    action["error"] = error_msg
        
        # Update state
        updates = {
            "completed_actions": completed_actions,
            "pending_actions": [a for a in pending_actions if a.get("status") not in ["completed", "completed_reasoning", "completed_fallback"]],
            "current_result": current_result
        }
        
        # Determine next phase
        if execution_errors and len(execution_errors) == len(pending_actions):
            # All actions failed
            updates["current_phase"] = ExecutionPhase.REFLECT.value
            updates["identified_issues"] = state.get("identified_issues", []) + execution_errors
        elif self.verification_enabled and current_result:
            # Proceed to verification
            updates["current_phase"] = ExecutionPhase.VERIFY.value
        else:
            # Skip verification, check for completion
            updates["current_phase"] = ExecutionPhase.COMPLETE.value
        
        # Record action phase in memory
        memory_entry = MemoryEntry(
            timestamp=time.time(),
            phase=ExecutionPhase.ACT,
            content=f"Executed {len(completed_actions)} actions",
            success=len(execution_errors) == 0,
            error="; ".join(execution_errors) if execution_errors else None,
            metadata={
                "actions_completed": len(completed_actions),
                "actions_failed": len(execution_errors),
                "has_result": current_result is not None
            }
        )
        updates["memory"] = state.get("memory", []) + [self._serialize_memory(memory_entry)]
        
        return updates
    
    async def _verify(self, state: RPAVHState) -> Dict[str, Any]:
        """Verify results and check quality against success criteria."""
        logger.info("RPAVH: Verification phase", agent=self.name)
        
        attempt_start = time.time()
        current_result = state.get("current_result")
        current_plan = state.get("current_plan", {})
        success_criteria = current_plan.get("success_criteria", [])
        
        verification_prompt = f"""
🔍 VERIFICATION PHASE - Quality Check

ORIGINAL REQUEST: {state['original_request']}
EXECUTION RESULT: {current_result}

SUCCESS CRITERIA: {success_criteria}
COMPLETED ACTIONS: {len(state.get('completed_actions', []))}

VERIFICATION TASKS:
1. Check if the result addresses the original request
2. Verify against defined success criteria  
3. Assess quality and completeness
4. Identify any missing elements or issues
5. Determine if additional work is needed

Provide verification assessment in JSON format:
{{
    "verification_passed": true/false,
    "quality_score": 0.0-1.0,
    "criteria_met": ["List of criteria satisfied"],
    "criteria_failed": ["List of criteria not met"],
    "issues_found": ["Any problems or deficiencies"],
    "completeness_assessment": "Assessment of how complete the solution is",
    "recommendation": "continue/retry/handoff/complete"
}}
"""

        try:
            response = await self.model.ainvoke([HumanMessage(content=verification_prompt)])
            verification_data = self._parse_json_response(response.content)
            
            verification_passed = verification_data.get("verification_passed", False)
            quality_score = float(verification_data.get("quality_score", 0.5))
            recommendation = verification_data.get("recommendation", "complete")
            
            updates = {
                "verification_passed": verification_passed,
                "current_phase": ExecutionPhase.COMPLETE.value if verification_passed else ExecutionPhase.REFLECT.value
            }
            
            # Handle verification recommendation
            if recommendation == "handoff" and self.handoff_enabled:
                updates["current_phase"] = ExecutionPhase.HANDOFF.value
                updates["requires_handoff"] = True
                updates["handoff_context"] = {
                    "reason": "Verification suggests handoff needed",
                    "issues": verification_data.get("issues_found", []),
                    "current_result": current_result,
                    "quality_score": quality_score
                }
            elif recommendation == "retry" and state["attempt_number"] < state["max_attempts"]:
                updates["current_phase"] = ExecutionPhase.REFLECT.value
                updates["attempt_number"] = state["attempt_number"] + 1
                updates["identified_issues"] = state.get("identified_issues", []) + verification_data.get("issues_found", [])
            
            # Record verification in memory
            memory_entry = MemoryEntry(
                timestamp=time.time(),
                phase=ExecutionPhase.VERIFY,
                content=f"Verification: {verification_data.get('completeness_assessment', '')}",
                success=verification_passed,
                metadata={
                    "quality_score": quality_score,
                    "criteria_met": len(verification_data.get("criteria_met", [])),
                    "criteria_failed": len(verification_data.get("criteria_failed", [])),
                    "recommendation": recommendation
                }
            )
            updates["memory"] = state.get("memory", []) + [self._serialize_memory(memory_entry)]
            
            # Record attempt
            attempt = AttemptRecord(
                attempt_number=state["attempt_number"],
                timestamp=attempt_start,
                phase=ExecutionPhase.VERIFY,
                action_taken="result_verification",
                result=verification_data,
                duration_seconds=time.time() - attempt_start
            )
            updates["attempt_history"] = state.get("attempt_history", []) + [self._serialize_attempt(attempt)]
            
            self._emit_phase_event(ExecutionPhase.VERIFY, "completed", {
                "verification_passed": verification_passed,
                "quality_score": quality_score,
                "recommendation": recommendation
            })
            
            return updates
            
        except Exception as e:
            logger.error("RPAVH: Verification failed", agent=self.name, error=str(e))
            
            # Default to completion on verification failure
            return {
                "verification_passed": True,  # Assume success if we can't verify
                "current_phase": ExecutionPhase.COMPLETE.value,
                "identified_issues": state.get("identified_issues", []) + [f"Verification failed: {str(e)}"]
            }
    
    async def _handoff(self, state: RPAVHState) -> Dict[str, Any]:
        """Coordinate handoff to another agent when needed."""
        logger.info("RPAVH: Handoff phase", agent=self.name)
        
        if not self.handoff_enabled or not self.handoff_callback:
            # Skip handoff if not enabled or no callback
            return {
                "current_phase": ExecutionPhase.COMPLETE.value,
                "requires_handoff": False
            }
        
        try:
            handoff_context = state.get("handoff_context", {})
            
            # Prepare handoff information
            handoff_data = {
                "original_request": state["original_request"],
                "current_result": state.get("current_result"),
                "context": handoff_context,
                "completed_actions": state.get("completed_actions", []),
                "issues": state.get("identified_issues", []),
                "source_agent": self.name,
                "handoff_reason": handoff_context.get("reason", "Agent coordination needed")
            }
            
            # Execute handoff callback
            handoff_result = await self.handoff_callback(handoff_data)
            
            # Process handoff result
            if handoff_result.get("accepted", False):
                # Handoff was successful
                updates = {
                    "current_phase": ExecutionPhase.COMPLETE.value,
                    "final_response": f"Task handed off to {handoff_result.get('target_agent', 'another agent')}. {handoff_result.get('message', '')}",
                    "execution_success": True,
                    "execution_complete": True
                }
                
                self._emit_phase_event(ExecutionPhase.HANDOFF, "completed", {
                    "target_agent": handoff_result.get("target_agent"),
                    "handoff_successful": True
                })
                
            else:
                # Handoff failed, continue processing
                updates = {
                    "current_phase": ExecutionPhase.COMPLETE.value,
                    "requires_handoff": False,
                    "identified_issues": state.get("identified_issues", []) + ["Handoff attempt failed"]
                }
                
                self._emit_phase_event(ExecutionPhase.HANDOFF, "failed", {
                    "reason": handoff_result.get("reason", "Handoff not accepted")
                })
            
            # Record handoff in memory
            memory_entry = MemoryEntry(
                timestamp=time.time(),
                phase=ExecutionPhase.HANDOFF,
                content=f"Handoff attempt: {handoff_result.get('message', '')}",
                success=handoff_result.get("accepted", False),
                metadata=handoff_result
            )
            updates["memory"] = state.get("memory", []) + [self._serialize_memory(memory_entry)]
            
            return updates
            
        except Exception as e:
            logger.error("RPAVH: Handoff failed", agent=self.name, error=str(e))
            
            return {
                "current_phase": ExecutionPhase.COMPLETE.value,
                "requires_handoff": False,
                "identified_issues": state.get("identified_issues", []) + [f"Handoff error: {str(e)}"]
            }
    
    async def _complete(self, state: RPAVHState) -> Dict[str, Any]:
        """Finalize execution and prepare response."""
        logger.info("RPAVH: Completion phase", agent=self.name, 
                   success=state.get("verification_passed", False))
        
        # Build final response
        current_result = state.get("current_result")
        completed_actions = state.get("completed_actions", [])
        
        if current_result:
            if isinstance(current_result, dict):
                final_response = current_result.get("message", str(current_result))
            else:
                final_response = str(current_result)
        elif completed_actions:
            # Summarize completed actions
            action_summary = []
            for action in completed_actions:
                result_summary = ""
                if action.get("result"):
                    if isinstance(action["result"], dict):
                        result_summary = action["result"].get("message", "")[:100]
                    else:
                        result_summary = str(action["result"])[:100]
                action_summary.append(f"- {action.get('description', 'Action')}: {result_summary}")
            
            final_response = f"Completed {len(completed_actions)} actions:\n" + "\n".join(action_summary)
        else:
            final_response = f"Processing completed for: {state['original_request']}"
        
        # Determine execution success
        execution_success = (
            state.get("verification_passed", True) and
            len(state.get("completed_actions", [])) > 0 and
            not any("failed" in action.get("status", "") for action in completed_actions)
        )
        
        updates = {
            "final_response": final_response,
            "execution_complete": True,
            "execution_success": execution_success,
            "current_phase": ExecutionPhase.COMPLETE.value
        }
        
        # Record completion in memory
        memory_entry = MemoryEntry(
            timestamp=time.time(),
            phase=ExecutionPhase.COMPLETE,
            content=f"Execution completed: {final_response[:200]}",
            success=execution_success,
            metadata={
                "total_attempts": state["attempt_number"],
                "actions_completed": len(completed_actions),
                "verification_passed": state.get("verification_passed", False)
            }
        )
        updates["memory"] = state.get("memory", []) + [self._serialize_memory(memory_entry)]
        
        self._emit_phase_event(ExecutionPhase.COMPLETE, "finished", {
            "execution_success": execution_success,
            "total_attempts": state["attempt_number"],
            "actions_completed": len(completed_actions)
        })
        
        return updates
    
    async def _handle_failure(self, state: RPAVHState) -> Dict[str, Any]:
        """Handle terminal failures and cleanup."""
        logger.error("RPAVH: Handling terminal failure", agent=self.name, 
                    attempts=state["attempt_number"])
        
        failure_summary = []
        for issue in state.get("identified_issues", []):
            failure_summary.append(f"- {issue}")
        
        failure_message = f"Task failed after {state['attempt_number']} attempts.\n"
        if failure_summary:
            failure_message += "Issues encountered:\n" + "\n".join(failure_summary)
        
        updates = {
            "final_response": failure_message,
            "execution_complete": True,
            "execution_success": False,
            "current_phase": ExecutionPhase.FAILED.value
        }
        
        # Record failure in memory
        memory_entry = MemoryEntry(
            timestamp=time.time(),
            phase=ExecutionPhase.FAILED,
            content=failure_message,
            success=False,
            metadata={
                "total_attempts": state["attempt_number"],
                "issues_count": len(state.get("identified_issues", []))
            }
        )
        updates["memory"] = state.get("memory", []) + [self._serialize_memory(memory_entry)]
        
        self._emit_phase_event(ExecutionPhase.FAILED, "terminal_failure", {
            "total_attempts": state["attempt_number"],
            "issues_count": len(state.get("identified_issues", []))
        })
        
        return updates
    
    # Phase transition logic
    def _after_reflect(self, state: RPAVHState) -> str:
        """Determine next phase after reflection."""
        if state.get("requires_handoff") and self.handoff_enabled:
            return "handoff"
        
        # Check if we should retry previous actions or plan new ones
        if state["attempt_number"] > 1 and state.get("pending_actions"):
            return "retry_previous"  # Skip to action phase
        
        return "plan"
    
    def _after_act(self, state: RPAVHState) -> str:
        """Determine next phase after action execution."""
        completed_actions = state.get("completed_actions", [])
        pending_actions = state.get("pending_actions", [])
        
        # Check if all actions failed
        failed_actions = [a for a in completed_actions if "failed" in a.get("status", "")]
        if failed_actions and len(failed_actions) == len(completed_actions):
            if state["attempt_number"] >= state["max_attempts"]:
                return "failed"
            else:
                return "reflect"  # Try again after reflection
        
        # Check if handoff is needed
        if state.get("requires_handoff") and self.handoff_enabled:
            return "handoff"
        
        # Check if verification is enabled and we have results
        if self.verification_enabled and state.get("current_result"):
            return "verify"
        
        # If no verification needed or no results, complete
        return "complete"
    
    def _after_verify(self, state: RPAVHState) -> str:
        """Determine next phase after verification."""
        if not state.get("verification_passed", False):
            if state["attempt_number"] >= state["max_attempts"]:
                return "failed"
            else:
                return "reflect"  # Retry after reflection
        
        if state.get("requires_handoff") and self.handoff_enabled:
            return "handoff"
        
        return "complete"
    
    def _after_handoff(self, state: RPAVHState) -> str:
        """Determine next phase after handoff attempt."""
        # If handoff was successful, we're done
        if state.get("execution_complete"):
            return "complete"
        
        # If handoff failed, continue with our own processing
        if state["attempt_number"] >= state["max_attempts"]:
            return "failed"
        
        return "reflect"
    
    # Utility methods
    def _build_reflection_context(self, state: RPAVHState) -> str:
        """Build context for reflection based on past attempts and memory."""
        context_parts = []
        
        # Add memory insights
        memory = state.get("memory", [])
        if memory:
            context_parts.append("PAST INSIGHTS:")
            for mem_data in memory[-3:]:  # Last 3 memory entries
                mem = self._deserialize_memory(mem_data)
                status = "✅" if mem.success else "❌"
                context_parts.append(f"{status} {mem.phase.value}: {mem.content[:100]}")
        
        # Add attempt history
        attempts = state.get("attempt_history", [])
        if attempts:
            context_parts.append("\\nATTEMPT HISTORY:")
            for attempt_data in attempts[-5:]:  # Last 5 attempts
                attempt = self._deserialize_attempt(attempt_data)
                status = "✅" if not attempt.error else "❌"
                context_parts.append(f"{status} {attempt.phase.value}: {attempt.action_taken}")
                if attempt.error:
                    context_parts.append(f"    Error: {attempt.error}")
        
        return "\\n".join(context_parts) if context_parts else "No previous context available."
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with fallback handling."""
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'```json\\s*({.*?})\\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try parsing the whole content
            return json.loads(content)
        except Exception:
            # Fallback to simple parsing
            return {"error": "Could not parse JSON response", "raw_content": content[:500]}
    
    def _serialize_memory(self, memory: MemoryEntry) -> Dict[str, Any]:
        """Serialize memory entry for state storage."""
        return {
            "timestamp": memory.timestamp,
            "phase": memory.phase.value,
            "content": memory.content,
            "success": memory.success,
            "error": memory.error,
            "metadata": memory.metadata
        }
    
    def _deserialize_memory(self, data: Dict[str, Any]) -> MemoryEntry:
        """Deserialize memory entry from state storage."""
        return MemoryEntry(
            timestamp=data["timestamp"],
            phase=ExecutionPhase(data["phase"]),
            content=data["content"],
            success=data["success"],
            error=data.get("error"),
            metadata=data.get("metadata", {})
        )
    
    def _serialize_attempt(self, attempt: AttemptRecord) -> Dict[str, Any]:
        """Serialize attempt record for state storage."""
        return {
            "attempt_number": attempt.attempt_number,
            "timestamp": attempt.timestamp,
            "phase": attempt.phase.value,
            "action_taken": attempt.action_taken,
            "tool_used": attempt.tool_used,
            "result": attempt.result,
            "error": attempt.error,
            "duration_seconds": attempt.duration_seconds
        }
    
    def _deserialize_attempt(self, data: Dict[str, Any]) -> AttemptRecord:
        """Deserialize attempt record from state storage."""
        return AttemptRecord(
            attempt_number=data["attempt_number"],
            timestamp=data["timestamp"],
            phase=ExecutionPhase(data["phase"]),
            action_taken=data["action_taken"],
            tool_used=data.get("tool_used"),
            result=data.get("result"),
            error=data.get("error"),
            duration_seconds=data.get("duration_seconds", 0.0)
        )
    
    def _emit_phase_event(self, phase: ExecutionPhase, event_type: str, data: Dict[str, Any]):
        """Emit event for phase transitions."""
        try:
            if self._event_emitter:
                event_data = {
                    "agent": self.name,
                    "phase": phase.value,
                    "event_type": event_type,
                    **data
                }
                self._event_emitter.emit("agent.phase", event_data)
        except Exception as e:
            logger.warning("Failed to emit phase event", error=str(e))
    
    # Public interface methods
    async def arun(
        self,
        message: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute the RPAVH cycle for the given message."""
        logger.info("RPAVH Agent starting", agent=self.name, request_preview=message[:100])
        
        initial_state = RPAVHState(
            messages=[HumanMessage(content=message)],
            original_request=message,
            thread_id=thread_id,
            current_phase=ExecutionPhase.REFLECT.value,
            attempt_number=1,
            max_attempts=self.max_attempts,
            memory=[],
            attempt_history=[],
            current_plan=None,
            reflection_notes=[],
            identified_issues=[],
            pending_actions=[],
            completed_actions=[],
            current_result=None,
            verification_passed=False,
            requires_handoff=False,
            handoff_target=None,
            handoff_context=None,
            final_response=None,
            execution_complete=False,
            execution_success=False
        )
        
        config = {"configurable": {"thread_id": thread_id or f"rpavh_{self.name}"}}
        
        try:
            final_state = await self.compiled_graph.ainvoke(initial_state, config=config, **kwargs)
            
            return {
                "message": final_state.get("final_response", "Task completed"),
                "success": final_state.get("execution_success", False),
                "attempts": final_state.get("attempt_number", 1),
                "actions_completed": len(final_state.get("completed_actions", [])),
                "verification_passed": final_state.get("verification_passed", False),
                "metadata": {
                    "phase": final_state.get("current_phase"),
                    "memory_entries": len(final_state.get("memory", [])),
                    "total_attempts": len(final_state.get("attempt_history", []))
                }
            }
            
        except Exception as e:
            logger.error("RPAVH Agent execution failed", agent=self.name, error=str(e))
            return {
                "message": f"Agent execution failed: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    def run(self, message: str, thread_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Synchronous wrapper for arun."""
        return asyncio.run(self.arun(message, thread_id, **kwargs))
    
    # Tool and resource management
    def set_tools(self, tools: List[BaseTool]) -> None:
        """Replace tools and update registry."""
        self.tools = list(tools)
        self.tool_registry = ToolRegistry()
        for tool in self.tools:
            self.tool_registry.register_tool_instance(tool)
        logger.info("RPAVH Agent tools updated", agent=self.name, tool_count=len(tools))
    
    def add_tools(self, tools: List[BaseTool]) -> None:
        """Add tools (deduplicate by name)."""
        existing_names = {t.name for t in self.tools}
        new_tools = [t for t in tools if t.name not in existing_names]
        
        for tool in new_tools:
            self.tools.append(tool)
            self.tool_registry.register_tool_instance(tool)
        
        logger.info("RPAVH Agent tools added", agent=self.name, new_tools=len(new_tools))
    
    def list_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
    
    def set_handoff_callback(self, callback: Callable) -> None:
        """Set callback for handling agent handoffs."""
        self.handoff_callback = callback
        logger.info("RPAVH Agent handoff callback set", agent=self.name)
    
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
                logger.info("RPAVH Agent adopted flow tools", agent=self.name, 
                          adopted_count=len(tools_to_add))