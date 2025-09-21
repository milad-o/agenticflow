from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ...core.events.event import AgenticEvent


class AgentState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class Agent:
    agent_id: str

    def __post_init__(self) -> None:
        self.state = AgentState.IDLE

    async def handle_event(self, event: AgenticEvent) -> None:
        """Minimal placeholder; real logic implemented in Phase 1."""
        _ = event
        # TODO: Implement FSM transition + behavior hooks
        return None
