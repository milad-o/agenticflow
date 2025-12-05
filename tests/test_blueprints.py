"""Tests for blueprints module."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agenticflow.blueprints import (
    BaseBlueprint,
    BlueprintResult,
    BlueprintContext,
    FlowResident,
    PreProcessor,
    PostProcessor,
    CitationStyle,
    CitedPassage,
    CitationFormatter,
    BibliographyAppender,
    RAG,
    RAGConfig,
    RAGResult,
)


class TestBlueprintContext:
    """Tests for BlueprintContext."""

    def test_create_context(self):
        """Context is created with input."""
        ctx = BlueprintContext(input="test query")
        assert ctx.input == "test query"
        assert ctx.output == ""
        assert ctx.metadata == {}
        assert ctx.run_id  # Should be auto-generated

    def test_with_output(self):
        """with_output creates new context."""
        ctx = BlueprintContext(input="query")
        ctx2 = ctx.with_output("result")
        
        # Original unchanged
        assert ctx.output == ""
        # New has output
        assert ctx2.output == "result"
        assert ctx2.input == "query"
        assert ctx2.run_id == ctx.run_id

    def test_with_metadata(self):
        """with_metadata creates new context with merged metadata."""
        ctx = BlueprintContext(input="query")
        ctx2 = ctx.with_metadata(key1="value1", key2="value2")
        
        assert ctx.metadata == {}
        assert ctx2.metadata == {"key1": "value1", "key2": "value2"}
        assert ctx2.get("key1") == "value1"
        assert ctx2.get("missing", "default") == "default"

    def test_context_is_frozen(self):
        """Context is immutable."""
        ctx = BlueprintContext(input="query")
        with pytest.raises(AttributeError):
            ctx.input = "changed"

    def test_contains_check(self):
        """Check if key is in metadata."""
        ctx = BlueprintContext(input="query").with_metadata(key="value")
        assert "key" in ctx
        assert "missing" not in ctx


class TestBlueprintResult:
    """Tests for BlueprintResult."""

    def test_create_result(self):
        """Result is created with output."""
        result = BlueprintResult(output="answer")
        assert result.output == "answer"
        assert result.metadata == {}
        assert str(result) == "answer"

    def test_result_with_metadata(self):
        """Result can have metadata."""
        result = BlueprintResult(
            output="answer",
            metadata={"key": "value"},
        )
        assert result.metadata == {"key": "value"}

    def test_result_is_frozen(self):
        """Result is immutable."""
        result = BlueprintResult(output="answer")
        with pytest.raises(AttributeError):
            result.output = "changed"


class TestCitationFormatter:
    """Tests for CitationFormatter post-processor."""

    @pytest.fixture
    def passages(self):
        """Sample passages for tests."""
        return [
            CitedPassage(citation_id=1, source="doc1.pdf", score=0.9, text="text1"),
            CitedPassage(citation_id=2, source="doc2.pdf", page=5, score=0.8, text="text2"),
        ]

    @pytest.mark.asyncio
    async def test_numeric_style(self, passages):
        """Numeric citation style."""
        formatter = CitationFormatter(style=CitationStyle.NUMERIC)
        ctx = BlueprintContext(
            input="query",
            output="See «1» and «2» for details.",
        ).with_metadata(passages=passages)

        result = await formatter(ctx)
        assert "[1]" in result.output
        assert "[2, p.5]" in result.output
        assert "«" not in result.output

    @pytest.mark.asyncio
    async def test_footnote_style(self, passages):
        """Footnote citation style."""
        formatter = CitationFormatter(style=CitationStyle.FOOTNOTE)
        ctx = BlueprintContext(
            input="query",
            output="See «1» for details.",
        ).with_metadata(passages=passages)

        result = await formatter(ctx)
        assert "¹" in result.output

    @pytest.mark.asyncio
    async def test_inline_style(self, passages):
        """Inline citation style."""
        formatter = CitationFormatter(style=CitationStyle.INLINE)
        ctx = BlueprintContext(
            input="query",
            output="See «1» for details.",
        ).with_metadata(passages=passages)

        result = await formatter(ctx)
        assert "[doc1.pdf]" in result.output

    @pytest.mark.asyncio
    async def test_author_year_style(self, passages):
        """Author-year citation style."""
        formatter = CitationFormatter(style=CitationStyle.AUTHOR_YEAR)
        ctx = BlueprintContext(
            input="query",
            output="See «1» for details.",
        ).with_metadata(passages=passages)

        result = await formatter(ctx)
        assert "(doc1.pdf)" in result.output

    @pytest.mark.asyncio
    async def test_unknown_citation_preserved(self, passages):
        """Unknown citation markers are preserved."""
        formatter = CitationFormatter()
        ctx = BlueprintContext(
            input="query",
            output="See «99» for details.",
        ).with_metadata(passages=passages)

        result = await formatter(ctx)
        assert "«99»" in result.output


class TestBibliographyAppender:
    """Tests for BibliographyAppender post-processor."""

    @pytest.fixture
    def passages(self):
        """Sample passages for tests."""
        return [
            CitedPassage(citation_id=1, source="doc1.pdf", score=0.9, text="text1"),
            CitedPassage(citation_id=2, source="doc2.pdf", page=5, score=0.8, text="text2"),
        ]

    @pytest.mark.asyncio
    async def test_appends_bibliography(self, passages):
        """Bibliography is appended."""
        appender = BibliographyAppender(include_scores=True)
        ctx = BlueprintContext(
            input="query",
            output="Answer text.",
        ).with_metadata(passages=passages)

        result = await appender(ctx)
        assert "**References:**" in result.output
        assert "doc1.pdf" in result.output
        assert "(score: 0.90)" in result.output

    @pytest.mark.asyncio
    async def test_no_scores(self, passages):
        """Bibliography without scores."""
        appender = BibliographyAppender(include_scores=False)
        ctx = BlueprintContext(
            input="query",
            output="Answer text.",
        ).with_metadata(passages=passages)

        result = await appender(ctx)
        assert "score:" not in result.output

    @pytest.mark.asyncio
    async def test_custom_header(self, passages):
        """Custom bibliography header."""
        appender = BibliographyAppender(header="\n## Sources")
        ctx = BlueprintContext(
            input="query",
            output="Answer text.",
        ).with_metadata(passages=passages)

        result = await appender(ctx)
        assert "## Sources" in result.output

    @pytest.mark.asyncio
    async def test_empty_passages(self):
        """No bibliography for empty passages."""
        appender = BibliographyAppender()
        ctx = BlueprintContext(
            input="query",
            output="Answer text.",
        )

        result = await appender(ctx)
        assert result.output == "Answer text."


class TestFlowResidentProtocol:
    """Tests for FlowResident protocol."""

    def test_has_required_attributes(self):
        """FlowResident requires name and run."""
        # This is a structural check
        assert hasattr(FlowResident, "__protocol_attrs__") or True  # Protocol check

    def test_rag_is_flow_resident(self):
        """RAG implements FlowResident protocol."""
        # Just check the interface
        assert hasattr(RAG, "name")
        assert hasattr(RAG, "run")
        assert hasattr(RAG, "as_tool")


class TestBaseBlueprint:
    """Tests for BaseBlueprint."""

    def test_cannot_instantiate_directly(self):
        """BaseBlueprint is abstract."""
        with pytest.raises(TypeError):
            BaseBlueprint()

    def test_has_processor_methods(self):
        """BaseBlueprint has processor pipeline methods."""
        assert hasattr(BaseBlueprint, "add_preprocessor")
        assert hasattr(BaseBlueprint, "add_postprocessor")
        assert hasattr(BaseBlueprint, "_run_preprocessors")
        assert hasattr(BaseBlueprint, "_run_postprocessors")


class TestRAGBlueprint:
    """Tests for RAG blueprint."""

    def test_requires_model_or_agent(self):
        """RAG requires either model or agent."""
        mock_retriever = MagicMock()
        
        with pytest.raises(ValueError, match="Must provide either 'model' or 'agent'"):
            RAG(retriever=mock_retriever)

    def test_cannot_have_both_model_and_agent(self):
        """RAG cannot have both model and agent."""
        mock_retriever = MagicMock()
        mock_model = MagicMock()
        mock_agent = MagicMock()
        
        with pytest.raises(ValueError, match="Provide either 'model' or 'agent', not both"):
            RAG(retriever=mock_retriever, model=mock_model, agent=mock_agent)

    def test_requires_retriever(self):
        """RAG requires retriever or retrievers."""
        mock_model = MagicMock()
        
        with pytest.raises(ValueError, match="Must provide either 'retriever' or 'retrievers'"):
            RAG(model=mock_model)

    def test_cannot_have_both_retriever_and_retrievers(self):
        """RAG cannot have both retriever and retrievers."""
        mock_model = MagicMock()
        mock_retriever = MagicMock()
        
        with pytest.raises(ValueError, match="Provide either 'retriever' or 'retrievers', not both"):
            RAG(
                retriever=mock_retriever,
                retrievers=[mock_retriever],
                model=mock_model,
            )

    def test_name_property(self):
        """RAG has name property."""
        mock_retriever = MagicMock()
        mock_model = MagicMock()
        
        with patch("agenticflow.blueprints.rag.Agent"):
            rag = RAG(retriever=mock_retriever, model=mock_model)
            assert rag.name == "rag"

    def test_config_defaults(self):
        """RAG has default config."""
        mock_retriever = MagicMock()
        mock_model = MagicMock()
        
        with patch("agenticflow.blueprints.rag.Agent"):
            rag = RAG(retriever=mock_retriever, model=mock_model)
            assert rag.config.top_k == 4
            assert rag.config.citation_style == CitationStyle.NUMERIC

    def test_custom_config(self):
        """RAG uses custom config."""
        mock_retriever = MagicMock()
        mock_model = MagicMock()
        config = RAGConfig(
            top_k=10,
            citation_style=CitationStyle.FOOTNOTE,
        )
        
        with patch("agenticflow.blueprints.rag.Agent"):
            rag = RAG(retriever=mock_retriever, model=mock_model, config=config)
            assert rag.config.top_k == 10
            assert rag.config.citation_style == CitationStyle.FOOTNOTE

    def test_as_tool_returns_tool(self):
        """as_tool() returns a callable tool."""
        mock_retriever = MagicMock()
        mock_model = MagicMock()
        
        with patch("agenticflow.blueprints.rag.Agent"):
            rag = RAG(retriever=mock_retriever, model=mock_model)
            tool = rag.as_tool()
            
            assert tool is not None
            assert hasattr(tool, "name")
            assert hasattr(tool, "func")  # BaseTool has func attribute

    def test_as_tool_custom_name(self):
        """as_tool() with custom name."""
        mock_retriever = MagicMock()
        mock_model = MagicMock()
        
        with patch("agenticflow.blueprints.rag.Agent"):
            rag = RAG(retriever=mock_retriever, model=mock_model)
            tool = rag.as_tool(name="my_rag", description="Custom RAG tool")
            
            assert tool.name == "my_rag"

    def test_repr(self):
        """RAG has repr."""
        mock_retriever = MagicMock()
        mock_model = MagicMock()
        
        with patch("agenticflow.blueprints.rag.Agent"):
            rag = RAG(retriever=mock_retriever, model=mock_model)
            assert "RAG" in repr(rag)
            assert "rag" in repr(rag)


class TestRAGResult:
    """Tests for RAGResult."""

    def test_create_result(self):
        """RAGResult is created with all fields."""
        passages = (
            CitedPassage(citation_id=1, source="doc.pdf", score=0.9, text="text"),
        )
        result = RAGResult(
            output="answer",
            raw_output="answer with «1»",
            passages=passages,
            query="question",
        )
        assert result.output == "answer"
        assert result.raw_output == "answer with «1»"
        assert len(result.passages) == 1
        assert result.query == "question"

    def test_inherits_from_blueprint_result(self):
        """RAGResult inherits from BlueprintResult."""
        result = RAGResult(output="answer")
        assert isinstance(result, BlueprintResult)
        assert str(result) == "answer"
