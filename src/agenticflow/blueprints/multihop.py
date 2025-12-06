"""
MultiHopRAG Blueprint.

Complex queries requiring multiple retrieval steps with evidence chain assembly.

Example:
    ```python
    from agenticflow.blueprints import MultiHopRAG

    multi_hop = MultiHopRAG(
        retriever=retriever,
        model=model,
        max_hops=3,
    )

    result = await multi_hop.run("How does X relate to Y through Z?")
    print(result)
    ```

Usage in Flow:
    ```python
    flow = Flow(
        agents=[multi_hop, fact_checker],
        topology="pipeline",
    )
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from agenticflow.agent import Agent
from agenticflow.blueprints.base import BaseBlueprint, BlueprintResult
from agenticflow.blueprints.context import BlueprintContext
from agenticflow.blueprints.processors import (
    CitationStyle,
    CitedPassage,
    CitationFormatter,
    BibliographyAppender,
)
from agenticflow.tools.base import tool

if TYPE_CHECKING:
    from agenticflow.models import BaseChatModel
    from agenticflow.retriever.base import Retriever


@dataclass(frozen=True, slots=True, kw_only=True)
class HopResult:
    """Result from a single retrieval hop.

    Attributes:
        hop_number: Which hop this is (1, 2, 3...).
        query: The query used for this hop.
        passages: Passages retrieved in this hop.
        reasoning: Agent's reasoning for this hop.
    """

    hop_number: int
    query: str
    passages: tuple[CitedPassage, ...] = ()
    reasoning: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class MultiHopRAGConfig:
    """Configuration for MultiHopRAG blueprint.

    Attributes:
        max_hops: Maximum number of retrieval hops.
        passages_per_hop: Number of passages to retrieve per hop.
        citation_style: How to format citations in output.
        include_evidence_chain: Include evidence chain in output.
        include_bibliography: Append bibliography to output.
    """

    max_hops: int = 3
    passages_per_hop: int = 3
    citation_style: CitationStyle = CitationStyle.NUMERIC
    include_evidence_chain: bool = True
    include_bibliography: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class MultiHopRAGResult(BlueprintResult):
    """Result from MultiHopRAG blueprint execution.

    Attributes:
        output: Final answer with citations.
        hops: Results from each retrieval hop.
        all_passages: All passages retrieved across hops.
        query: Original query.
        num_hops: Number of hops performed.
    """

    hops: tuple[HopResult, ...] = ()
    all_passages: tuple[CitedPassage, ...] = ()
    query: str = ""
    num_hops: int = 0


class MultiHopRAG(BaseBlueprint):
    """Multi-hop Retrieval-Augmented Generation blueprint.

    Handles complex queries that require multiple retrieval steps.
    The agent decomposes the query, retrieves iteratively, and
    assembles an evidence chain.

    Flow-compatible: can be used as a resident in Flow topologies.
    Tool-compatible: can be converted to tool via `as_tool()`.

    Example - Basic:
        ```python
        multi_hop = MultiHopRAG(
            retriever=retriever,
            model=model,
        )
        result = await multi_hop.run("How does A affect B through C?")
        ```

    Example - Custom Config:
        ```python
        multi_hop = MultiHopRAG(
            retriever=retriever,
            model=model,
            config=MultiHopRAGConfig(
                max_hops=5,
                passages_per_hop=5,
            ),
        )
        ```
    """

    SYSTEM_PROMPT = """You are a research assistant that answers complex questions through iterative retrieval.

For multi-hop questions:
1. Break down the question into sub-questions
2. Use search_documents to find relevant information for each part
3. Build on previous findings to refine your search
4. Cite sources using the markers provided (e.g., «1», «2»)
5. Synthesize a comprehensive answer from all evidence

