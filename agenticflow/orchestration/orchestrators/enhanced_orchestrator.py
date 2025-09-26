"""
Enhanced Orchestrator with LangGraph Brain

This orchestrator uses a sophisticated LangGraph state machine for:
- Intelligent task scheduling and execution
- Dynamic agent allocation and load balancing  
- Real-time progress monitoring and adaptation
- Error handling and recovery strategies
- Memory and historical context
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict, Set
from enum import Enum

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agenticflow.core.events.event_bus import EventBus, Event, EventType
from agenticflow.observability.flow_logger import get_flow_logger, LogLevel
from agenticflow.orchestration.planners.planner import Plan, PlanTask


class OrchestratorPhase(Enum):
    INITIALIZE = "initialize"
    PREPARE_EXECUTION = "prepare_execution"
    ALLOCATE_AGENTS = "allocate_agents"
    EXECUTE_TASKS = "execute_tasks"
    MONITOR_PROGRESS = "monitor_progress"
    HANDLE_RESULTS = "handle_results"
    RECOVER_ERRORS = "recover_errors"
    FINALIZE = "finalize"
    COMPLETE = "complete"


class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class EnhancedOrchestratorState(TypedDict, total=False):
    # Core execution context
    plan: Plan
    thread_id: str
    available_agents: List[Dict[str, Any]]
    
    # Task tracking
    task_statuses: Dict[str, str]
    task_results: Dict[str, Any]
    task_errors: Dict[str, str]
    task_assignments: Dict[str, str]
    
    # Execution state
    ready_tasks: List[str]
    running_tasks: Set[str]
    completed_tasks: Set[str]
    failed_tasks: Set[str]
    
    # Agent management  
    agent_workloads: Dict[str, int]
    agent_capabilities: Dict[str, List[str]]
    
    # Progress and monitoring
    execution_progress: float
    start_time: datetime
    estimated_completion: Optional[datetime]
    
    # Memory and adaptation
    execution_memory: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    error_recovery_attempts: Dict[str, int]
    
    # State management
    current_phase: str
    orchestrator_complete: bool
    final_results: Dict[str, Any]


class EnhancedOrchestratorGraphFactory:
    """
    Factory for creating Enhanced Orchestrator LangGraph brain.
    
    Creates sophisticated orchestration workflows with adaptive scheduling,
    intelligent error recovery, and performance optimization.
    """
    
    def __init__(
        self,
        model,
        event_bus: Optional[EventBus] = None,
        max_concurrent_tasks: int = 5,
        max_retry_attempts: int = 3,
        enable_adaptive_scheduling: bool = True
    ):
        self.model = model
        self.event_bus = event_bus
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_retry_attempts = max_retry_attempts
        self.enable_adaptive_scheduling = enable_adaptive_scheduling
        self.logger = get_flow_logger()
    
    def create_graph(self) -> StateGraph:
        """Create the Enhanced Orchestrator StateGraph."""
        graph = StateGraph(EnhancedOrchestratorState)
        
        # Add orchestration nodes
        graph.add_node("initialize", self._initialize_orchestration)
        graph.add_node("prepare_execution", self._prepare_execution)
        graph.add_node("allocate_agents", self._allocate_agents)
        graph.add_node("execute_tasks", self._execute_tasks)
        graph.add_node("monitor_progress", self._monitor_progress)
        graph.add_node("handle_results", self._handle_results)
        graph.add_node("recover_errors", self._recover_errors)
        graph.add_node("finalize", self._finalize_orchestration)
        
        # Enhanced orchestration flow
        graph.add_edge(START, "initialize")
        graph.add_edge("initialize", "prepare_execution")
        graph.add_edge("prepare_execution", "allocate_agents")
        graph.add_edge("allocate_agents", "execute_tasks")
        graph.add_edge("execute_tasks", "monitor_progress")
        
        # Smart transitions for progress monitoring
        graph.add_conditional_edges(
            "monitor_progress",
            self._after_monitor_progress,
            {
                "handle_results": "handle_results",
                "recover_errors": "recover_errors",
                "continue_execution": "execute_tasks",
                "finalize": "finalize"
            }
        )
        
        graph.add_conditional_edges(
            "handle_results",
            self._after_handle_results,
            {
                "continue_execution": "execute_tasks",
                "finalize": "finalize"
            }
        )
        
        graph.add_conditional_edges(
            "recover_errors",
            self._after_recover_errors,
            {
                "retry_execution": "execute_tasks",
                "allocate_agents": "allocate_agents",
                "finalize": "finalize"
            }
        )
        
        graph.add_edge("finalize", END)
        
        return graph
    
    async def _initialize_orchestration(self, state: EnhancedOrchestratorState) -> Dict[str, Any]:
        """Initialize the enhanced orchestration process."""
        plan = state.get("plan")
        
        self.logger.orchestrator("🚀 Initializing enhanced orchestration",
                                task_count=len(plan.tasks) if plan else 0,
                                level=LogLevel.SUCCESS)
        
        if self.event_bus:
            await self.event_bus.emit_async(Event(
                event_type=EventType.TASK_STARTED,
                source="enhanced_orchestrator",
                data={
                    "phase": "initialize",
                    "thread_id": state.get("thread_id", ""),
                    "task_count": len(plan.tasks) if plan else 0,
                    "timestamp": datetime.now().isoformat()
                },
                channel="orchestrator"
            ))
        
        # Initialize task tracking
        task_statuses = {}
        if plan:
            for task in plan.tasks:
                task_statuses[task.id] = TaskStatus.PENDING.value
        
        return {
            "task_statuses": task_statuses,
            "task_results": {},
            "task_errors": {},
            "task_assignments": {},
            "running_tasks": set(),
            "completed_tasks": set(),
            "failed_tasks": set(),
            "agent_workloads": {},
            "execution_progress": 0.0,
            "start_time": datetime.now(),
            "execution_memory": [],
            "performance_metrics": {},
            "error_recovery_attempts": {},
            "current_phase": OrchestratorPhase.PREPARE_EXECUTION.value,
            "orchestrator_complete": False
        }
    
    async def _prepare_execution(self, state: EnhancedOrchestratorState) -> Dict[str, Any]:
        """Prepare execution environment and analyze plan."""
        plan = state.get("plan")
        
        self.logger.orchestrator("🔍 Preparing execution environment",
                                analysis_type="dag_topology,dependencies,resources",
                                level=LogLevel.INFO)
        
        if not plan or not plan.tasks:
            self.logger.orchestrator("⚠️ No tasks to execute",
                                    level=LogLevel.WARNING)
            return {
                "current_phase": OrchestratorPhase.FINALIZE.value,
                "orchestrator_complete": True
            }
        
        # Analyze DAG and find ready tasks
        ready_tasks = []
        for task in plan.tasks:
            if not task.dependencies:
                ready_tasks.append(task.id)
                state["task_statuses"][task.id] = TaskStatus.READY.value
        
        self.logger.orchestrator(f"📋 Execution preparation completed",
                               ready_tasks=len(ready_tasks),
                               total_tasks=len(plan.tasks),
                               level=LogLevel.SUCCESS)
        
        # Log DAG structure
        dag_info = {
            "nodes": [{"id": t.id, "description": t.description} for t in plan.tasks],
            "edges": [{"from": dep, "to": t.id} for t in plan.tasks for dep in t.dependencies]
        }
        self.logger.orchestrator("🗺️ Task DAG structure analyzed",
                                dag_structure=dag_info,
                                level=LogLevel.INFO)
        
        return {
            "ready_tasks": ready_tasks,
            "current_phase": OrchestratorPhase.ALLOCATE_AGENTS.value
        }
    
    async def _allocate_agents(self, state: EnhancedOrchestratorState) -> Dict[str, Any]:
        """Intelligently allocate agents to ready tasks."""
        ready_tasks = state.get("ready_tasks", [])
        available_agents = state.get("available_agents", [])
        plan = state.get("plan")
        
        self.logger.orchestrator("🎯 Allocating agents to ready tasks",
                                ready_task_count=len(ready_tasks),
                                available_agents=len(available_agents),
                                level=LogLevel.INFO)
        
        if not ready_tasks:
            return {"current_phase": OrchestratorPhase.MONITOR_PROGRESS.value}
        
        # Smart agent allocation
        new_assignments = {}
        agent_workloads = state.get("agent_workloads", {})
        
        # Initialize agent workloads
        for agent in available_agents:
            agent_name = agent.get("name", "unknown")
            if agent_name not in agent_workloads:
                agent_workloads[agent_name] = 0
        
        # Get task objects
        task_dict = {task.id: task for task in plan.tasks}
        
        # Allocate ready tasks to least loaded agents
        for task_id in ready_tasks[:self.max_concurrent_tasks]:
            if task_id in state.get("task_assignments", {}):
                continue  # Already assigned
                
            task = task_dict.get(task_id)
            best_agent = self._find_best_agent(task, available_agents, agent_workloads)
            
            if best_agent:
                new_assignments[task_id] = best_agent
                agent_workloads[best_agent] = agent_workloads.get(best_agent, 0) + 1
                
                self.logger.orchestrator(f"✅ Assigned {task_id} → {best_agent}",
                                       task_id=task_id,
                                       agent=best_agent,
                                       workload=agent_workloads[best_agent],
                                       level=LogLevel.SUCCESS)
        
        # Update assignments
        current_assignments = state.get("task_assignments", {})
        current_assignments.update(new_assignments)
        
        return {
            "task_assignments": current_assignments,
            "agent_workloads": agent_workloads,
            "current_phase": OrchestratorPhase.EXECUTE_TASKS.value
        }
    
    async def _execute_tasks(self, state: EnhancedOrchestratorState) -> Dict[str, Any]:
        """Execute assigned tasks."""
        ready_tasks = state.get("ready_tasks", [])
        assignments = state.get("task_assignments", {})
        plan = state.get("plan")
        
        self.logger.orchestrator("⚡ Executing assigned tasks",
                                execution_batch_size=len([t for t in ready_tasks if t in assignments]),
                                level=LogLevel.INFO)
        
        # Execute tasks (simulated for now)
        running_tasks = state.get("running_tasks", set())
        task_results = state.get("task_results", {})
        task_statuses = state.get("task_statuses", {})
        
        task_dict = {task.id: task for task in plan.tasks}
        
        for task_id in ready_tasks:
            if task_id in assignments and task_id not in running_tasks:
                # Start task execution
                running_tasks.add(task_id)
                task_statuses[task_id] = TaskStatus.RUNNING.value
                
                self.logger.orchestrator(f"🏃 Starting task execution: {task_id}",
                                       task_id=task_id,
                                       assigned_agent=assignments[task_id],
                                       level=LogLevel.INFO)
                
                # Emit task start event
                if self.event_bus:
                    await self.event_bus.emit_async(Event(
                        event_type=EventType.TASK_STARTED,
                        source="enhanced_orchestrator",
                        data={
                            "task_id": task_id,
                            "agent": assignments[task_id],
                            "description": task_dict[task_id].description,
                            "timestamp": datetime.now().isoformat()
                        },
                        channel="orchestrator"
                    ))
        
        # Simulate task completion (replace with actual agent execution)
        import random
        for task_id in list(running_tasks):
            if random.random() < 0.3:  # 30% chance to complete per cycle
                # Task completed
                running_tasks.remove(task_id)
                state.get("completed_tasks", set()).add(task_id)
                task_statuses[task_id] = TaskStatus.COMPLETED.value
                task_results[task_id] = {"status": "success", "result": f"Result for {task_id}"}
                
                self.logger.orchestrator(f"✅ Task completed: {task_id}",
                                       task_id=task_id,
                                       execution_time="simulated",
                                       level=LogLevel.SUCCESS)
                
                # Free up agent workload
                agent = assignments[task_id]
                agent_workloads = state.get("agent_workloads", {})
                if agent in agent_workloads:
                    agent_workloads[agent] = max(0, agent_workloads[agent] - 1)
        
        return {
            "running_tasks": running_tasks,
            "task_results": task_results,
            "task_statuses": task_statuses,
            "current_phase": OrchestratorPhase.MONITOR_PROGRESS.value
        }
    
    async def _monitor_progress(self, state: EnhancedOrchestratorState) -> Dict[str, Any]:
        """Monitor execution progress and determine next actions."""
        plan = state.get("plan")
        completed_tasks = state.get("completed_tasks", set())
        failed_tasks = state.get("failed_tasks", set())
        running_tasks = state.get("running_tasks", set())
        
        total_tasks = len(plan.tasks) if plan else 0
        progress = len(completed_tasks) / total_tasks if total_tasks > 0 else 1.0
        
        self.logger.orchestrator("📊 Monitoring execution progress",
                                progress_percent=f"{progress*100:.1f}%",
                                completed=len(completed_tasks),
                                running=len(running_tasks),
                                failed=len(failed_tasks),
                                total=total_tasks,
                                level=LogLevel.INFO)
        
        # Check for newly ready tasks
        newly_ready = []
        task_statuses = state.get("task_statuses", {})
        
        if plan:
            for task in plan.tasks:
                if (task_statuses.get(task.id) == TaskStatus.PENDING.value and 
                    all(dep in completed_tasks for dep in task.dependencies)):
                    newly_ready.append(task.id)
                    task_statuses[task.id] = TaskStatus.READY.value
        
        if newly_ready:
            self.logger.orchestrator(f"🔓 New tasks became ready: {', '.join(newly_ready)}",
                                   newly_ready_count=len(newly_ready),
                                   level=LogLevel.INFO)
        
        # Update ready tasks
        current_ready = state.get("ready_tasks", [])
        all_ready = list(set(current_ready + newly_ready))
        
        return {
            "execution_progress": progress,
            "ready_tasks": all_ready,
            "task_statuses": task_statuses,
            "current_phase": self._determine_next_phase(state)
        }
    
    async def _handle_results(self, state: EnhancedOrchestratorState) -> Dict[str, Any]:
        """Handle completed task results and process outputs."""
        task_results = state.get("task_results", {})
        completed_tasks = state.get("completed_tasks", set())
        
        self.logger.orchestrator("📦 Processing task results",
                                completed_results=len([r for r in task_results.values() if r.get("status") == "success"]),
                                level=LogLevel.INFO)
        
        # Process results (implement actual result handling logic)
        processed_results = {}
        for task_id, result in task_results.items():
            if task_id in completed_tasks:
                processed_results[task_id] = {
                    "status": result.get("status", "unknown"),
                    "data": result.get("result", ""),
                    "processed_at": datetime.now().isoformat()
                }
        
        return {
            "processed_results": processed_results,
            "current_phase": self._determine_next_phase(state)
        }
    
    async def _recover_errors(self, state: EnhancedOrchestratorState) -> Dict[str, Any]:
        """Handle error recovery and retry logic."""
        failed_tasks = state.get("failed_tasks", set())
        error_attempts = state.get("error_recovery_attempts", {})
        
        self.logger.orchestrator("🔧 Processing error recovery",
                                failed_task_count=len(failed_tasks),
                                level=LogLevel.WARNING)
        
        recovery_actions = {}
        for task_id in failed_tasks:
            attempts = error_attempts.get(task_id, 0)
            if attempts < self.max_retry_attempts:
                recovery_actions[task_id] = "retry"
                error_attempts[task_id] = attempts + 1
                
                self.logger.orchestrator(f"🔄 Scheduling retry for {task_id}",
                                       task_id=task_id,
                                       attempt_number=error_attempts[task_id],
                                       level=LogLevel.INFO)
            else:
                recovery_actions[task_id] = "abandon"
                self.logger.orchestrator(f"❌ Abandoning failed task {task_id}",
                                       task_id=task_id,
                                       max_attempts_reached=True,
                                       level=LogLevel.ERROR)
        
        return {
            "error_recovery_attempts": error_attempts,
            "recovery_actions": recovery_actions,
            "current_phase": self._determine_next_phase(state)
        }
    
    async def _finalize_orchestration(self, state: EnhancedOrchestratorState) -> Dict[str, Any]:
        """Finalize orchestration and compile results."""
        completed_tasks = state.get("completed_tasks", set())
        failed_tasks = state.get("failed_tasks", set())
        task_results = state.get("task_results", {})
        start_time = state.get("start_time")
        
        execution_time = (datetime.now() - start_time).total_seconds() if start_time else 0
        
        final_results = {
            "status": "completed" if not failed_tasks else "partial",
            "completed_tasks": list(completed_tasks),
            "failed_tasks": list(failed_tasks),
            "execution_time_seconds": execution_time,
            "task_results": task_results,
            "summary": {
                "total_tasks": len(completed_tasks) + len(failed_tasks),
                "successful": len(completed_tasks),
                "failed": len(failed_tasks),
                "success_rate": len(completed_tasks) / (len(completed_tasks) + len(failed_tasks)) if (completed_tasks or failed_tasks) else 0
            }
        }
        
        self.logger.orchestrator("🎯 Orchestration finalized",
                                final_status=final_results["status"],
                                success_rate=f"{final_results['summary']['success_rate']*100:.1f}%",
                                total_execution_time=f"{execution_time:.1f}s",
                                level=LogLevel.SUCCESS)
        
        if self.event_bus:
            await self.event_bus.emit_async(Event(
                event_type=EventType.TASK_COMPLETED,
                source="enhanced_orchestrator",
                data={
                    "phase": "finalize",
                    "final_results": final_results,
                    "timestamp": datetime.now().isoformat()
                },
                channel="orchestrator"
            ))
        
        return {
            "final_results": final_results,
            "orchestrator_complete": True,
            "current_phase": OrchestratorPhase.COMPLETE.value
        }
    
    def _determine_next_phase(self, state: EnhancedOrchestratorState) -> str:
        """Determine the next orchestration phase based on current state."""
        ready_tasks = state.get("ready_tasks", [])
        running_tasks = state.get("running_tasks", set())
        failed_tasks = state.get("failed_tasks", set())
        completed_tasks = state.get("completed_tasks", set())
        plan = state.get("plan")
        
        total_tasks = len(plan.tasks) if plan else 0
        
        # Check if all tasks are done
        if len(completed_tasks) + len(failed_tasks) >= total_tasks:
            return OrchestratorPhase.FINALIZE.value
        
        # Check if we have failed tasks to recover
        if failed_tasks:
            return OrchestratorPhase.RECOVER_ERRORS.value
        
        # Check if we have completed tasks to handle
        if completed_tasks and state.get("task_results"):
            return OrchestratorPhase.HANDLE_RESULTS.value
        
        # Check if we have ready tasks or are still running
        if ready_tasks or running_tasks:
            return OrchestratorPhase.EXECUTE_TASKS.value
        
        return OrchestratorPhase.MONITOR_PROGRESS.value
    
    def _after_monitor_progress(self, state: EnhancedOrchestratorState) -> str:
        """Determine next step after monitoring progress."""
        return self._determine_next_phase(state)
    
    def _after_handle_results(self, state: EnhancedOrchestratorState) -> str:
        """Determine next step after handling results."""
        return self._determine_next_phase(state)
    
    def _after_recover_errors(self, state: EnhancedOrchestratorState) -> str:
        """Determine next step after error recovery."""
        return self._determine_next_phase(state)
    
    def _find_best_agent(self, task: PlanTask, agents: List[Dict], workloads: Dict[str, int]) -> Optional[str]:
        """Find the best agent for a task based on capabilities and workload."""
        if not agents:
            return None
        
        best_agent = None
        best_score = -1
        
        for agent in agents:
            agent_name = agent.get("name", "unknown")
            agent_caps = set(agent.get("capabilities", []))
            task_caps = set(task.capabilities if hasattr(task, 'capabilities') else [])
            
            # Calculate capability match score
            capability_score = len(agent_caps.intersection(task_caps)) if task_caps else 1
            
            # Factor in workload (prefer less loaded agents)
            workload = workloads.get(agent_name, 0)
            workload_penalty = workload * 0.5
            
            total_score = capability_score - workload_penalty
            
            if total_score > best_score:
                best_score = total_score
                best_agent = agent_name
        
        return best_agent


class EnhancedOrchestrator:
    """
    Enhanced Orchestrator with sophisticated LangGraph brain.
    
    Replaces simple orchestration with adaptive task scheduling,
    intelligent agent allocation, and comprehensive progress monitoring.
    """
    
    def __init__(
        self, 
        model, 
        event_bus: Optional[EventBus] = None,
        max_concurrent_tasks: int = 5
    ):
        self.model = model
        self.event_bus = event_bus
        self.max_concurrent_tasks = max_concurrent_tasks
        self.factory = EnhancedOrchestratorGraphFactory(model, event_bus, max_concurrent_tasks)
        self.compiled_graph = self.factory.create_graph().compile()
        self.logger = get_flow_logger()
    
    async def arun(self, plan: Plan, available_agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced orchestration with LangGraph brain."""
        self.logger.orchestrator("🧠 Enhanced orchestrator brain activated",
                                plan_task_count=len(plan.tasks),
                                available_agents=len(available_agents),
                                level=LogLevel.SUCCESS)
        
        # Initialize state
        initial_state = {
            "plan": plan,
            "thread_id": f"orchestrate_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "available_agents": available_agents
        }
        
        try:
            # Execute enhanced orchestration graph
            final_state = None
            async for chunk in self.compiled_graph.astream(initial_state):
                final_state = chunk
                # Optional: yield intermediate progress
            
            # Extract results
            if final_state and "final_results" in final_state:
                results = final_state["final_results"]
                self.logger.orchestrator("🎯 Enhanced orchestration completed successfully",
                                        final_status=results.get("status", "unknown"),
                                        success_rate=f"{results.get('summary', {}).get('success_rate', 0)*100:.1f}%",
                                        level=LogLevel.SUCCESS)
                return results
            else:
                # Fallback
                self.logger.orchestrator("⚠️ Enhanced orchestration fallback triggered", 
                                        level=LogLevel.WARNING)
                return {"status": "failed", "error": "No results generated"}
                
        except Exception as e:
            self.logger.orchestrator(f"❌ Enhanced orchestration failed: {str(e)}",
                                    error=str(e),
                                    level=LogLevel.ERROR)
            return {"status": "error", "error": str(e)}