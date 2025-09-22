import asyncio
import pytest

pytestmark = pytest.mark.asyncio


async def _redis_available(url: str) -> bool:
    try:
        from redis import asyncio as redis  # type: ignore
    except Exception:
        return False
    try:
        client = redis.from_url(url)
        await client.ping()
        await client.close()
        return True
    except Exception:
        return False


async def _append_async(lst, m):
    lst.append(m)


@pytest.mark.timeout(5)
async def test_redisbus_publish_broadcast():
    url = "redis://localhost:6379"
    if not await _redis_available(url):
        pytest.skip("Redis not available or redis.asyncio missing")

    from agenticflow.communication.bus.redis import RedisBus
    from agenticflow.communication.bus.base import Message

    bus1 = RedisBus(url=url)
    bus2 = RedisBus(url=url)
    await bus1.start()
    await bus2.start()

    topic = "topic.redis.test"
    seen1, seen2 = [], []

    bus1.subscribe(topic, lambda m: _append_async(seen1, m))
    bus2.subscribe(topic, lambda m: _append_async(seen2, m))

    # Give background listeners time to subscribe
    await asyncio.sleep(0.05)

    await bus1.publish(Message(topic=topic, type="evt", payload={"x": 1, "trace": "t", "hdr": True}, headers={"trace_id": "t"}))

    # Allow message propagation
    await asyncio.sleep(0.1)

    assert len(seen1) == 1 and len(seen2) == 1
    assert seen1[0].payload["x"] == 1 and seen2[0].payload["x"] == 1
    # headers should round-trip
    assert seen1[0].headers.get("trace_id") == "t"

    await bus1.close()
    await bus2.close()


@pytest.mark.timeout(5)
async def test_redisbus_request_response_roundtrip():
    url = "redis://localhost:6379"
    if not await _redis_available(url):
        pytest.skip("Redis not available or redis.asyncio missing")

    from agenticflow.communication.bus.redis import RedisBus
    from agenticflow.communication.bus.base import Message

    bus = RedisBus(url=url)
    await bus.start()

    async def server_handler(msg: Message):
        assert msg.reply_to
        # round-trip correlation
        await bus.publish(Message(topic=msg.reply_to, type="reply", payload={"ok": True}, correlation_id=msg.correlation_id, headers={"trace_id": msg.headers.get("trace_id", "")}))

    bus.subscribe("svc.redis.echo", server_handler)
    await asyncio.sleep(0.05)

    req = Message(topic="svc.redis.echo", type="ask", payload={"q": 42}, headers={"trace_id": "trace-1"})
    reply = await bus.request("svc.redis.echo", req, timeout=1.0)

    assert reply.type == "reply"
    assert reply.payload["ok"] is True
    assert reply.correlation_id is not None
    assert reply.headers.get("trace_id") == "trace-1"

    await bus.close()
