"""
RAG (Retrieval-Augmented Generation) capability.

A thin capability that provides document search tools to agents.
Document loading and indexing happens OUTSIDE this capability.

Example (single retriever):
    ```python
    from agenticflow import Agent
    from agenticflow.capabilities import RAG
    from agenticflow.retriever import DenseRetriever
    from agenticflow.vectorstore import VectorStore
    from agenticflow.document import DocumentLoader, RecursiveCharacterSplitter

    # 1. Load and index documents (outside RAG)
    loader = DocumentLoader()
    docs = await loader.load_directory("docs/")
    chunks = RecursiveCharacterSplitter(chunk_size=1000).split_documents(docs)

    store = VectorStore(embeddings=embeddings)
    await store.add_documents(chunks)

    # 2. Create retriever and RAG
    rag = RAG(DenseRetriever(store))

    # 3. Add to agent
    agent = Agent(model=model, capabilities=[rag])
    answer = await agent.run("What are the key findings?")
    ```

Example (multiple retrievers with fusion):
    ```python
    from agenticflow.retriever import DenseRetriever, BM25Retriever

    dense = DenseRetriever(store)
    sparse = BM25Retriever(chunks)

    # RAG creates ensemble internally
    rag = RAG(
        retrievers=[dense, sparse],
        weights=[0.6, 0.4],
        fusion="rrf",  # or "linear", "max", "voting"
    )
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from agenticflow.capabilities.base import BaseCapability
from agenticflow.tools.base import tool

if TYPE_CHECKING:
    from agenticflow.retriever.base import FusionStrategy, Retriever
    from agenticflow.retriever.rerankers.base import Reranker


# ============================================================
# Citation Types
# ============================================================


class CitationStyle(Enum):
    """Citation formatting styles."""

    NUMERIC = "numeric"  # [1], [2], [3]
    AUTHOR_YEAR = "author_year"  # (Smith, 2023)
    FOOTNOTE = "footnote"  # ¹, ², ³
    INLINE = "inline"  # [source.pdf], [doc.md]


@dataclass(frozen=True, slots=True, kw_only=True)
class CitedPassage:
    """A cited passage from a retrieved document.

    Attributes:
        citation_id: Citation reference number (1, 2, 3...).
        source: Source document name.
        page: Page number if available.
        chunk_index: Chunk index within document.
        score: Relevance score (0.0-1.0).
        text: The passage text.
    """

    citation_id: int
    source: str
    page: int | None = None
    chunk_index: int | None = None
    score: float = 0.0
    text: str = ""

    def format_reference(
        self,
        style: CitationStyle = CitationStyle.NUMERIC,
        include_page: bool = True,
    ) -> str:
        """Format as citation reference.

        Args:
            style: Citation style to use.
            include_page: Whether to include page number.

        Returns:
            Formatted citation string.
        """
        if style == CitationStyle.NUMERIC:
            if include_page and self.page is not None:
                return f"[{self.citation_id}, p.{self.page}]"
            return f"[{self.citation_id}]"
        elif style == CitationStyle.FOOTNOTE:
            superscripts = "⁰¹²³⁴⁵⁶⁷⁸⁹"
            num_str = "".join(superscripts[int(d)] for d in str(self.citation_id))
            return num_str
        elif style == CitationStyle.INLINE:
            return f"[{self.source}]"
        elif style == CitationStyle.AUTHOR_YEAR:
            return f"({self.source})"
        return f"[{self.citation_id}]"

    def format_full(self, include_score: bool = True) -> str:
        """Format as full bibliography entry.

        Args:
            include_score: Whether to include relevance score.

        Returns:
            Full citation with source, page, and optionally score.
        """
        parts = [f"[{self.citation_id}]", self.source]
        if self.page is not None:
            parts.append(f"p.{self.page}")
        if include_score:
            parts.append(f"(score: {self.score:.2f})")
        return " ".join(parts)


@dataclass(frozen=True, slots=True, kw_only=True)
class RAGConfig:
    """Configuration for RAG capability.

    The RAG tool sends minimal context to the LLM (just IDs + content).
    Full citation formatting happens deterministically post-processing.

    Attributes:
        top_k: Default number of results to retrieve.
        score_threshold: Minimum score to include in results (0.0-1.0).
        max_passage_length: Truncate passages longer than this (0 = no limit).
        citation_style: How to format citations in final output.
        include_score_in_bibliography: Show scores in bibliography.

    Example:
        ```python
        config = RAGConfig(
            top_k=5,
            citation_style=CitationStyle.AUTHOR_YEAR,
            max_passage_length=500,
        )
        rag = RAG(retriever, config=config)
        ```
    """

    # Retrieval settings
    top_k: int = 4
    score_threshold: float = 0.0
    max_passage_length: int = 0  # 0 = no limit

    # Citation formatting (for post-processing, NOT sent to LLM)
    citation_style: CitationStyle = CitationStyle.NUMERIC
    include_score_in_bibliography: bool = True


# ============================================================
# RAG Capability
# ============================================================


class RAG(BaseCapability):
    """RAG (Retrieval-Augmented Generation) capability.

    A thin capability that provides document search tools to agents.
    Document loading and indexing happens OUTSIDE this capability.

    Example (single retriever):
        ```python
        from agenticflow import Agent
        from agenticflow.capabilities import RAG
        from agenticflow.retriever import DenseRetriever
        from agenticflow.vectorstore import VectorStore

        # Prepare retriever
        store = VectorStore(embeddings=embeddings)
        await store.add_documents(chunks)
        retriever = DenseRetriever(store)

        # Create RAG and add to agent
        rag = RAG(retriever)
        agent = Agent(model=model, capabilities=[rag])
        ```

    Example (multiple retrievers with fusion):
        ```python
        from agenticflow.retriever import DenseRetriever, BM25Retriever

        # Create multiple retrievers
        dense = DenseRetriever(store)
        sparse = BM25Retriever(chunks)

        # RAG fuses them automatically (default: RRF)
        rag = RAG(
            retrievers=[dense, sparse],
            weights=[0.6, 0.4],
            fusion="rrf",  # or "linear", "max", "voting"
        )
        ```
    """

    DEFAULT_INSTRUCTIONS = """When answering questions:
