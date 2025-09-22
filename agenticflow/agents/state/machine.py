from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, TYPE_CHECKING

from ...core.events.event import AgenticEvent

if TYPE_CHECKING:
    from ..base.agent import AgentState

Guard = Callable[["AgentState", AgenticEvent], bool]


@dataclass(frozen=True)
class Transition:
    from_state: Optional["AgentState"]
    to_state: "AgentState"
    event_type: str
    guard: Optional[Guard] = None


class StateMachine:
    def __init__(self, transitions: Tuple[Transition, ...]):
        self._t = transitions

    def find_transition(self, current: "AgentState", event: AgenticEvent) -> Optional[Transition]:
        for tr in self._t:
            if tr.from_state in (None, current) and tr.event_type == event.event_type:
                return tr
        return None

    async def transition(self, current: "AgentState", event: AgenticEvent) -> Optional["AgentState"]:
        tr = self.find_transition(current, event)
        if tr is None:
            return None
        if tr.guard is None or tr.guard(current, event):
            return tr.to_state
        return None
