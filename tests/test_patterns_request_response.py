import asyncio
import pytest

from agenticflow.communication.bus.memory import InMemoryBus
from agenticflow.communication.patterns.request_response import rpc_call, register_rpc_handler


@pytest.mark.asyncio
async def test_rpc_call_inmemory_preserves_correlation():
    bus = InMemoryBus()

    async def handler(payload, msg):
        # Echo back with additional field
        assert msg.correlation_id is not None
        return {"ok": True, "seen": payload.get("x")}

    register_rpc_handler(bus, "svc.add", handler)

    reply = await rpc_call(bus, "svc.add", payload={"x": 7}, msg_type="add", timeout=1.0)
    assert reply.correlation_id is not None
    assert reply.type == "add.reply"
    assert reply.payload["ok"] is True and reply.payload["seen"] == 7


@pytest.mark.asyncio
async def test_rpc_call_timeout():
    bus = InMemoryBus()

    # No handler registered; request should timeout
    with pytest.raises(asyncio.TimeoutError):
        await rpc_call(bus, "svc.none", payload={}, timeout=0.05)
