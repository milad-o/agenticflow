"""
Enhanced System-Aware Agent with Memory

This agent understands its place in the AgenticFlow system and includes:
- System hierarchy awareness (reports to orchestrator)
- Enhanced memory with persistent context
- Superior communication and status reporting
- Collaborative task execution with progress updates
- Enhanced brain with reflection and decision-making
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, TypedDict, Union
from enum import Enum

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from agenticflow.core.events.event_bus import EventBus, Event, EventType
from agenticflow.observability.flow_logger import get_flow_logger, LogLevel


class AgentRole(Enum):
    SUBORDINATE = "subordinate"  # Reports to orchestrator
    PEER = "peer"               # Collaborates with other agents
    LEADER = "leader"           # Can delegate to other agents


class SystemContext(BaseModel):
    """Context about the agent's place in the system."""
    agent_id: str
    role: AgentRole
    superior: Optional[str] = None  # orchestrator or parent agent
    peers: List[str] = []
    subordinates: List[str] = []
    current_task_id: Optional[str] = None
    assigned_by: Optional[str] = None
    
    # System capabilities
    event_bus_available: bool = False
    can_delegate: bool = False
    can_request_assistance: bool = True
    must_report_progress: bool = True


class AgentMemory(BaseModel):
    """Enhanced agent memory structure."""
    # Task memory
    current_task: Optional[Dict[str, Any]] = None
    task_history: List[Dict[str, Any]] = []
    
    # Interaction memory
    conversations: List[Dict[str, Any]] = []
    decisions_made: List[Dict[str, Any]] = []
    reflections: List[Dict[str, Any]] = []
    
    # System memory
    system_context: Optional[SystemContext] = None
    collaboration_history: List[Dict[str, Any]] = []
    performance_metrics: Dict[str, float] = {}
    
    # Learning memory
    successful_patterns: List[Dict[str, Any]] = []
    failure_patterns: List[Dict[str, Any]] = []
    improvement_notes: List[str] = []


class EnhancedAgentPhase(Enum):
    INITIALIZE = "initialize"
    UNDERSTAND_TASK = "understand_task"
    PLAN_EXECUTION = "plan_execution"
    REFLECT_ON_CONTEXT = "reflect_on_context"
    EXECUTE_ACTION = "execute_action"
    REPORT_PROGRESS = "report_progress"
    HANDLE_FEEDBACK = "handle_feedback"
    FINALIZE = "finalize"
    COMPLETE = "complete"


class EnhancedAgentState(TypedDict, total=False):
    # Core state
    task_description: str
    task_id: str
    system_context: SystemContext
    memory: AgentMemory
    
    # Execution state
    current_plan: List[Dict[str, Any]]
    execution_progress: float
    current_action: Optional[Dict[str, Any]]
    
    # Communication state
    pending_reports: List[Dict[str, Any]]
    received_feedback: List[Dict[str, Any]]
    collaboration_requests: List[Dict[str, Any]]
    
    # Results
    execution_result: Optional[Dict[str, Any]]
    reflection_notes: str
    lessons_learned: List[str]
    
    # State management
    current_phase: str
    agent_complete: bool


