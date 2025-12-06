"""
FactCheck Blueprint.

Verify claims against retrieved sources with confidence scoring.

Example:
    ```python
    from agenticflow.blueprints import FactCheck

    fact_check = FactCheck(
        retriever=retriever,
        model=model,
    )

    result = await fact_check.run("The Eiffel Tower is 300 meters tall")
    print(result)  # Verdict with evidence
    ```

Usage in Flow:
    ```python
    flow = Flow(
        agents=[rag, fact_check],
        topology="pipeline",
    )
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from agenticflow.agent import Agent
from agenticflow.blueprints.base import BaseBlueprint, BlueprintResult
from agenticflow.blueprints.context import BlueprintContext
from agenticflow.blueprints.processors import CitedPassage
from agenticflow.tools.base import tool

if TYPE_CHECKING:
    from agenticflow.models import BaseChatModel
    from agenticflow.retriever.base import Retriever


class Verdict(str, Enum):
    """Fact-check verdict."""

    SUPPORTED = "supported"
    REFUTED = "refuted"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_ENOUGH_EVIDENCE = "not_enough_evidence"


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceItem:
    """A piece of evidence for/against a claim.

    Attributes:
        passage: The source passage.
        supports: Whether this evidence supports (True) or refutes (False) the claim.
        relevance: How relevant this evidence is (0.0-1.0).
        explanation: Why this evidence is relevant.
    """

    passage: CitedPassage
    supports: bool
    relevance: float = 0.0
    explanation: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class FactCheckConfig:
    """Configuration for FactCheck blueprint.

    Attributes:
        num_evidence: Number of evidence passages to retrieve.
        confidence_threshold: Minimum confidence for verdict.
        require_multiple_sources: Require 2+ sources for high confidence.
    """

    num_evidence: int = 5
    confidence_threshold: float = 0.6
    require_multiple_sources: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class FactCheckResult(BlueprintResult):
    """Result from FactCheck blueprint execution.

    Attributes:
        output: Formatted verdict with explanation.
        verdict: The fact-check verdict.
        confidence: Confidence in the verdict (0.0-1.0).
        claim: The original claim.
        supporting_evidence: Evidence that supports the claim.
        refuting_evidence: Evidence that refutes the claim.
    """

    verdict: Verdict = Verdict.NOT_ENOUGH_EVIDENCE
    confidence: float = 0.0
    claim: str = ""
    supporting_evidence: tuple[EvidenceItem, ...] = ()
    refuting_evidence: tuple[EvidenceItem, ...] = ()


class FactCheck(BaseBlueprint):
    """Fact-checking blueprint.

    Verifies claims against retrieved sources and provides
    a verdict with confidence scoring and evidence.

    Flow-compatible: can be used as a resident in Flow topologies.
    Tool-compatible: can be converted to tool via `as_tool()`.

    Example - Basic:
        ```python
        fact_check = FactCheck(
            retriever=retriever,
            model=model,
        )
        result = await fact_check.run("The moon is made of cheese")
        print(f"Verdict: {result.verdict}, Confidence: {result.confidence}")
        ```

    Example - In Pipeline:
        ```python
        # RAG generates answer, FactCheck verifies it
        flow = Flow(
            agents=[rag, fact_check],
            topology="pipeline",
        )
        ```
    """

    SYSTEM_PROMPT = """You are a fact-checker that verifies claims against evidence.

Your task:
1. Use search_evidence to find relevant sources
2. Analyze whether the evidence SUPPORTS or REFUTES the claim
3. Provide a verdict with confidence level

Be objective and cite specific evidence. If evidence is conflicting or insufficient, say so.

