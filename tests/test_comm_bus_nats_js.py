import asyncio
import pytest

pytestmark = pytest.mark.asyncio


async def _nats_js_available(servers: str) -> bool:
    try:
        import nats  # type: ignore
    except Exception:
        return False
    try:
        nc = await nats.connect(servers=servers)
        js = nc.jetstream()
        # Try a simple API call; if it errors, JS might not be available
        await js.add_stream(name="AF_TEST", subjects=["topic.*"])  # may exist already
        await nc.close()
        return True
    except Exception:
        return False


async def _append_async(lst, m):
    lst.append(m)


@pytest.mark.timeout(10)
async def test_nats_js_publish_broadcast():
    servers = "nats://127.0.0.1:4222"
    if not await _nats_js_available(servers):
        pytest.skip("NATS JetStream not available")

    from agenticflow.communication.bus.nats_js import NatsJetStreamBus
    from agenticflow.communication.bus.base import Message

    bus1 = NatsJetStreamBus(servers=servers)
    bus2 = NatsJetStreamBus(servers=servers)
    await bus1.start()
    await bus2.start()

    topic = "topic.njs.test"
    seen1, seen2 = [], []

    bus1.subscribe(topic, lambda m: _append_async(seen1, m))
    bus2.subscribe(topic, lambda m: _append_async(seen2, m))

    await asyncio.sleep(0.05)

    await bus1.publish(Message(topic=topic, type="evt", payload={"x": 99}))
    await asyncio.sleep(0.3)

    assert len(seen1) >= 1 and len(seen2) >= 1

    await bus1.close()
    await bus2.close()


@pytest.mark.timeout(10)
async def test_nats_js_request_response():
    servers = "nats://127.0.0.1:4222"
    if not await _nats_js_available(servers):
        pytest.skip("NATS JetStream not available")

    from agenticflow.communication.bus.nats_js import NatsJetStreamBus
    from agenticflow.communication.bus.base import Message

    bus = NatsJetStreamBus(servers=servers)
    await bus.start()

    async def handler(msg: Message):
        assert msg.reply_to
        await bus.publish(Message(topic=msg.reply_to, type="reply", payload={"ok": True}, correlation_id=msg.correlation_id))

    bus.subscribe("svc.njs.echo", handler)
    await asyncio.sleep(0.05)

    req = Message(topic="svc.njs.echo", type="ask", payload={"q": 1})
    reply = await bus.request("svc.njs.echo", req, timeout=2.0)
    assert reply.type == "reply" and reply.payload.get("ok") is True

    await bus.close()
