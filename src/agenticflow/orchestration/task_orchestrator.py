"""
AgenticFlow Task Orchestrator - Integrated Coordination Engine
===========================================================

This module provides AgenticFlow's core orchestration capabilities:
- Real-time streaming and progress updates
- Interactive task control and interruption
- Multi-agent coordination and communication
- Advanced workflow management with DAGs
- Event-driven architecture with unified messaging

This is the primary orchestration interface for AgenticFlow.
"""

import asyncio
import time
import threading
import weakref
from typing import Dict, List, Set, Optional, Any, Callable, AsyncGenerator, Union
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
import uuid

import structlog
from ..communication.a2a_handler import A2AHandler, A2AMessage, MessageType
from .task_management import TaskNode, TaskState, TaskResult, TaskError, TaskExecutor, RetryPolicy, TaskPriority
from .task_dag import TaskDAG
# Configuration is now integrated directly into TaskOrchestrator

logger = structlog.get_logger(__name__)


class CoordinationEventType(Enum):
    """Types of coordination events."""
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_INTERRUPTED = "task_interrupted"
    COORDINATOR_CONNECTED = "coordinator_connected"
    COORDINATOR_DISCONNECTED = "coordinator_disconnected"
    REAL_TIME_UPDATE = "real_time_update"
    AGENT_COORDINATION = "agent_coordination"
    WORKFLOW_STATUS = "workflow_status"


@dataclass
class CoordinationEvent:
    """Event data for coordination system."""
    event_type: CoordinationEventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    coordinator_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamSubscription:
    """Stream subscription for real-time updates."""
    subscriber_id: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    event_types: Set[CoordinationEventType] = field(default_factory=set)
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True


@dataclass
class ConnectedCoordinator:
    """Information about connected coordinators."""
    coordinator_id: str
    coordinator_type: str  # "human", "agent", "supervisor", "system"
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    subscriptions: Set[str] = field(default_factory=set)
    capabilities: Dict[str, bool] = field(default_factory=dict)


class InteractiveTaskNode(TaskNode):
    """Enhanced TaskNode with interactive capabilities."""
    
    def __init__(self, *args, **kwargs):
        # Extract our custom parameters before calling super()
        self.streaming_enabled = kwargs.pop('streaming_enabled', True)
        self.interruptible = kwargs.pop('interruptible', True)
        
        # Initialize parent class
        super().__init__(*args, **kwargs)
        
        # Add our enhancements
        self.interrupt_flag = threading.Event()
        self.coordination_data: Dict[str, Any] = {}
        self.subscribers: Set[str] = set()
        self.last_stream_update = datetime.now(timezone.utc)
    
    def is_interrupted(self) -> bool:
        """Check if task is interrupted."""
        return self.interrupt_flag.is_set()
    
    def interrupt(self, reason: str = "User interrupt") -> None:
        """Interrupt the task."""
        if self.interruptible:
            self.interrupt_flag.set()
            self.context["interrupt_reason"] = reason


