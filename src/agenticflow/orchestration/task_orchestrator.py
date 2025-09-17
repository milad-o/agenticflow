"""
Task Orchestrator for AgenticFlow

Coordinates complex workflows with dependencies, parallel execution,
real-time status tracking, and sophisticated error recovery.
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime
import structlog

from .task_management import (
    TaskNode, TaskState, TaskResult, TaskError, TaskExecutor, 
    FunctionTaskExecutor, ErrorCategory, RetryPolicy
)
from .task_dag import TaskDAG, CyclicDependencyError

logger = structlog.get_logger(__name__)


class WorkflowStatus:
    """Real-time status tracking for workflow execution."""
    
    def __init__(self):
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.running_tasks = 0
        self.pending_tasks = 0
        self.cancelled_tasks = 0
        
        # Real-time tracking
        self.active_workers: Dict[str, asyncio.Task] = {}
        self.task_states: Dict[str, TaskState] = {}
        self.progress_callbacks: List[Callable] = []
    
    def update_from_dag(self, dag: TaskDAG) -> None:
        """Update status from current DAG state."""
        self.total_tasks = len(dag.tasks)
        
        # Count by state
        state_counts = defaultdict(int)
        for task in dag.tasks.values():
            state_counts[task.state] += 1
            self.task_states[task.task_id] = task.state
        
        self.completed_tasks = state_counts[TaskState.COMPLETED]
        self.failed_tasks = state_counts[TaskState.FAILED]
        self.running_tasks = state_counts[TaskState.RUNNING]
        self.pending_tasks = state_counts[TaskState.PENDING] + state_counts[TaskState.READY]
        self.cancelled_tasks = state_counts[TaskState.CANCELLED]
    
    def get_progress_percentage(self) -> float:
        """Get overall progress as percentage."""
        if self.total_tasks == 0:
            return 100.0
        return (self.completed_tasks / self.total_tasks) * 100.0
    
    def is_complete(self) -> bool:
        """Check if workflow is complete (all tasks finished)."""
        return (self.completed_tasks + self.failed_tasks + self.cancelled_tasks) >= self.total_tasks
    
    def add_progress_callback(self, callback: Callable) -> None:
        """Add callback for progress updates."""
        self.progress_callbacks.append(callback)
    
    async def notify_progress(self) -> None:
        """Notify all registered callbacks of progress."""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    callback(self)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary."""
        return {
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "running_tasks": self.running_tasks,
            "pending_tasks": self.pending_tasks,
            "cancelled_tasks": self.cancelled_tasks,
            "progress_percentage": self.get_progress_percentage(),
            "is_complete": self.is_complete(),
            "active_workers": len(self.active_workers)
        }


