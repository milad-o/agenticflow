"""Task Status Tracker for centralized task lifecycle management.

This module provides a centralized system for tracking task status throughout
the entire lifecycle, integrating with the event bus and orchestrator to 
eliminate loops and provide single source of truth for task state.
"""

import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog

from agenticflow.core.events import EventBus, Event, EventType, EventEmitter

logger = structlog.get_logger()


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    ASSIGNED = "assigned" 
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass 
class TaskRecord:
    """Complete task record with full lifecycle tracking."""
    task_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    # Results and context
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress_data: Dict[str, Any] = field(default_factory=dict)
    
    # Execution metadata
    attempt_count: int = 0
    max_attempts: int = 3
    execution_time: Optional[float] = None
    
    def can_execute(self) -> bool:
        """Check if task can be executed."""
        return (
            self.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED] and
            self.attempt_count < self.max_attempts
        )
    
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    def is_active(self) -> bool:
        """Check if task is actively running."""
        return self.status in [TaskStatus.STARTING, TaskStatus.IN_PROGRESS]


class TaskStatusTracker(EventEmitter):
    """Centralized task status tracking system."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        super().__init__("TaskStatusTracker", event_bus)
        self.tasks: Dict[str, TaskRecord] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}  # task_id -> dependents
        self._locks: Dict[str, asyncio.Lock] = {}
        
        # Subscribe to task lifecycle events
        self.event_bus.subscribe(EventType.TASK_STARTED, self._on_task_started, "orchestrator")
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed, "orchestrator") 
        self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed, "orchestrator")
        self.event_bus.subscribe(EventType.TASK_PROGRESS, self._on_task_progress, "orchestrator")
    
    async def create_task(self, task_id: str, description: str, dependencies: List[str] = None) -> TaskRecord:
        """Create a new task record."""
        if task_id in self.tasks:
            logger.warning("Task already exists", task_id=task_id)
            return self.tasks[task_id]
        
        task = TaskRecord(
            task_id=task_id,
            description=description,
            dependencies=dependencies or []
        )
        
        self.tasks[task_id] = task
        self._locks[task_id] = asyncio.Lock()
        
        # Update dependency graph
        for dep in task.dependencies:
            if dep not in self._dependency_graph:
                self._dependency_graph[dep] = set()
            self._dependency_graph[dep].add(task_id)
        
        logger.info("Task created", task_id=task_id, dependencies=task.dependencies)
        
        # Note: Don't emit TASK_STARTED here - only when actually starting execution
        # This is just task creation/registration
        
        return task
    
    async def assign_task(self, task_id: str, agent_name: str) -> bool:
        """Assign task to an agent."""
        if task_id not in self.tasks:
            logger.error("Cannot assign unknown task", task_id=task_id)
            return False
        
        async with self._locks[task_id]:
            task = self.tasks[task_id]
            
            if task.status != TaskStatus.PENDING:
                logger.warning("Task not in pending state for assignment", 
                             task_id=task_id, status=task.status.value)
                return False
            
            if not self._dependencies_satisfied(task_id):
                logger.warning("Dependencies not satisfied for assignment", 
                             task_id=task_id, dependencies=task.dependencies)
                return False
            
            task.status = TaskStatus.ASSIGNED
            task.assigned_agent = agent_name
            task.assigned_at = datetime.utcnow()
            
            logger.info("Task assigned", task_id=task_id, agent=agent_name)
            
            return True
    
    async def start_task(self, task_id: str) -> bool:
        """Mark task as started."""
        if task_id not in self.tasks:
            logger.error("Cannot start unknown task", task_id=task_id)
            return False
        
        async with self._locks[task_id]:
            task = self.tasks[task_id]
            
            # Only start if assigned and dependencies satisfied
            if task.status != TaskStatus.ASSIGNED:
                logger.warning("Task not in assigned state for starting", 
                             task_id=task_id, status=task.status.value)
                return False
                             
            if not self._dependencies_satisfied(task_id):
                logger.warning("Dependencies not satisfied for starting", 
                             task_id=task_id, dependencies=task.dependencies)
                return False
            
            if not task.can_execute():
                logger.warning("Task cannot be executed", 
                             task_id=task_id, status=task.status.value, 
                             attempt_count=task.attempt_count)
                return False
            
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.utcnow()
            task.attempt_count += 1
            
            logger.info("Task started", task_id=task_id, agent=task.assigned_agent, 
                       attempt=task.attempt_count)
            
            return True
    
    async def complete_task(self, task_id: str, result: Dict[str, Any] = None) -> bool:
        """Mark task as completed."""
        if task_id not in self.tasks:
            logger.error("Cannot complete unknown task", task_id=task_id)
            return False
        
        async with self._locks[task_id]:
            task = self.tasks[task_id]
            
            if task.is_terminal():
                logger.debug("Task already in terminal state", 
                             task_id=task_id, status=task.status.value)
                return False
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result or {}
            
            if task.started_at:
                task.execution_time = (task.completed_at - task.started_at).total_seconds()
            
            logger.info("Task completed", task_id=task_id, agent=task.assigned_agent,
                       execution_time=task.execution_time)
            
            # Emit completion event
            await self.emit_event_async(
                EventType.TASK_COMPLETED,
                data={
                    "task_id": task_id,
                    "agent": task.assigned_agent,
                    "result": result,
                    "execution_time": task.execution_time
                },
                channel="orchestrator"
            )
            
            # Check if dependent tasks can now be executed
            await self._notify_dependents(task_id)
            
            return True
    
    async def fail_task(self, task_id: str, error: str) -> bool:
        """Mark task as failed."""
        if task_id not in self.tasks:
            logger.error("Cannot fail unknown task", task_id=task_id)
            return False
        
        async with self._locks[task_id]:
            task = self.tasks[task_id]
            
            if task.is_terminal():
                logger.debug("Task already in terminal state", 
                             task_id=task_id, status=task.status.value)
                return False
            
            task.status = TaskStatus.FAILED
            task.failed_at = datetime.utcnow()
            task.error = error
            
            logger.error("Task failed", task_id=task_id, agent=task.assigned_agent, error=error)
            
            # Emit failure event
            await self.emit_event_async(
                EventType.TASK_FAILED,
                data={
                    "task_id": task_id,
                    "agent": task.assigned_agent,
                    "error": error,
                    "attempt_count": task.attempt_count
                },
                channel="orchestrator"
            )
            
            return True
    
    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """Get task record."""
        return self.tasks.get(task_id)
    
    def get_ready_tasks(self) -> List[TaskRecord]:
        """Get tasks that are ready to be assigned (dependencies satisfied)."""
        ready = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and self._dependencies_satisfied(task.task_id):
                ready.append(task)
        return ready
    
    def get_active_tasks(self) -> List[TaskRecord]:
        """Get currently active tasks."""
        return [task for task in self.tasks.values() if task.is_active()]
    
    def get_completed_tasks(self) -> List[TaskRecord]:
        """Get completed tasks."""
        return [task for task in self.tasks.values() if task.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[TaskRecord]:
        """Get failed tasks.""" 
        return [task for task in self.tasks.values() if task.status == TaskStatus.FAILED]
    
    def is_workflow_complete(self) -> bool:
        """Check if entire workflow is complete (all tasks are terminal)."""
        return all(task.is_terminal() for task in self.tasks.values())
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of workflow status."""
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(1 for task in self.tasks.values() if task.status == status)
        
        total_tasks = len(self.tasks)
        completed_tasks = status_counts.get(TaskStatus.COMPLETED.value, 0)
        failed_tasks = status_counts.get(TaskStatus.FAILED.value, 0)
        
        return {
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "failure_rate": failed_tasks / total_tasks if total_tasks > 0 else 0,
            "is_complete": self.is_workflow_complete()
        }
    
    def _dependencies_satisfied(self, task_id: str) -> bool:
        """Check if all dependencies are satisfied for a task."""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _notify_dependents(self, completed_task_id: str):
        """Notify dependent tasks that a dependency is complete."""
        dependents = self._dependency_graph.get(completed_task_id, set())
        for dependent_id in dependents:
            if self._dependencies_satisfied(dependent_id):
                logger.info("Dependencies satisfied for task", task_id=dependent_id)
                
                # Emit event that task is ready
                await self.emit_event_async(
                    EventType.DATA_AVAILABLE,
                    data={
                        "task_id": dependent_id,
                        "dependencies_completed": True,
                        "completed_dependency": completed_task_id
                    },
                    channel="orchestrator"
                )
    
    # Event handlers  
    def _on_task_started(self, event: Event):
        """Handle task started events from agents."""
        # This handler is for events from agents, not for auto-starting tasks
        # Task starting should be controlled by orchestrator execution flow
        pass
    
    def _on_task_completed(self, event: Event):
        """Handle task completed events from agents."""
        task_id = event.data.get("task_id")
        result = event.data.get("result")
        if task_id and task_id in self.tasks:
            asyncio.create_task(self.complete_task(task_id, result))
    
    def _on_task_failed(self, event: Event):
        """Handle task failed events from agents."""
        task_id = event.data.get("task_id") 
        error = event.data.get("error", "Unknown error")
        if task_id and task_id in self.tasks:
            asyncio.create_task(self.fail_task(task_id, error))
    
    def _on_task_progress(self, event: Event):
        """Handle task progress events."""
        task_id = event.data.get("task_id")
        if task_id and task_id in self.tasks:
            task = self.tasks[task_id]
            task.progress_data.update(event.data.get("progress", {}))
            logger.debug("Task progress updated", task_id=task_id)