from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from .base import CommunicationBus, Message, MessageHandler, BackpressureHook


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


class RedisStreamsBus(CommunicationBus):
    """Redis Streams-based CommunicationBus (PoC).

    Uses XADD/XREADGROUP with a consumer group per topic.
    Idempotency is best-effort via an in-memory set of message IDs per topic.
    """

    def __init__(self, *, url: str = "redis://localhost:6379", group: str = "af_group", on_backpressure: BackpressureHook | None = None, dlq_enabled: bool = True, dlq_suffix: str = ".DLQ", max_handler_retries: int = 3, handler_backoff_ms: int = 100) -> None:
        self.url = url
        self.group = group
        self._on_backpressure = on_backpressure
        self._client = None
        self._tasks: Dict[str, asyncio.Task] = {}
        self._subs: Dict[str, List[Tuple[str, MessageHandler]]] = {}
        self._processed: Dict[str, set[str]] = {}
        self._dlq_enabled = dlq_enabled
        self._dlq_suffix = dlq_suffix
        self._max_handler_retries = max_handler_retries
        self._handler_backoff_ms = handler_backoff_ms

    async def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from redis import asyncio as redis  # type: ignore
        except Exception as e:
            raise RuntimeError("redis.asyncio is required for RedisStreamsBus") from e
        self._client = redis.from_url(self.url)
        return self._client

    async def start(self) -> None:
        await self._ensure_client()

    async def close(self) -> None:
        for t in list(self._tasks.values()):
            t.cancel()
        await asyncio.gather(*list(self._tasks.values()), return_exceptions=True)
        self._tasks.clear()
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None

    def subscribe(self, topic: str, handler: MessageHandler) -> str:
        sub_id = str(uuid4())
        self._subs.setdefault(topic, []).append((sub_id, handler))
        if topic not in self._tasks:
            self._tasks[topic] = asyncio.create_task(self._listen_topic(topic))
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        for topic, lst in list(self._subs.items()):
            self._subs[topic] = [(sid, h) for (sid, h) in lst if sid != subscription_id]
            if not self._subs[topic]:
                self._subs.pop(topic, None)
                task = self._tasks.pop(topic, None)
                if task:
                    task.cancel()

    async def publish(self, message: Message) -> None:
        client = await self._ensure_client()
        # Metrics
        from ...observability.metrics import get_meter
        meter = get_meter("bus:redis_streams")
        import time as _t
        t0 = _t.perf_counter()
        try:
            # Ensure group exists
            try:
                await client.xgroup_create(name=message.topic, groupname=self.group, id="$", mkstream=True)
            except Exception:
                # Group may already exist
                pass
            await client.xadd(message.topic, {"data": _msg_to_json(message)})
        finally:
            try:
                meter.inc("published")
                meter.record("publish_ms", (_t.perf_counter() - t0) * 1000.0)
            except Exception:
                pass

    async def _listen_topic(self, topic: str) -> None:
        client = await self._ensure_client()
        # Ensure group exists
        try:
            await client.xgroup_create(name=topic, groupname=self.group, id="$", mkstream=True)
        except Exception:
            pass
        consumer = f"{self.group}-{uuid4()}"
        self._processed.setdefault(topic, set())
        try:
            while True:
                streams = {topic: ">"}
                resp = await client.xreadgroup(self.group, consumer, streams, count=10, block=500)
                if not resp:
                    await asyncio.sleep(0)
                    continue
                # resp is list of (stream, [(id, {field: value}), ...])
                for (_stream, entries) in resp:
                    for (msg_id, fields) in entries:
                        try:
                            data = fields.get("data")
                            if isinstance(data, (bytes, bytearray)):
                                data = data.decode("utf-8")
                            m = _json_to_msg(str(data))
                            # idempotency by message.id
                            if m.id in self._processed[topic]:
                                await client.xack(topic, self.group, msg_id)
                                continue
                            self._processed[topic].add(m.id)
                            for (_, h) in list(self._subs.get(topic, [])):
                                # Retry handler on failure
                                tries = 0
                                while True:
                                    try:
                                        await h(m)
                                        break
                                    except Exception:
                                        tries += 1
                                        if tries > self._max_handler_retries:
                                            if self._dlq_enabled:
                                                try:
                                                    await client.xadd(topic + self._dlq_suffix, {"data": fields.get("data")})
                                                except Exception:
                                                    pass
                                            raise
                                        await asyncio.sleep(self._handler_backoff_ms / 1000.0)
                            await client.xack(topic, self.group, msg_id)
                        except Exception:
                            # Send to DLQ and ack to avoid loops
                            try:
                                if self._dlq_enabled:
                                    await client.xadd(topic + self._dlq_suffix, {"data": fields.get("data")})
                                await client.xack(topic, self.group, msg_id)
                            except Exception:
                                pass
        except asyncio.CancelledError:
            return

    async def drain_dlq(self, topic: str, handler: MessageHandler, *, max_messages: int = 100) -> int:
        """Drain up to max_messages from the DLQ for the given topic and invoke handler per message.
        Returns number of messages processed.
        """
        client = await self._ensure_client()
        processed = 0
        name = topic + self._dlq_suffix
        try:
            resp = await client.xread({name: "0-0"}, count=max_messages, block=10)
            if not resp:
                return 0
            for (_stream, entries) in resp:
                for (_id, fields) in entries:
                    data = fields.get("data")
                    if isinstance(data, (bytes, bytearray)):
                        data = data.decode("utf-8")
                    m = _json_to_msg(str(data))
                    await handler(m)
                    processed += 1
            return processed
        except Exception:
            return processed
        except Exception:
            await asyncio.sleep(0.05)
            return