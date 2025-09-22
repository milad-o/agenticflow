from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional
from uuid import uuid4

from ..bus.base import CommunicationBus, Message


async def rpc_call(
    bus: CommunicationBus,
    topic: str,
    *,
    payload: Dict[str, Any],
    msg_type: str = "rpc",
    timeout: float = 5.0,
    headers: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> Message:
    """Perform a request/response over a CommunicationBus with correlation.

    Returns the reply Message.
    """
    cid = correlation_id or str(uuid4())
    req = Message(topic=topic, type=msg_type, payload=payload, correlation_id=cid, headers=headers or {})
    reply = await bus.request(topic, req, timeout=timeout)
    # Ensure correlation preserved (bus.request sets correlation_id correctly)
    return reply


def register_rpc_handler(
    bus: CommunicationBus,
    topic: str,
    handler: Callable[[Dict[str, Any], Message], Awaitable[Dict[str, Any]]],
) -> str:
    """Register an RPC handler.

    The handler receives (payload, original_message) and must return a reply payload dict.
    """
    async def _on_message(msg: Message):
        if not msg.reply_to:
            return  # Ignore messages not expecting a reply
        response_payload = await handler(msg.payload, msg)
        reply = Message(topic=msg.reply_to, type=f"{msg.type}.reply", payload=response_payload, correlation_id=msg.correlation_id)
        await bus.publish(reply)

    return bus.subscribe(topic, _on_message)
