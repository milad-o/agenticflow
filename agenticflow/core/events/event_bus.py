"""Event Bus system for agent coordination and task lifecycle management.

The Event Bus enables decoupled communication between agents and orchestrators
through event-driven architecture. Agents emit events about their status,
task completion, and data availability, while orchestrators subscribe to
coordinate workflows efficiently.
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import structlog
from datetime import datetime
import uuid

logger = structlog.get_logger()


class EventType(Enum):
    """Standard event types for agent coordination."""
    
    # Task lifecycle events
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_PROGRESS = "task.progress"
    
    # Data flow events
    DATA_AVAILABLE = "data.available"
    DATA_PROCESSED = "data.processed"
    DATA_ERROR = "data.error"
    
    # Agent coordination events
    AGENT_READY = "agent.ready"
    AGENT_BUSY = "agent.busy"
    AGENT_ERROR = "agent.error"
    
    # System events
    FLOW_STARTED = "flow.started"
    FLOW_COMPLETED = "flow.completed"
    FLOW_ERROR = "flow.error"


@dataclass
class Event:
    """Event message containing coordination information."""
    
    event_type: EventType
    source: str  # Agent or component name
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target: Optional[str] = None  # Specific target agent/component
    channel: str = "default"  # Event channel for filtering


class EventBus:
    """Central event bus for agent coordination."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._async_subscribers: Dict[str, List[Callable[[Event], Any]]] = {}
        self._channels: Dict[str, Dict[str, List[Callable]]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        
    def subscribe(self, event_type: Union[EventType, str], callback: Callable[[Event], None], channel: str = "default"):
        """Subscribe to events of a specific type."""
        event_key = event_type.value if isinstance(event_type, EventType) else event_type
        
        if channel not in self._channels:
            self._channels[channel] = {}
        if event_key not in self._channels[channel]:
            self._channels[channel][event_key] = []
        
        self._channels[channel][event_key].append(callback)
        logger.info("Event subscription added", event_type=event_key, channel=channel)
    
    def subscribe_async(self, event_type: Union[EventType, str], callback: Callable[[Event], Any], channel: str = "default"):
        """Subscribe to events with async callback."""
        event_key = event_type.value if isinstance(event_type, EventType) else event_type
        
        if event_key not in self._async_subscribers:
            self._async_subscribers[event_key] = []
        
        self._async_subscribers[event_key].append(callback)
        logger.info("Async event subscription added", event_type=event_key, channel=channel)
    
    def emit(self, event: Event):
        """Emit an event to all subscribers."""
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        logger.info("Event emitted", 
                   event_type=event.event_type.value, 
                   source=event.source, 
                   channel=event.channel,
                   event_id=event.event_id)
        
        # Notify channel-specific subscribers
        channel_subs = self._channels.get(event.channel, {})
        event_subs = channel_subs.get(event.event_type.value, [])
        
        for callback in event_subs:
            try:
                callback(event)
            except Exception as e:
                logger.error("Event callback failed", 
                           event_type=event.event_type.value,
                           error=str(e))
    
    async def emit_async(self, event: Event):
        """Emit event and handle async subscribers."""
        self.emit(event)  # Handle sync subscribers first
        
        # Handle async subscribers
        async_subs = self._async_subscribers.get(event.event_type.value, [])
        if async_subs:
            await asyncio.gather(*[
                self._safe_async_call(callback, event) for callback in async_subs
            ])
    
    async def _safe_async_call(self, callback: Callable, event: Event):
        """Safely call async callback with error handling."""
        try:
            await callback(event)
        except Exception as e:
            logger.error("Async event callback failed",
                        event_type=event.event_type.value,
                        error=str(e))
    
    def get_events(self, 
                   event_type: Optional[Union[EventType, str]] = None,
                   source: Optional[str] = None,
                   channel: Optional[str] = None,
                   limit: int = 100) -> List[Event]:
        """Query event history with filters."""
        events = self._event_history[-limit:]
        
        if event_type:
            type_value = event_type.value if isinstance(event_type, EventType) else event_type
            events = [e for e in events if e.event_type.value == type_value]
        
        if source:
            events = [e for e in events if e.source == source]
        
        if channel:
            events = [e for e in events if e.channel == channel]
        
        return events
    
    def clear_history(self):
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")


# Global event bus instance
_global_event_bus = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


class EventEmitter:
    """Mixin for components that emit events."""
    
    def __init__(self, name: str, event_bus: Optional[EventBus] = None):
        self.name = name
        self.event_bus = event_bus or get_event_bus()
    
    def emit_event(self, event_type: EventType, data: Dict[str, Any] = None, 
                   channel: str = "default", target: Optional[str] = None):
        """Emit an event."""
        event = Event(
            event_type=event_type,
            source=self.name,
            data=data or {},
            channel=channel,
            target=target
        )
        self.event_bus.emit(event)
        return event
    
    async def emit_event_async(self, event_type: EventType, data: Dict[str, Any] = None,
                              channel: str = "default", target: Optional[str] = None):
        """Emit an event asynchronously."""
        event = Event(
            event_type=event_type,
            source=self.name,
            data=data or {},
            channel=channel,
            target=target
        )
        await self.event_bus.emit_async(event)
        return event


class TaskLifecycleManager:
    """Manages task lifecycle through events."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
        # Subscribe to task lifecycle events
        self.event_bus.subscribe(EventType.TASK_STARTED, self._on_task_started, "tasks")
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed, "tasks")
        self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed, "tasks")
    
    def _on_task_started(self, event: Event):
        """Handle task started event."""
        task_id = event.data.get("task_id")
        if task_id:
            self.active_tasks[task_id] = {
                "status": "running",
                "agent": event.source,
                "started_at": event.timestamp,
                "data": event.data
            }
    
    def _on_task_completed(self, event: Event):
        """Handle task completed event."""
        task_id = event.data.get("task_id")
        if task_id and task_id in self.active_tasks:
            self.active_tasks[task_id].update({
                "status": "completed",
                "completed_at": event.timestamp,
                "result": event.data.get("result")
            })
    
    def _on_task_failed(self, event: Event):
        """Handle task failed event.""" 
        task_id = event.data.get("task_id")
        if task_id and task_id in self.active_tasks:
            self.active_tasks[task_id].update({
                "status": "failed",
                "failed_at": event.timestamp,
                "error": event.data.get("error")
            })
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task."""
        return self.active_tasks.get(task_id)
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all active tasks."""
        return {tid: info for tid, info in self.active_tasks.items() 
                if info["status"] == "running"}
    
    def get_completed_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all completed tasks."""
        return {tid: info for tid, info in self.active_tasks.items() 
                if info["status"] == "completed"}