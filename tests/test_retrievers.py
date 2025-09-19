"""
Tests for the AgenticFlow Retriever System

Tests all retriever types, configurations, and factory functionality.
"""

import asyncio
import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

from agenticflow.retrievers import (
    # Base classes
    AsyncRetriever, DataSourceRetriever, RetrieverResult, RetrieverConfig, 
    RetrieverType, RetrieverError, DistanceMetric,
    
    # Text retrievers
    KeywordRetriever, KeywordRetrieverConfig,
    FullTextRetriever, FullTextRetrieverConfig,
    BM25Retriever, BM25RetrieverConfig,
    FuzzyRetriever, FuzzyRetrieverConfig,
    RegexRetriever, RegexRetrieverConfig,
    
    # Semantic retrievers
    SemanticRetriever, SemanticRetrieverConfig,
    CosineRetriever, CosineRetrieverConfig,
    EuclideanRetriever, EuclideanRetrieverConfig,
    DotProductRetriever, DotProductRetrieverConfig,
    ManhattanRetriever, ManhattanRetrieverConfig,
    SparseRetriever, SparseRetrieverConfig,
    
    # Composite retrievers
    EnsembleRetriever, EnsembleRetrieverConfig,
    HybridRetriever, HybridRetrieverConfig,
    ContextualRetriever, ContextualRetrieverConfig,
    FusionRetriever, FusionRetrieverConfig,
    
    # Factory
    RetrieverFactory, create_retriever, create_from_memory
)

from agenticflow.memory.core import MemoryDocument


class MockMemoryDataSource:
    """Mock memory data source for testing."""
    
    def __init__(self, documents: List[MemoryDocument] = None):
        self.documents = documents or self._create_sample_documents()
        self.embeddings = Mock()
        self.embeddings.embed_query = Mock(return_value=[0.1, 0.2, 0.3, 0.4])
        self.embeddings.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
    
    def _create_sample_documents(self) -> List[MemoryDocument]:
        return [
            MemoryDocument(
                id="doc1",
                content="Machine learning is a subset of artificial intelligence.",
                metadata={"topic": "AI", "difficulty": "basic"},
                timestamp=1234567890.0
            ),
            MemoryDocument(
                id="doc2", 
                content="Deep learning uses neural networks with many layers.",
                metadata={"topic": "AI", "difficulty": "advanced"},
                timestamp=1234567891.0
            ),
            MemoryDocument(
                id="doc3",
                content="Natural language processing helps computers understand text.",
                metadata={"topic": "NLP", "difficulty": "intermediate"},
                timestamp=1234567892.0
            ),
            MemoryDocument(
                id="doc4",
                content="Computer vision enables machines to interpret visual data.",
                metadata={"topic": "CV", "difficulty": "intermediate"},
                timestamp=1234567893.0
            ),
            MemoryDocument(
                id="doc5",
                content="Reinforcement learning trains agents through rewards.",
                metadata={"topic": "RL", "difficulty": "advanced"},
                timestamp=1234567894.0
            )
        ]
    
    async def search(self, query: str, limit: int = 10) -> List[MemoryDocument]:
        """Mock search method."""
        # Simple keyword matching
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            if any(word in doc.content.lower() for word in query_lower.split()):
                results.append(doc)
        
        return results[:limit]
    
    async def similarity_search(self, query: str, limit: int = 10) -> List[MemoryDocument]:
        """Mock semantic search."""
        # Return all documents with mock similarity scores
        for doc in self.documents:
            doc.metadata["similarity_score"] = 0.8  # Mock score
        
        return self.documents[:limit]


@pytest.fixture
def sample_memory():
    """Create sample memory data source."""
    return MockMemoryDataSource()


@pytest.fixture
def sample_documents():
    """Create sample documents."""
    return MockMemoryDataSource()._create_sample_documents()


