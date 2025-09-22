import asyncio
import pytest

pytestmark = pytest.mark.asyncio


async def _nats_available(servers: str) -> bool:
    try:
        import nats  # type: ignore
    except Exception:
        return False
    try:
        nc = await nats.connect(servers=servers)
        await nc.close()
        return True
    except Exception:
        return False


async def _append_async(lst, m):
    lst.append(m)


@pytest.mark.timeout(5)
async def test_natsbus_publish_broadcast():
    servers = "nats://127.0.0.1:4222"
    if not await _nats_available(servers):
        pytest.skip("NATS not available or nats-py missing")

    from agenticflow.communication.bus.nats import NatsBus
    from agenticflow.communication.bus.base import Message

    bus1 = NatsBus(servers=servers)
    bus2 = NatsBus(servers=servers)
    await bus1.start()
    await bus2.start()

    topic = "topic.nats.test"
    seen1, seen2 = [], []

    bus1.subscribe(topic, lambda m: _append_async(seen1, m))
    bus2.subscribe(topic, lambda m: _append_async(seen2, m))

    await asyncio.sleep(0.05)

    await bus1.publish(Message(topic=topic, type="evt", payload={"x": 1}, headers={"trace_id": "t"}))

    await asyncio.sleep(0.1)

    assert len(seen1) == 1 and len(seen2) == 1
    assert seen1[0].payload["x"] == 1 and seen2[0].payload["x"] == 1

    await bus1.close()
    await bus2.close()


@pytest.mark.timeout(5)
async def test_natsbus_request_response_roundtrip():
    servers = "nats://127.0.0.1:4222"
    if not await _nats_available(servers):
        pytest.skip("NATS not available or nats-py missing")

    from agenticflow.communication.bus.nats import NatsBus
    from agenticflow.communication.bus.base import Message

    bus = NatsBus(servers=servers)
    await bus.start()

    async def server_handler(msg: Message):
        assert msg.reply_to
        await bus.publish(Message(topic=msg.reply_to, type="reply", payload={"ok": True}, correlation_id=msg.correlation_id, headers=msg.headers))

    bus.subscribe("svc.nats.echo", server_handler)
    await asyncio.sleep(0.05)

    req = Message(topic="svc.nats.echo", type="ask", payload={"q": 42}, headers={"trace_id": "trace-1"})
    reply = await bus.request("svc.nats.echo", req, timeout=1.0)

    assert reply.type == "reply"
    assert reply.payload["ok"] is True
    assert reply.correlation_id is not None
    assert reply.headers.get("trace_id") == "trace-1"

    await bus.close()