class WorkflowStatus:
    """Workflow status with streaming and coordination capabilities."""
    
    def __init__(self):
        # Core status tracking
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.running_tasks = 0
        self.pending_tasks = 0
        self.cancelled_tasks = 0
        self.interrupted_tasks = 0
        
        # Real-time tracking
        self.active_workers: Dict[str, asyncio.Task] = {}
        self.task_states: Dict[str, TaskState] = {}
        self.progress_callbacks: List[Callable] = []
        self.stream_subscribers: Dict[str, StreamSubscription] = {}
        
        # Coordination tracking
        self.coordination_actions = 0
        self.agent_interactions = 0
        self.coordinator_queries = 0
    
    def update_from_dag(self, dag: TaskDAG) -> None:
        """Update status from DAG with enhanced tracking."""
        self.total_tasks = len(dag.tasks)
        
        # Count by state with enhanced states
        state_counts = {state: 0 for state in TaskState}
        for task in dag.tasks.values():
            state_counts[task.state] += 1
            self.task_states[task.task_id] = task.state
        
        self.completed_tasks = state_counts[TaskState.COMPLETED]
        self.failed_tasks = state_counts[TaskState.FAILED]
        self.running_tasks = state_counts[TaskState.RUNNING]
        self.pending_tasks = state_counts[TaskState.PENDING] + state_counts[TaskState.READY]
        self.cancelled_tasks = state_counts[TaskState.CANCELLED]
        # Count interrupted tasks if they exist
        if hasattr(TaskState, 'INTERRUPTED'):
            self.interrupted_tasks = state_counts.get(TaskState.INTERRUPTED, 0)
    
    def get_progress_percentage(self) -> float:
        """Get overall progress percentage."""
        if self.total_tasks == 0:
            return 100.0
        return (self.completed_tasks / self.total_tasks) * 100.0
    
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return (self.completed_tasks + self.failed_tasks + 
                self.cancelled_tasks + self.interrupted_tasks) >= self.total_tasks
    
    def add_progress_callback(self, callback: Callable) -> None:
        """Add callback for progress updates."""
        self.progress_callbacks.append(callback)
    
    async def notify_progress(self) -> None:
        """Notify all registered callbacks."""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    callback(self)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary with enhanced info."""
        return {
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "running_tasks": self.running_tasks,
            "pending_tasks": self.pending_tasks,
            "cancelled_tasks": self.cancelled_tasks,
            "interrupted_tasks": self.interrupted_tasks,
            "progress_percentage": self.get_progress_percentage(),
            "is_complete": self.is_complete(),
            "active_workers": len(self.active_workers),
            "coordination_actions": self.coordination_actions,
            "agent_interactions": self.agent_interactions,
            "coordinator_queries": self.coordinator_queries,
            "stream_subscribers": len(self.stream_subscribers)
        }


class CoordinationManager:
    """Handles multi-agent coordination and communication."""
    
    def __init__(self, orchestrator_id: str):
        self.orchestrator_id = orchestrator_id
        self.connected_coordinators: Dict[str, ConnectedCoordinator] = {}
        self.stream_subscriptions: Dict[str, StreamSubscription] = {}
        self.event_handlers: Dict[CoordinationEventType, List[Callable]] = {}
        self.coordination_locks: Dict[str, asyncio.Lock] = {}
        self.stream_queues: Dict[str, asyncio.Queue] = {}
        self._background_tasks: Set[asyncio.Task] = set()
    
    def register_event_handler(self, event_type: CoordinationEventType, handler: Callable):
        """Register event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def emit_event(self, event: CoordinationEvent):
        """Emit coordination event."""
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.warning(f"Event handler failed: {e}")
    
    async def connect_coordinator(self, coordinator_id: str, coordinator_type: str, 
                                capabilities: Dict[str, bool] = None) -> bool:
        """Connect a coordinator to the system."""
        coordinator = ConnectedCoordinator(
            coordinator_id=coordinator_id,
            coordinator_type=coordinator_type,
            capabilities=capabilities or {}
        )
        
        self.connected_coordinators[coordinator_id] = coordinator
        self.stream_queues[coordinator_id] = asyncio.Queue()
        
        await self.emit_event(CoordinationEvent(
            event_type=CoordinationEventType.COORDINATOR_CONNECTED,
            coordinator_id=coordinator_id,
            data={"coordinator_type": coordinator_type, "capabilities": capabilities}
        ))
        
        return True
    
    async def disconnect_coordinator(self, coordinator_id: str) -> bool:
        """Disconnect a coordinator."""
        if coordinator_id not in self.connected_coordinators:
            return False
        
        # Remove subscriptions
        to_remove = [sub_id for sub_id, sub in self.stream_subscriptions.items() 
                    if sub.subscriber_id == coordinator_id]
        for sub_id in to_remove:
            del self.stream_subscriptions[sub_id]
        
        del self.connected_coordinators[coordinator_id]
        self.stream_queues.pop(coordinator_id, None)
        
        await self.emit_event(CoordinationEvent(
            event_type=CoordinationEventType.COORDINATOR_DISCONNECTED,
            coordinator_id=coordinator_id
        ))
        
        return True
    
    def create_stream_subscription(self, subscriber_id: str, 
                                 event_types: Set[CoordinationEventType] = None,
                                 task_id: str = None, agent_id: str = None,
                                 filters: Dict[str, Any] = None) -> str:
        """Create stream subscription."""
        subscription_id = str(uuid.uuid4())
        subscription = StreamSubscription(
            subscriber_id=subscriber_id,
            task_id=task_id,
            agent_id=agent_id,
            event_types=event_types or set(),
            filters=filters or {}
        )
        
        self.stream_subscriptions[subscription_id] = subscription
        
        if subscriber_id in self.connected_coordinators:
            self.connected_coordinators[subscriber_id].subscriptions.add(subscription_id)
        
        return subscription_id
    
    async def send_real_time_update(self, update_data: Dict[str, Any], 
                                   task_id: str = None, agent_id: str = None):
        """Send real-time update to subscribers."""
        event = CoordinationEvent(
            event_type=CoordinationEventType.REAL_TIME_UPDATE,
            task_id=task_id,
            agent_id=agent_id,
            data=update_data
        )
        
        # Send to matching subscriptions
        for subscription in self.stream_subscriptions.values():
            if self._matches_subscription(event, subscription):
                coordinator_id = subscription.subscriber_id
                if coordinator_id in self.stream_queues:
                    try:
                        await self.stream_queues[coordinator_id].put(event)
                    except Exception as e:
                        logger.warning(f"Failed to queue update for {coordinator_id}: {e}")
        
        await self.emit_event(event)
    
    def _matches_subscription(self, event: CoordinationEvent, subscription: StreamSubscription) -> bool:
        """Check if event matches subscription."""
        if subscription.event_types and event.event_type not in subscription.event_types:
            return False
        
        if subscription.task_id and event.task_id != subscription.task_id:
            return False
        
        if subscription.agent_id and event.agent_id != subscription.agent_id:
            return False
        
        # Apply additional filters
        for filter_key, filter_value in subscription.filters.items():
            if event.data.get(filter_key) != filter_value:
                return False
        
        return True
    
    async def stream_task_updates(self, coordinator_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream task updates to coordinator."""
        if coordinator_id not in self.stream_queues:
            return
        
        queue = self.stream_queues[coordinator_id]
        
        try:
            while True:
                try:
                    # Wait for update with timeout for heartbeat
                    event = await asyncio.wait_for(queue.get(), timeout=5.0)
                    
                    yield {
                        "type": event.event_type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "task_id": event.task_id,
                        "agent_id": event.agent_id,
                        "coordinator_id": event.coordinator_id,
                        "data": event.data
                    }
                    
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield {
                        "type": "heartbeat",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "coordinator_id": coordinator_id
                    }
                    
        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for coordinator {coordinator_id}")
        except Exception as e:
            logger.error(f"Stream error for coordinator {coordinator_id}: {e}")
    
    async def coordinate_task(self, task_id: str, coordinator_id: str, 
                            coordination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task coordination request."""
        if task_id not in self.coordination_locks:
            self.coordination_locks[task_id] = asyncio.Lock()
        
        async with self.coordination_locks[task_id]:
            try:
                await self.emit_event(CoordinationEvent(
                    event_type=CoordinationEventType.AGENT_COORDINATION,
                    task_id=task_id,
                    coordinator_id=coordinator_id,
                    data=coordination_data
                ))
                
                return {"success": True, "coordination_id": str(uuid.uuid4())}
                
            except Exception as e:
                return {"success": False, "error": str(e)}


class TaskOrchestrator:
    """
    AgenticFlow Task Orchestrator with integrated capabilities.
    
    This is the core orchestration engine that combines:
    - Complex workflow execution with DAGs
    - Real-time streaming and progress updates  
    - Interactive task control and interruption
    - Multi-agent coordination and communication
    - Event-driven architecture
    """
    
    def __init__(self, max_concurrent_tasks: int = 10,
                 default_timeout: Optional[float] = None,
                 default_retry_policy: Optional[RetryPolicy] = None,
                 enable_streaming: bool = True,
                 enable_coordination: bool = True,
                 stream_interval: float = 0.5,
                 coordination_timeout: int = 60):
        
        self.orchestrator_id = str(uuid.uuid4())
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = default_timeout
        self.default_retry_policy = default_retry_policy or RetryPolicy()
        
        # Integrated coordination configuration
        self.stream_interval = stream_interval
        self.coordination_timeout = coordination_timeout
        
        # Core components
        self.dag = TaskDAG()
        self.status = WorkflowStatus()
        self.executors: Dict[str, TaskExecutor] = {}
        
        # Enhanced coordination
        self.coordination = CoordinationManager(self.orchestrator_id)
        self.communication: Optional[A2AHandler] = None
        
        # Execution state
        self.running = False
        self.cancellation_requested = False
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Enhanced tracking
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        self.interrupted_tasks: Set[str] = set()
        self.retry_queue: asyncio.Queue = asyncio.Queue()
        
        # Streaming and coordination
        self.enable_streaming = enable_streaming
        self.enable_coordination = enable_coordination
        self._background_tasks: Set[asyncio.Task] = set()
        
        # Agent registry
        self._registered_agents: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        
        self.logger = logger.bind(component="enhanced_orchestrator", 
                                orchestrator_id=self.orchestrator_id)
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for coordination."""
        self.coordination.register_event_handler(
            CoordinationEventType.TASK_STARTED, 
            self._handle_task_started_event
        )
        self.coordination.register_event_handler(
            CoordinationEventType.TASK_COMPLETED,
            self._handle_task_completed_event
        )
    
    async def _handle_task_started_event(self, event: CoordinationEvent):
        """Handle task started event."""
        self.status.agent_interactions += 1
        self.logger.info(f"Task started: {event.task_id}")
    
    async def _handle_task_completed_event(self, event: CoordinationEvent):
        """Handle task completed event."""
        self.status.coordination_actions += 1
        self.logger.info(f"Task completed: {event.task_id}")
    
    def register_agent(self, agent_id: str, agent_ref: Any) -> None:
        """Register an agent with the orchestrator."""
        self._registered_agents[agent_id] = agent_ref
        self.logger.info(f"Registered agent: {agent_id}")
    
    def add_interactive_task(self, task_id: str, name: str, executor: TaskExecutor,
                           dependencies: Optional[List[str]] = None,
                           streaming_enabled: bool = True,
                           interruptible: bool = True,
                           **task_kwargs) -> InteractiveTaskNode:
        """Add an interactive task to the workflow."""
        
        task = InteractiveTaskNode(
            task_id=task_id,
            name=name,
            timeout=task_kwargs.get('timeout', self.default_timeout),
            retry_policy=task_kwargs.get('retry_policy', self.default_retry_policy),
            streaming_enabled=streaming_enabled,
            interruptible=interruptible,
            **{k: v for k, v in task_kwargs.items() 
               if k not in ['timeout', 'retry_policy', 'streaming_enabled', 'interruptible']}
        )
        
        # Add to DAG
        self.dag.add_task(task)
        
        # Update status to reflect new task
        self.status.update_from_dag(self.dag)
        
        # Store executor
        self.executors[task_id] = executor
        
        # Add dependencies
        if dependencies:
            for dep_id in dependencies:
                if dep_id not in self.dag.tasks:
                    raise ValueError(f"Dependency task '{dep_id}' does not exist")
                self.dag.add_dependency(task_id, dep_id)
        
        self.logger.debug(f"Added interactive task '{task_id}' with {len(dependencies or [])} dependencies")
        return task
    
    async def execute_workflow_with_streaming(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow with real-time streaming."""
        if self.running:
            raise RuntimeError("Workflow is already running")
        
        self.running = True
        self.cancellation_requested = False
        self.status.started_at = datetime.now(timezone.utc)
        
        try:
            # Validate DAG
            is_valid, issues = self.dag.validate_dag()
            if not is_valid:
                raise ValueError(f"Invalid workflow DAG: {issues}")
            
            self.logger.info(f"Starting enhanced workflow with {len(self.dag.tasks)} tasks")
            
            # Start background tasks
            if self.enable_streaming:
                monitor_task = asyncio.create_task(self._stream_workflow_progress())
                self._background_tasks.add(monitor_task)
            
            retry_task = asyncio.create_task(self._retry_worker())
            self._background_tasks.add(retry_task)
            
            # Execute with streaming
            async for update in self._execute_workflow_with_coordination():
                yield update
                
            self.status.completed_at = datetime.now(timezone.utc)
            self.status.update_from_dag(self.dag)
            
            yield {
                "type": "workflow_completed",
                "status": self.status.to_dict(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            yield {
                "type": "workflow_error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            raise
        finally:
            await self._cleanup_background_tasks()
            self.running = False
    
    async def _execute_workflow_with_coordination(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow with coordination capabilities."""
        active_tasks = set()
        
        while not self.cancellation_requested:
            # Update status
            self.status.update_from_dag(self.dag)
            
            # Stream status update
            if self.enable_streaming:
                await self.coordination.send_real_time_update({
                    "update_type": "workflow_status",
                    "status": self.status.to_dict(),
                    "active_tasks": len(active_tasks)
                })
                
                yield {
                    "type": "status_update",
                    "data": self.status.to_dict(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Check completion
            if self.status.is_complete():
                self.logger.info("Enhanced workflow completed")
                break
            
            # Get ready tasks
            ready_tasks = self.dag.get_ready_tasks(self.completed_tasks)
            
            # Start new tasks with coordination
            for task in ready_tasks:
                if len(active_tasks) >= self.max_concurrent_tasks:
                    break
                if task.task_id not in active_tasks:
                    active_tasks.add(task.task_id)
                    
                    # Emit task started event
                    await self.coordination.emit_event(CoordinationEvent(
                        event_type=CoordinationEventType.TASK_STARTED,
                        task_id=task.task_id,
                        data={"name": task.name, "description": task.description}
                    ))
                    
                    asyncio.create_task(self._execute_interactive_task(task, active_tasks))
            
            await asyncio.sleep(0.1)
        
        # Wait for remaining tasks
        while active_tasks and not self.cancellation_requested:
            await asyncio.sleep(0.1)
    
    async def _execute_interactive_task(self, task: InteractiveTaskNode, active_tasks: set):
        """Execute an interactive task with full coordination."""
        try:
            async with self.semaphore:
                if self.cancellation_requested:
                    await task.set_state(TaskState.CANCELLED)
                    return
                
                await task.set_state(TaskState.RUNNING)
                self.status.active_workers[task.task_id] = asyncio.current_task()
                
                # Check if ready to run
                if not task.is_ready(self.completed_tasks):
                    await task.set_state(TaskState.BLOCKED)
                    return
                
                executor = self.executors[task.task_id]
                
                # Execute with streaming progress
                start_time = time.time()
                
                try:
                    # Stream start event
                    if task.streaming_enabled:
                        await self.coordination.send_real_time_update({
                            "update_type": "task_execution_started",
                            "task_name": task.name,
                            "started_at": start_time
                        }, task.task_id)
                    
                    # Execute task with interruption checking
                    result = await self._execute_with_interruption_check(
                        executor, task, start_time
                    )
                    
                    # Handle result
                    task.attempts += 1
                    task.result = result
                    
                    if result.success:
                        await task.set_state(TaskState.COMPLETED)
                        self.completed_tasks.add(task.task_id)
                        
                        # Emit completion event
                        await self.coordination.emit_event(CoordinationEvent(
                            event_type=CoordinationEventType.TASK_COMPLETED,
                            task_id=task.task_id,
                            data={"result": result.to_dict()}
                        ))
                        
                    else:
                        await self._handle_task_failure(task, result.error)
                
                except asyncio.CancelledError:
                    if task.is_interrupted():
                        await task.set_state(TaskState.CANCELLED)
                        self.interrupted_tasks.add(task.task_id)
                        
                        await self.coordination.emit_event(CoordinationEvent(
                            event_type=CoordinationEventType.TASK_INTERRUPTED,
                            task_id=task.task_id,
                            data={"reason": task.context.get("interrupt_reason", "Unknown")}
                        ))
                    else:
                        await task.set_state(TaskState.CANCELLED)
                
        finally:
            active_tasks.discard(task.task_id)
            self.status.active_workers.pop(task.task_id, None)
    
    async def _execute_with_interruption_check(self, executor: TaskExecutor, 
                                             task: InteractiveTaskNode, 
                                             start_time: float) -> TaskResult:
        """Execute task with interruption checking."""
        execution_context = self._build_execution_context(task)
        
        # Create execution task
        execution_task = asyncio.create_task(executor.execute(task, execution_context))
        
        # Monitor for interruption
        while not execution_task.done():
            if task.is_interrupted():
                execution_task.cancel()
                try:
                    await execution_task
                except asyncio.CancelledError:
                    pass
                
                from .task_management import ErrorCategory
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error=TaskError(
                        error_type="InterruptedError",
                        message="Task was interrupted",
                        category=ErrorCategory.LOGIC,
                        timestamp=datetime.now(timezone.utc)
                    ),
                    execution_time=time.time() - start_time
                )
            
            # Stream progress if enabled
            if task.streaming_enabled:
                progress = min(0.9, (time.time() - start_time) / 10.0)  # Estimate progress
                await self.coordination.send_real_time_update({
                    "update_type": "task_progress",
                    "progress": progress,
                    "elapsed_time": time.time() - start_time
                }, task.task_id)
            
            await asyncio.sleep(0.5)  # Check every 500ms
        
        return await execution_task
    
    async def interrupt_task(self, task_id: str, reason: str = "User interrupt") -> bool:
        """Interrupt a specific task."""
        if task_id not in self.dag.tasks:
            return False
        
        task = self.dag.tasks[task_id]
        if isinstance(task, InteractiveTaskNode):
            task.interrupt(reason)
            
            await self.coordination.emit_event(CoordinationEvent(
                event_type=CoordinationEventType.TASK_INTERRUPTED,
                task_id=task_id,
                data={"reason": reason}
            ))
            
            return True
        
        return False
    
    async def interrupt_all_tasks(self, reason: str = "Global interrupt") -> List[str]:
        """Interrupt all running tasks."""
        interrupted_tasks = []
        
        for task in self.dag.tasks.values():
            if isinstance(task, InteractiveTaskNode) and task.state == TaskState.RUNNING:
                task.interrupt(reason)
                interrupted_tasks.append(task.task_id)
        
        self.cancellation_requested = True
        
        for task_id in interrupted_tasks:
            await self.coordination.emit_event(CoordinationEvent(
                event_type=CoordinationEventType.TASK_INTERRUPTED,
                task_id=task_id,
                data={"reason": reason}
            ))
        
        return interrupted_tasks
    
    def create_stream_subscription(self, coordinator_id: str, 
                                 event_types: Set[CoordinationEventType] = None,
                                 task_filters: Dict[str, str] = None) -> str:
        """Create stream subscription for real-time updates."""
        return self.coordination.create_stream_subscription(
            subscriber_id=coordinator_id,
            event_types=event_types,
            task_id=task_filters.get("task_id") if task_filters else None,
            agent_id=task_filters.get("agent_id") if task_filters else None,
            filters=task_filters or {}
        )
    
    async def stream_updates(self, coordinator_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream real-time updates to coordinator."""
        async for update in self.coordination.stream_task_updates(coordinator_id):
            yield update
    
    async def connect_coordinator(self, coordinator_id: str, coordinator_type: str = "human") -> bool:
        """Connect a coordinator for real-time interaction."""
        return await self.coordination.connect_coordinator(coordinator_id, coordinator_type)
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status."""
        return {
            "orchestrator_id": self.orchestrator_id,
            "workflow_status": self.status.to_dict(),
            "coordination": {
                "connected_coordinators": len(self.coordination.connected_coordinators),
                "active_subscriptions": len(self.coordination.stream_subscriptions),
                "coordination_actions": self.status.coordination_actions
            },
            "execution": {
                "running": self.running,
                "cancellation_requested": self.cancellation_requested,
                "background_tasks": len(self._background_tasks)
            },
            "agents": len(self._registered_agents)
        }
    
    async def _stream_workflow_progress(self):
        """Background task for streaming workflow progress."""
        try:
            while self.running:
                # Update and stream status
                self.status.update_from_dag(self.dag)
                await self.status.notify_progress()
                
                # Stream to all subscribers
                await self.coordination.send_real_time_update({
                    "update_type": "workflow_heartbeat",
                    "status": self.status.to_dict()
                })
                
                await asyncio.sleep(self.stream_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
    
    async def _retry_worker(self):
        """Worker for handling task retries."""
        try:
            while self.running:
                try:
                    retry_time, task_id = await asyncio.wait_for(
                        self.retry_queue.get(), timeout=1.0
                    )
                    
                    current_time = time.time()
                    if retry_time > current_time:
                        await asyncio.sleep(retry_time - current_time)
                    
                    if task_id in self.dag.tasks:
                        task = self.dag.tasks[task_id]
                        if task.state == TaskState.RETRYING:
                            await task.set_state(TaskState.PENDING)
                
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            pass
    
    async def _handle_task_failure(self, task: InteractiveTaskNode, error: Optional[TaskError]):
        """Handle task failure with retry logic."""
        if error:
            await task.set_state(TaskState.FAILED, error)
        else:
            await task.set_state(TaskState.FAILED)
        
        if task.can_retry():
            await task.set_state(TaskState.RETRYING)
            retry_delay = task.get_retry_delay()
            retry_time = time.time() + retry_delay
            await self.retry_queue.put((retry_time, task.task_id))
        else:
            self.failed_tasks.add(task.task_id)
            await self.coordination.emit_event(CoordinationEvent(
                event_type=CoordinationEventType.TASK_FAILED,
                task_id=task.task_id,
                data={"error": error.to_dict() if error else None}
            ))
    
    def _build_execution_context(self, task: InteractiveTaskNode) -> Dict[str, Any]:
        """Build execution context for task."""
        context = {
            "task_id": task.task_id,
            "task": task,  # Add task reference for interruption checking
            "workflow_status": self.status.to_dict(),
            "orchestrator_id": self.orchestrator_id
        }
        
        # Add dependency results
        for dep_id in task.dependencies:
            if dep_id in self.completed_tasks:
                dep_task = self.dag.tasks[dep_id]
                if dep_task.result and dep_task.result.success:
                    context[f"{dep_id}_result"] = dep_task.result.result
        
        return context
    
    async def _cleanup_background_tasks(self):
        """Clean up background tasks."""
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._background_tasks.clear()