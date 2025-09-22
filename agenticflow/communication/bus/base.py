from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional
from uuid import uuid4

MessageHandler = Callable[["Message"], Awaitable[None]]
BackpressureHook = Callable[[str, int], Awaitable[None]]


@dataclass(frozen=True)
class Message:
    topic: str
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    headers: Dict[str, Any] = field(default_factory=dict)


class CommunicationBus(ABC):
    @abstractmethod
    def subscribe(self, topic: str, handler: MessageHandler) -> str: ...

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None: ...

    @abstractmethod
    async def publish(self, message: Message) -> None: ...

    async def request(self, topic: str, message: Message, *, timeout: float = 5.0) -> Message:
        """Default request/response built on publish/subscribe via reply_to."""
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[Message] = loop.create_future()
        reply_topic = f"_reply.{uuid4()}"
        message = Message(
            topic=topic,
            type=message.type,
            payload=message.payload,
            correlation_id=message.correlation_id or message.id,
            reply_to=reply_topic,
            headers=message.headers,
        )

        sub_id = self.subscribe(reply_topic, _make_once_handler(fut))
        try:
            await self.publish(message)
            return await asyncio.wait_for(fut, timeout=timeout)
        finally:
            self.unsubscribe(sub_id)


def _make_once_handler(fut: asyncio.Future[Message]) -> MessageHandler:
    async def _handler(msg: Message) -> None:
        if not fut.done():
            fut.set_result(msg)
    return _handler
