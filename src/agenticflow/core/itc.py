"""
Interactive Task Control (ITC) Core Module
==========================================

Core ITC functionality that enables real-time interaction, interruption, and dynamic 
task modification across all types of coordinators - humans, supervisor agents, 
coordinator agents, and other AI systems.

This enables any entity to:
- Query task status in real-time
- Interrupt and modify running tasks
- Have conversational interactions about work
- Coordinate across multiple agents
- Dynamically adjust plans and priorities

Works like a conversation with Claude - any coordinator can interrupt, ask questions,
modify plans, and have natural real-time interaction with AI systems.
"""

import asyncio
import threading
import time
from typing import Dict, List, Optional, Any, Callable, Union, AsyncGenerator, Set
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
import uuid
import weakref
from contextlib import asynccontextmanager
import json

from ..config.settings import ITCConfig


class InterruptedError(Exception):
    """Exception raised when a task is interrupted."""
    pass


class ITCEventType(Enum):
    """Types of ITC events."""
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress" 
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_INTERRUPTED = "task_interrupted"
    COORDINATOR_QUERY = "coordinator_query"
    STATUS_REQUEST = "status_request"
    PLAN_MODIFICATION = "plan_modification"
    AGENT_COORDINATION = "agent_coordination"
    
    # Streaming and real-time events
    STREAM_START = "stream_start"
    STREAM_DATA = "stream_data"
    STREAM_END = "stream_end"
    COORDINATOR_CONNECTED = "coordinator_connected"
    COORDINATOR_DISCONNECTED = "coordinator_disconnected"
    REAL_TIME_UPDATE = "real_time_update"


class ITCStatus(Enum):
    """ITC system status."""
    IDLE = "idle"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    WAITING_FOR_INPUT = "waiting_for_input"
    COORDINATING = "coordinating"


@dataclass
class ITCEvent:
    """ITC event data structure."""
    event_type: ITCEventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    coordinator_id: Optional[str] = None
    coordinator_type: str = "human"  # human, agent, supervisor, coordinator


@dataclass
class StreamSubscription:
    """Represents a streaming subscription for real-time updates."""
    subscriber_id: str
    task_id: Optional[str] = None  # None for global updates
    agent_id: Optional[str] = None  # None for all agents
    event_types: Set[ITCEventType] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True


@dataclass
class ConnectedCoordinator:
    """Represents a connected coordinator for real-time interaction."""
    coordinator_id: str
    coordinator_type: str  # human, agent, supervisor, coordinator
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    subscriptions: Set[str] = field(default_factory=set)  # subscription IDs
    capabilities: Dict[str, bool] = field(default_factory=dict)
    status: str = "active"


