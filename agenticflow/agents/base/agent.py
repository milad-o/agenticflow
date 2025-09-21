from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

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
        """Minimal placeholder for event-driven behavior."""
        _ = event
        return None

    async def perform_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Default synchronous task execution placeholder.

        Concrete agents should override this to implement custom behaviors.
        """
        _ = (task_type, params)
        return {"status": "ok"}
