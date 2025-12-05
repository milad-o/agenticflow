"""
Base classes for blueprints.

Blueprints are pre-configured agent workflows that can:
- Participate in Flows as residents (like Agents)
- Be used as tools in other Agents
- Apply pre/post processing around agent execution

Architecture:
    Flow (container)
    ├── Agent (resident)
    ├── Blueprint (resident) ← implements FlowResident
    └── ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from agenticflow.blueprints.context import BlueprintContext

if TYPE_CHECKING:
    from agenticflow.tools.base import BaseTool


# Type aliases for processors
PreProcessor = Callable[[BlueprintContext], Awaitable[BlueprintContext]]
PostProcessor = Callable[[BlueprintContext], Awaitable[BlueprintContext]]


@dataclass(frozen=True, slots=True, kw_only=True)
class BlueprintResult:
    """Result from a blueprint execution.

    Attributes:
        output: The main output string.
        metadata: Additional metadata from execution.
        context: Full execution context (for advanced usage).
    """

    output: str
    metadata: dict[str, Any] = field(default_factory=dict)
    context: BlueprintContext | None = None

    def __str__(self) -> str:
        return self.output


class BaseBlueprint(ABC):
    """Base class for all blueprints.

    Blueprints are pre-configured agent workflows with:
    - Sensible defaults for common patterns
    - Pre-processing of inputs (query rewriting, context injection)
    - Post-processing of outputs (formatting, validation)
    - Flow compatibility (can be used as Flow residents)
    - Tool conversion (can be used as tools in other Agents)

    Blueprints implement the FlowResident protocol:
    - `name` property for routing
    - `run()` returning string for Flow compatibility

    Example:
        ```python
        class MyBlueprint(BaseBlueprint):
            @property
            def name(self) -> str:
                return "my-blueprint"

            async def run(self, input: str, **kwargs) -> str:
                # Pre-process
                ctx = BlueprintContext(input=input)
                ctx = await self._run_preprocessors(ctx)

                # Execute
                output = await self._agent.run(ctx.input)
                ctx = ctx.with_output(output)

                # Post-process
                ctx = await self._run_postprocessors(ctx)
                return ctx.output

            async def run_detailed(self, input: str, **kwargs) -> BlueprintResult:
                # Same as run() but returns full result with metadata
                ...
        ```

    Usage in Flow:
        ```python
        flow = Flow(
            agents=[agent1, MyBlueprint(), agent2],
            topology="pipeline",
        )
        ```

    Usage as Tool:
        ```python
        agent = Agent(tools=[my_blueprint.as_tool()])
        ```
    """

    # Pre and post processors (subclasses can override)
    _preprocessors: list[PreProcessor]
    _postprocessors: list[PostProcessor]

    def __init__(self) -> None:
        """Initialize processor lists."""
        self._preprocessors = []
        self._postprocessors = []

    @property
    @abstractmethod
    def name(self) -> str:
        """Blueprint name (used by Flow for routing)."""
        ...

    @abstractmethod
    async def run(self, input: str, **kwargs: Any) -> str:
        """Execute the blueprint (Flow-compatible).

        This is the primary interface called by Flow topologies.
        Returns string output for compatibility.

        For full metadata, use `run_detailed()`.

        Args:
            input: The input query or text.
            **kwargs: Additional arguments.

        Returns:
            String output.
        """
        ...

    async def run_detailed(self, input: str, **kwargs: Any) -> BlueprintResult:
        """Execute and return detailed result with metadata.

        Override this in subclasses to provide rich results.
        Default implementation wraps `run()`.

        Args:
            input: The input query or text.
            **kwargs: Additional arguments.

        Returns:
            BlueprintResult with output and metadata.
        """
        output = await self.run(input, **kwargs)
        return BlueprintResult(output=output)

    def as_tool(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> BaseTool:
        """Convert blueprint to a tool for use in other Agents.

        Args:
            name: Override tool name (default: blueprint name).
            description: Override tool description.

        Returns:
            Tool that executes this blueprint.

        Example:
            ```python
            rag = RAG(retriever=retriever, model=model)
            
            supervisor = Agent(
                tools=[rag.as_tool()],
                model=model,
            )
            ```
        """
        from agenticflow.tools.base import tool

        blueprint = self
        tool_name = name or self.name
        tool_desc = description or f"Execute the {self.name} blueprint."

        @tool(name=tool_name, description=tool_desc)
        async def blueprint_tool(query: str) -> str:
            """Execute blueprint with given query."""
            return await blueprint.run(query)

        return blueprint_tool

    # ================================================================
    # Processor pipeline helpers
    # ================================================================

    async def _run_preprocessors(self, ctx: BlueprintContext) -> BlueprintContext:
        """Run all pre-processors in order.

        Args:
            ctx: Current context.

        Returns:
            Modified context.
        """
        for processor in self._preprocessors:
            ctx = await processor(ctx)
        return ctx

    async def _run_postprocessors(self, ctx: BlueprintContext) -> BlueprintContext:
        """Run all post-processors in order.

        Args:
            ctx: Current context (with output set).

        Returns:
            Modified context.
        """
        for processor in self._postprocessors:
            ctx = await processor(ctx)
        return ctx

    def add_preprocessor(self, processor: PreProcessor) -> None:
        """Add a pre-processor to the pipeline.

        Args:
            processor: Async function (ctx) -> ctx.
        """
        self._preprocessors.append(processor)

    def add_postprocessor(self, processor: PostProcessor) -> None:
        """Add a post-processor to the pipeline.

        Args:
            processor: Async function (ctx) -> ctx.
        """
        self._postprocessors.append(processor)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
