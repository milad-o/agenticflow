from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional
from uuid import uuid4, UUID
import time


@dataclass(frozen=True)
class AgenticEvent:
    """Immutable event with basic causality and tracing fields.

    This is the canonical event envelope to be used across the system.
    """

    id: UUID
    event_type: str
    payload: Mapping[str, Any]
    timestamp_ns: int
    trace_id: str
    span_id: Optional[str] = None

    @staticmethod
    def create(event_type: str, payload: Mapping[str, Any], trace_id: str, span_id: Optional[str] = None) -> "AgenticEvent":
        return AgenticEvent(
            id=uuid4(),
            event_type=event_type,
            payload=dict(payload),  # ensure immutability by copying
            timestamp_ns=time.time_ns(),
            trace_id=trace_id,
            span_id=span_id,
        )