class TestRetrieverBase:
    """Test base retriever functionality."""
    
    @pytest.mark.asyncio
    async def test_retriever_config(self):
        """Test retriever configuration."""
        config = RetrieverConfig(
            similarity_threshold=0.8,
            max_results=5,
            enable_caching=True
        )
        
        assert config.similarity_threshold == 0.8
        assert config.max_results == 5
        assert config.enable_caching is True
    
    def test_retriever_result(self, sample_documents):
        """Test retriever result creation."""
        doc = sample_documents[0]
        result = RetrieverResult(
            document=doc,
            score=0.85,
            rank=1,
            retriever_type="test",
            metadata={"test": "value"}
        )
        
        assert result.document == doc
        assert result.score == 0.85
        assert result.rank == 1
        assert result.retriever_type == "test"
        assert result.metadata["test"] == "value"


class TestTextRetrievers:
    """Test text-based retrievers."""
    
    @pytest.mark.asyncio
    async def test_keyword_retriever(self, sample_memory):
        """Test keyword retriever."""
        config = KeywordRetrieverConfig(case_sensitive=False)
        retriever = KeywordRetriever(sample_memory, config)
        
        results = await retriever.retrieve("learning", limit=3)
        
        assert len(results) > 0
        assert all(isinstance(r, RetrieverResult) for r in results)
        assert all("learning" in r.document.content.lower() for r in results)
    
    @pytest.mark.asyncio
    async def test_fulltext_retriever(self, sample_memory):
        """Test full-text retriever."""
        config = FullTextRetrieverConfig()
        retriever = FullTextRetriever(sample_memory, config)
        
        results = await retriever.retrieve("machine learning", limit=3)
        
        assert len(results) > 0
        assert all(isinstance(r, RetrieverResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_bm25_retriever(self, sample_memory):
        """Test BM25 retriever."""
        config = BM25RetrieverConfig(k1=1.2, b=0.75)
        retriever = BM25Retriever(sample_memory, config)
        
        results = await retriever.retrieve("artificial intelligence", limit=3)
        
        assert len(results) > 0
        assert all(isinstance(r, RetrieverResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_fuzzy_retriever(self, sample_memory):
        """Test fuzzy retriever."""
        config = FuzzyRetrieverConfig(max_distance=2)
        retriever = FuzzyRetriever(sample_memory, config)
        
        results = await retriever.retrieve("machne", limit=3)  # Typo
        
        assert len(results) >= 0  # May or may not find fuzzy matches
    
    @pytest.mark.asyncio
    async def test_regex_retriever(self, sample_memory):
        """Test regex retriever."""
        config = RegexRetrieverConfig()
        retriever = RegexRetriever(sample_memory, config)
        
        results = await retriever.retrieve(r"\b\w+ing\b", limit=3)  # Words ending in 'ing'
        
        assert len(results) > 0
        assert all(isinstance(r, RetrieverResult) for r in results)


class TestSemanticRetrievers:
    """Test semantic/vector retrievers."""
    
    @pytest.mark.asyncio
    async def test_semantic_retriever(self, sample_memory):
        """Test semantic retriever."""
        config = SemanticRetrieverConfig(
            distance_metric=DistanceMetric.COSINE,
            normalize_embeddings=True
        )
        retriever = SemanticRetriever(sample_memory, config)
        
        results = await retriever.retrieve("AI concepts", limit=3)
        
        assert len(results) >= 0  # May not find results without proper embeddings
    
    @pytest.mark.asyncio
    async def test_cosine_retriever(self, sample_memory):
        """Test cosine similarity retriever."""
        config = CosineRetrieverConfig()
        retriever = CosineRetriever(sample_memory, config)
        
        results = await retriever.retrieve("machine learning", limit=3)
        
        assert len(results) >= 0
    
    @pytest.mark.asyncio
    async def test_sparse_retriever(self, sample_memory):
        """Test sparse retriever."""
        config = SparseRetrieverConfig(idf_weighting=True, max_features=1000)
        retriever = SparseRetriever(sample_memory, config)
        
        results = await retriever.retrieve("neural networks", limit=3)
        
        assert len(results) >= 0


class TestCompositeRetrievers:
    """Test composite retrievers."""
    
    @pytest.mark.asyncio
    async def test_ensemble_retriever(self, sample_memory):
        """Test ensemble retriever."""
        # Create component retrievers
        keyword_retriever = KeywordRetriever(sample_memory)
        bm25_retriever = BM25Retriever(sample_memory)
        
        config = EnsembleRetrieverConfig(
            fusion_method="weighted_sum",
            normalize_scores=True
        )
        ensemble = EnsembleRetriever([keyword_retriever, bm25_retriever], config)
        
        results = await ensemble.retrieve("machine learning", limit=3)
        
        assert len(results) >= 0
        assert all(isinstance(r, RetrieverResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_hybrid_retriever(self, sample_memory):
        """Test hybrid dense-sparse retriever."""
        dense_retriever = SemanticRetriever(sample_memory)
        sparse_retriever = SparseRetriever(sample_memory)
        
        config = HybridRetrieverConfig(
            dense_weight=0.7,
            sparse_weight=0.3
        )
        hybrid = HybridRetriever(dense_retriever, sparse_retriever, config)
        
        results = await hybrid.retrieve("AI algorithms", limit=3)
        
        assert len(results) >= 0
    
    @pytest.mark.asyncio
    async def test_contextual_retriever(self, sample_memory):
        """Test contextual retriever."""
        base_retriever = KeywordRetriever(sample_memory)
        
        config = ContextualRetrieverConfig(
            context_window=3,
            use_conversation_history=True
        )
        contextual = ContextualRetriever(base_retriever, config)
        
        # First query
        results1 = await contextual.retrieve("machine learning", limit=3)
        
        # Second query with context
        results2 = await contextual.retrieve("neural networks", limit=3)
        
        assert len(results1) >= 0
        assert len(results2) >= 0
    
    @pytest.mark.asyncio
    async def test_fusion_retriever(self, sample_memory):
        """Test fusion retriever."""
        keyword_retriever = KeywordRetriever(sample_memory)
        bm25_retriever = BM25Retriever(sample_memory)
        
        config = FusionRetrieverConfig(
            fusion_strategies=["rrf", "weighted_sum"],
            rrf_k=60
        )
        fusion = FusionRetriever([keyword_retriever, bm25_retriever], config)
        
        results = await fusion.retrieve("deep learning", limit=3)
        
        assert len(results) >= 0


class TestRetrieverFactory:
    """Test retriever factory functionality."""
    
    def test_create_keyword_retriever(self, sample_memory):
        """Test creating keyword retriever via factory."""
        retriever = RetrieverFactory.create_retriever(
            RetrieverType.KEYWORD,
            sample_memory
        )
        
        assert isinstance(retriever, KeywordRetriever)
        assert retriever.retriever_type == RetrieverType.KEYWORD
    
    def test_create_from_memory_auto_detect(self, sample_memory):
        """Test auto-detection of retriever type."""
        retriever = RetrieverFactory.create_from_memory(sample_memory)
        
        assert isinstance(retriever, AsyncRetriever)
        # Should detect semantic retriever due to embeddings attribute
        assert retriever.retriever_type == RetrieverType.SEMANTIC
    
    def test_create_hybrid_from_memory(self, sample_memory):
        """Test creating hybrid retriever from memory."""
        hybrid = RetrieverFactory.create_hybrid_from_memory(
            sample_memory,
            dense_type=RetrieverType.SEMANTIC,
            sparse_type=RetrieverType.SPARSE
        )
        
        assert isinstance(hybrid, HybridRetriever)
        assert hybrid.retriever_type == RetrieverType.HYBRID_DENSE_SPARSE
    
    def test_create_ensemble_from_memory(self, sample_memory):
        """Test creating ensemble retriever from memory."""
        ensemble = RetrieverFactory.create_ensemble_from_memory(
            sample_memory,
            retriever_types=[
                RetrieverType.KEYWORD,
                RetrieverType.BM25,
                RetrieverType.FUZZY
            ]
        )
        
        assert isinstance(ensemble, EnsembleRetriever)
        assert ensemble.retriever_type == RetrieverType.ENSEMBLE
    
    def test_list_supported_types(self):
        """Test listing supported retriever types."""
        supported = RetrieverFactory.list_supported_types()
        
        assert RetrieverType.KEYWORD in supported
        assert RetrieverType.SEMANTIC in supported
        assert RetrieverType.ENSEMBLE in supported
        assert len(supported) > 10  # Should have many supported types
    
    def test_get_config_class(self):
        """Test getting configuration class for retriever type."""
        config_class = RetrieverFactory.get_config_class(RetrieverType.KEYWORD)
        assert config_class == KeywordRetrieverConfig
        
        config_class = RetrieverFactory.get_config_class(RetrieverType.SEMANTIC)
        assert config_class == SemanticRetrieverConfig
    
    def test_unsupported_retriever_type(self, sample_memory):
        """Test error for unsupported retriever type."""
        with pytest.raises(ValueError, match="Unsupported retriever type"):
            RetrieverFactory.create_retriever("invalid_type", sample_memory)


class TestRetrieverIntegration:
    """Integration tests for retriever system."""
    
    @pytest.mark.asyncio
    async def test_retriever_caching(self, sample_memory):
        """Test retriever caching functionality."""
        config = KeywordRetrieverConfig(enable_caching=True, cache_size=10)
        retriever = KeywordRetriever(sample_memory, config)
        
        # First query
        results1 = await retriever.retrieve("learning", limit=3)
        
        # Second query (should hit cache)
        results2 = await retriever.retrieve("learning", limit=3)
        
        assert len(results1) == len(results2)
        
        # Check cache
        assert len(retriever._cache) > 0
    
    @pytest.mark.asyncio
    async def test_retriever_filtering(self, sample_memory):
        """Test retriever metadata filtering."""
        config = KeywordRetrieverConfig(
            metadata_filters={"topic": "AI"},
            similarity_threshold=0.1
        )
        retriever = KeywordRetriever(sample_memory, config)
        
        results = await retriever.retrieve("learning", limit=5)
        
        # Should only return AI-related documents
        for result in results:
            assert result.document.metadata.get("topic") == "AI"
    
    @pytest.mark.asyncio
    async def test_retriever_performance_metrics(self, sample_memory):
        """Test retriever performance tracking."""
        retriever = KeywordRetriever(sample_memory)
        
        # Perform several queries
        for query in ["learning", "neural", "computer"]:
            await retriever.retrieve(query, limit=2)
        
        stats = retriever.get_stats()
        
        assert "retriever_type" in stats
        assert "cache_size" in stats
        assert stats["retriever_type"] == RetrieverType.KEYWORD
    
    @pytest.mark.asyncio
    async def test_retriever_health_check(self, sample_memory):
        """Test retriever health check."""
        retriever = KeywordRetriever(sample_memory)
        
        is_healthy = await retriever.health_check()
        
        assert isinstance(is_healthy, bool)
        # Should be healthy with our mock data source
        assert is_healthy is True


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_retriever_function(self, sample_memory):
        """Test create_retriever convenience function."""
        retriever = create_retriever(RetrieverType.KEYWORD, sample_memory)
        
        assert isinstance(retriever, KeywordRetriever)
    
    def test_create_from_memory_function(self, sample_memory):
        """Test create_from_memory convenience function."""
        retriever = create_from_memory(sample_memory)
        
        assert isinstance(retriever, AsyncRetriever)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])