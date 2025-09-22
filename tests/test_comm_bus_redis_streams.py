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


@pytest.mark.timeout(10)
async def test_redis_streams_publish_broadcast():
    url = "redis://localhost:6379"
    if not await _redis_available(url):
        pytest.skip("Redis not available")

    from agenticflow.communication.bus.redis_streams import RedisStreamsBus
    from agenticflow.communication.bus.base import Message

    bus1 = RedisStreamsBus(url=url, group="af_test")
    bus2 = RedisStreamsBus(url=url, group="af_test")
    await bus1.start()
    await bus2.start()

    topic = "topic.redis.streams"
    seen1, seen2 = [], []

    bus1.subscribe(topic, lambda m: _append_async(seen1, m))
    bus2.subscribe(topic, lambda m: _append_async(seen2, m))

    await asyncio.sleep(0.05)

    await bus1.publish(Message(topic=topic, type="evt", payload={"x": 123}))
    await asyncio.sleep(0.2)

    assert len(seen1) >= 1 and len(seen2) >= 1
    assert seen1[0].payload["x"] == 123

    await bus1.close()
    await bus2.close()


@pytest.mark.timeout(10)
async def test_redis_streams_request_response():
    url = "redis://localhost:6379"
    if not await _redis_available(url):
        pytest.skip("Redis not available")

    from agenticflow.communication.bus.redis_streams import RedisStreamsBus
    from agenticflow.communication.bus.base import Message

    bus = RedisStreamsBus(url=url, group="af_test")
    await bus.start()

    async def handler(msg: Message):
        assert msg.reply_to
        await bus.publish(Message(topic=msg.reply_to, type="reply", payload={"ok": True}, correlation_id=msg.correlation_id))

    bus.subscribe("svc.rs.echo", handler)
    await asyncio.sleep(0.05)

    req = Message(topic="svc.rs.echo", type="ask", payload={"q": 7})
    reply = await bus.request("svc.rs.echo", req, timeout=2.0)
    assert reply.type == "reply" and reply.payload.get("ok") is True

    await bus.close()
