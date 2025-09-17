"""
Task management system for AgenticFlow.

Provides comprehensive task orchestration with async queues, task tracking,
priorities, dependencies, deadlines, and status management.
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Awaitable

import structlog
from pydantic import BaseModel, Field

from ..config.settings import TaskConfig

logger = structlog.get_logger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_DEPENDENCIES = "waiting_dependencies"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):
    """Task representation with metadata."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Task name or description")
    task_type: str = Field("general", description="Type of task")
    
    # Task content
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task data/parameters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    # Priority and scheduling
    priority: TaskPriority = Field(TaskPriority.NORMAL)
    deadline: Optional[datetime] = Field(None)
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")
    
    # Dependencies
    dependencies: Set[str] = Field(default_factory=set, description="Task IDs this depends on")
    dependents: Set[str] = Field(default_factory=set, description="Task IDs that depend on this")
    
    # Execution metadata
    status: TaskStatus = Field(TaskStatus.PENDING)
    assigned_agent: Optional[str] = Field(None)
    result: Optional[Any] = Field(None)
    error: Optional[str] = Field(None)
    
    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    
    # Retry handling
    retry_count: int = Field(0)
    max_retries: int = Field(3)
    
    def duration(self) -> Optional[float]:
        """Get task execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def is_overdue(self) -> bool:
        """Check if task is past its deadline."""
        if not self.deadline:
            return False
        return datetime.now(timezone.utc) > self.deadline
    
    def can_execute(self, completed_tasks: Set[str]) -> bool:
        """Check if task can be executed (all dependencies met)."""
        return self.dependencies.issubset(completed_tasks)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "status": self.status.value,
            "priority": self.priority.value,
            "assigned_agent": self.assigned_agent,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "duration": self.duration(),
            "is_overdue": self.is_overdue(),
            "retry_count": self.retry_count,
            "result": self.result,
            "error": self.error,
        }


class TaskQueue:
    """Priority-based async task queue with dependency support."""
    
    def __init__(self, maxsize: int = 0) -> None:
        """Initialize task queue."""
        self._tasks: Dict[str, Task] = {}
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize)
        self._completed_tasks: Set[str] = set()
        self._waiting_dependencies: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
    
    async def put(self, task: Task) -> None:
        """Add task to queue."""
        async with self._lock:
            self._tasks[task.id] = task
            
            if task.can_execute(self._completed_tasks):
                task.status = TaskStatus.QUEUED
                priority_value = self._get_priority_value(task)
                await self._queue.put((priority_value, time.time(), task))
            else:
                task.status = TaskStatus.WAITING_DEPENDENCIES
                self._waiting_dependencies[task.id] = task
    
    async def get(self) -> Task:
        """Get next task from queue."""
        _, _, task = await self._queue.get()
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)
        return task
    
    async def task_completed(self, task_id: str, result: Optional[Any] = None, error: Optional[str] = None) -> None:
        """Mark task as completed and check for dependent tasks."""
        async with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = TaskStatus.COMPLETED if not error else TaskStatus.FAILED
                task.completed_at = datetime.now(timezone.utc)
                task.result = result
                task.error = error
                
                if not error:
                    self._completed_tasks.add(task_id)
                    
                    # Check waiting tasks that might now be ready
                    ready_tasks = []
                    for waiting_id, waiting_task in list(self._waiting_dependencies.items()):
                        if waiting_task.can_execute(self._completed_tasks):
                            ready_tasks.append(waiting_task)
                            del self._waiting_dependencies[waiting_id]
                    
                    # Add ready tasks to queue
                    for ready_task in ready_tasks:
                        ready_task.status = TaskStatus.QUEUED
                        priority_value = self._get_priority_value(ready_task)
                        await self._queue.put((priority_value, time.time(), ready_task))
    
    def _get_priority_value(self, task: Task) -> int:
        """Get numeric priority value (lower = higher priority)."""
        priority_map = {
            TaskPriority.URGENT: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3,
        }
        base_priority = priority_map.get(task.priority, 2)
        
        # Boost priority for overdue tasks
        if task.is_overdue():
            base_priority = max(0, base_priority - 1)
        
        return base_priority
    
    def qsize(self) -> int:
        """Get queue size."""
        return self._queue.qsize()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics."""
        status_counts = {}
        for task in self._tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(self._tasks),
            "queued_tasks": self.qsize(),
            "waiting_dependencies": len(self._waiting_dependencies),
            "completed_tasks": len(self._completed_tasks),
            "status_breakdown": status_counts,
        }


