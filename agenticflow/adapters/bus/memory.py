from __future__ import annotations

from typing import Dict, List

from ...core.events.bus import EventBus, EventHandler
from ...core.events.event import AgenticEvent


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._subs: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subs.setdefault(event_type, []).append(handler)

    async def publish(self, event: AgenticEvent) -> None:
        for h in self._subs.get(event.event_type, []):
            await h(event)
