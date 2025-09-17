"""
Task Management System for AgenticFlow

Provides comprehensive task state tracking, dependency management,
and orchestration capabilities for complex multi-step workflows.
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union
from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger(__name__)


class TaskState(str, Enum):
    """States that a task can be in during execution."""
    PENDING = "pending"           # Task created but not started
    READY = "ready"              # Dependencies satisfied, ready to run
    RUNNING = "running"          # Currently executing
    COMPLETED = "completed"      # Successfully finished
    FAILED = "failed"           # Failed with error
    RETRYING = "retrying"       # Failed but retrying
    CANCELLED = "cancelled"     # Cancelled before completion
    BLOCKED = "blocked"         # Waiting for dependencies
    TIMEOUT = "timeout"         # Exceeded time limit


class TaskPriority(int, Enum):
    """Task execution priorities."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class ErrorCategory(str, Enum):
    """Categories of errors for different retry strategies."""
    TRANSIENT = "transient"     # Network timeouts, temporary failures
    RESOURCE = "resource"       # Memory, CPU, quota issues
    CONFIG = "config"          # Configuration or parameter errors
    LOGIC = "logic"            # Business logic errors
    FATAL = "fatal"            # Unrecoverable errors


@dataclass
class TaskError:
    """Represents an error that occurred during task execution."""
    error_type: str
    message: str
    category: ErrorCategory
    timestamp: datetime
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat(),
            "stack_trace": self.stack_trace,
            "context": self.context
        }


@dataclass
class TaskResult:
    """Result of task execution with metadata."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[TaskError] = None
    execution_time: float = 0.0
    attempts: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None,
            "execution_time": self.execution_time,
            "attempts": self.attempts,
            "metadata": self.metadata
        }


@dataclass
class RetryPolicy:
    """Configuration for task retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_categories: Set[ErrorCategory] = field(
        default_factory=lambda: {ErrorCategory.TRANSIENT, ErrorCategory.RESOURCE}
    )
    
    def should_retry(self, error: TaskError, attempt: int) -> bool:
        """Determine if a task should be retried based on error and attempt count."""
        if attempt >= self.max_attempts:
            return False
        return error.category in self.retry_categories
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay before retry based on attempt number."""
        delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay


class TaskNode:
    """Represents a single task in a workflow with dependencies and state tracking."""
    
    def __init__(
        self,
        task_id: str,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        retry_policy: Optional[RetryPolicy] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.priority = priority
        self.timeout = timeout
        self.retry_policy = retry_policy or RetryPolicy()
        self.context = context or {}
        
        # State tracking
        self.state = TaskState.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.last_error_at: Optional[datetime] = None
        
        # Dependencies
        self.dependencies: Set[str] = set()  # Task IDs this task depends on
        self.dependents: Set[str] = set()    # Task IDs that depend on this task
        
        # Execution tracking
        self.attempts = 0
        self.errors: List[TaskError] = []
        self.result: Optional[TaskResult] = None
        
        # Async execution
        self.future: Optional[asyncio.Future] = None
        self.cancel_requested = False
        
        # Locks
        self._state_lock = asyncio.Lock()
        
        self.logger = logger.bind(task_id=task_id, task_name=name)
    
    async def set_state(self, new_state: TaskState, error: Optional[TaskError] = None) -> None:
        """Thread-safe state transition with logging."""
        async with self._state_lock:
            old_state = self.state
            self.state = new_state
            
            # Update timestamps
            now = datetime.now()
            if new_state == TaskState.RUNNING:
                self.started_at = now
            elif new_state in {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED, TaskState.TIMEOUT}:
                self.completed_at = now
            elif new_state == TaskState.FAILED and error:
                self.last_error_at = now
                self.errors.append(error)
            
            self.logger.info(f"Task state: {old_state} → {new_state}")
    
    def add_dependency(self, task_id: str) -> None:
        """Add a dependency to this task."""
        self.dependencies.add(task_id)
        self.logger.debug(f"Added dependency: {task_id}")
    
    def remove_dependency(self, task_id: str) -> None:
        """Remove a dependency from this task."""
        self.dependencies.discard(task_id)
        self.logger.debug(f"Removed dependency: {task_id}")
    
    def add_dependent(self, task_id: str) -> None:
        """Add a task that depends on this one."""
        self.dependents.add(task_id)
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if task is ready to run (all dependencies completed)."""
        return self.dependencies.issubset(completed_tasks)
    
    def can_retry(self) -> bool:
        """Check if task can be retried based on retry policy."""
        if not self.errors:
            return True
        
        latest_error = self.errors[-1]
        return self.retry_policy.should_retry(latest_error, self.attempts)
    
    def get_retry_delay(self) -> float:
        """Get delay before next retry attempt."""
        return self.retry_policy.get_delay(self.attempts)
    
    def get_execution_time(self) -> Optional[float]:
        """Get total execution time if task has completed."""
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()
    
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state (won't change further)."""
        return self.state in {
            TaskState.COMPLETED, 
            TaskState.CANCELLED, 
            TaskState.TIMEOUT,
            TaskState.FAILED  # Only terminal if no retries left
        } and not self.can_retry()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "state": self.state.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time": self.get_execution_time(),
            "attempts": self.attempts,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "errors": [error.to_dict() for error in self.errors],
            "result": self.result.to_dict() if self.result else None,
            "context": self.context
        }


