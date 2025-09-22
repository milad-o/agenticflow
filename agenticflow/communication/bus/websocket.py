from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from typing import Dict, List, Tuple

import websockets

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


class LocalWebSocketServerBus(CommunicationBus):
    def __init__(self, host: str = "127.0.0.1", port: int = 0, *, max_subscribers: int = 1000, on_backpressure: BackpressureHook | None = None) -> None:
        self.host = host
        self.port = port
        self._server = None
        self._clients: List[websockets.WebSocketServerProtocol] = []
        self._subs: Dict[str, List[Tuple[str, MessageHandler]]] = {}
        self._max_subs = max_subscribers
        self._on_backpressure = on_backpressure

    async def start(self) -> None:
        async def handler(ws):
            self._clients.append(ws)
            try:
                async for message in ws:
                    msg = _json_to_msg(message)
                    await self._dispatch_local(msg)
            finally:
                if ws in self._clients:
                    self._clients.remove(ws)

        self._server = await websockets.serve(handler, self.host, self.port)
        # If port was 0, get the assigned port
        self.port = self._server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    def subscribe(self, topic: str, handler: MessageHandler) -> str:
        sub_id = str(id(handler))
        lst = self._subs.setdefault(topic, [])
        lst.append((sub_id, handler))
        if len(lst) > self._max_subs and self._on_backpressure is not None:
            asyncio.create_task(self._on_backpressure(topic, len(lst)))
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        for topic, lst in list(self._subs.items()):
            self._subs[topic] = [(sid, h) for (sid, h) in lst if sid != subscription_id]
            if not self._subs[topic]:
                self._subs.pop(topic, None)

    async def publish(self, message: Message) -> None:
        # Inject trace context
        try:
            inject_trace_context(message.headers)
        except Exception:
            pass
        # Metrics
        meter = get_meter("bus:websocket")
        import time as _t
        t0 = _t.perf_counter()
        # Dispatch locally
        await self._dispatch_local(message)
        # Broadcast to all connected clients
        if self._clients:
            data = _msg_to_json(message)
            await asyncio.gather(*[ws.send(data) for ws in list(self._clients)])
        try:
            meter.inc("published")
            meter.record("publish_ms", (_t.perf_counter() - t0) * 1000.0)
        except Exception:
            pass

    async def _dispatch_local(self, message: Message) -> None:
        for (sid, handler) in list(self._subs.get(message.topic, [])):
            with use_trace_context_from_headers(message.headers):
                await handler(message)


class LocalWebSocketClientBus(CommunicationBus):
    def __init__(self, url: str) -> None:
        self.url = url
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._recv_task: asyncio.Task | None = None
        self._subs: Dict[str, List[Tuple[str, MessageHandler]]] = {}

    async def connect(self) -> None:
        self._ws = await websockets.connect(self.url)
        self._recv_task = asyncio.create_task(self._recv_loop())

    async def close(self) -> None:
        if self._recv_task:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except Exception:
                pass
            self._recv_task = None
        if self._ws:
            await self._ws.close()
            self._ws = None

    def subscribe(self, topic: str, handler: MessageHandler) -> str:
        sub_id = str(id(handler))
        self._subs.setdefault(topic, []).append((sub_id, handler))
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        for topic, lst in list(self._subs.items()):
            self._subs[topic] = [(sid, h) for (sid, h) in lst if sid != subscription_id]
            if not self._subs[topic]:
                self._subs.pop(topic, None)

    async def publish(self, message: Message) -> None:
        if not self._ws:
            raise RuntimeError("Client not connected")
        await self._ws.send(_msg_to_json(message))

    async def _recv_loop(self) -> None:
        assert self._ws is not None
        try:
            async for data in self._ws:
                msg = _json_to_msg(data)
                for (sid, handler) in list(self._subs.get(msg.topic, [])):
                    with use_trace_context_from_headers(msg.headers):
                        await handler(msg)
        except asyncio.CancelledError:
            pass
