"""Base classes for blueprints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True, kw_only=True)
class BlueprintResult:
    """Result from a blueprint execution.

    Attributes:
        output: The main output string.
        metadata: Additional metadata from execution.
    """

    output: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.output


class BaseBlueprint(ABC):
    """Base class for all blueprints.

    Blueprints are pre-configured agent workflows with:
    - Sensible defaults
    - Pre-processing of inputs
    - Post-processing of outputs (deterministic)

    They leverage the Agent and Flow system internally.

    Example:
        ```python
        class MyBlueprint(BaseBlueprint):
            name = "my-blueprint"

            async def run(self, input: str, **kwargs) -> BlueprintResult:
                # Use internal agent/flow
                result = await self._agent.run(input)
                return BlueprintResult(output=result)
        ```
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Blueprint name."""
        ...

    @abstractmethod
    async def run(self, input: str, **kwargs: Any) -> BlueprintResult:
        """Execute the blueprint.

        Args:
            input: The input query or text.
            **kwargs: Additional arguments.

        Returns:
            BlueprintResult with output and metadata.
        """
        ...