class TaskExecutor(ABC):
    """Abstract base class for task execution logic."""
    
    @abstractmethod
    async def execute(self, task: TaskNode, context: Dict[str, Any]) -> TaskResult:
        """Execute a task and return the result."""
        pass


class FunctionTaskExecutor(TaskExecutor):
    """Executes tasks using callable functions."""
    
    def __init__(self, func: Callable, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    async def execute(self, task: TaskNode, context: Dict[str, Any]) -> TaskResult:
        """Execute the function with provided arguments."""
        start_time = time.time()
        
        try:
            # Merge context with task context
            merged_context = {**context, **task.context}
            
            # Prepare kwargs with merged context, but avoid parameter collisions
            # Get the function signature to check for parameter name conflicts
            import inspect
            sig = inspect.signature(self.func)
            param_names = list(sig.parameters.keys())
            param_names_set = set(param_names)
            
            # Define reserved system keys that should not be passed to task functions
            reserved_keys = {'task_id', 'task_name', 'task_state', 'created_at', 'started_at', 'completed_at'}
            
            # Determine which parameters are already filled by positional arguments
            num_positional_args = len(self.args)
            positional_param_names = param_names[:num_positional_args]
            positional_param_names_set = set(positional_param_names)
            
            # Check if function accepts **kwargs
            accepts_var_kwargs = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
            
            # Only pass context values that are:
            # 1. Accepted by the function parameter names (or function accepts **kwargs)
            # 2. Not already filled by positional arguments
            # 3. Not already in self.kwargs (constructor kwargs take precedence)
            safe_context = {
                k: v for k, v in merged_context.items() 
                if (k in param_names_set or accepts_var_kwargs)
                and k not in positional_param_names_set
                and k not in self.kwargs
            }
            final_kwargs = {**self.kwargs, **safe_context}
            
            # Execute function (handle both sync and async)
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(*self.args, **final_kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: self.func(*self.args, **final_kwargs)
                )
            
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                execution_time=execution_time,
                attempts=task.attempts + 1
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Categorize error
            error_category = self._categorize_error(e)
            
            task_error = TaskError(
                error_type=type(e).__name__,
                message=str(e),
                category=error_category,
                timestamp=datetime.now(),
                stack_trace=None,  # Could add traceback.format_exc() here
                context={"args": self.args, "kwargs": self.kwargs}
            )
            
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=task_error,
                execution_time=execution_time,
                attempts=task.attempts + 1
            )
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error for retry policy decisions."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Network and connectivity errors
        if any(term in error_message for term in ['timeout', 'connection', 'network', 'unreachable']):
            return ErrorCategory.TRANSIENT
        
        # Resource errors
        if any(term in error_message for term in ['memory', 'disk', 'quota', 'limit']):
            return ErrorCategory.RESOURCE
        
        # Configuration errors
        if any(term in error_message for term in ['config', 'parameter', 'missing', 'invalid']):
            return ErrorCategory.CONFIG
        
        # Logic errors
        if error_type in ['ValueError', 'TypeError', 'AttributeError']:
            return ErrorCategory.LOGIC
        
        # Default to transient for unknown errors
        return ErrorCategory.TRANSIENT