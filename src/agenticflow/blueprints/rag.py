"""
RAG (Retrieval-Augmented Generation) Blueprint.

A pre-configured agent workflow for retrieval-augmented generation.
Uses an internal Agent with search tools and composable post-processors
for citation formatting.

Example:
    ```python
    from agenticflow.blueprints import RAG
    from agenticflow.retriever import DenseRetriever
    from agenticflow.vectorstore import VectorStore

    # Prepare retriever (outside blueprint)
    store = VectorStore(embeddings=embeddings)
    await store.add_documents(chunks)
    retriever = DenseRetriever(store)

    # Create blueprint
    rag = RAG(retriever=retriever, model=model)

    # Query - returns formatted answer with citations
    result = await rag.run("What are the key findings?")
    print(result)
    ```

Usage in Flow:
    ```python
    flow = Flow(
        agents=[rag, fact_checker, writer],
        topology="pipeline",
    )
    ```

Usage as Tool:
    ```python
    supervisor = Agent(tools=[rag.as_tool()])
    ```

Citation Design:
    - Agent sees unique markers: «1», «2» (collision-resistant)
    - Agent references these in its response
    - Post-processing replaces markers with formatted citations
    - Bibliography appended deterministically
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from agenticflow.agent import Agent
from agenticflow.blueprints.base import BaseBlueprint, BlueprintResult
from agenticflow.blueprints.context import BlueprintContext
from agenticflow.blueprints.processors import (
    CITE_MARKER_PATTERN,
    BibliographyAppender,
    CitationFormatter,
    CitationStyle,
    CitedPassage,
)
from agenticflow.tools.base import tool

if TYPE_CHECKING:
    from agenticflow.models import BaseChatModel
    from agenticflow.retriever.base import FusionStrategy, Retriever
    from agenticflow.retriever.rerankers.base import Reranker


@dataclass(frozen=True, slots=True, kw_only=True)
class RAGConfig:
    """Configuration for RAG blueprint.

    Attributes:
        top_k: Default number of results to retrieve.
        score_threshold: Minimum score to include (0.0-1.0).
        max_passage_length: Truncate passages (0 = no limit).
        citation_style: How to format citations in output.
        include_bibliography: Append bibliography to output.
        include_score_in_bibliography: Show scores in bibliography.
    """

    top_k: int = 4
    score_threshold: float = 0.0
    max_passage_length: int = 0

    citation_style: CitationStyle = CitationStyle.NUMERIC
    include_bibliography: bool = True
    include_score_in_bibliography: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class RAGResult(BlueprintResult):
    """Result from RAG blueprint execution.

    Attributes:
        output: Formatted answer with citations and bibliography.
        raw_output: Raw agent output with «1» markers.
        passages: Retrieved passages used.
        query: Original query.
    """

    raw_output: str = ""
    passages: tuple[CitedPassage, ...] = ()
    query: str = ""


class RAG(BaseBlueprint):
    """Retrieval-Augmented Generation blueprint.

    Creates an internal Agent with search tools and handles
    citation formatting via composable post-processors.

    Flow-compatible: can be used as a resident in Flow topologies.
    Tool-compatible: can be converted to tool via `as_tool()`.

    Example - Standalone:
        ```python
        from agenticflow.blueprints import RAG

        rag = RAG(retriever=retriever, model=model)
        result = await rag.run("What are the key findings?")
        print(result)  # Formatted with citations + bibliography
        ```

    Example - In Flow:
        ```python
        flow = Flow(
            agents=[rag, fact_checker],
            topology="pipeline",
        )
        result = await flow.run("Research X")
        ```

    Example - As Tool:
        ```python
        supervisor = Agent(tools=[rag.as_tool()])
        ```

    Example - Multiple retrievers:
        ```python
        rag = RAG(
            retrievers=[dense_retriever, sparse_retriever],
            weights=[0.6, 0.4],
            fusion="rrf",
            model=model,
        )
        ```
    """

    SYSTEM_PROMPT = """You are a research assistant that answers questions based on retrieved documents.