class TaskOrchestrator:
    """
    Orchestrates complex workflows with sophisticated task management.
    
    Features:
    - Dependency-aware execution
    - Parallel task execution with configurable concurrency
    - Real-time status tracking and progress monitoring
    - Sophisticated retry and error recovery
    - Graceful shutdown and cancellation
    - Performance monitoring and optimization
    """
    
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        default_timeout: Optional[float] = None,
        default_retry_policy: Optional[RetryPolicy] = None
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = default_timeout
        self.default_retry_policy = default_retry_policy or RetryPolicy()
        
        # Core components
        self.dag = TaskDAG()
        self.status = WorkflowStatus()
        self.executors: Dict[str, TaskExecutor] = {}
        
        # Execution state
        self.running = False
        self.cancellation_requested = False
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Tracking
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        self.retry_queue: asyncio.Queue = asyncio.Queue()
        
        self.logger = logger.bind(component="task_orchestrator")
    
    @property
    def task_dag(self) -> TaskDAG:
        """Access to the internal DAG for compatibility."""
        return self.dag
    
    @property
    def tasks(self) -> Dict[str, TaskNode]:
        """Access to tasks for compatibility."""
        return self.dag.tasks
    
    def add_task(
        self,
        task_id: str,
        name: str,
        executor: TaskExecutor,
        dependencies: Optional[List[str]] = None,
        **task_kwargs
    ) -> TaskNode:
        """Add a task to the workflow."""
        # Create task node
        task = TaskNode(
            task_id=task_id,
            name=name,
            timeout=task_kwargs.get('timeout', self.default_timeout),
            retry_policy=task_kwargs.get('retry_policy', self.default_retry_policy),
            **{k: v for k, v in task_kwargs.items() if k not in ['timeout', 'retry_policy']}
        )
        
        # Add to DAG
        self.dag.add_task(task)
        
        # Store executor
        self.executors[task_id] = executor
        
        # Add dependencies
        if dependencies:
            for dep_id in dependencies:
                if dep_id not in self.dag.tasks:
                    raise ValueError(f"Dependency task '{dep_id}' does not exist")
                self.dag.add_dependency(task_id, dep_id)
        
        self.logger.debug(f"Added task '{task_id}' with {len(dependencies or [])} dependencies")
        return task
    
    def add_function_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        **task_kwargs
    ) -> str:
        """Add a function-based task to the workflow."""
        executor = FunctionTaskExecutor(func, *args, **(kwargs or {}))
        self.add_task(task_id, name, executor, dependencies, **task_kwargs)
        return task_id
    
    async def execute_workflow(self) -> Dict[str, Any]:
        """Execute the entire workflow."""
        if self.running:
            raise RuntimeError("Workflow is already running")
        
        self.running = True
        self.cancellation_requested = False
        self.status.started_at = datetime.now()
        
        try:
            # Validate DAG
            is_valid, issues = self.dag.validate_dag()
            if not is_valid:
                raise ValueError(f"Invalid workflow DAG: {issues}")
            
            self.logger.info(f"Starting workflow execution with {len(self.dag.tasks)} tasks")
            
            # Start monitoring and retry workers
            monitor_task = asyncio.create_task(self._monitor_workflow())
            retry_task = asyncio.create_task(self._retry_worker())
            
            # Continuous execution loop that handles retries
            await self._execute_workflow_continuously()
            
            # Clean up
            monitor_task.cancel()
            retry_task.cancel()
            
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
            
            try:
                await retry_task
            except asyncio.CancelledError:
                pass
            
            self.status.completed_at = datetime.now()
            
            # Update final status counts
            self.status.update_from_dag(self.dag)
            
            return self._generate_workflow_result()
        
        finally:
            self.running = False
    
    async def _execute_workflow_continuously(self) -> None:
        """Continuously execute tasks as they become ready, including retries."""
        active_tasks = set()
        
        while not self.cancellation_requested:
            # Update status
            self.status.update_from_dag(self.dag)
            
            # Check if workflow is complete
            if self.status.is_complete():
                self.logger.info("Workflow completed")
                break
            
            # Get ready tasks (properly sorted by priority)
            ready_tasks = self.dag.get_ready_tasks(self.completed_tasks)
            
            # Start new tasks if we have capacity
            for task in ready_tasks:
                if len(active_tasks) >= self.max_concurrent_tasks:
                    break
                if task.task_id not in active_tasks:
                    active_tasks.add(task.task_id)
                    asyncio.create_task(self._execute_and_cleanup_task(task, active_tasks))
            
            # If no active tasks and no ready tasks, check for deadlock
            if not active_tasks and not ready_tasks:
                pending_tasks = [t for t in self.dag.tasks.values() if t.state in {TaskState.PENDING, TaskState.RETRYING}]
                if pending_tasks:
                    self.logger.warning(f"Possible deadlock: {len(pending_tasks)} pending tasks but none ready")
                    resolved = await self._diagnose_deadlock()
                    # If deadlock resolution didn't help, break to avoid infinite loop
                    if not resolved and not any(t.state == TaskState.PENDING for t in self.dag.tasks.values()):
                        self.logger.warning("Breaking execution loop - deadlock detected")
                        break
            
            # Brief sleep to prevent busy waiting
            await asyncio.sleep(0.1)
        
        # Wait for remaining active tasks to complete
        while active_tasks and not self.cancellation_requested:
            await asyncio.sleep(0.1)
    
    async def _execute_and_cleanup_task(self, task: TaskNode, active_tasks: set) -> None:
        """Execute a task and clean up from active set when done."""
        try:
            await self._execute_single_task(task)
        finally:
            active_tasks.discard(task.task_id)
    
    async def _execute_dag(self) -> None:
        """Execute the DAG using level-by-level parallel execution."""
        try:
            execution_levels = self.dag.get_execution_levels()
            self.logger.info(f"Executing {len(execution_levels)} levels with max parallelism of "
                           f"{max(len(level) for level in execution_levels)}")
            
            for level_num, task_ids in enumerate(execution_levels):
                if self.cancellation_requested:
                    break
                
                self.logger.debug(f"Starting execution level {level_num + 1} with {len(task_ids)} tasks")
                
                # Start all tasks in this level
                level_tasks = []
                for task_id in task_ids:
                    if self.cancellation_requested:
                        break
                    
                    task = self.dag.tasks[task_id]
                    if task.state == TaskState.PENDING:
                        level_tasks.append(asyncio.create_task(self._execute_single_task(task)))
                
                # Wait for all tasks in this level to complete
                if level_tasks:
                    await asyncio.gather(*level_tasks, return_exceptions=True)
                
                self.logger.debug(f"Completed execution level {level_num + 1}")
        
        except Exception as e:
            self.logger.error(f"DAG execution failed: {e}")
            await self._cancel_remaining_tasks()
            raise
    
    async def _execute_single_task(self, task: TaskNode) -> None:
        """Execute a single task with full error handling and retry logic."""
        async with self.semaphore:  # Limit concurrency
            if self.cancellation_requested:
                await task.set_state(TaskState.CANCELLED)
                return
            
            await task.set_state(TaskState.RUNNING)
            self.status.active_workers[task.task_id] = asyncio.current_task()
            
            try:
                # Check if ready to run
                if not task.is_ready(self.completed_tasks):
                    await task.set_state(TaskState.BLOCKED)
                    self.logger.warning(f"Task {task.task_id} not ready to run")
                    return
                
                # Execute with timeout
                executor = self.executors[task.task_id]
                execution_context = self._build_execution_context(task)
                
                if task.timeout:
                    result = await asyncio.wait_for(
                        executor.execute(task, execution_context),
                        timeout=task.timeout
                    )
                else:
                    result = await executor.execute(task, execution_context)
                
                # Handle result
                task.attempts += 1
                task.result = result
                
                if result.success:
                    await task.set_state(TaskState.COMPLETED)
                    self.completed_tasks.add(task.task_id)
                    self.logger.info(f"Task {task.task_id} completed successfully")
                else:
                    await self._handle_task_failure(task, result.error)
            
            except asyncio.TimeoutError:
                await self._handle_task_timeout(task)
            except asyncio.CancelledError:
                await task.set_state(TaskState.CANCELLED)
                self.logger.info(f"Task {task.task_id} was cancelled")
            except Exception as e:
                error = TaskError(
                    error_type=type(e).__name__,
                    message=str(e),
                    category=ErrorCategory.FATAL,
                    timestamp=datetime.now()
                )
                await self._handle_task_failure(task, error)
            
            finally:
                self.status.active_workers.pop(task.task_id, None)
    
    async def _handle_task_failure(self, task: TaskNode, error: Optional[TaskError]) -> None:
        """Handle task failure with retry logic."""
        if error:
            await task.set_state(TaskState.FAILED, error)
        else:
            await task.set_state(TaskState.FAILED)
        
        # Check if should retry
        if task.can_retry():
            await task.set_state(TaskState.RETRYING)
            retry_delay = task.get_retry_delay()
            
            self.logger.info(f"Scheduling retry for task {task.task_id} in {retry_delay:.2f}s "
                           f"(attempt {task.attempts + 1}/{task.retry_policy.max_attempts})")
            
            # Schedule retry
            retry_time = time.time() + retry_delay
            await self.retry_queue.put((retry_time, task.task_id))
        else:
            # Mark task as permanently failed
            await task.set_state(TaskState.FAILED)
            self.failed_tasks.add(task.task_id)
            self.logger.error(f"Task {task.task_id} failed permanently after {task.attempts} attempts")
    
    async def _handle_task_timeout(self, task: TaskNode) -> None:
        """Handle task timeout."""
        error = TaskError(
            error_type="TimeoutError",
            message=f"Task exceeded timeout of {task.timeout}s",
            category=ErrorCategory.TRANSIENT,
            timestamp=datetime.now()
        )
        
        await task.set_state(TaskState.TIMEOUT, error)
        
        # Timeout can be retried if policy allows
        if task.can_retry():
            await self._handle_task_failure(task, error)
        else:
            self.failed_tasks.add(task.task_id)
    
    def _build_execution_context(self, task: TaskNode) -> Dict[str, Any]:
        """Build execution context with completed task results."""
        context = {"task_id": task.task_id, "workflow_status": self.status.to_dict()}
        
        # Add results from completed dependencies
        for dep_id in task.dependencies:
            if dep_id in self.completed_tasks:
                dep_task = self.dag.tasks[dep_id]
                if dep_task.result and dep_task.result.success:
                    context[f"{dep_id}_result"] = dep_task.result.result
        
        return context
    
    async def _monitor_workflow(self) -> None:
        """Monitor workflow progress and handle deadlocks."""
        last_progress_time = time.time()
        
        while self.running and not self.cancellation_requested:
            await asyncio.sleep(1.0)
            
            self.status.update_from_dag(self.dag)
            await self.status.notify_progress()
            
            # Check for deadlocks (no progress for too long)
            if self.status.running_tasks == 0 and not self.status.is_complete():
                current_time = time.time()
                if current_time - last_progress_time > 30:  # 30 second deadlock threshold
                    self.logger.warning("Potential deadlock detected - no running tasks but workflow incomplete")
                    await self._diagnose_deadlock()
            else:
                last_progress_time = time.time()
    
    async def _retry_worker(self) -> None:
        """Worker that handles scheduled retries."""
        while self.running and not self.cancellation_requested:
            try:
                # Wait for retry with timeout
                retry_time, task_id = await asyncio.wait_for(self.retry_queue.get(), timeout=1.0)
                
                # Wait until retry time
                current_time = time.time()
                if retry_time > current_time:
                    await asyncio.sleep(retry_time - current_time)
                
                # Check if task still needs retry
                if task_id in self.dag.tasks:
                    task = self.dag.tasks[task_id]
                    if task.state == TaskState.RETRYING:
                        await task.set_state(TaskState.PENDING)
                        # Task will be picked up by next execution cycle
            
            except asyncio.TimeoutError:
                continue  # Check cancellation and loop
            except asyncio.CancelledError:
                break
    
    async def _diagnose_deadlock(self) -> bool:
        """Diagnose and attempt to resolve deadlocks."""
        blocked_tasks = self.dag.get_blocked_tasks(self.completed_tasks)
        resolved_count = 0
        
        if blocked_tasks:
            self.logger.warning(f"Found {len(blocked_tasks)} blocked tasks:")
            for task in blocked_tasks:
                missing_deps = task.dependencies - self.completed_tasks
                failed_deps = missing_deps.intersection(self.failed_tasks)
                
                if failed_deps:
                    self.logger.error(f"Task {task.task_id} blocked by failed dependencies: {failed_deps}")
                    await task.set_state(TaskState.FAILED)
                    self.failed_tasks.add(task.task_id)
                    resolved_count += 1
        
        # Also check for tasks stuck in retry loop for too long
        current_time = time.time()
        for task in self.dag.tasks.values():
            if task.state == TaskState.RETRYING and task.attempts >= task.retry_policy.max_attempts:
                self.logger.error(f"Task {task.task_id} exceeded max retry attempts, marking as failed")
                await task.set_state(TaskState.FAILED)
                self.failed_tasks.add(task.task_id)
                resolved_count += 1
        
        return resolved_count > 0
    
    async def cancel_workflow(self) -> None:
        """Cancel the running workflow gracefully."""
        if not self.running:
            return
        
        self.logger.info("Cancelling workflow...")
        self.cancellation_requested = True
        
        # Cancel all active workers
        await self._cancel_remaining_tasks()
    
    async def _cancel_remaining_tasks(self) -> None:
        """Cancel all remaining tasks."""
        # Cancel active workers
        for task_id, worker in self.status.active_workers.items():
            if not worker.done():
                worker.cancel()
        
        # Mark pending/blocked tasks as cancelled
        for task in self.dag.tasks.values():
            if task.state in {TaskState.PENDING, TaskState.READY, TaskState.BLOCKED}:
                await task.set_state(TaskState.CANCELLED)
    
    def _generate_workflow_result(self) -> Dict[str, Any]:
        """Generate comprehensive workflow execution result."""
        execution_time = None
        if self.status.started_at and self.status.completed_at:
            execution_time = (self.status.completed_at - self.status.started_at).total_seconds()
        
        # Collect task results
        task_results = {}
        for task_id, task in self.dag.tasks.items():
            task_results[task_id] = task.to_dict()
        
        # Calculate success rate
        total_tasks = len(self.dag.tasks)
        success_rate = (self.status.completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        return {
            "workflow_id": id(self),
            "status": self.status.to_dict(),
            "execution_time": execution_time,
            "success_rate": success_rate,
            "dag_stats": self.dag.get_dag_stats(),
            "task_results": task_results,
            "cancelled": self.cancellation_requested,
            "errors": [
                task.errors for task in self.dag.tasks.values() if task.errors
            ]
        }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        self.status.update_from_dag(self.dag)
        return self.status.to_dict()
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        task = self.dag.tasks.get(task_id)
        return task.to_dict() if task else None
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics for the workflow."""
        self.status.update_from_dag(self.dag)
        
        execution_time = None
        if self.status.started_at and self.status.completed_at:
            execution_time = (self.status.completed_at - self.status.started_at).total_seconds()
        elif self.status.started_at:
            execution_time = (datetime.now() - self.status.started_at).total_seconds()
        
        return {
            "total_tasks": self.status.total_tasks,
            "completed_tasks": self.status.completed_tasks,
            "failed_tasks": self.status.failed_tasks,
            "running_tasks": self.status.running_tasks,
            "pending_tasks": self.status.pending_tasks,
            "cancelled_tasks": self.status.cancelled_tasks,
            "execution_time": execution_time or 0.0,
            "success_rate": (self.status.completed_tasks / max(1, self.status.total_tasks)) * 100,
            "progress_percentage": self.status.get_progress_percentage(),
            "is_complete": self.status.is_complete(),
            "active_workers": len(self.status.active_workers)
        }
