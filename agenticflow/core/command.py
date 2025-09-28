"""Command pattern using LangGraph's Command for agent flow control."""

from typing import Any, Dict, Optional
from langgraph.types import Command
from .state import AgentMessage


def create_agent_response_command(
    message: AgentMessage,
    goto: str = "supervisor",
    additional_updates: Optional[Dict[str, Any]] = None
) -> Command:
    """Helper to create a LangGraph Command with an agent response message.

    Args:
        message: The response message from the agent
        goto: Where to route next (default: back to supervisor)
        additional_updates: Any additional state updates

    Returns:
        LangGraph Command with the message and routing information
    """
    update = {"messages": [message]}
    if additional_updates:
        update.update(additional_updates)

    return Command(
        goto=goto,
        update=update
    )


def create_finish_command(
    final_message: Optional[AgentMessage] = None,
    additional_updates: Optional[Dict[str, Any]] = None
) -> Command:
    """Helper to create a LangGraph Command that finishes execution.

    Args:
        final_message: Optional final message
        additional_updates: Any additional state updates

    Returns:
        LangGraph Command that ends execution
    """
    update = {}
    if final_message:
        update["messages"] = [final_message]
    if additional_updates:
        update.update(additional_updates)

    return Command(
        goto="__end__",  # LangGraph END convention
        update=update
    )