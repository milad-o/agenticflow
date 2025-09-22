from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from .base import CommunicationBus, Message, MessageHandler, BackpressureHook
from ...observability.tracing import inject_trace_context, use_trace_context_from_headers
from ...observability.metrics import get_meter


def _msg_to_json(m: Message) -> str:
    return json.dumps({
        "topic": m.topic,
        "type": m.type,
        "payload": m.payload,
        "id": m.id,
        "correlation_id": m.correlation_id,
        "reply_to": m.reply_to,
        "headers": m.headers,
    })


def _json_to_msg(s: str) -> Message:
    d = json.loads(s)
    return Message(
        topic=d["topic"],
        type=d["type"],
        payload=d.get("payload", {}),
        id=d.get("id"),
        correlation_id=d.get("correlation_id"),
        reply_to=d.get("reply_to"),
        headers=d.get("headers", {}),
    )


class RedisBus(CommunicationBus):
    """Minimal PoC Redis-backed CommunicationBus using redis.asyncio Pub/Sub.

    Notes:
    - No hard dependency: if redis.asyncio is unavailable, operations will raise a clear error.
    - Connects lazily on first subscribe/publish (or explicitly via start()).
    - Each subscribed topic spins a background task listening on a Redis Pub/Sub channel of the same name.
    - Correlation id and headers are preserved via JSON serialization.
    """

    def __init__(self, *, url: str = "redis://localhost:6379", on_backpressure: BackpressureHook | None = None) -> None:
        self.url = url
        self._on_backpressure = on_backpressure
        self._client = None  # type: ignore[var-annotated]
        self._pubsubs: Dict[str, Any] = {}
        self._subs: Dict[str, List[Tuple[str, MessageHandler]]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    async def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from redis import asyncio as redis  # type: ignore
        except Exception as e:
            raise RuntimeError("redis.asyncio is required for RedisBus but is not installed") from e
        self._client = redis.from_url(self.url)
        try:
            await self._client.ping()
        except Exception:
            # Allow lazy connectivity; ping failures may just mean server down
            pass
        return self._client

    async def start(self) -> None:
        await self._ensure_client()

    async def close(self) -> None:
        # Cancel listeners
        for topic, task in list(self._tasks.items()):
            task.cancel()
        # Best-effort await cancellations
        await asyncio.gather(*list(self._tasks.values()), return_exceptions=True)
        self._tasks.clear()
        # Close pubsubs
        for ps in list(self._pubsubs.values()):
            try:
                await ps.close()
            except Exception:
                pass
        self._pubsubs.clear()
        # Close client
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None

    def subscribe(self, topic: str, handler: MessageHandler) -> str:
        sub_id = str(uuid4())
        self._subs.setdefault(topic, []).append((sub_id, handler))
        # Launch background listener if not already
        if topic not in self._tasks:
            self._tasks[topic] = asyncio.create_task(self._listen_topic(topic))
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        for topic, lst in list(self._subs.items()):
            self._subs[topic] = [(sid, h) for (sid, h) in lst if sid != subscription_id]
            if not self._subs[topic]:
                # No more local subscribers; stop listening to Redis channel
                self._subs.pop(topic, None)
                task = self._tasks.pop(topic, None)
                if task:
                    task.cancel()
                ps = self._pubsubs.pop(topic, None)
                if ps is not None:
                    # Close pubsub asynchronously
                    asyncio.create_task(self._aclose_pubsub(ps))

    async def _aclose_pubsub(self, pubsub) -> None:
        try:
            await pubsub.close()
        except Exception:
            pass

    async def publish(self, message: Message) -> None:
        client = await self._ensure_client()
        try:
            inject_trace_context(message.headers)
        except Exception:
            pass
        meter = get_meter("bus:redis")
        import time as _t
        t0 = _t.perf_counter()
        data = _msg_to_json(message)
        try:
            await client.publish(message.topic, data)
        finally:
            try:
                meter.inc("published")
                meter.record("publish_ms", (_t.perf_counter() - t0) * 1000.0)
            except Exception:
                pass

    async def _listen_topic(self, topic: str) -> None:
        client = await self._ensure_client()
        try:
            pubsub = client.pubsub()
            await pubsub.subscribe(topic)
            self._pubsubs[topic] = pubsub
            async for item in pubsub.listen():
                if item is None:
                    await asyncio.sleep(0)
                    continue
                # redis-py returns dicts with types: message, subscribe, etc.
                if item.get("type") != "message":
                    continue
                data = item.get("data")
                if isinstance(data, (bytes, bytearray)):
                    data = data.decode("utf-8")
                try:
                    msg = _json_to_msg(str(data))
                except Exception:
                    continue
                for (_, handler) in list(self._subs.get(topic, [])):
                    with use_trace_context_from_headers(msg.headers):
                        await handler(msg)
        except asyncio.CancelledError:
            pass
        except Exception:
            # Background task errors are swallowed to keep PoC simple
            await asyncio.sleep(0.01)
        finally:
            ps = self._pubsubs.pop(topic, None)
            if ps is not None:
                try:
                    await ps.close()
                except Exception:
                    pass
            self._tasks.pop(topic, None)
