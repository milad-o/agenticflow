from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Iterable, List

from .event import AgenticEvent


class EventStore(ABC):
    """Persistent, queryable event storage interface."""

    @abstractmethod
    async def append(self, stream_id: str, events: Iterable[AgenticEvent]) -> None: ...

    @abstractmethod
    async def read_stream(self, stream_id: str, from_offset: int = 0) -> AsyncIterator[AgenticEvent]: ...

    @abstractmethod
    async def query_all(self) -> AsyncIterator[AgenticEvent]: ...

    @abstractmethod
    async def replay(self, stream_id: str) -> List[AgenticEvent]: ...
