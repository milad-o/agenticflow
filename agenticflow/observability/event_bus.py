"""Event bus for observability."""

import asyncio
from typing import List, Dict, Any, Callable, Optional
from .events import Event
from .subscribers import BaseSubscriber


class EventBus:
    """Central event dispatcher for observability."""
    
    def __init__(self):
        self._subscribers: List[BaseSubscriber] = []
        self._event_queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def add_subscriber(self, subscriber: BaseSubscriber) -> None:
        """Add a subscriber to the event bus."""
        self._subscribers.append(subscriber)
    
    def remove_subscriber(self, subscriber: BaseSubscriber) -> None:
        """Remove a subscriber from the event bus."""
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
    
    async def emit_event(self, event: Event) -> None:
        """Emit an event to all subscribers."""
        if not self._running:
            await self._start()
        
        await self._event_queue.put(event)
    
    def emit_event_sync(self, event: Event) -> None:
        """Emit an event synchronously (for immediate processing)."""
        for subscriber in self._subscribers:
            try:
                if hasattr(subscriber, 'handle_event_sync'):
                    subscriber.handle_event_sync(event)
                else:
                    # Fallback to async if sync not available
                    asyncio.create_task(subscriber.handle_event(event))
            except Exception as e:
                print(f"Error in subscriber {subscriber.__class__.__name__}: {e}")
    
    async def _start(self) -> None:
        """Start the event bus processing."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_events())
    
    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                event = await self._event_queue.get()
                await self._dispatch_event(event)
                self._event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing event: {e}")
    
    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch event to all subscribers."""
        for subscriber in self._subscribers:
            try:
                await subscriber.handle_event(event)
            except Exception as e:
                print(f"Error in subscriber {subscriber.__class__.__name__}: {e}")
    
    async def stop(self) -> None:
        """Stop the event bus."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    def get_subscriber_count(self) -> int:
        """Get the number of active subscribers."""
        return len(self._subscribers)
    
    def get_event_queue_size(self) -> int:
        """Get the current event queue size."""
        return self._event_queue.qsize()
    
    def clear_subscribers(self) -> None:
        """Clear all subscribers."""
        self._subscribers.clear()
    
    async def wait_for_empty_queue(self) -> None:
        """Wait for all events in queue to be processed."""
        await self._event_queue.join()


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def reset_global_event_bus() -> None:
    """Reset the global event bus (useful for testing)."""
    global _global_event_bus
    if _global_event_bus:
        asyncio.create_task(_global_event_bus.stop())
    _global_event_bus = None
