from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from ...core.events.event import AgenticEvent
from ...core.events.store import EventStore


class InMemoryEventStore(EventStore):
    def __init__(self) -> None:
        # stream_id -> list of events
        self._streams: Dict[str, List[AgenticEvent]] = {}

    async def append(self, stream_id: str, events: Iterable[AgenticEvent]) -> None:
        self._streams.setdefault(stream_id, []).extend(list(events))

    async def read_stream(self, stream_id: str, from_offset: int = 0):
        for ev in self._streams.get(stream_id, [])[from_offset:]:
            yield ev

    async def query_all(self):
        for _, events in self._streams.items():
            for ev in events:
                yield ev

    async def replay(self, stream_id: str) -> List[AgenticEvent]:
        return list(self._streams.get(stream_id, []))
