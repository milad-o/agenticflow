import asyncio
import pytest

from agenticflow.communication.bus.websocket import LocalWebSocketServerBus, LocalWebSocketClientBus
from agenticflow.communication.bus.base import Message


@pytest.mark.asyncio
async def test_websocket_request_response():
    server = LocalWebSocketServerBus(host="127.0.0.1", port=0)
    await server.start()

    async def server_handler(msg: Message):
        assert msg.reply_to
        await server.publish(Message(topic=msg.reply_to, type="reply", payload={"ok": True}, correlation_id=msg.correlation_id))

    server.subscribe("svc.echo", server_handler)

    client = LocalWebSocketClientBus(url=f"ws://{server.host}:{server.port}")
    await client.connect()

    req = Message(topic="svc.echo", type="ask", payload={"q": 1})
    reply = await client.request("svc.echo", req, timeout=1.0)
    assert reply.type == "reply"
    assert reply.payload["ok"] is True

    await client.close()
    await server.stop()


@pytest.mark.asyncio
async def test_websocket_broadcast_from_server_to_client():
    server = LocalWebSocketServerBus(host="127.0.0.1", port=0)
    await server.start()

    client = LocalWebSocketClientBus(url=f"ws://{server.host}:{server.port}")
    await client.connect()

    seen = []
    client.subscribe("topic.news", lambda m: _append_async(seen, m))
    await server.publish(Message(topic="topic.news", type="evt", payload={"n": 1}))

    # Give the client a short time to receive
    await asyncio.sleep(0.05)
    assert len(seen) == 1
    assert seen[0].payload["n"] == 1

    await client.close()
    await server.stop()


async def _append_async(lst, m):
    lst.append(m)