class TaskManager:
    """Comprehensive task management system."""
    
    def __init__(self, config: TaskConfig) -> None:
        """Initialize task manager."""
        self.config = config
        self.logger = logger.bind(component="task_manager")
        
        # Task storage and queues
        self._tasks: Dict[str, Task] = {}
        self._task_queue = TaskQueue(maxsize=config.queue_max_size)
        
        # Execution control
        self._running = False
        self._workers: List[asyncio.Task] = []
        self._execution_semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
        
        # Task handlers
        self._task_handlers: Dict[str, Callable[[Task], Awaitable[Any]]] = {}
        
        # Statistics
        self._stats = {
            "total_processed": 0,
            "successful_completions": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0,
        }
    
    async def start(self) -> None:
        """Start the task manager."""
        if self._running:
            return
        
        self._running = True
        
        # Start worker tasks
        for i in range(self.config.max_concurrent_tasks):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker)
        
        self.logger.info(f"Task manager started with {len(self._workers)} workers")
    
    async def stop(self) -> None:
        """Stop the task manager."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to complete
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        self.logger.info("Task manager stopped")
    
    def register_handler(self, task_type: str, handler: Callable[[Task], Awaitable[Any]]) -> None:
        """Register a handler for a specific task type."""
        self._task_handlers[task_type] = handler
        self.logger.debug(f"Registered handler for task type: {task_type}")
    
    async def submit_task(
        self,
        name: str,
        task_type: str = "general",
        payload: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        deadline: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Submit a new task."""
        task = Task(
            name=name,
            task_type=task_type,
            payload=payload or {},
            priority=priority,
            deadline=deadline,
            dependencies=set(dependencies or []),
            **kwargs
        )
        
        self._tasks[task.id] = task
        await self._task_queue.put(task)
        
        self.logger.info(f"Submitted task {task.id}: {name}")
        return task.id
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.WAITING_DEPENDENCIES]:
                task.status = TaskStatus.CANCELLED
                self.logger.info(f"Cancelled task {task_id}")
                return True
        
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with specific status."""
        return [task for task in self._tasks.values() if task.status == status]
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks."""
        return [task for task in self._tasks.values() if task.is_overdue()]
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[Task]:
        """Wait for a task to complete."""
        start_time = time.time()
        
        while self._running:
            task = self.get_task(task_id)
            if not task:
                return None
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return task
            
            if timeout and (time.time() - start_time) > timeout:
                break
            
            await asyncio.sleep(0.1)
        
        return None
    
    async def _worker_loop(self, worker_name: str) -> None:
        """Main worker loop for processing tasks."""
        worker_logger = self.logger.bind(worker=worker_name)
        
        while self._running:
            try:
                # Get next task (with timeout to allow graceful shutdown)
                try:
                    task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Process task with semaphore to limit concurrency
                async with self._execution_semaphore:
                    await self._execute_task(task, worker_logger)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                worker_logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _execute_task(self, task: Task, worker_logger: structlog.BoundLogger) -> None:
        """Execute a single task."""
        task_logger = worker_logger.bind(task_id=task.id, task_name=task.name)
        
        try:
            task_logger.info("Starting task execution")
            
            # Check for timeout
            if self.config.task_timeout > 0:
                result = await asyncio.wait_for(
                    self._call_task_handler(task),
                    timeout=self.config.task_timeout
                )
            else:
                result = await self._call_task_handler(task)
            
            # Mark as completed
            await self._task_queue.task_completed(task.id, result=result)
            
            self._stats["successful_completions"] += 1
            task_logger.info("Task completed successfully")
            
        except asyncio.TimeoutError:
            error_msg = f"Task timed out after {self.config.task_timeout}s"
            await self._handle_task_error(task, error_msg, task_logger)
            
        except Exception as e:
            error_msg = f"Task execution failed: {e}"
            await self._handle_task_error(task, error_msg, task_logger)
        
        finally:
            self._stats["total_processed"] += 1
            self._update_average_execution_time(task)
    
    async def _call_task_handler(self, task: Task) -> Any:
        """Call the appropriate handler for the task."""
        handler = self._task_handlers.get(task.task_type)
        
        if not handler:
            raise ValueError(f"No handler registered for task type: {task.task_type}")
        
        return await handler(task)
    
    async def _handle_task_error(self, task: Task, error_msg: str, task_logger: structlog.BoundLogger) -> None:
        """Handle task execution error with retry logic."""
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # Retry the task
            task_logger.warning(f"Task failed, retrying ({task.retry_count}/{task.max_retries}): {error_msg}")
            
            # Add delay before retry
            await asyncio.sleep(self.config.retry_delay * task.retry_count)
            
            # Reset task status and re-queue
            task.status = TaskStatus.QUEUED
            task.started_at = None
            priority_value = self._task_queue._get_priority_value(task)
            await self._task_queue._queue.put((priority_value, time.time(), task))
        else:
            # Mark as failed
            await self._task_queue.task_completed(task.id, error=error_msg)
            self._stats["failed_tasks"] += 1
            task_logger.error(f"Task failed after {task.max_retries} retries: {error_msg}")
    
    def _update_average_execution_time(self, task: Task) -> None:
        """Update average execution time statistics."""
        duration = task.duration()
        if duration is not None:
            current_avg = self._stats["average_execution_time"]
            total_processed = self._stats["total_processed"]
            
            # Update running average
            self._stats["average_execution_time"] = (
                (current_avg * (total_processed - 1) + duration) / total_processed
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive task manager statistics."""
        queue_stats = self._task_queue.get_statistics()
        
        return {
            **self._stats,
            **queue_stats,
            "running": self._running,
            "active_workers": len([w for w in self._workers if not w.done()]),
            "registered_handlers": list(self._task_handlers.keys()),
        }
    
    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent task history."""
        # Sort by creation time, most recent first
        sorted_tasks = sorted(
            self._tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )
        
        return [task.to_dict() for task in sorted_tasks[:limit]]