@dataclass
class InteractiveTask:
    """Represents a task that can be interacted with and controlled."""
    task_id: str
    description: str
    agent_id: str
    status: str = "running"
    progress: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    interrupt_flag: threading.Event = field(default_factory=threading.Event)
    metadata: Dict[str, Any] = field(default_factory=dict)
    controlling_coordinator: Optional[str] = None
    coordinator_type: str = "system"
    
    # Streaming and real-time features
    streaming_enabled: bool = True
    subscribers: Set[str] = field(default_factory=set)  # coordinator IDs
    last_stream_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ITCEventBus:
    """Event bus for ITC system communication."""
    
    def __init__(self):
        self._subscribers: Dict[ITCEventType, List[Callable]] = {}
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: ITCEventType, callback: Callable[[ITCEvent], None]) -> None:
        """Subscribe to ITC events."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: ITCEventType, callback: Callable) -> None:
        """Unsubscribe from ITC events."""
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [
                    cb for cb in self._subscribers[event_type] if cb != callback
                ]
    
    async def emit(self, event: ITCEvent) -> None:
        """Emit an ITC event to all subscribers."""
        with self._lock:
            callbacks = self._subscribers.get(event.event_type, []).copy()
        
        # Call callbacks asynchronously
        tasks = []
        for callback in callbacks:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(callback(event))
            else:
                # Run sync callbacks in thread pool
                tasks.append(asyncio.get_event_loop().run_in_executor(None, callback, event))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class ITCManager:
    """Core Interactive Task Control manager for real-time coordination.
    
    Enables any coordinator (human, supervisor agent, coordinator agent) to:
    - Query task status in real-time
    - Interrupt and modify running tasks  
    - Have conversational interactions about work
    - Coordinate across multiple agents
    - Dynamically adjust plans and priorities
    """
    
    def __init__(self, config: Optional[ITCConfig] = None):
        self.config = config or ITCConfig()
        self.event_bus = ITCEventBus()
        self.status = ITCStatus.IDLE
        self.active_tasks: Dict[str, InteractiveTask] = {}
        self._agents: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self._lock = threading.RLock()
        self._conversation_history: List[Dict[str, Any]] = []
        self._global_interrupt = threading.Event()
        
        # Streaming and real-time coordination
        self._connected_coordinators: Dict[str, ConnectedCoordinator] = {}
        self._stream_subscriptions: Dict[str, StreamSubscription] = {}
        self._streaming_tasks: Set[str] = set()
        self._stream_queues: Dict[str, asyncio.Queue] = {}  # coordinator_id -> queue
        self._coordination_locks: Dict[str, asyncio.Lock] = {}  # task_id -> lock
        
        # Background streaming
        self._background_streaming_task: Optional[asyncio.Task] = None
        self._background_monitoring_enabled = False
        
        # Statistics
        self._stats = {
            "tasks_started": 0,
            "tasks_completed": 0,
            "tasks_interrupted": 0,
            "coordinator_interactions": 0,
            "agent_queries": 0,
            "human_queries": 0,
            "started_at": datetime.now(timezone.utc)
        }
    
    def register_agent(self, agent_id: str, agent_ref: Any) -> None:
        """Register an agent with ITC system."""
        self._agents[agent_id] = agent_ref
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Get registered agent by ID."""
        return self._agents.get(agent_id)
    
    def register_coordinator(self, coordinator_id: str, coordinator_ref: Any, coordinator_type: str = "agent") -> None:
        """Register a coordinator (supervisor/coordinator agent) with ITC system."""
        self._agents[coordinator_id] = coordinator_ref
        # Could add coordinator-specific tracking here if needed
    
    def get_status(self) -> Dict[str, Any]:
        """Get current ITC system status."""
        with self._lock:
            return {
                "status": self.status.value,
                "active_tasks": len(self.active_tasks),
                "task_details": [
                    {
                        "task_id": task.task_id,
                        "description": task.description[:100],
                        "agent_id": task.agent_id,
                        "status": task.status,
                        "progress": task.progress,
                        "duration": (datetime.now(timezone.utc) - task.started_at).total_seconds(),
                        "controlling_coordinator": task.controlling_coordinator,
                        "coordinator_type": task.coordinator_type
                    }
                    for task in self.active_tasks.values()
                ],
                "global_interrupt": self._global_interrupt.is_set(),
                "conversation_length": len(self._conversation_history),
                "registered_agents": len(self._agents),
                "stats": self._stats.copy(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def start_task(self, 
                        task_id: str, 
                        description: str, 
                        agent_id: str,
                        metadata: Optional[Dict[str, Any]] = None,
                        controlling_coordinator: Optional[str] = None,
                        coordinator_type: str = "system") -> InteractiveTask:
        """Start a new interactive task."""
        task = InteractiveTask(
            task_id=task_id,
            description=description,
            agent_id=agent_id,
            metadata=metadata or {},
            controlling_coordinator=controlling_coordinator,
            coordinator_type=coordinator_type
        )
        
        with self._lock:
            self.active_tasks[task_id] = task
            self.status = ITCStatus.RUNNING
            self._stats["tasks_started"] += 1
        
        # Emit event
        await self.event_bus.emit(ITCEvent(
            event_type=ITCEventType.TASK_STARTED,
            agent_id=agent_id,
            task_id=task_id,
            data={
                "description": description,
                "metadata": metadata,
                "controlling_coordinator": controlling_coordinator,
                "coordinator_type": coordinator_type
            }
        ))
        
        return task
    
    async def update_task_progress(self, task_id: str, progress: float, status_info: Optional[str] = None) -> None:
        """Update task progress with real-time streaming support."""
        task = None
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.progress = progress
                task.last_stream_update = datetime.now(timezone.utc)
                if status_info:
                    task.metadata["status_info"] = status_info
        
        if task:
            # Send real-time update to subscribers
            await self.send_real_time_update(
                update_data={
                    "progress": progress,
                    "status_info": status_info,
                    "update_type": "progress"
                },
                task_id=task_id,
                agent_id=task.agent_id
            )
            
            # Emit progress event
            await self.event_bus.emit(ITCEvent(
                event_type=ITCEventType.TASK_PROGRESS,
                task_id=task_id,
                data={
                    "progress": progress,
                    "status_info": status_info
                }
            ))
    
    async def complete_task(self, task_id: str, result: Optional[Any] = None) -> None:
        """Mark task as completed."""
        task = None
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks.pop(task_id)
                task.status = "completed"
                self._stats["tasks_completed"] += 1
                
                if not self.active_tasks:
                    self.status = ITCStatus.IDLE
        
        if task:
            await self.event_bus.emit(ITCEvent(
                event_type=ITCEventType.TASK_COMPLETED,
                agent_id=task.agent_id,
                task_id=task_id,
                data={"result": result}
            ))
    
    async def interrupt_task(self, task_id: str, reason: str = "User interrupt") -> bool:
        """Interrupt a specific task."""
        task = None
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.interrupt_flag.set()
                task.status = "interrupted"
                task.metadata["interrupt_reason"] = reason
                self._stats["tasks_interrupted"] += 1
        
        if task:
            await self.event_bus.emit(ITCEvent(
                event_type=ITCEventType.TASK_INTERRUPTED,
                agent_id=task.agent_id,
                task_id=task_id,
                data={"reason": reason}
            ))
            return True
        
        return False
    
    async def interrupt_all(self, reason: str = "Global interrupt") -> List[str]:
        """Interrupt all active tasks."""
        interrupted_tasks = []
        
        with self._lock:
            self._global_interrupt.set()
            self.status = ITCStatus.INTERRUPTED
            
            for task_id, task in self.active_tasks.items():
                task.interrupt_flag.set()
                task.status = "interrupted"
                task.metadata["interrupt_reason"] = reason
                interrupted_tasks.append(task_id)
                self._stats["tasks_interrupted"] += 1
        
        # Emit events for each interrupted task
        for task_id in interrupted_tasks:
            task = self.active_tasks[task_id]
            await self.event_bus.emit(ITCEvent(
                event_type=ITCEventType.TASK_INTERRUPTED,
                agent_id=task.agent_id,
                task_id=task_id,
                data={"reason": reason}
            ))
        
        return interrupted_tasks
    
    def clear_interrupts(self) -> None:
        """Clear all interrupt flags."""
        with self._lock:
            self._global_interrupt.clear()
            for task in self.active_tasks.values():
                task.interrupt_flag.clear()
            
            if self.status == ITCStatus.INTERRUPTED:
                self.status = ITCStatus.RUNNING if self.active_tasks else ITCStatus.IDLE
    
    def is_interrupted(self, task_id: Optional[str] = None) -> bool:
        """Check if task or system is interrupted."""
        if self._global_interrupt.is_set():
            return True
        
        if task_id and task_id in self.active_tasks:
            return self.active_tasks[task_id].interrupt_flag.is_set()
        
        return False
    
    async def handle_interaction(self, 
                                query: str, 
                                requestor_id: Optional[str] = None,
                                requestor_type: str = "human") -> Dict[str, Any]:
        """Handle real-time interaction from any coordinator (human, supervisor, agent)."""
        self._stats["coordinator_interactions"] += 1
        if requestor_type == "human":
            self._stats["human_queries"] += 1
        elif requestor_type in ["agent", "supervisor", "coordinator"]:
            self._stats["agent_queries"] += 1
        
        # Add to conversation history
        query_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": f"{requestor_type}_query",
            "content": query,
            "requestor_id": requestor_id,
            "requestor_type": requestor_type
        }
        self._conversation_history.append(query_entry)
        
        # Emit event
        await self.event_bus.emit(ITCEvent(
            event_type=ITCEventType.COORDINATOR_QUERY,
            coordinator_id=requestor_id,
            coordinator_type=requestor_type,
            data={
                "query": query,
                "requestor_type": requestor_type
            }
        ))
        
        # Analyze query and provide response
        response = await self._process_interaction_query(query, requestor_id, requestor_type)
        
        # Add response to history
        response_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "system_response",
            "content": response,
            "requestor_id": requestor_id,
            "requestor_type": requestor_type
        }
        self._conversation_history.append(response_entry)
        
        return {
            "query": query,
            "response": response,
            "timestamp": query_entry["timestamp"],
            "conversation_id": len(self._conversation_history) // 2,
            "requestor_type": requestor_type
        }
    
    async def handle_user_query(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle real-time user query (convenience method for humans)."""
        return await self.handle_interaction(query, user_id, "human")
    
    async def handle_agent_query(self, query: str, agent_id: str) -> Dict[str, Any]:
        """Handle real-time agent query (for supervisor/coordinator agents)."""
        return await self.handle_interaction(query, agent_id, "agent")
    
    async def _process_user_query(self, query: str, user_id: Optional[str] = None) -> str:
        """Process user query and generate response."""
        query_lower = query.lower().strip()
        
        # Handle status queries
        if any(word in query_lower for word in ["status", "progress", "what", "how"]):
            status = self.get_status()
            if status["active_tasks"] == 0:
                return "I'm currently idle. No active tasks running."
            else:
                tasks_info = []
                for task in status["task_details"]:
                    tasks_info.append(
                        f"Task '{task['description']}' is {task['progress']:.0f}% complete "
                        f"(running for {task['duration']:.1f}s)"
                    )
                return f"Currently running {len(tasks_info)} task(s):\n" + "\n".join(tasks_info)
        
        # Handle interrupt requests
        if any(word in query_lower for word in ["stop", "interrupt", "cancel", "halt"]):
            interrupted = await self.interrupt_all("User requested stop")
            if interrupted:
                return f"Interrupted {len(interrupted)} active task(s): {', '.join(interrupted)}"
            else:
                return "No active tasks to interrupt."
        
        # Handle resume requests
        if any(word in query_lower for word in ["resume", "continue", "proceed"]):
            self.clear_interrupts()
            return "Cleared interrupt flags. Tasks can resume."
        
        # Default response
        return f"I understand you asked: '{query}'. I can help with status queries, interrupts, or task management. What would you like to know?"
    
    async def modify_task_plan(self, task_id: str, modifications: Dict[str, Any]) -> bool:
        """Modify an active task's plan or parameters."""
        with self._lock:
            if task_id not in self.active_tasks:
                return False
            
            task = self.active_tasks[task_id]
            task.metadata.update(modifications)
        
        # Emit modification event
        await self.event_bus.emit(ITCEvent(
            event_type=ITCEventType.PLAN_MODIFICATION,
            task_id=task_id,
            data={"modifications": modifications}
        ))
        
        return True
    
    async def connect_coordinator(self, 
                                 coordinator_id: str, 
                                 coordinator_type: str = "agent",
                                 capabilities: Optional[Dict[str, bool]] = None) -> ConnectedCoordinator:
        """Connect a coordinator for real-time interaction."""
        coordinator = ConnectedCoordinator(
            coordinator_id=coordinator_id,
            coordinator_type=coordinator_type,
            capabilities=capabilities or {}
        )
        
        with self._lock:
            self._connected_coordinators[coordinator_id] = coordinator
            # Create stream queue for this coordinator
            self._stream_queues[coordinator_id] = asyncio.Queue(maxsize=1000)
        
        # Enable background monitoring if this is the first coordinator
        if len(self._connected_coordinators) == 1:
            self.enable_background_monitoring()
        
        # Emit connection event
        await self.event_bus.emit(ITCEvent(
            event_type=ITCEventType.COORDINATOR_CONNECTED,
            coordinator_id=coordinator_id,
            data={
                "coordinator_type": coordinator_type,
                "capabilities": capabilities
            }
        ))
        
        return coordinator
    
    async def disconnect_coordinator(self, coordinator_id: str) -> bool:
        """Disconnect a coordinator."""
        with self._lock:
            if coordinator_id not in self._connected_coordinators:
                return False
            
            coordinator = self._connected_coordinators[coordinator_id]
            coordinator.status = "disconnected"
            
            # Clean up subscriptions
            for sub_id in list(coordinator.subscriptions):
                if sub_id in self._stream_subscriptions:
                    del self._stream_subscriptions[sub_id]
            
            # Remove from connected coordinators
            del self._connected_coordinators[coordinator_id]
            
            # Clean up stream queue
            if coordinator_id in self._stream_queues:
                del self._stream_queues[coordinator_id]
        
        # Emit disconnection event
        await self.event_bus.emit(ITCEvent(
            event_type=ITCEventType.COORDINATOR_DISCONNECTED,
            coordinator_id=coordinator_id
        ))
        
        return True
    
    def create_stream_subscription(self, 
                                  coordinator_id: str,
                                  task_id: Optional[str] = None,
                                  agent_id: Optional[str] = None,
                                  event_types: Optional[Set[ITCEventType]] = None) -> str:
        """Create a stream subscription for real-time updates."""
        subscription_id = str(uuid.uuid4())
        
        subscription = StreamSubscription(
            subscriber_id=coordinator_id,
            task_id=task_id,
            agent_id=agent_id,
            event_types=event_types or {ITCEventType.TASK_PROGRESS, ITCEventType.REAL_TIME_UPDATE}
        )
        
        with self._lock:
            self._stream_subscriptions[subscription_id] = subscription
            if coordinator_id in self._connected_coordinators:
                self._connected_coordinators[coordinator_id].subscriptions.add(subscription_id)
        
        return subscription_id
    
    def cancel_stream_subscription(self, subscription_id: str) -> bool:
        """Cancel a stream subscription."""
        with self._lock:
            if subscription_id not in self._stream_subscriptions:
                return False
            
            subscription = self._stream_subscriptions[subscription_id]
            coordinator_id = subscription.subscriber_id
            
            # Remove from coordinator's subscriptions
            if coordinator_id in self._connected_coordinators:
                self._connected_coordinators[coordinator_id].subscriptions.discard(subscription_id)
            
            # Remove subscription
            del self._stream_subscriptions[subscription_id]
        
        return True
    
    async def stream_task_updates(self, coordinator_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream real-time task updates to a coordinator."""
        if coordinator_id not in self._connected_coordinators:
            raise ValueError(f"Coordinator {coordinator_id} not connected")
        
        queue = self._stream_queues.get(coordinator_id)
        if not queue:
            raise ValueError(f"No stream queue for coordinator {coordinator_id}")
        
        try:
            while True:
                # Wait for next update with timeout
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=self.config.stream_interval)
                    yield update
                except asyncio.TimeoutError:
                    # Send heartbeat if no updates
                    yield {
                        "type": "heartbeat",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "coordinator_id": coordinator_id
                    }
                
                # Check if coordinator is still connected
                if coordinator_id not in self._connected_coordinators:
                    break
                    
        except GeneratorExit:
            # Clean cleanup when stream ends
            pass
    
    async def send_real_time_update(self, 
                                   update_data: Dict[str, Any],
                                   task_id: Optional[str] = None,
                                   agent_id: Optional[str] = None) -> None:
        """Send real-time update to subscribed coordinators."""
        update = {
            "type": "real_time_update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_id": agent_id,
            "data": update_data
        }
        
        # Find matching subscriptions
        matching_coordinators = set()
        for subscription in self._stream_subscriptions.values():
            if not subscription.active:
                continue
                
            # Check if subscription matches this update
            if subscription.task_id and subscription.task_id != task_id:
                continue
            if subscription.agent_id and subscription.agent_id != agent_id:
                continue
            if ITCEventType.REAL_TIME_UPDATE not in subscription.event_types:
                continue
                
            matching_coordinators.add(subscription.subscriber_id)
        
        # Send to matching coordinators
        for coordinator_id in matching_coordinators:
            if coordinator_id in self._stream_queues:
                try:
                    await self._stream_queues[coordinator_id].put(update)
                except asyncio.QueueFull:
                    # Handle queue overflow
                    pass
    
    async def coordinate_task(self, 
                            task_id: str, 
                            coordinator_id: str, 
                            coordination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate a task between agents with real-time feedback."""
        if task_id not in self.active_tasks:
            return {"error": f"Task {task_id} not found"}
        
        # Get coordination lock for this task
        if task_id not in self._coordination_locks:
            self._coordination_locks[task_id] = asyncio.Lock()
        
        async with self._coordination_locks[task_id]:
            task = self.active_tasks[task_id]
            
            # Update task with coordination data
            task.metadata.update(coordination_data)
            task.controlling_coordinator = coordinator_id
            
            # Send coordination update to all subscribers
            await self.send_real_time_update(
                update_data={
                    "coordination_action": "task_coordinated",
                    "coordinator_id": coordinator_id,
                    "coordination_data": coordination_data
                },
                task_id=task_id,
                agent_id=task.agent_id
            )
            
            # Emit coordination event
            await self.event_bus.emit(ITCEvent(
                event_type=ITCEventType.AGENT_COORDINATION,
                task_id=task_id,
                coordinator_id=coordinator_id,
                data=coordination_data
            ))
            
            return {
                "success": True,
                "task_id": task_id,
                "coordinator_id": coordinator_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def enable_background_monitoring(self) -> None:
        """Enable background monitoring and streaming."""
        if not self._background_monitoring_enabled:
            self._background_monitoring_enabled = True
            if not self._background_streaming_task:
                self._background_streaming_task = asyncio.create_task(self._background_monitoring_loop())
    
    def disable_background_monitoring(self) -> None:
        """Disable background monitoring and streaming."""
        self._background_monitoring_enabled = False
        if self._background_streaming_task and not self._background_streaming_task.done():
            self._background_streaming_task.cancel()
            self._background_streaming_task = None
    
    async def _background_monitoring_loop(self) -> None:
        """Background monitoring loop for automatic streaming and coordination."""
        try:
            while self._background_monitoring_enabled:
                # Monitor active tasks and send automatic updates
                await self._process_background_updates()
                
                # Check for stale connections and cleanup
                await self._cleanup_stale_connections()
                
                # Sleep for the configured stream interval
                await asyncio.sleep(self.config.stream_interval)
                
        except asyncio.CancelledError:
            # Task was cancelled, cleanup gracefully
            pass
        except Exception as e:
            # Log error but don't crash the monitoring loop
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Background monitoring error: {e}")
    
    async def _process_background_updates(self) -> None:
        """Process background updates for active tasks."""
        current_time = datetime.now(timezone.utc)
        
        for task_id, task in list(self.active_tasks.items()):
            # Check if task needs a status update
            time_since_update = (current_time - task.last_stream_update).total_seconds()
            
            if time_since_update > self.config.stream_interval * 2:  # Send update every 2 intervals
                # Send background status update
                await self.send_real_time_update(
                    update_data={
                        "status": task.status,
                        "progress": task.progress,
                        "duration": (current_time - task.started_at).total_seconds(),
                        "update_type": "background_status",
                        "background": True
                    },
                    task_id=task_id,
                    agent_id=task.agent_id
                )
                
                # Update last stream time
                task.last_stream_update = current_time
    
    async def _cleanup_stale_connections(self) -> None:
        """Cleanup stale coordinator connections."""
        current_time = datetime.now(timezone.utc)
        stale_coordinators = []
        
        for coord_id, coordinator in self._connected_coordinators.items():
            # Consider connection stale if no activity for max_stream_duration
            time_inactive = (current_time - coordinator.last_activity).total_seconds()
            
            if time_inactive > self.config.max_stream_duration:
                stale_coordinators.append(coord_id)
        
        # Disconnect stale coordinators
        for coord_id in stale_coordinators:
            await self.disconnect_coordinator(coord_id)
    
    def get_connected_coordinators(self) -> Dict[str, Dict[str, Any]]:
        """Get list of connected coordinators."""
        with self._lock:
            return {
                coord_id: {
                    "coordinator_type": coord.coordinator_type,
                    "connected_at": coord.connected_at.isoformat(),
                    "last_activity": coord.last_activity.isoformat(),
                    "status": coord.status,
                    "subscriptions": len(coord.subscriptions),
                    "capabilities": coord.capabilities
                }
                for coord_id, coord in self._connected_coordinators.items()
            }
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history."""
        history = self._conversation_history
        if limit:
            history = history[-limit:]
        return history
    
    @asynccontextmanager
    async def interruptible_context(self, task_id: str):
        """Context manager for interruptible operations."""
        task = self.active_tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        try:
            yield task
        finally:
            # Check if interrupted during operation
            if task.interrupt_flag.is_set():
                raise InterruptedError(f"Task {task_id} was interrupted")


# Global ITC manager instance
_itc_manager: Optional[ITCManager] = None


def get_itc_manager() -> ITCManager:
    """Get global Interactive Task Control manager instance."""
    global _itc_manager
    if _itc_manager is None:
        _itc_manager = ITCManager()
    return _itc_manager


def initialize_itc(config: Optional[ITCConfig] = None) -> ITCManager:
    """Initialize global ITC manager with config."""
    global _itc_manager
    _itc_manager = ITCManager(config)
    return _itc_manager




# Decorators and utilities for easy ITC integration

def interruptible(task_id_param: str = "task_id"):
    """Decorator to make async functions interruptible via ITC."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get task_id from parameters
            task_id = kwargs.get(task_id_param)
            if not task_id:
                # Try to extract from args based on function signature
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if task_id_param in param_names:
                    idx = param_names.index(task_id_param)
                    if len(args) > idx:
                        task_id = args[idx]
            
            if task_id:
                itc = get_itc_manager()
                
                # Check for interruption before execution
                if itc.is_interrupted(task_id):
                    raise InterruptedError(f"Task {task_id} was interrupted")
                
                # Execute with periodic interrupt checking
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Mark task as failed if it exists
                    if task_id in itc.active_tasks:
                        await itc.complete_task(task_id, {"error": str(e)})
                    raise
            else:
                # Execute normally if no task_id
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def itc_checkpoint(task_id: str, progress: float, status_info: str = None):
    """Manual checkpoint for ITC progress tracking."""
    async def checkpoint():
        itc = get_itc_manager()
        if itc.is_interrupted(task_id):
            raise InterruptedError(f"Task {task_id} interrupted at checkpoint")
        await itc.update_task_progress(task_id, progress, status_info)
    
    return checkpoint()


