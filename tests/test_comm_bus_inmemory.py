import asyncio
import pytest

from agenticflow.communication.bus.base import Message
from agenticflow.communication.bus.memory import InMemoryBus


@pytest.mark.asyncio
async def test_publish_broadcast():
    bus = InMemoryBus()
    topic = "topic.test"
    seen1, seen2 = [], []

    bus.subscribe(topic, lambda m: _append_async(seen1, m))
    bus.subscribe(topic, lambda m: _append_async(seen2, m))

    await bus.publish(Message(topic=topic, type="evt", payload={"x": 1}))

    assert len(seen1) == 1 and len(seen2) == 1
    assert seen1[0].payload["x"] == 1 and seen2[0].payload["x"] == 1


@pytest.mark.asyncio
async def test_request_response_roundtrip():
    bus = InMemoryBus()

    # server
    async def server_handler(msg: Message):
        assert msg.reply_to
        await bus.publish(Message(topic=msg.reply_to, type="reply", payload={"ok": True}, correlation_id=msg.correlation_id))

    bus.subscribe("svc.echo", server_handler)

    # client
    req = Message(topic="svc.echo", type="ask", payload={"q": 42})
    reply = await bus.request("svc.echo", req, timeout=1.0)

    assert reply.type == "reply"
    assert reply.payload["ok"] is True


async def _append_async(lst, m):
    lst.append(m)