IMPORTANT: Always respond in this exact format:
VERDICT: [SUPPORTED|REFUTED|PARTIALLY_SUPPORTED|NOT_ENOUGH_EVIDENCE]
CONFIDENCE: [0.0-1.0]
EXPLANATION: [Your detailed explanation with citations using «n» markers]"""

    def __init__(
        self,
        retriever: Retriever,
        model: BaseChatModel,
        *,
        config: FactCheckConfig | None = None,
    ) -> None:
        """Create FactCheck blueprint.

        Args:
            retriever: Retriever for evidence search.
            model: LLM model for reasoning.
            config: Configuration options.

        Example:
            ```python
            fact_check = FactCheck(
                retriever=retriever,
                model=model,
                config=FactCheckConfig(num_evidence=10),
            )
            ```
        """
        super().__init__()

        self._retriever = retriever
        self._model = model
        self._config = config or FactCheckConfig()

        # Track evidence
        self._passages: list[CitedPassage] = []

        # Create internal agent
        self._agent = Agent(
            name="factcheck-agent",
            model=model,
            tools=[self._create_search_tool()],
            instructions=self.SYSTEM_PROMPT,
        )

    @property
    def name(self) -> str:
        return "factcheck"

    @property
    def config(self) -> FactCheckConfig:
        """Current configuration."""
        return self._config

    def _create_search_tool(self):
        """Create the evidence search tool."""
        blueprint = self
        cfg = self._config

        @tool
        async def search_evidence(query: str) -> str:
            """Search for evidence to verify a claim.

            Args:
                query: Search query related to the claim.

            Returns:
                Retrieved evidence passages with citation markers.
            """
            results = await blueprint._retriever.retrieve(
                query, k=cfg.num_evidence, include_scores=True
            )

            if not results:
                return "No evidence found for this query."

            lines = []
            for i, result in enumerate(results, 1):
                doc = result.document
                passage = CitedPassage(
                    citation_id=i,
                    source=doc.metadata.get("source", "unknown"),
                    page=doc.metadata.get("page"),
                    score=result.score,
                    text=doc.text,
                )
                blueprint._passages.append(passage)
                lines.append(f"«{i}» [{passage.source}] {doc.text}")

            return "\n\n".join(lines)

        return search_evidence

    def _reset_state(self) -> None:
        """Reset internal state for new claim."""
        self._passages = []

    def _parse_response(self, response: str) -> tuple[Verdict, float, str]:
        """Parse the agent's structured response.

        Args:
            response: Raw agent response.

        Returns:
            Tuple of (verdict, confidence, explanation).
        """
        verdict = Verdict.NOT_ENOUGH_EVIDENCE
        confidence = 0.0
        explanation = response

        lines = response.strip().split("\n")
        for line in lines:
            line_upper = line.upper().strip()
            if line_upper.startswith("VERDICT:"):
                verdict_str = line.split(":", 1)[1].strip().upper()
                verdict_str = verdict_str.replace(" ", "_")
                try:
                    verdict = Verdict(verdict_str.lower())
                except ValueError:
                    pass
            elif line_upper.startswith("CONFIDENCE:"):
                try:
                    conf_str = line.split(":", 1)[1].strip()
                    confidence = float(conf_str)
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, IndexError):
                    pass
            elif line_upper.startswith("EXPLANATION:"):
                explanation = line.split(":", 1)[1].strip()
                # Get rest of response as explanation
                idx = response.find("EXPLANATION:")
                if idx >= 0:
                    explanation = response[idx + len("EXPLANATION:") :].strip()

        return verdict, confidence, explanation

    def _format_output(
        self,
        verdict: Verdict,
        confidence: float,
        explanation: str,
    ) -> str:
        """Format the final output."""
        verdict_emoji = {
            Verdict.SUPPORTED: "✓",
            Verdict.REFUTED: "✗",
            Verdict.PARTIALLY_SUPPORTED: "◐",
            Verdict.NOT_ENOUGH_EVIDENCE: "?",
        }

        emoji = verdict_emoji.get(verdict, "?")
        verdict_display = verdict.value.replace("_", " ").title()

        output = f"""{emoji} **{verdict_display}** (confidence: {confidence:.0%})

{explanation}"""

        # Add bibliography
        if self._passages:
            output += "\n\n---\n**Sources:**"
            seen_sources: set[str] = set()
            for p in self._passages:
                if p.source not in seen_sources:
                    seen_sources.add(p.source)
                    output += f"\n[{p.citation_id}] {p.source}"
                    if p.page:
                        output += f" p.{p.page}"

        return output

    async def run(self, input: str, **kwargs: Any) -> str:
        """Execute FactCheck and return formatted output (Flow-compatible).

        Args:
            input: The claim to verify.
            **kwargs: Additional arguments passed to agent.

        Returns:
            Formatted verdict with explanation and sources.
        """
        result = await self.run_detailed(input, **kwargs)
        return result.output

    async def run_detailed(
        self,
        input: str,
        **kwargs: Any,
    ) -> FactCheckResult:
        """Execute FactCheck with full metadata.

        Args:
            input: The claim to verify.
            **kwargs: Additional arguments passed to agent.

        Returns:
            FactCheckResult with verdict, confidence, and evidence.
        """
        # Reset state
        self._reset_state()

        # Create verification prompt
        prompt = f"""Verify this claim:

"{input}"

Search for evidence and provide your verdict."""

        # Run agent
        raw_output = await self._agent.run(prompt, **kwargs)

        # Parse response
        verdict, confidence, explanation = self._parse_response(raw_output)

        # Format output
        formatted = self._format_output(verdict, confidence, explanation)

        # Categorize evidence (simplified - in practice, the agent would classify)
        supporting = []
        refuting = []
        for p in self._passages:
            # High-scoring passages are considered relevant
            if p.score > 0.5:
                item = EvidenceItem(
                    passage=p,
                    supports=verdict == Verdict.SUPPORTED,
                    relevance=p.score,
                )
                if verdict in (Verdict.SUPPORTED, Verdict.PARTIALLY_SUPPORTED):
                    supporting.append(item)
                elif verdict == Verdict.REFUTED:
                    refuting.append(item)

        return FactCheckResult(
            output=formatted,
            verdict=verdict,
            confidence=confidence,
            claim=input,
            supporting_evidence=tuple(supporting),
            refuting_evidence=tuple(refuting),
            metadata={
                "num_sources": len(self._passages),
                "unique_sources": len({p.source for p in self._passages}),
            },
        )


__all__ = [
    "FactCheck",
    "FactCheckConfig",
    "FactCheckResult",
    "Verdict",
    "EvidenceItem",
]
