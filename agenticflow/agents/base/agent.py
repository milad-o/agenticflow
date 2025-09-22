from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from ...core.events.event import AgenticEvent
from ...core.exceptions.base import InvalidTransitionError
from ..state.machine import StateMachine, Transition


class AgentState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class Agent:
    agent_id: str

    def __post_init__(self) -> None:
        self.state = AgentState.IDLE
        # Default minimal FSM transitions
        self.state_machine = StateMachine(
            transitions=(
                Transition(AgentState.IDLE, AgentState.PROCESSING, "task_assigned"),
                Transition(AgentState.PROCESSING, AgentState.IDLE, "task_completed"),
                Transition(AgentState.PROCESSING, AgentState.ERROR, "task_failed"),
                Transition(AgentState.ERROR, AgentState.IDLE, "error_resolved"),
            )
        )

    async def handle_event(self, event: AgenticEvent) -> None:
        """Apply FSM transition or reject invalid transitions."""
        new_state = await self.state_machine.transition(self.state, event)
        if new_state is None:
            raise InvalidTransitionError(
                f"Invalid transition: {self.state.value} + {event.event_type}"
            )
        self.state = new_state
        return None

    async def perform_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Default synchronous task execution placeholder.

        Concrete agents should override this to implement custom behaviors.
        """
        _ = (task_type, params)
        return {"status": "ok"}

    async def compensate_task(self, task_type: str, params: Dict[str, Any], result: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
        """Optional compensation hook; default is no-op.

        Agents that need compensation can override this.
        """
        _ = (task_type, params, result)
        return None