class EnhancedSystemAwareAgentFactory:
    """
    Factory for creating Enhanced System-Aware Agent LangGraph brain.
    
    Creates agents that understand their system role, maintain memory,
    and collaborate effectively within the AgenticFlow architecture.
    """
    
    def __init__(
        self,
        model,
        agent_id: str,
        event_bus: Optional[EventBus] = None,
        system_context: Optional[SystemContext] = None,
        enable_memory: bool = True,
        memory_retention_days: int = 7,
        tools: Optional[List] = None
    ):
        self.model = model
        self.agent_id = agent_id
        self.event_bus = event_bus
        self.system_context = system_context or SystemContext(
            agent_id=agent_id,
            role=AgentRole.SUBORDINATE,
            event_bus_available=event_bus is not None
        )
        self.enable_memory = enable_memory
        self.memory_retention_days = memory_retention_days
        self.logger = get_flow_logger()
        
        # Initialize memory checkpoint
        self.memory_saver = MemorySaver() if enable_memory else None
    
    def create_graph(self) -> StateGraph:
        """Create the Enhanced System-Aware Agent StateGraph."""
        graph = StateGraph(EnhancedAgentState)
        
        # Add agent nodes
        graph.add_node("initialize", self._initialize_agent)
        graph.add_node("understand_task", self._understand_task)
        graph.add_node("plan_execution", self._plan_execution)
        graph.add_node("reflect_on_context", self._reflect_on_context)
        graph.add_node("execute_action", self._execute_action)
        graph.add_node("report_progress", self._report_progress)
        graph.add_node("handle_feedback", self._handle_feedback)
        graph.add_node("finalize", self._finalize_execution)
        
        # Enhanced agent flow
        graph.add_edge(START, "initialize")
        graph.add_edge("initialize", "understand_task")
        graph.add_edge("understand_task", "plan_execution")
        graph.add_edge("plan_execution", "reflect_on_context")
        graph.add_edge("reflect_on_context", "execute_action")
        
        # Smart transitions
        graph.add_conditional_edges(
            "execute_action",
            self._after_execute_action,
            {
                "report_progress": "report_progress",
                "continue_execution": "execute_action",
                "handle_feedback": "handle_feedback",
                "finalize": "finalize"
            }
        )
        
        graph.add_conditional_edges(
            "report_progress",
            self._after_report_progress,
            {
                "continue_execution": "execute_action",
                "handle_feedback": "handle_feedback",
                "finalize": "finalize"
            }
        )
        
        graph.add_conditional_edges(
            "handle_feedback",
            self._after_handle_feedback,
            {
                "continue_execution": "execute_action",
                "reflect_on_context": "reflect_on_context",
                "finalize": "finalize"
            }
        )
        
        graph.add_edge("finalize", END)
        
        return graph
    
    async def _initialize_agent(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Initialize the enhanced system-aware agent."""
        self.logger.agent(f"🚀 Enhanced system-aware agent {self.agent_id} initializing",
                          role=self.system_context.role.value,
                          superior=self.system_context.superior,
                          level=LogLevel.SUCCESS)
        
        # Initialize memory
        memory = state.get("memory") or AgentMemory(system_context=self.system_context)
        
        # Report to superior
        if self.system_context.superior and self.event_bus:
            await self._report_to_superior("agent_initialized", {
                "agent_id": self.agent_id,
                "role": self.system_context.role.value,
                "capabilities": getattr(self.system_context, 'capabilities', []),
                "timestamp": datetime.now().isoformat()
            })
        
        if self.event_bus:
            await self.event_bus.emit_async(Event(
                event_type=EventType.TASK_STARTED,
                source=f"enhanced_agent_{self.agent_id}",
                data={
                    "phase": "initialize",
                    "agent_id": self.agent_id,
                    "system_role": self.system_context.role.value,
                    "timestamp": datetime.now().isoformat()
                },
                channel="agent"
            ))
        
        return {
            "system_context": self.system_context,
            "memory": memory,
            "current_phase": EnhancedAgentPhase.UNDERSTAND_TASK.value,
            "execution_progress": 0.0,
            "pending_reports": [],
            "received_feedback": [],
            "collaboration_requests": [],
            "agent_complete": False
        }
    
    async def _understand_task(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Understand the assigned task with system context."""
        task_description = state.get("task_description", "")
        task_id = state.get("task_id", "unknown")
        memory = state.get("memory", AgentMemory())
        
        self.logger.agent(f"🔍 Understanding assigned task: {task_id}",
                          task_preview=task_description[:80] + "...",
                          assigned_by=self.system_context.assigned_by,
                          level=LogLevel.INFO)
        
        # Use LLM to understand task in system context
        understanding_prompt = f"""
        As Agent {self.agent_id}, I need to understand this task within my system role:
        
        TASK: {task_description}
        TASK_ID: {task_id}
        
        MY SYSTEM CONTEXT:
        - Role: {self.system_context.role.value}
        - Superior: {self.system_context.superior}
        - Must report progress: {self.system_context.must_report_progress}
        - Can request assistance: {self.system_context.can_request_assistance}
        
        PAST EXPERIENCE: {json.dumps([t for t in memory.task_history[-3:]], indent=2) if memory.task_history else "None"}
        
        Analyze this task and provide:
        1. Task objectives and success criteria
        2. Required resources and capabilities
        3. Potential challenges and risks
        4. Need for collaboration or assistance
        5. Reporting requirements to superior
        6. Estimated complexity and time
        
        Return as structured JSON.
        """
        
        try:
            response = await self.model.ainvoke([HumanMessage(content=understanding_prompt)])
            understanding_text = response.content if hasattr(response, 'content') else str(response)
            
            task_understanding = self._extract_json_understanding(understanding_text)
            
            self.logger.agent("📊 Task understanding completed",
                            complexity=task_understanding.get("complexity", "unknown"),
                            requires_assistance=task_understanding.get("need_for_collaboration", False),
                            level=LogLevel.SUCCESS)
            
            # Update memory
            memory.current_task = {
                "task_id": task_id,
                "description": task_description,
                "understanding": task_understanding,
                "started_at": datetime.now().isoformat()
            }
            
            return {
                "memory": memory,
                "task_understanding": task_understanding,
                "current_phase": EnhancedAgentPhase.PLAN_EXECUTION.value
            }
            
        except Exception as e:
            self.logger.agent(f"❌ Task understanding failed: {str(e)}",
                            error=str(e),
                            level=LogLevel.ERROR)
            return {
                "memory": memory,
                "task_understanding": {"complexity": "unknown", "objectives": [task_description]},
                "current_phase": EnhancedAgentPhase.PLAN_EXECUTION.value
            }
    
    async def _plan_execution(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Plan task execution considering system constraints."""
        task_understanding = state.get("task_understanding", {})
        memory = state.get("memory", AgentMemory())
        
        self.logger.agent("⚡ Planning task execution",
                          planning_scope="system_aware,resource_conscious",
                          level=LogLevel.INFO)
        
        planning_prompt = f"""
        As Agent {self.agent_id}, plan the execution of this task:
        
        TASK UNDERSTANDING: {json.dumps(task_understanding, indent=2)}
        
        SYSTEM CONSTRAINTS:
        - I report to: {self.system_context.superior}
        - Must provide progress updates: {self.system_context.must_report_progress}
        - Can request help: {self.system_context.can_request_assistance}
        
        LEARNED PATTERNS: {json.dumps(memory.successful_patterns[-3:], indent=2) if memory.successful_patterns else "None"}
        
        Create a step-by-step execution plan:
        1. Break down into actionable steps
        2. Identify progress reporting points
        3. Note where assistance might be needed
        4. Include reflection and learning points
        5. Plan for potential failure recovery
        
        Return as JSON array of steps with progress_percentage, reporting_required, assistance_needed flags.
        """
        
        try:
            response = await self.model.ainvoke([HumanMessage(content=planning_prompt)])
            plan_text = response.content if hasattr(response, 'content') else str(response)
            
            execution_plan = self._extract_json_plan(plan_text)
            
            self.logger.agent(f"📋 Execution plan created",
                            plan_steps=len(execution_plan),
                            reporting_points=len([s for s in execution_plan if s.get("reporting_required", False)]),
                            level=LogLevel.SUCCESS)
            
            # Log plan steps
            for i, step in enumerate(execution_plan, 1):
                self.logger.agent(f"📋 Step {i}: {step.get('description', 'Unknown')}",
                                step_id=i,
                                progress_target=step.get("progress_percentage", 0),
                                level=LogLevel.INFO)
            
            return {
                "current_plan": execution_plan,
                "current_phase": EnhancedAgentPhase.REFLECT_ON_CONTEXT.value
            }
            
        except Exception as e:
            self.logger.agent(f"❌ Execution planning failed: {str(e)}",
                            error=str(e),
                            level=LogLevel.ERROR)
            # Fallback plan
            return {
                "current_plan": [{"description": "Execute task", "progress_percentage": 100}],
                "current_phase": EnhancedAgentPhase.REFLECT_ON_CONTEXT.value
            }
    
    async def _reflect_on_context(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Reflect on current context and prepare for execution."""
        memory = state.get("memory", AgentMemory())
        current_plan = state.get("current_plan", [])
        
        self.logger.agent("🤔 Reflecting on execution context",
                          reflection_type="contextual,historical,strategic",
                          level=LogLevel.INFO)
        
        reflection_prompt = f"""
        As Agent {self.agent_id}, reflect on the current execution context:
        
        CURRENT PLAN: {json.dumps(current_plan, indent=2)}
        
        SYSTEM POSITION:
        - Role: {self.system_context.role.value}
        - Reporting to: {self.system_context.superior}
        - Collaboration available: {self.system_context.can_request_assistance}
        
        MEMORY CONTEXT:
        - Past successes: {len(memory.successful_patterns)}
        - Past failures: {len(memory.failure_patterns)}
        - Recent decisions: {json.dumps(memory.decisions_made[-2:], indent=2) if memory.decisions_made else "None"}
        
        Provide reflection on:
        1. Readiness to execute (confidence level)
        2. Potential systemic risks or blockers
        3. Opportunities for collaboration
        4. Learning objectives for this execution
        5. Success metrics alignment with system goals
        
        Return as JSON with confidence_score (0-1) and insights.
        """
        
        try:
            response = await self.model.ainvoke([HumanMessage(content=reflection_prompt)])
            reflection_text = response.content if hasattr(response, 'content') else str(response)
            
            reflection_result = self._extract_json_reflection(reflection_text)
            
            confidence = reflection_result.get("confidence_score", 0.7)
            
            self.logger.agent("💭 Context reflection completed",
                            confidence_score=confidence,
                            readiness_level="high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low",
                            level=LogLevel.SUCCESS)
            
            # Update memory with reflection
            memory.reflections.append({
                "timestamp": datetime.now().isoformat(),
                "task_id": state.get("task_id"),
                "reflection": reflection_result,
                "confidence": confidence
            })
            
            return {
                "memory": memory,
                "reflection_notes": reflection_result.get("insights", "Ready to proceed"),
                "execution_confidence": confidence,
                "current_phase": EnhancedAgentPhase.EXECUTE_ACTION.value
            }
            
        except Exception as e:
            self.logger.agent(f"❌ Context reflection failed: {str(e)}",
                            error=str(e),
                            level=LogLevel.ERROR)
            return {
                "memory": memory,
                "reflection_notes": "Proceeding with standard execution",
                "execution_confidence": 0.6,
                "current_phase": EnhancedAgentPhase.EXECUTE_ACTION.value
            }
    
    async def _execute_action(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Execute the current action step."""
        current_plan = state.get("current_plan", [])
        execution_progress = state.get("execution_progress", 0.0)
        memory = state.get("memory", AgentMemory())
        
        # Find next action to execute
        next_action = None
        for step in current_plan:
            if step.get("progress_percentage", 0) > execution_progress:
                next_action = step
                break
        
        if not next_action:
            return {"current_phase": EnhancedAgentPhase.FINALIZE.value}
        
        self.logger.agent(f"🏃 Executing action: {next_action.get('description', 'Unknown')}",
                          action_id=next_action.get('id', 'unknown'),
                          progress_target=next_action.get('progress_percentage', 0),
                          level=LogLevel.INFO)
        
        # Simulate action execution
        try:
            # This would be replaced with actual action execution logic
            await asyncio.sleep(0.1)  # Simulate work
            
            action_result = {
                "status": "success",
                "description": next_action.get("description", ""),
                "result": f"Completed: {next_action.get('description', '')}",
                "timestamp": datetime.now().isoformat()
            }
            
            new_progress = next_action.get("progress_percentage", execution_progress + 10)
            
            self.logger.agent(f"✅ Action completed successfully",
                            progress_achieved=f"{new_progress}%",
                            level=LogLevel.SUCCESS)
            
            # Update memory with decision
            memory.decisions_made.append({
                "timestamp": datetime.now().isoformat(),
                "task_id": state.get("task_id"),
                "action": next_action,
                "result": action_result
            })
            
            return {
                "memory": memory,
                "current_action": action_result,
                "execution_progress": new_progress,
                "current_phase": self._determine_next_action_phase(state, next_action, new_progress)
            }
            
        except Exception as e:
            self.logger.agent(f"❌ Action execution failed: {str(e)}",
                            error=str(e),
                            level=LogLevel.ERROR)
            
            return {
                "memory": memory,
                "current_action": {"status": "failed", "error": str(e)},
                "current_phase": EnhancedAgentPhase.HANDLE_FEEDBACK.value
            }
    
    async def _report_progress(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Report progress to superior/orchestrator."""
        execution_progress = state.get("execution_progress", 0.0)
        current_action = state.get("current_action", {})
        task_id = state.get("task_id", "unknown")
        
        if not self.system_context.must_report_progress:
            return {"current_phase": self._determine_next_phase_after_report(state)}
        
        progress_report = {
            "agent_id": self.agent_id,
            "task_id": task_id,
            "progress_percentage": execution_progress,
            "current_status": current_action.get("status", "in_progress"),
            "last_action": current_action.get("description", ""),
            "timestamp": datetime.now().isoformat(),
            "next_steps": "Continuing execution" if execution_progress < 100 else "Ready to finalize"
        }
        
        self.logger.agent(f"📊 Reporting progress to superior",
                          progress=f"{execution_progress}%",
                          status=current_action.get("status", "unknown"),
                          superior=self.system_context.superior,
                          level=LogLevel.INFO)
        
        # Report to superior
        if self.system_context.superior and self.event_bus:
            await self._report_to_superior("progress_update", progress_report)
        
        return {
            "pending_reports": [],  # Clear pending reports
            "current_phase": self._determine_next_phase_after_report(state)
        }
    
    async def _handle_feedback(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Handle feedback from superior or peers."""
        received_feedback = state.get("received_feedback", [])
        memory = state.get("memory", AgentMemory())
        
        if not received_feedback:
            return {"current_phase": self._determine_next_phase_after_feedback(state)}
        
        self.logger.agent("📨 Processing received feedback",
                          feedback_count=len(received_feedback),
                          level=LogLevel.INFO)
        
        # Process feedback and adjust accordingly
        for feedback in received_feedback:
            self.logger.agent(f"📝 Feedback: {feedback.get('message', 'No message')}",
                            from_entity=feedback.get('from', 'unknown'),
                            feedback_type=feedback.get('type', 'general'),
                            level=LogLevel.INFO)
        
        # Update memory with feedback
        memory.collaboration_history.extend(received_feedback)
        
        return {
            "memory": memory,
            "received_feedback": [],  # Clear processed feedback
            "current_phase": self._determine_next_phase_after_feedback(state)
        }
    
    async def _finalize_execution(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Finalize task execution and report results."""
        execution_progress = state.get("execution_progress", 0.0)
        memory = state.get("memory", AgentMemory())
        task_id = state.get("task_id", "unknown")
        
        execution_result = {
            "status": "completed" if execution_progress >= 100 else "partial",
            "progress_achieved": execution_progress,
            "task_id": task_id,
            "agent_id": self.agent_id,
            "completion_time": datetime.now().isoformat(),
            "lessons_learned": []
        }
        
        self.logger.agent("🎯 Task execution finalized",
                          final_status=execution_result["status"],
                          progress_achieved=f"{execution_progress}%",
                          level=LogLevel.SUCCESS)
        
        # Update task history
        if memory.current_task:
            memory.current_task["completed_at"] = datetime.now().isoformat()
            memory.current_task["result"] = execution_result
            memory.task_history.append(memory.current_task)
            memory.current_task = None
        
        # Final report to superior
        if self.system_context.superior and self.event_bus:
            await self._report_to_superior("task_completed", execution_result)
        
        if self.event_bus:
            await self.event_bus.emit_async(Event(
                event_type=EventType.TASK_COMPLETED,
                source=f"enhanced_agent_{self.agent_id}",
                data=execution_result,
                channel="agent"
            ))
        
        return {
            "memory": memory,
            "execution_result": execution_result,
            "agent_complete": True,
            "current_phase": EnhancedAgentPhase.COMPLETE.value
        }
    
    # Helper methods
    async def _report_to_superior(self, report_type: str, data: Dict[str, Any]):
        """Report to superior entity."""
        if self.event_bus and self.system_context.superior:
            await self.event_bus.emit_async(Event(
                event_type=EventType.STATUS_UPDATE,
                source=f"enhanced_agent_{self.agent_id}",
                data={
                    "report_type": report_type,
                    "from_agent": self.agent_id,
                    "to_superior": self.system_context.superior,
                    **data
                },
                channel="system_communication"
            ))
    
    def _determine_next_action_phase(self, state: EnhancedAgentState, action: Dict, progress: float) -> str:
        """Determine next phase after action execution."""
        if progress >= 100:
            return EnhancedAgentPhase.FINALIZE.value
        elif action.get("reporting_required", False):
            return EnhancedAgentPhase.REPORT_PROGRESS.value
        else:
            return EnhancedAgentPhase.EXECUTE_ACTION.value
    
    def _determine_next_phase_after_report(self, state: EnhancedAgentState) -> str:
        """Determine next phase after reporting."""
        progress = state.get("execution_progress", 0.0)
        return EnhancedAgentPhase.FINALIZE.value if progress >= 100 else EnhancedAgentPhase.EXECUTE_ACTION.value
    
    def _determine_next_phase_after_feedback(self, state: EnhancedAgentState) -> str:
        """Determine next phase after handling feedback."""
        return EnhancedAgentPhase.EXECUTE_ACTION.value
    
    def _after_execute_action(self, state: EnhancedAgentState) -> str:
        """Determine next step after action execution."""
        current_action = state.get("current_action", {})
        progress = state.get("execution_progress", 0.0)
        
        if current_action.get("status") == "failed":
            return "handle_feedback"
        elif progress >= 100:
            return "finalize"
        elif self.system_context.must_report_progress and progress % 25 == 0:  # Report every 25%
            return "report_progress"
        else:
            return "continue_execution"
    
    def _after_report_progress(self, state: EnhancedAgentState) -> str:
        """Determine next step after reporting progress."""
        return self._determine_next_phase_after_report(state)
    
    def _after_handle_feedback(self, state: EnhancedAgentState) -> str:
        """Determine next step after handling feedback."""
        return self._determine_next_phase_after_feedback(state)
    
    # JSON extraction utilities
    def _extract_json_understanding(self, text: str) -> Dict[str, Any]:
        """Extract task understanding from LLM response."""
        try:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"complexity": "moderate", "objectives": ["Complete assigned task"]}
    
    def _extract_json_plan(self, text: str) -> List[Dict[str, Any]]:
        """Extract execution plan from LLM response."""
        try:
            import re
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return [{"description": "Execute task", "progress_percentage": 100}]
    
    def _extract_json_reflection(self, text: str) -> Dict[str, Any]:
        """Extract reflection from LLM response."""
        try:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"confidence_score": 0.7, "insights": "Ready to proceed"}


class EnhancedSystemAwareAgent:
    """
    Enhanced System-Aware Agent with memory and superior communication.
    
    This agent understands its role within the AgenticFlow system,
    maintains memory across tasks, and reports to its superior.
    """
    
    def __init__(
        self,
        model,
        agent_id: str,
        event_bus: Optional[EventBus] = None,
        superior: Optional[str] = None,
        role: AgentRole = AgentRole.SUBORDINATE,
        capabilities: List[str] = None
    ):
        self.model = model
        self.agent_id = agent_id
        self.event_bus = event_bus
        
        # Create system context
        self.system_context = SystemContext(
            agent_id=agent_id,
            role=role,
            superior=superior,
            event_bus_available=event_bus is not None,
            can_request_assistance=True,
            must_report_progress=True
        )
        
        self.factory = EnhancedSystemAwareAgentFactory(
            model, agent_id, event_bus, self.system_context
        )
        self.compiled_graph = self.factory.create_graph().compile(
            checkpointer=self.factory.memory_saver
        )
        self.logger = get_flow_logger()
    
    async def arun(self, task_description: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute task with enhanced system awareness and memory."""
        task_id = task_id or f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.agent(f"🧠 Enhanced system-aware agent {self.agent_id} activated",
                          task_id=task_id,
                          role=self.system_context.role.value,
                          superior=self.system_context.superior,
                          level=LogLevel.SUCCESS)
        
        # Initialize state
        initial_state = {
            "task_description": task_description,
            "task_id": task_id,
            "system_context": self.system_context
        }
        
        try:
            # Execute enhanced agent graph with memory
            final_state = None
            thread_config = {"configurable": {"thread_id": f"agent_{self.agent_id}_{task_id}"}}
            
            async for chunk in self.compiled_graph.astream(initial_state, thread_config):
                final_state = chunk
            
            # Extract results
            if final_state and "execution_result" in final_state:
                result = final_state["execution_result"]
                self.logger.agent(f"🎯 Enhanced agent {self.agent_id} completed successfully",
                                final_status=result.get("status", "unknown"),
                                progress_achieved=f"{result.get('progress_achieved', 0)}%",
                                level=LogLevel.SUCCESS)
                return result
            else:
                # Fallback
                self.logger.agent(f"⚠️ Enhanced agent {self.agent_id} fallback triggered", 
                                level=LogLevel.WARNING)
                return {"status": "failed", "error": "No results generated"}
                
        except Exception as e:
            self.logger.agent(f"❌ Enhanced agent {self.agent_id} failed: {str(e)}",
                            error=str(e),
                            level=LogLevel.ERROR)
            return {"status": "error", "error": str(e)}