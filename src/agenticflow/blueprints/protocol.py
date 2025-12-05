"""
FlowResident Protocol - shared interface for Flow participants.

Both Agent and Blueprint implement this protocol, allowing Flow
to treat them uniformly in topologies.

Example:
    from agenticflow import Agent, Flow
    from agenticflow.blueprints import RAG

    # Both Agent and Blueprint work as Flow residents
    flow = Flow(
        agents=[
            Agent(name="writer", model=model),
            RAG(retriever=retriever, model=model),  # Blueprint as resident
        ],
        topology="pipeline",
    )
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FlowResident(Protocol):
    """Protocol for entities that can participate in a Flow.

    Both Agent and Blueprint implement this protocol, enabling
    uniform treatment in Flow topologies.

    Required:
        - name: Unique identifier for routing
        - run(): Execute with input, return string output

    Optional:
        - as_tool(): Convert to tool for use in other agents
    """

    @property
    def name(self) -> str:
        """Unique name for this resident (used by Flow for routing)."""
        ...

    async def run(self, input: str, **kwargs: Any) -> str:
        """Execute the resident with given input.

        Args:
            input: The input prompt or query.
            **kwargs: Additional execution arguments.

        Returns:
            String output (Flow-compatible).
        """
        ...


__all__ = ["FlowResident"]
