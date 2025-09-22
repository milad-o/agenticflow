import asyncio
import pytest

from agenticflow.reliability.circuit_breaker import CircuitBreaker
from agenticflow.core.exceptions.base import CircuitOpenError


@pytest.mark.asyncio
async def test_circuit_opens_after_failures():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    async def failing():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await cb.call(failing)
    with pytest.raises(RuntimeError):
        await cb.call(failing)

    assert cb.state() == "OPEN"

    # Now it should raise CircuitOpenError without calling
    with pytest.raises(CircuitOpenError):
        await cb.call(failing)


@pytest.mark.asyncio
async def test_circuit_half_open_then_close_on_success():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)

    async def failing():
        raise RuntimeError("boom")

    async def success():
        return 42

    # Open it
    with pytest.raises(RuntimeError):
        await cb.call(failing)
    assert cb.state() == "OPEN"

    # Wait to allow half-open probe
    await asyncio.sleep(0.06)
    result = await cb.call(success)
    assert result == 42
    assert cb.state() == "CLOSED"
