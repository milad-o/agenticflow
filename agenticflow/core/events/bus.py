from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from .event import AgenticEvent

EventHandler = Callable[[AgenticEvent], Awaitable[None]]


class EventBus(ABC):
    """Publish/subscribe event bus interface."""

    @abstractmethod
    async def publish(self, event: AgenticEvent) -> None: ...

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None: ...
