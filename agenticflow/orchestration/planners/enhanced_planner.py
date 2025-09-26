"""
Enhanced Planner with LangGraph Brain

This planner uses a sophisticated LangGraph state machine for:
- Multi-step task analysis
- Intelligent task decomposition 
- Dependency detection and ordering
- Agent capability matching
- Memory and reflection
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict
from enum import Enum

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agenticflow.core.events.event_bus import EventBus, Event, EventType
from agenticflow.observability.flow_logger import get_flow_logger, LogLevel
from .planner import PlanTask, Plan


class PlannerPhase(Enum):
    INITIALIZE = "initialize"
    ANALYZE_REQUEST = "analyze_request"
    DECOMPOSE_TASKS = "decompose_tasks"
    DETECT_DEPENDENCIES = "detect_dependencies"
    MATCH_CAPABILITIES = "match_capabilities"
    VALIDATE_PLAN = "validate_plan"
    FINALIZE = "finalize"
    COMPLETE = "complete"


class EnhancedPlannerState(TypedDict, total=False):
    # Core request info
    original_request: str
    thread_id: str
    agent_catalog: List[Dict[str, Any]]
    
    # Planner analysis
    request_analysis: Dict[str, Any]
    task_candidates: List[Dict[str, Any]]
    dependency_map: Dict[str, List[str]]
    capability_matches: Dict[str, str]
    
    # Memory and context
    planning_memory: List[Dict[str, Any]]
    reflection_notes: str
    confidence_score: float
    
    # Results
    final_plan: Plan
    execution_metadata: Dict[str, Any]
    
    # State management
    current_phase: str
    attempt_number: int
    max_attempts: int
    planner_complete: bool


class EnhancedPlannerGraphFactory:
    """
    Factory for creating Enhanced Planner LangGraph brain.
    
    Creates sophisticated planning workflows with memory, reflection,
    and intelligent task decomposition.
    """
    
    def __init__(
        self,
        model,
        event_bus: Optional[EventBus] = None,
        use_memory: bool = True,
        use_reflection: bool = True,
        max_planning_attempts: int = 3
    ):
        self.model = model
        self.event_bus = event_bus
        self.use_memory = use_memory
        self.use_reflection = use_reflection
        self.max_planning_attempts = max_planning_attempts
        self.logger = get_flow_logger()
    
    def create_graph(self) -> StateGraph:
        """Create the Enhanced Planner StateGraph."""
        graph = StateGraph(EnhancedPlannerState)
        
        # Add planning nodes
        graph.add_node("initialize", self._initialize_planning)
        graph.add_node("analyze_request", self._analyze_request)
        graph.add_node("decompose_tasks", self._decompose_tasks)
        graph.add_node("detect_dependencies", self._detect_dependencies)
        graph.add_node("match_capabilities", self._match_capabilities)
        graph.add_node("validate_plan", self._validate_plan)
        graph.add_node("finalize", self._finalize_plan)
        
        # Enhanced planning flow
        graph.add_edge(START, "initialize")
        graph.add_edge("initialize", "analyze_request")
        graph.add_edge("analyze_request", "decompose_tasks")
        graph.add_edge("decompose_tasks", "detect_dependencies")
        graph.add_edge("detect_dependencies", "match_capabilities")
        graph.add_edge("match_capabilities", "validate_plan")
        
        # Smart transitions
        graph.add_conditional_edges(
            "validate_plan",
            self._after_validate_plan,
            {
                "finalize": "finalize",
                "retry_decompose": "decompose_tasks",
                "complete": END
            }
        )
        
        graph.add_edge("finalize", END)
        
        return graph
    
    async def _initialize_planning(self, state: EnhancedPlannerState) -> Dict[str, Any]:
        """Initialize the enhanced planning process."""
        self.logger.planner("🚀 Initializing enhanced planning process", 
                          request_preview=state.get("original_request", "")[:80] + "...",
                          level=LogLevel.SUCCESS)
        
        if self.event_bus:
            await self.event_bus.emit_async(Event(
                event_type=EventType.TASK_STARTED,
                source="enhanced_planner",
                data={
                    "phase": "initialize",
                    "request": state.get("original_request", ""),
                    "thread_id": state.get("thread_id", ""),
                    "timestamp": datetime.now().isoformat()
                },
                channel="planner"
            ))
        
        return {
            "current_phase": PlannerPhase.ANALYZE_REQUEST.value,
            "attempt_number": 1,
            "max_attempts": self.max_planning_attempts,
            "planning_memory": [],
            "confidence_score": 0.0,
            "planner_complete": False
        }
    
    async def _analyze_request(self, state: EnhancedPlannerState) -> Dict[str, Any]:
        """Analyze the user request with LLM reasoning."""
        request = state.get("original_request", "")
        
        self.logger.planner("🔍 Analyzing user request with LLM", 
                          analysis_type="deep_semantic",
                          level=LogLevel.INFO)
        
        analysis_prompt = f"""
        Analyze this user request for task planning:
        
        REQUEST: {request}
        
        Provide a structured analysis:
        1. Primary objectives (what needs to be accomplished)
        2. Secondary objectives (implicit requirements)
        3. Input requirements (data, files, information needed)
        4. Output requirements (deliverables expected)
        5. Complexity assessment (simple/moderate/complex)
        6. Estimated task count (how many atomic tasks)
        7. Critical dependencies (sequential vs parallel opportunities)
        8. Risk factors (potential failure points)
        
        Return as JSON with these exact keys.
        """
        
        try:
            response = await self.model.ainvoke([HumanMessage(content=analysis_prompt)])
            analysis_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON analysis
            analysis = self._extract_json_analysis(analysis_text)
            
            self.logger.planner("📊 Request analysis completed",
                              complexity=analysis.get("complexity", "unknown"),
                              estimated_tasks=analysis.get("estimated_task_count", 0),
                              level=LogLevel.SUCCESS)
            
            return {
                "request_analysis": analysis,
                "current_phase": PlannerPhase.DECOMPOSE_TASKS.value
            }
            
        except Exception as e:
            self.logger.planner(f"❌ Request analysis failed: {str(e)}", 
                              error=str(e), 
                              level=LogLevel.ERROR)
            return {
                "request_analysis": {"complexity": "unknown", "estimated_task_count": 1},
                "current_phase": PlannerPhase.DECOMPOSE_TASKS.value
            }
    
    async def _decompose_tasks(self, state: EnhancedPlannerState) -> Dict[str, Any]:
        """Decompose request into atomic tasks."""
        request = state.get("original_request", "")
        analysis = state.get("request_analysis", {})
        
        self.logger.planner("⚡ Decomposing request into atomic tasks",
                          base_complexity=analysis.get("complexity", "unknown"),
                          level=LogLevel.INFO)
        
        decomposition_prompt = f"""
        Break down this request into ATOMIC tasks based on the analysis:
        
        REQUEST: {request}
        ANALYSIS: {json.dumps(analysis, indent=2)}
        
        Create atomic tasks following these rules:
        1. Each task should be a SINGLE action
        2. Tasks should be specific and measurable
        3. Include priority (1=highest, 5=lowest)
        4. Suggest required capabilities for each task
        
        Return JSON array of tasks:
        [
            {{
                "id": "task_1",
                "description": "specific action description",
                "priority": 1,
                "estimated_duration": "5m",
                "capabilities_needed": ["file_read", "analysis"],
                "inputs": ["file_path"],
                "outputs": ["analysis_data"]
            }}
        ]
        """
        
        try:
            response = await self.model.ainvoke([HumanMessage(content=decomposition_prompt)])
            tasks_text = response.content if hasattr(response, 'content') else str(response)
            
            task_candidates = self._extract_json_tasks(tasks_text)
            
            self.logger.planner(f"🔨 Task decomposition completed",
                              tasks_created=len(task_candidates),
                              level=LogLevel.SUCCESS)
            
            # Log each task
            for i, task in enumerate(task_candidates, 1):
                self.logger.planner(f"📋 Task {i}: {task.get('description', 'Unknown')}",
                                  task_id=task.get('id', f'task_{i}'),
                                  priority=task.get('priority', 'unset'),
                                  capabilities=task.get('capabilities_needed', []),
                                  level=LogLevel.INFO)
            
            return {
                "task_candidates": task_candidates,
                "current_phase": PlannerPhase.DETECT_DEPENDENCIES.value
            }
            
        except Exception as e:
            self.logger.planner(f"❌ Task decomposition failed: {str(e)}", 
                              error=str(e),
                              level=LogLevel.ERROR)
            # Fallback to simple task
            return {
                "task_candidates": [{"id": "task_1", "description": request, "priority": 1}],
                "current_phase": PlannerPhase.DETECT_DEPENDENCIES.value
            }
    
    async def _detect_dependencies(self, state: EnhancedPlannerState) -> Dict[str, Any]:
        """Detect and map task dependencies."""
        tasks = state.get("task_candidates", [])
        
        self.logger.planner("🔗 Detecting task dependencies and ordering",
                          task_count=len(tasks),
                          level=LogLevel.INFO)
        
        if len(tasks) <= 1:
            return {
                "dependency_map": {},
                "current_phase": PlannerPhase.MATCH_CAPABILITIES.value
            }
        
        dependency_prompt = f"""
        Analyze these tasks for dependencies:
        
        TASKS: {json.dumps(tasks, indent=2)}
        
        Determine:
        1. Which tasks must complete before others can start
        2. Which tasks can run in parallel
        3. Critical path through the task network
        
        Return JSON mapping each task_id to its dependencies:
        {{
            "task_2": ["task_1"],
            "task_3": ["task_1", "task_2"],
            "task_4": ["task_1"]
        }}
        """
        
        try:
            response = await self.model.ainvoke([HumanMessage(content=dependency_prompt)])
            deps_text = response.content if hasattr(response, 'content') else str(response)
            
            dependency_map = self._extract_json_dependencies(deps_text)
            
            # Log dependency relationships
            for task_id, deps in dependency_map.items():
                if deps:
                    self.logger.planner(f"🔗 {task_id} depends on: {', '.join(deps)}",
                                      task_id=task_id,
                                      dependencies=deps,
                                      level=LogLevel.INFO)
            
            parallel_tasks = [tid for tid, deps in dependency_map.items() if not deps]
            if parallel_tasks:
                self.logger.planner(f"⚡ Parallel execution opportunities: {', '.join(parallel_tasks)}",
                                  parallel_count=len(parallel_tasks),
                                  level=LogLevel.INFO)
            
            return {
                "dependency_map": dependency_map,
                "current_phase": PlannerPhase.MATCH_CAPABILITIES.value
            }
            
        except Exception as e:
            self.logger.planner(f"❌ Dependency detection failed: {str(e)}", 
                              error=str(e),
                              level=LogLevel.ERROR)
            return {
                "dependency_map": {},
                "current_phase": PlannerPhase.MATCH_CAPABILITIES.value
            }
    
    async def _match_capabilities(self, state: EnhancedPlannerState) -> Dict[str, Any]:
        """Match tasks with agent capabilities."""
        tasks = state.get("task_candidates", [])
        agents = state.get("agent_catalog", [])
        
        self.logger.planner("🎯 Matching tasks with agent capabilities",
                          agent_count=len(agents),
                          task_count=len(tasks),
                          level=LogLevel.INFO)
        
        capability_matches = {}
        
        if not agents:
            self.logger.planner("⚠️ No agents available - using generic assignment", 
                              level=LogLevel.WARNING)
            return {
                "capability_matches": capability_matches,
                "current_phase": PlannerPhase.VALIDATE_PLAN.value
            }
        
        # Simple capability matching (can be enhanced with LLM)
        for task in tasks:
            task_id = task.get("id", "unknown")
            needed_caps = task.get("capabilities_needed", [])
            
            best_agent = None
            best_score = 0
            
            for agent in agents:
                agent_name = agent.get("name", "unknown")
                agent_caps = agent.get("capabilities", [])
                
                # Calculate match score
                score = len(set(needed_caps) & set(agent_caps))
                if score > best_score:
                    best_score = score
                    best_agent = agent_name
            
            if best_agent:
                capability_matches[task_id] = best_agent
                self.logger.planner(f"✅ Matched {task_id} → {best_agent}",
                                  task_id=task_id,
                                  assigned_agent=best_agent,
                                  match_score=best_score,
                                  level=LogLevel.SUCCESS)
        
        return {
            "capability_matches": capability_matches,
            "current_phase": PlannerPhase.VALIDATE_PLAN.value
        }
    
    async def _validate_plan(self, state: EnhancedPlannerState) -> Dict[str, Any]:
        """Validate the complete plan."""
        tasks = state.get("task_candidates", [])
        dependencies = state.get("dependency_map", {})
        matches = state.get("capability_matches", {})
        
        self.logger.planner("🔍 Validating complete execution plan",
                          validation_checks="completeness,consistency,feasibility",
                          level=LogLevel.INFO)
        
        # Validation checks
        validation_results = {
            "has_tasks": len(tasks) > 0,
            "dependencies_valid": self._validate_dependencies(tasks, dependencies),
            "agents_matched": len(matches) == len(tasks) if tasks else True,
            "no_circular_deps": self._check_circular_dependencies(dependencies)
        }
        
        all_valid = all(validation_results.values())
        
        if all_valid:
            self.logger.planner("✅ Plan validation successful - ready for execution",
                              validation_score=100,
                              level=LogLevel.SUCCESS)
            return {
                "current_phase": PlannerPhase.FINALIZE.value,
                "confidence_score": 0.9
            }
        else:
            failed_checks = [k for k, v in validation_results.items() if not v]
            self.logger.planner(f"⚠️ Plan validation issues found: {', '.join(failed_checks)}",
                              failed_checks=failed_checks,
                              level=LogLevel.WARNING)
            
            return {
                "current_phase": PlannerPhase.FINALIZE.value,  # Proceed anyway with warning
                "confidence_score": 0.6
            }
    
    async def _finalize_plan(self, state: EnhancedPlannerState) -> Dict[str, Any]:
        """Finalize the execution plan."""
        tasks = state.get("task_candidates", [])
        dependencies = state.get("dependency_map", {})
        matches = state.get("capability_matches", {})
        
        self.logger.planner("🎯 Finalizing execution plan",
                          final_task_count=len(tasks),
                          level=LogLevel.SUCCESS)
        
        # Convert to Plan format
        plan_tasks = []
        for task in tasks:
            plan_task = PlanTask(
                id=task.get("id", "unknown"),
                description=task.get("description", ""),
                priority=task.get("priority", 1),
                dependencies=dependencies.get(task.get("id", ""), []),
                agent=matches.get(task.get("id", ""), None),
                capabilities=task.get("capabilities_needed", [])
            )
            plan_tasks.append(plan_task)
        
        final_plan = Plan(tasks=plan_tasks)
        
        # Log final plan summary
        self.logger.planner("📋 Final execution plan created",
                          dag_structure={
                              "nodes": [{"id": t.id, "description": t.description, "agent": t.agent} for t in plan_tasks],
                              "edges": [{"from": dep, "to": t.id} for t in plan_tasks for dep in t.dependencies]
                          },
                          level=LogLevel.SUCCESS)
        
        if self.event_bus:
            await self.event_bus.emit_async(Event(
                event_type=EventType.TASK_COMPLETED,
                source="enhanced_planner",
                data={
                    "phase": "finalize",
                    "task_count": len(plan_tasks),
                    "has_dependencies": bool(dependencies),
                    "confidence_score": state.get("confidence_score", 0.0),
                    "timestamp": datetime.now().isoformat()
                },
                channel="planner"
            ))
        
        return {
            "final_plan": final_plan,
            "planner_complete": True,
            "current_phase": PlannerPhase.COMPLETE.value
        }
    
    def _after_validate_plan(self, state: EnhancedPlannerState) -> str:
        """Determine next step after validation."""
        confidence = state.get("confidence_score", 0.0)
        attempt = state.get("attempt_number", 1)
        max_attempts = state.get("max_attempts", 3)
        
        if confidence >= 0.8 or attempt >= max_attempts:
            return "finalize"
        elif confidence >= 0.6:
            return "finalize"  # Proceed with warning
        else:
            return "retry_decompose"
    
    # Utility methods
    def _extract_json_analysis(self, text: str) -> Dict[str, Any]:
        """Extract JSON analysis from LLM response."""
        try:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"complexity": "moderate", "estimated_task_count": 2}
    
    def _extract_json_tasks(self, text: str) -> List[Dict[str, Any]]:
        """Extract task list from LLM response."""
        try:
            import re
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return []
    
    def _extract_json_dependencies(self, text: str) -> Dict[str, List[str]]:
        """Extract dependency mapping from LLM response."""
        try:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {}
    
    def _validate_dependencies(self, tasks: List[Dict], dependencies: Dict[str, List[str]]) -> bool:
        """Validate dependency references exist."""
        task_ids = {t.get("id") for t in tasks}
        for deps in dependencies.values():
            if not all(dep in task_ids for dep in deps):
                return False
        return True
    
    def _check_circular_dependencies(self, dependencies: Dict[str, List[str]]) -> bool:
        """Check for circular dependencies."""
        # Simple cycle detection
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependencies.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        return not any(has_cycle(node) for node in dependencies.keys())


class EnhancedPlanner:
    """
    Enhanced Planner with sophisticated LangGraph brain.
    
    Replaces the simple Planner with multi-phase planning,
    memory, reflection, and intelligent task decomposition.
    """
    
    def __init__(self, model, event_bus: Optional[EventBus] = None):
        self.model = model
        self.event_bus = event_bus
        self.factory = EnhancedPlannerGraphFactory(model, event_bus)
        self.compiled_graph = self.factory.create_graph().compile()
        self.logger = get_flow_logger()
    
    async def aplan(self, user_request: str, agent_catalog: Optional[List[Dict[str, Any]]] = None) -> Plan:
        """Enhanced planning with LangGraph brain."""
        self.logger.planner("🧠 Enhanced planner brain activated",
                          request_preview=user_request[:60] + "...",
                          agent_catalog_size=len(agent_catalog or []),
                          level=LogLevel.SUCCESS)
        
        # Initialize state
        initial_state = {
            "original_request": user_request,
            "thread_id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "agent_catalog": agent_catalog or []
        }
        
        try:
            # Execute enhanced planning graph
            final_state = None
            async for chunk in self.compiled_graph.astream(initial_state):
                final_state = chunk
            
            # Extract plan
            if final_state and "final_plan" in final_state:
                plan = final_state["final_plan"]
                self.logger.planner("🎯 Enhanced planning completed successfully",
                                  plan_tasks=len(plan.tasks),
                                  confidence=final_state.get("confidence_score", 0.0),
                                  level=LogLevel.SUCCESS)
                return plan
            else:
                # Fallback
                self.logger.planner("⚠️ Enhanced planning fallback triggered", 
                                  level=LogLevel.WARNING)
                return Plan(tasks=[PlanTask(id="task_1", description=user_request, priority=1)])
                
        except Exception as e:
            self.logger.planner(f"❌ Enhanced planning failed: {str(e)}",
                              error=str(e),
                              level=LogLevel.ERROR)
            return Plan(tasks=[PlanTask(id="task_1", description=user_request, priority=1)])