Think step by step. If initial results don't fully answer the question, search again with refined queries."""

    def __init__(
        self,
        retriever: Retriever,
        model: BaseChatModel,
        *,
        config: MultiHopRAGConfig | None = None,
    ) -> None:
        """Create MultiHopRAG blueprint.

        Args:
            retriever: Retriever for document search.
            model: LLM model for reasoning.
            config: Configuration options.

        Example:
            ```python
            multi_hop = MultiHopRAG(
                retriever=retriever,
                model=model,
                config=MultiHopRAGConfig(max_hops=5),
            )
            ```
        """
        super().__init__()

        self._retriever = retriever
        self._model = model
        self._config = config or MultiHopRAGConfig()

        # Track passages across hops
        self._all_passages: list[CitedPassage] = []
        self._hop_results: list[HopResult] = []
        self._citation_counter = 0

        # Create internal agent
        self._agent = Agent(
            name="multihop-rag-agent",
            model=model,
            tools=[self._create_search_tool()],
            instructions=self.SYSTEM_PROMPT,
        )

        # Setup post-processors
        cfg = self._config
        self._postprocessors = [
            CitationFormatter(style=cfg.citation_style),
        ]
        if cfg.include_bibliography:
            self._postprocessors.append(BibliographyAppender(include_scores=True))

    @property
    def name(self) -> str:
        return "multihop-rag"

    @property
    def config(self) -> MultiHopRAGConfig:
        """Current configuration."""
        return self._config

    def _create_search_tool(self):
        """Create the search tool for multi-hop retrieval."""
        blueprint = self
        cfg = self._config

        @tool
        async def search_documents(query: str, num_results: int = 3) -> str:
            """Search documents for relevant passages.

            Use this iteratively to build understanding:
            - First search for initial context
            - Refine queries based on what you learn
            - Search for connections between concepts

            Args:
                query: Search query.
                num_results: Number of passages to retrieve.

            Returns:
                Retrieved passages with citation markers.
            """
            k = min(num_results, cfg.passages_per_hop)
            results = await blueprint._retriever.retrieve(query, k=k, include_scores=True)

            if not results:
                return "No relevant passages found for this query."

            passages = []
            lines = []

            for result in results:
                blueprint._citation_counter += 1
                cid = blueprint._citation_counter

                doc = result.document
                passage = CitedPassage(
                    citation_id=cid,
                    source=doc.metadata.get("source", "unknown"),
                    page=doc.metadata.get("page"),
                    score=result.score,
                    text=doc.text,
                )
                passages.append(passage)
                blueprint._all_passages.append(passage)

                lines.append(f"«{cid}» {doc.text}")

            # Track this hop
            hop = HopResult(
                hop_number=len(blueprint._hop_results) + 1,
                query=query,
                passages=tuple(passages),
            )
            blueprint._hop_results.append(hop)

            return "\n\n".join(lines)

        return search_documents

    def _reset_state(self) -> None:
        """Reset internal state for new query."""
        self._all_passages = []
        self._hop_results = []
        self._citation_counter = 0

    async def run(self, input: str, **kwargs: Any) -> str:
        """Execute MultiHopRAG and return formatted output (Flow-compatible).

        Args:
            input: The complex question to answer.
            **kwargs: Additional arguments passed to agent.

        Returns:
            Formatted string with citations and evidence chain.
        """
        result = await self.run_detailed(input, **kwargs)
        return result.output

    async def run_detailed(
        self,
        input: str,
        **kwargs: Any,
    ) -> MultiHopRAGResult:
        """Execute MultiHopRAG with full metadata.

        Args:
            input: The complex question to answer.
            **kwargs: Additional arguments passed to agent.

        Returns:
            MultiHopRAGResult with output, hops, and evidence.
        """
        # Reset state for new query
        self._reset_state()

        # Enhance prompt to encourage multi-hop reasoning
        enhanced_input = f"""Answer this question thoroughly, using multiple searches if needed:

{input}

Remember: Search iteratively, building on previous findings. Cite all sources."""

        # Run agent (will use search tool multiple times)
        raw_output = await self._agent.run(enhanced_input, **kwargs)

        # Build context with all passages
        ctx = BlueprintContext(
            input=input,
            output=raw_output,
        ).with_metadata(passages=self._all_passages)

        # Add evidence chain if configured
        if self._config.include_evidence_chain and len(self._hop_results) > 1:
            evidence_chain = self._format_evidence_chain()
            ctx = ctx.with_output(raw_output + evidence_chain)

        # Run post-processors (citation formatting, bibliography)
        for processor in self._postprocessors:
            ctx = await processor(ctx)

        return MultiHopRAGResult(
            output=ctx.output,
            hops=tuple(self._hop_results),
            all_passages=tuple(self._all_passages),
            query=input,
            num_hops=len(self._hop_results),
            context=ctx,
            metadata={
                "num_hops": len(self._hop_results),
                "total_passages": len(self._all_passages),
                "citation_style": self._config.citation_style.value,
            },
        )

    def _format_evidence_chain(self) -> str:
        """Format the evidence chain showing retrieval progression."""
        if not self._hop_results:
            return ""

        lines = ["\n\n---\n**Evidence Chain:**"]
        for hop in self._hop_results:
            cites = ", ".join(f"«{p.citation_id}»" for p in hop.passages)
            lines.append(f"- Hop {hop.hop_number}: \"{hop.query}\" → {cites}")

        return "\n".join(lines)


__all__ = [
    "MultiHopRAG",
    "MultiHopRAGConfig",
    "MultiHopRAGResult",
    "HopResult",
]
