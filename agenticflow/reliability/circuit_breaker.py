from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from ..core.exceptions.base import CircuitOpenError


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout: float = 5.0  # seconds

    def __post_init__(self) -> None:
        self._state: str = "CLOSED"
        self._failures: int = 0
        self._opened_at: Optional[float] = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[[], Awaitable[object]]) -> object:
        async with self._lock:
            now = time.monotonic()
            if self._state == "OPEN":
                if self._opened_at is not None and (now - self._opened_at) >= self.recovery_timeout:
                    # Move to half-open; allow a trial call outside lock
                    self._state = "HALF_OPEN"
                else:
                    raise CircuitOpenError("circuit open")

        # Execute outside of lock to avoid blocking others
        try:
            result = await func()
        except Exception:
            async with self._lock:
                self._failures += 1
                if self._failures >= self.failure_threshold:
                    self._state = "OPEN"
                    self._opened_at = time.monotonic()
                # remain CLOSED or HALF_OPEN but failure recorded
            raise

        # Success path
        async with self._lock:
            if self._state in ("HALF_OPEN", "OPEN"):
                # Close on successful probe
                self._state = "CLOSED"
                self._opened_at = None
            self._failures = 0
        return result

    # Introspection for tests/metrics
    def state(self) -> str:
        return self._state

    def failures(self) -> int:
        return self._failures
