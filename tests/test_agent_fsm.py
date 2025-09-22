import pytest

from agenticflow.agents.base.agent import Agent, AgentState
from agenticflow.core.events.event import AgenticEvent
from agenticflow.core.exceptions.base import InvalidTransitionError


def make_event(t: str) -> AgenticEvent:
    return AgenticEvent.create(t, {}, trace_id="t")


@pytest.mark.asyncio
async def test_fsm_valid_transitions():
    a = Agent("a1")
    assert a.state == AgentState.IDLE

    # IDLE + task_assigned -> PROCESSING
    await a.handle_event(make_event("task_assigned"))
    assert a.state == AgentState.PROCESSING

    # PROCESSING + task_completed -> IDLE
    await a.handle_event(make_event("task_completed"))
    assert a.state == AgentState.IDLE


@pytest.mark.asyncio
async def test_fsm_invalid_transition_rejected():
    a = Agent("a1")
    assert a.state == AgentState.IDLE

    # IDLE + task_completed is invalid
    with pytest.raises(InvalidTransitionError):
        await a.handle_event(make_event("task_completed"))
    # State unchanged
    assert a.state == AgentState.IDLE
