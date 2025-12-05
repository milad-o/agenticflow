"""
RAG (Retrieval-Augmented Generation) Blueprint.

A pre-configured agent workflow for retrieval-augmented generation.
Uses an internal Agent with search tools and deterministic citation formatting.

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
    print(result.output)
    ```

Citation Design:
    - Agent sees unique markers: «1», «2» (collision-resistant)
    - Agent references these in its response
    - Post-processing replaces markers with formatted citations
    - Bibliography appended deterministically
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from agenticflow.blueprints.base import BaseBlueprint, BlueprintResult
from agenticflow.agent import Agent
from agenticflow.tools.base import tool

if TYPE_CHECKING:
    from agenticflow.models import BaseChatModel
    from agenticflow.retriever.base import FusionStrategy, Retriever
    from agenticflow.retriever.rerankers.base import Reranker


# Citation marker: «1», «2» - guillemets are collision-resistant
CITE_MARKER_PATTERN = re.compile(r"«(\d+)»")


class CitationStyle(Enum):
    """Citation formatting styles for final output."""

    NUMERIC = "numeric"  # [1], [2], [3]
    AUTHOR_YEAR = "author_year"  # (Source, 2023)
    FOOTNOTE = "footnote"  # ¹, ², ³
    INLINE = "inline"  # [source.pdf]


@dataclass(frozen=True, slots=True, kw_only=True)
class CitedPassage:
    """A retrieved passage with citation metadata.

    Attributes:
        citation_id: Citation reference number (1, 2, 3...).
        source: Source document name.
        page: Page number if available.
        score: Relevance score (0.0-1.0).
        text: The passage text.
    """

    citation_id: int
    source: str
    page: int | None = None
    score: float = 0.0
    text: str = ""


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
    citation formatting deterministically.

    Example:
        ```python
        from agenticflow.blueprints import RAG

        rag = RAG(retriever=retriever, model=model)
        result = await rag.run("What are the key findings?")
        print(result.output)  # Formatted with citations + bibliography
        ```

    Example with multiple retrievers:
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

        Raises:
            ValueError: If neither model nor agent provided, or both provided.
        """
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

        # Storage for last search results (for citation mapping)
        self._last_passages: list[CitedPassage] = []

        # Create or use agent
        if agent is not None:
            # Advanced mode: use provided agent, add search tool
            self._agent = agent
            # Add search tool to agent's direct tools
            self._agent._direct_tools.append(self._create_search_tool())
        else:
            # Simple mode: create minimal agent
            self._agent = Agent(
                name="rag-agent",
                model=model,
                tools=[self._create_search_tool()],
                instructions=self.SYSTEM_PROMPT,
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

        self._last_passages = passages
        return passages

    async def run(
        self,
        query: str,
        *,
        include_bibliography: bool | None = None,
        **kwargs: Any,
    ) -> RAGResult:
        """Execute RAG: retrieve, generate, format citations.

        Args:
            query: The question to answer.
            include_bibliography: Override config setting.
            **kwargs: Additional arguments passed to agent.

        Returns:
            RAGResult with formatted output and metadata.
        """
        # Run agent (uses search tool internally)
        raw_output = await self._agent.run(query, **kwargs)

        # Post-process: replace «1» → [1] and add bibliography
        formatted = self._format_output(
            raw_output,
            include_bibliography=include_bibliography,
        )

        return RAGResult(
            output=formatted,
            raw_output=raw_output,
            passages=tuple(self._last_passages),
            query=query,
            metadata={
                "num_passages": len(self._last_passages),
                "citation_style": self._config.citation_style.value,
            },
        )

    def _format_output(
        self,
        raw: str,
        include_bibliography: bool | None = None,
    ) -> str:
        """Format raw output with citations and bibliography.

        Replaces «1», «2» markers with formatted citations.
        Appends bibliography if configured.
        """
        cfg = self._config
        include_bib = (
            include_bibliography
            if include_bibliography is not None
            else cfg.include_bibliography
        )

        # Build citation lookup
        citation_map: dict[int, CitedPassage] = {
            p.citation_id: p for p in self._last_passages
        }

        # Replace markers with formatted citations
        def replace_marker(match: re.Match) -> str:
            cid = int(match.group(1))
            passage = citation_map.get(cid)
            if not passage:
                return match.group(0)  # Keep original if not found
            return self._format_citation(passage)

        formatted = CITE_MARKER_PATTERN.sub(replace_marker, raw)

        # Append bibliography
        if include_bib and self._last_passages:
            formatted += self._format_bibliography()

        return formatted

    def _format_citation(self, passage: CitedPassage) -> str:
        """Format a single citation reference."""
        style = self._config.citation_style

        if style == CitationStyle.NUMERIC:
            if passage.page is not None:
                return f"[{passage.citation_id}, p.{passage.page}]"
            return f"[{passage.citation_id}]"
        elif style == CitationStyle.FOOTNOTE:
            superscripts = "⁰¹²³⁴⁵⁶⁷⁸⁹"
            num_str = "".join(superscripts[int(d)] for d in str(passage.citation_id))
            return num_str
        elif style == CitationStyle.INLINE:
            return f"[{passage.source}]"
        elif style == CitationStyle.AUTHOR_YEAR:
            return f"({passage.source})"

        return f"[{passage.citation_id}]"

    def _format_bibliography(self) -> str:
        """Format bibliography section."""
        if not self._last_passages:
            return ""

        cfg = self._config

        # Deduplicate by source
        seen: dict[str, CitedPassage] = {}
        for p in self._last_passages:
            if p.source not in seen:
                seen[p.source] = p

        lines = ["\n\n---\n**References:**"]
        for p in seen.values():
            parts = [f"[{p.citation_id}]", p.source]
            if p.page is not None:
                parts.append(f"p.{p.page}")
            if cfg.include_score_in_bibliography:
                parts.append(f"(score: {p.score:.2f})")
            lines.append(" ".join(parts))

        return "\n".join(lines)

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
