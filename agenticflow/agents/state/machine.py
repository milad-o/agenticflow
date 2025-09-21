from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from . import agent as agent_mod
from ...core.events.event import AgenticEvent

Guard = Callable[[agent_mod.AgentState, AgenticEvent], bool]


@dataclass(frozen=True)
class Transition:
    from_state: Optional[agent_mod.AgentState]
    to_state: agent_mod.AgentState
    event_type: str
    guard: Optional[Guard] = None


class StateMachine:
    def __init__(self, transitions: Tuple[Transition, ...]):
        self._t = transitions

    async def transition(self, current: agent_mod.AgentState, event: AgenticEvent) -> agent_mod.AgentState:
        for tr in self._t:
            if tr.from_state in (None, current) and tr.event_type == event.event_type:
                if tr.guard is None or tr.guard(current, event):
                    return tr.to_state
        return current
