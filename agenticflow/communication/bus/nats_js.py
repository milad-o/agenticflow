from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from .base import CommunicationBus, Message, MessageHandler


def _msg_to_bytes(m: Message) -> bytes:
    return json.dumps({
        "topic": m.topic,
        "type": m.type,
        "payload": m.payload,
        "id": m.id,
        "correlation_id": m.correlation_id,
        "reply_to": m.reply_to,
        "headers": m.headers,
    }).encode("utf-8")


def _bytes_to_msg(b: bytes) -> Message:
    d = json.loads(b.decode("utf-8"))
    return Message(
        topic=d["topic"],
        type=d["type"],
        payload=d.get("payload", {}),
        id=d.get("id"),
        correlation_id=d.get("correlation_id"),
        reply_to=d.get("reply_to"),
        headers=d.get("headers", {}),
    )


class NatsJetStreamBus(CommunicationBus):
    """Minimal NATS JetStream PoC adapter."""

    def __init__(self, *, servers: str = "nats://127.0.0.1:4222", stream: str = "AF_TEST", subjects_prefix: str = "topic.", dlq_enabled: bool = True, dlq_suffix: str = ".DLQ", max_handler_retries: int = 3, handler_backoff_ms: int = 100) -> None:
        self.servers = servers
        self.stream = stream
        self.prefix = subjects_prefix
        self._nc = None
        self._js = None
        self._subs: Dict[str, List[Tuple[str, MessageHandler]]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._processed: Dict[str, set[str]] = {}
        self._dlq_enabled = dlq_enabled
        self._dlq_suffix = dlq_suffix
        self._max_handler_retries = max_handler_retries
        self._handler_backoff_ms = handler_backoff_ms

    async def _ensure_js(self):
        if self._js is not None:
            return self._js
        try:
            import nats  # type: ignore
        except Exception as e:
            raise RuntimeError("nats-py is required for NatsJetStreamBus") from e
        self._nc = await nats.connect(servers=self.servers)
        self._js = self._nc.jetstream()
        # Ensure a stream exists that matches prefix
        try:
            await self._js.add_stream(name=self.stream, subjects=[f"{self.prefix}*"])
        except Exception:
            # likely exists
            pass
        return self._js

    async def start(self) -> None:
        await self._ensure_js()

    async def close(self) -> None:
        for t in list(self._tasks.values()):
            t.cancel()
        await asyncio.gather(*list(self._tasks.values()), return_exceptions=True)
        self._tasks.clear()
        if self._nc is not None:
            try:
                await self._nc.close()
            except Exception:
                pass
            self._nc = None
        self._js = None

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
        js = await self._ensure_js()
        subject = message.topic
        # Metrics
        from ...observability.metrics import get_meter
        meter = get_meter("bus:nats_js")
        import time as _t
        t0 = _t.perf_counter()
        try:
            await js.publish(subject, _msg_to_bytes(message))
        finally:
            try:
                meter.inc("published")
                meter.record("publish_ms", (_t.perf_counter() - t0) * 1000.0)
            except Exception:
                pass

    async def _listen_topic(self, topic: str) -> None:
        js = await self._ensure_js()
        durable = f"af_durable_{topic.replace('.', '_')}"
        self._processed.setdefault(topic, set())
        try:
            sub = await js.pull_subscribe(topic, durable=durable)
            while True:
                msgs = await sub.fetch(10, timeout=0.5)
                for msg in msgs:
                    try:
                        m = _bytes_to_msg(msg.data)
                        if m.id in self._processed[topic]:
                            await msg.ack()
                            continue
                        self._processed[topic].add(m.id)
                        for (_, h) in list(self._subs.get(topic, [])):
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
                                                await self._js.publish(topic + self._dlq_suffix, msg.data)
                                            except Exception:
                                                pass
                                        raise
                                    await asyncio.sleep(self._handler_backoff_ms / 1000.0)
                        await msg.ack()
                    except Exception:
                        try:
                            if self._dlq_enabled:
                                await self._js.publish(topic + self._dlq_suffix, msg.data)
                            await msg.ack()
                        except Exception:
                            pass
        except asyncio.CancelledError:
            return
        except Exception:
            await asyncio.sleep(0.05)
            return