from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Tuple
from uuid import uuid4

from .base import CommunicationBus, Message, MessageHandler, BackpressureHook
from ...observability.tracing import inject_trace_context, use_trace_context_from_headers
from ...observability.metrics import get_meter


@asynccontextmanager
async def _async_use_context(headers, handler, message):
    with use_trace_context_from_headers(headers):
        yield await handler(message)


class InMemoryBus(CommunicationBus):
    def __init__(self, *, max_subscribers: int = 1000, on_backpressure: BackpressureHook | None = None) -> None:
        self._subs: Dict[str, List[Tuple[str, MessageHandler]]] = {}
        self._max_subs = max_subscribers
        self._on_backpressure = on_backpressure

    def subscribe(self, topic: str, handler: MessageHandler) -> str:
        sub_id = str(uuid4())
        lst = self._subs.setdefault(topic, [])
        lst.append((sub_id, handler))
        if len(lst) > self._max_subs and self._on_backpressure is not None:
            # fire-and-forget notification
            asyncio.create_task(self._on_backpressure(topic, len(lst)))
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        for topic, lst in list(self._subs.items()):
            self._subs[topic] = [(sid, h) for (sid, h) in lst if sid != subscription_id]
            if not self._subs[topic]:
                self._subs.pop(topic, None)

    async def publish(self, message: Message) -> None:
        # Inject current trace context into headers before delivery
        try:
            inject_trace_context(message.headers)
        except Exception:
            pass
        # Metrics
        meter = get_meter("bus:memory")
        import time as _t
        t0 = _t.perf_counter()
        for (sid, handler) in list(self._subs.get(message.topic, [])):
            # Activate context for handler execution
            try:
                async with _async_use_context(message.headers, handler, message):
                    pass
            except NameError:
                # Fallback for Python <3.10 without async contextmanager; inline
                with use_trace_context_from_headers(message.headers):
                    await handler(message)
        try:
            meter.inc("published")
            meter.record("publish_ms", (_t.perf_counter() - t0) * 1000.0)
        except Exception:
            pass
