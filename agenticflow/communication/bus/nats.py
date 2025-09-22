from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, List, Tuple
from uuid import uuid4

from .base import CommunicationBus, Message, MessageHandler, BackpressureHook
from ...observability.tracing import inject_trace_context, use_trace_context_from_headers
from ...observability.metrics import get_meter


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


class NatsBus(CommunicationBus):
    """Minimal PoC NATS-backed CommunicationBus using nats-py.

    - Lazy connection via start() or on first publish/subscribe
    - JSON message encoding preserving correlation and headers
    """

    def __init__(self, *, servers: str = "nats://127.0.0.1:4222", on_backpressure: BackpressureHook | None = None) -> None:
        self.servers = servers
        self._on_backpressure = on_backpressure
        self._client = None  # type: ignore[var-annotated]
        self._subs: Dict[str, List[Tuple[str, MessageHandler]]] = {}
        self._nats_sub_ids: Dict[str, int] = {}

    async def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            import nats  # type: ignore
        except Exception as e:
            raise RuntimeError("nats-py is required for NatsBus but is not installed") from e
        self._client = await nats.connect(servers=self.servers)
        return self._client

    async def start(self) -> None:
        await self._ensure_client()

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None
        self._subs.clear()
        self._nats_sub_ids.clear()

    def subscribe(self, topic: str, handler: MessageHandler) -> str:
        sub_id = str(uuid4())
        self._subs.setdefault(topic, []).append((sub_id, handler))
        # Ensure a NATS subscription exists for this topic
        if topic not in self._nats_sub_ids:
            asyncio.create_task(self._subscribe_topic_with_nats(topic))
        return sub_id

    async def _subscribe_topic_with_nats(self, topic: str) -> None:
        nc = await self._ensure_client()

        async def _nats_handler(msg):
            try:
                message = _bytes_to_msg(msg.data)
                # NATS uses reply subject; map to Message.reply_to for consumers
                if msg.reply:
                    message = Message(
                        topic=message.topic,
                        type=message.type,
                        payload=message.payload,
                        id=message.id,
                        correlation_id=message.correlation_id,
                        reply_to=msg.reply,
                        headers=message.headers,
                    )
                for (_, h) in list(self._subs.get(topic, [])):
                    with use_trace_context_from_headers(message.headers):
                        await h(message)
            except Exception:
                pass

        sid = await nc.subscribe(topic, cb=_nats_handler)
        self._nats_sub_ids[topic] = sid

    def unsubscribe(self, subscription_id: str) -> None:
        for topic, lst in list(self._subs.items()):
            self._subs[topic] = [(sid, h) for (sid, h) in lst if sid != subscription_id]
            if not self._subs[topic]:
                self._subs.pop(topic, None)
                sid = self._nats_sub_ids.pop(topic, None)
                if sid is not None:
                    asyncio.create_task(self._drain_topic_subscription(topic, sid))

    async def _drain_topic_subscription(self, topic: str, sid: int) -> None:
        try:
            nc = await self._ensure_client()
            await nc.unsubscribe(sid)
        except Exception:
            pass

    async def publish(self, message: Message) -> None:
        nc = await self._ensure_client()
        try:
            inject_trace_context(message.headers)
        except Exception:
            pass
        meter = get_meter("bus:nats")
        import time as _t
        t0 = _t.perf_counter()
        try:
            await nc.publish(message.topic, _msg_to_bytes(message), reply=message.reply_to)
        finally:
            try:
                meter.inc("published")
                meter.record("publish_ms", (_t.perf_counter() - t0) * 1000.0)
            except Exception:
                pass
