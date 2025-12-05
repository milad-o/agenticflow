"""
BlueprintContext - Immutable execution context for blueprints.

The context flows through the entire blueprint pipeline:
    input → [pre-processors] → agent → [post-processors] → output

It carries metadata accumulated at each stage and provides
thread-safe, immutable state management.

Example:
    ctx = BlueprintContext(input="What is RAG?")
    ctx = ctx.with_metadata(passages=retrieved_passages)
    ctx = ctx.with_output(agent_response)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self


@dataclass(frozen=True, slots=True, kw_only=True)
class BlueprintContext:
    """Immutable context flowing through blueprint pipeline.

    Context is created at the start of `Blueprint.run()` and flows through:
    1. Pre-processors (can add metadata)
    2. Agent execution
    3. Post-processors (can transform output)

    The frozen dataclass ensures thread-safety for concurrent executions.

    Attributes:
        input: Original user input.
        output: Current output (set after agent runs).
        metadata: Accumulated metadata from processors.
        run_id: Unique identifier for this run.
    """

    input: str
    output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    run_id: str = ""

    def __post_init__(self) -> None:
        """Generate run_id if not provided."""
        if not self.run_id:
            import uuid

            # Use object.__setattr__ since frozen=True
            object.__setattr__(self, "run_id", str(uuid.uuid4())[:8])

    def with_output(self, output: str) -> Self:
        """Create new context with updated output.

        Args:
            output: The new output string.

        Returns:
            New BlueprintContext with updated output.
        """
        return BlueprintContext(
            input=self.input,
            output=output,
            metadata=self.metadata,
            run_id=self.run_id,
        )

    def with_metadata(self, **kwargs: Any) -> Self:
        """Create new context with additional metadata.

        Args:
            **kwargs: Metadata key-value pairs to add.

        Returns:
            New BlueprintContext with merged metadata.

        Example:
            ctx = ctx.with_metadata(
                passages=passages,
                retrieval_time_ms=42,
            )
        """
        return BlueprintContext(
            input=self.input,
            output=self.output,
            metadata={**self.metadata, **kwargs},
            run_id=self.run_id,
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key.

        Args:
            key: Metadata key.
            default: Default if key not found.

        Returns:
            The metadata value or default.
        """
        return self.metadata.get(key, default)

    def __contains__(self, key: str) -> bool:
        """Check if metadata key exists."""
        return key in self.metadata


__all__ = ["BlueprintContext"]