1. Use search_documents to find relevant information first
2. Base answers ONLY on retrieved passages - do not make up information
3. Cite sources using [1], [2], etc. matching the search results
4. Include page numbers when available: [1, p.5]
5. If information isn't in documents, say so explicitly"""

    def __init__(
        self,
        retriever: Retriever | None = None,
        *,
        retrievers: list[Retriever] | None = None,
        weights: list[float] | None = None,
        fusion: FusionStrategy | str = "rrf",
        reranker: Reranker | None = None,
        config: RAGConfig | None = None,
    ) -> None:
        """Create RAG capability.

        Args:
            retriever: Single retriever for document search.
            retrievers: Multiple retrievers to ensemble (alternative to retriever).
            weights: Weights for each retriever (default: equal weights).
            fusion: Fusion strategy: "rrf", "linear", "max", "voting".
            reranker: Optional reranker for two-stage retrieval.
            config: RAG configuration options.

        Example:
            ```python
            # Single retriever
            rag = RAG(DenseRetriever(store))

            # Multiple retrievers with fusion
            rag = RAG(
                retrievers=[dense, sparse],
                weights=[0.6, 0.4],
                fusion="rrf",
            )

            # With reranking
            rag = RAG(
                retriever=dense,
                reranker=CrossEncoderReranker(),
            )
            ```

        Raises:
            ValueError: If neither retriever nor retrievers is provided,
                or if both are provided.
        """
        # Validate inputs
        if retriever is None and not retrievers:
            raise ValueError("Must provide either 'retriever' or 'retrievers'")
        if retriever is not None and retrievers:
            raise ValueError("Provide either 'retriever' or 'retrievers', not both")

        # Build the retriever
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
        self._last_citations: list[CitedPassage] = []

    # ================================================================
    # Properties
    # ================================================================

    @property
    def name(self) -> str:
        return "rag"

    @property
    def description(self) -> str:
        return "Document retrieval and search"

    @property
    def tools(self) -> list:
        return self._create_tools()

    @property
    def retriever(self) -> Retriever:
        """The underlying retriever."""
        return self._retriever

    @property
    def citations(self) -> list[CitedPassage]:
        """Citations from last search."""
        return list(self._last_citations)

    @property
    def top_k(self) -> int:
        """Default number of results to retrieve."""
        return self._config.top_k

    # ================================================================
    # Search
    # ================================================================

    async def search(self, query: str, k: int | None = None) -> list[CitedPassage]:
        """Search for relevant passages.

        Args:
            query: Search query.
            k: Number of results (default: config.top_k).

        Returns:
            List of cited passages with source and score.

        Example:
            ```python
            passages = await rag.search("machine learning best practices", k=5)
            for p in passages:
                print(f"{p.format_reference()}: {p.text[:100]}...")
            ```
        """
        k = k or self._config.top_k

        # Retrieve with scores
        results = await self._retriever.retrieve(query, k=k, include_scores=True)

        # Rerank if configured
        if self._reranker and results:
            results = await self._reranker.rerank(query, results, k=k)

        # Convert to cited passages
        passages = []
        for i, result in enumerate(results, 1):
            doc = result.document
            passage = CitedPassage(
                citation_id=i,
                source=doc.metadata.get("source", "unknown"),
                page=doc.metadata.get("page"),
                chunk_index=doc.metadata.get("chunk_index"),
                score=result.score,
                text=doc.text,
            )
            passages.append(passage)

        self._last_citations = passages
        return passages

    def format_bibliography(
        self,
        passages: list[CitedPassage] | None = None,
        title: str = "References",
    ) -> str:
        """Format passages as bibliography.

        Args:
            passages: Passages to format (default: last search results).
            title: Bibliography section title.

        Returns:
            Formatted bibliography string.
        """
        passages = passages or self._last_citations

        if not passages:
            return ""

        # Deduplicate by source
        seen_sources: dict[str, CitedPassage] = {}
        for p in passages:
            if p.source not in seen_sources:
                seen_sources[p.source] = p

        lines = [f"\n---\n**{title}:**"]
        for p in seen_sources.values():
            lines.append(
                p.format_full(
                    include_score=self._config.include_score_in_bibliography,
                )
            )

        return "\n".join(lines)

    # ================================================================
    # Tools
    # ================================================================

    def _create_tools(self) -> list:
        """Create RAG tools for the agent.

        The tool sends MINIMAL context to the LLM:
        - Just [id] + content (no metadata bloat)
        - Citations are stored internally and mapped deterministically

        The LLM just needs to reference [1], [2], etc.
        Full citation formatting happens in format_response().
        """
        cap = self
        cfg = self._config

        @tool
        async def search_documents(query: str, num_results: int = 4) -> str:
            """Search documents for relevant passages.

            Args:
                query: Search query.
                num_results: Number of passages (default: 4).

            Returns:
                Passages with IDs. Reference using [1], [2], etc.
            """
            k = min(num_results, 10)
            passages = await cap.search(query, k=k)

            if not passages:
                return "No relevant passages found."

            # Filter by score threshold
            if cfg.score_threshold > 0:
                passages = [p for p in passages if p.score >= cfg.score_threshold]
                if not passages:
                    return "No passages met the relevance threshold."

            # Format MINIMAL output for LLM: just [id] + content
            # NO source, page, score - that's all handled deterministically later
            lines = []
            for p in passages:
                text = p.text
                if cfg.max_passage_length > 0 and len(text) > cfg.max_passage_length:
                    text = text[: cfg.max_passage_length] + "..."
                lines.append(f"[{p.citation_id}] {text}")

            return "\n\n".join(lines)

        return [search_documents]

    def format_response(
        self,
        response: str,
        passages: list[CitedPassage] | None = None,
        include_bibliography: bool = True,
    ) -> str:
        """Format LLM response with proper citations.

        Replaces [1], [2] references with formatted citations
        based on citation_style, and optionally appends bibliography.

        This is the DETERMINISTIC post-processing step - no LLM involved.

        Args:
            response: Raw LLM response containing [1], [2] references.
            passages: Passages to use (default: last search results).
            include_bibliography: Whether to append bibliography.

        Returns:
            Response with formatted citations and optional bibliography.

        Example:
            ```python
            raw = await agent.run("What did Mary look like?")
            # raw: "Mary had yellow hair [1] and a sour expression [2]."

            formatted = rag.format_response(raw)
            # formatted: "Mary had yellow hair [1] and a sour expression [2].
            #
            # ---
            # **References:**
            # [1] the_secret_garden.txt p.1 (score: 0.92)
            # [2] the_secret_garden.txt p.1 (score: 0.87)"
            ```
        """
        passages = passages or self._last_citations
        if not passages:
            return response

        result = response

        # Optionally append bibliography
        if include_bibliography:
            result += self.format_bibliography(passages)

        return result


__all__ = [
    "RAG",
    "RAGConfig",
    "CitedPassage",
    "CitationStyle",
]