Instructions:
1. Use the search_documents tool to find relevant information
2. Base your answer ONLY on the retrieved passages
3. Cite sources using the markers provided (e.g., «1», «2»)
4. If information isn't in the documents, say so explicitly
5. Be concise and accurate"""

    def __init__(
        self,
        retriever: Retriever | None = None,
        model: BaseChatModel | None = None,
        *,
        agent: Agent | None = None,
        retrievers: list[Retriever] | None = None,
        weights: list[float] | None = None,
        fusion: FusionStrategy | str = "rrf",
        reranker: Reranker | None = None,
        config: RAGConfig | None = None,
        postprocessors: list | None = None,
    ) -> None:
        """Create RAG blueprint.

        Provide either `model` (simple) or `agent` (advanced):
        - `model`: Blueprint creates a simple internal agent
        - `agent`: Use your pre-configured agent (with memory, interceptors, etc.)

        Args:
            retriever: Single retriever for document search.
            model: LLM model (simple mode - blueprint creates agent).
            agent: Pre-configured agent (advanced mode - you control agent config).
            retrievers: Multiple retrievers to ensemble.
            weights: Weights for each retriever.
            fusion: Fusion strategy: "rrf", "linear", "max", "voting".
            reranker: Optional reranker for two-stage retrieval.
            config: RAG configuration options.
            postprocessors: Custom post-processors (override default citation formatting).

        Example (simple - just model):
            ```python
            rag = RAG(retriever=retriever, model=model)
            ```

        Example (advanced - pre-configured agent):
            ```python
            agent = Agent(
                model=model,
                memory=memory,
                intercept=[BudgetGuard(...)],
            )
            rag = RAG(retriever=retriever, agent=agent)
            ```

        Example (custom processors):
            ```python
            rag = RAG(
                retriever=retriever,
                model=model,
                postprocessors=[
                    CitationFormatter(style=CitationStyle.FOOTNOTE),
                    # No bibliography
                ],
            )
            ```

        Raises:
            ValueError: If neither model nor agent provided, or both provided.
        """
        super().__init__()

        # Validate model/agent
        if model is None and agent is None:
            raise ValueError("Must provide either 'model' or 'agent'")
        if model is not None and agent is not None:
            raise ValueError("Provide either 'model' or 'agent', not both")

        # Validate retriever
        if retriever is None and not retrievers:
            raise ValueError("Must provide either 'retriever' or 'retrievers'")
        if retriever is not None and retrievers:
            raise ValueError("Provide either 'retriever' or 'retrievers', not both")

        # Build retriever
        if retrievers:
            from agenticflow.retriever import EnsembleRetriever
            from agenticflow.retriever.base import FusionStrategy as FS

            fusion_strategy = FS(fusion) if isinstance(fusion, str) else fusion
            self._retriever = EnsembleRetriever(
                retrievers=retrievers,
                weights=weights,
                fusion=fusion_strategy,
            )
        else:
            self._retriever = retriever  # type: ignore

        self._reranker = reranker
        self._config = config or RAGConfig()

        # Create or use agent
        if agent is not None:
            self._agent = agent
            self._agent._direct_tools.append(self._create_search_tool())
        else:
            self._agent = Agent(
                name="rag-agent",
                model=model,
                tools=[self._create_search_tool()],
                instructions=self.SYSTEM_PROMPT,
            )

        # Setup post-processors
        if postprocessors is not None:
            self._postprocessors = list(postprocessors)
        else:
            # Default: citation formatting + bibliography
            cfg = self._config
            self._postprocessors = [
                CitationFormatter(style=cfg.citation_style),
            ]
            if cfg.include_bibliography:
                self._postprocessors.append(
                    BibliographyAppender(include_scores=cfg.include_score_in_bibliography)
                )

    @property
    def name(self) -> str:
        return "rag"

    @property
    def retriever(self) -> Retriever:
        """The underlying retriever."""
        return self._retriever

    @property
    def config(self) -> RAGConfig:
        """Current configuration."""
        return self._config

    def _create_search_tool(self):
        """Create the search tool for the internal agent."""
        blueprint = self
        cfg = self._config

        @tool
        async def search_documents(query: str, num_results: int = 4) -> str:
            """Search documents for relevant passages.

            Args:
                query: Search query.
                num_results: Number of passages to retrieve.

            Returns:
                Retrieved passages with citation markers.
            """
            k = min(num_results, 10)
            passages = await blueprint._search(query, k=k)

            if not passages:
                return "No relevant passages found."

            # Filter by score threshold
            if cfg.score_threshold > 0:
                passages = [p for p in passages if p.score >= cfg.score_threshold]
                if not passages:
                    return "No passages met the relevance threshold."

            # Format for agent: «id» + content (minimal, collision-resistant)
            lines = []
            for p in passages:
                text = p.text
                if cfg.max_passage_length > 0 and len(text) > cfg.max_passage_length:
                    text = text[: cfg.max_passage_length] + "..."
                lines.append(f"«{p.citation_id}» {text}")

            return "\n\n".join(lines)

        return search_documents

    async def _search(self, query: str, k: int) -> list[CitedPassage]:
        """Internal search method."""
        results = await self._retriever.retrieve(query, k=k, include_scores=True)

        if self._reranker and results:
            results = await self._reranker.rerank(query, results, k=k)

        passages = []
        for i, result in enumerate(results, 1):
            doc = result.document
            passage = CitedPassage(
                citation_id=i,
                source=doc.metadata.get("source", "unknown"),
                page=doc.metadata.get("page"),
                score=result.score,
                text=doc.text,
            )
            passages.append(passage)

        return passages

    async def run(self, input: str, **kwargs: Any) -> str:
        """Execute RAG and return formatted output (Flow-compatible).

        Args:
            input: The question to answer.
            **kwargs: Additional arguments passed to agent.

        Returns:
            Formatted string with citations and bibliography.
        """
        result = await self.run_detailed(input, **kwargs)
        return result.output

    async def run_detailed(
        self,
        input: str,
        *,
        include_bibliography: bool | None = None,
        **kwargs: Any,
    ) -> RAGResult:
        """Execute RAG with full metadata.

        Args:
            input: The question to answer.
            include_bibliography: Override config setting.
            **kwargs: Additional arguments passed to agent.

        Returns:
            RAGResult with formatted output and metadata.
        """
        # Run agent (uses search tool internally)
        raw_output = await self._agent.run(input, **kwargs)

        # Get passages from last search (via search tool closure)
        passages = await self._search(input, k=self._config.top_k)

        # Build context with passages
        ctx = BlueprintContext(
            input=input,
            output=raw_output,
        ).with_metadata(passages=passages)

        # Handle bibliography override
        if include_bibliography is False:
            # Remove BibliographyAppender if present
            processors = [
                p for p in self._postprocessors
                if not isinstance(p, BibliographyAppender)
            ]
        elif include_bibliography is True and not any(
            isinstance(p, BibliographyAppender) for p in self._postprocessors
        ):
            # Add BibliographyAppender if not present
            processors = list(self._postprocessors) + [
                BibliographyAppender(
                    include_scores=self._config.include_score_in_bibliography
                )
            ]
        else:
            processors = self._postprocessors

        # Run post-processors
        for processor in processors:
            ctx = await processor(ctx)

        return RAGResult(
            output=ctx.output,
            raw_output=raw_output,
            passages=tuple(passages),
            query=input,
            context=ctx,
            metadata={
                "num_passages": len(passages),
                "citation_style": self._config.citation_style.value,
            },
        )

    # ================================================================
    # Direct access methods (for advanced usage)
    # ================================================================

    async def search(self, query: str, k: int | None = None) -> list[CitedPassage]:
        """Direct search without generation.

        Args:
            query: Search query.
            k: Number of results.

        Returns:
            List of cited passages.
        """
        return await self._search(query, k=k or self._config.top_k)


__all__ = [
    "RAG",
    "RAGConfig",
    "RAGResult",
    "CitationStyle",
    "CitedPassage",
]
