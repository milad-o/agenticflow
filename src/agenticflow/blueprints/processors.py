"""
Citation processors for RAG blueprint.

These are composable post-processors that handle citation formatting
and bibliography generation. They can be used independently or combined.

Example:
    from agenticflow.blueprints.processors import (
        CitationFormatter,
        BibliographyAppender,
    )

    rag = RAG(
        retriever=retriever,
        model=model,
        postprocessors=[
            CitationFormatter(style=CitationStyle.NUMERIC),
            BibliographyAppender(include_scores=True),
        ],
    )
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agenticflow.blueprints.context import BlueprintContext

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


class CitationFormatter:
    """Post-processor that replaces «n» markers with formatted citations.

    Transforms agent output from:
        "According to «1», the answer is X."
    To:
        "According to [1], the answer is X."

    The actual format depends on the citation style.
    """

    # Superscript digits for footnote style
    SUPERSCRIPTS = "⁰¹²³⁴⁵⁶⁷⁸⁹"

    def __init__(self, style: CitationStyle = CitationStyle.NUMERIC) -> None:
        """Create citation formatter.

        Args:
            style: Citation formatting style.
        """
        self.style = style

    async def __call__(self, ctx: BlueprintContext) -> BlueprintContext:
        """Format citations in the output.

        Args:
            ctx: Blueprint context with output and passages in metadata.

        Returns:
            Context with formatted citations.
        """
        passages: list[CitedPassage] = ctx.get("passages", [])
        citation_map = {p.citation_id: p for p in passages}

        def replace_marker(match: re.Match) -> str:
            cid = int(match.group(1))
            passage = citation_map.get(cid)
            if not passage:
                return match.group(0)  # Keep original if not found
            return self._format_single(passage)

        formatted = CITE_MARKER_PATTERN.sub(replace_marker, ctx.output)
        return ctx.with_output(formatted)

    def _format_single(self, passage: CitedPassage) -> str:
        """Format a single citation reference."""
        if self.style == CitationStyle.NUMERIC:
            if passage.page is not None:
                return f"[{passage.citation_id}, p.{passage.page}]"
            return f"[{passage.citation_id}]"
        elif self.style == CitationStyle.FOOTNOTE:
            num_str = "".join(
                self.SUPERSCRIPTS[int(d)] for d in str(passage.citation_id)
            )
            return num_str
        elif self.style == CitationStyle.INLINE:
            return f"[{passage.source}]"
        elif self.style == CitationStyle.AUTHOR_YEAR:
            return f"({passage.source})"

        return f"[{passage.citation_id}]"


class BibliographyAppender:
    """Post-processor that appends a bibliography section.

    Adds a formatted reference list at the end of the output.
    """

    def __init__(
        self,
        *,
        include_scores: bool = True,
        header: str = "\n\n---\n**References:**",
    ) -> None:
        """Create bibliography appender.

        Args:
            include_scores: Show relevance scores in bibliography.
            header: Header text for bibliography section.
        """
        self.include_scores = include_scores
        self.header = header

    async def __call__(self, ctx: BlueprintContext) -> BlueprintContext:
        """Append bibliography to output.

        Args:
            ctx: Blueprint context with passages in metadata.

        Returns:
            Context with bibliography appended.
        """
        passages: list[CitedPassage] = ctx.get("passages", [])
        if not passages:
            return ctx

        bibliography = self._format_bibliography(passages)
        return ctx.with_output(ctx.output + bibliography)

    def _format_bibliography(self, passages: list[CitedPassage]) -> str:
        """Format bibliography section."""
        # Deduplicate by source
        seen: dict[str, CitedPassage] = {}
        for p in passages:
            if p.source not in seen:
                seen[p.source] = p

        lines = [self.header]
        for p in seen.values():
            parts = [f"[{p.citation_id}]", p.source]
            if p.page is not None:
                parts.append(f"p.{p.page}")
            if self.include_scores:
                parts.append(f"(score: {p.score:.2f})")
            lines.append(" ".join(parts))

        return "\n".join(lines)


__all__ = [
    "CITE_MARKER_PATTERN",
    "CitationStyle",
    "CitedPassage",
    "CitationFormatter",
    "BibliographyAppender",
]
