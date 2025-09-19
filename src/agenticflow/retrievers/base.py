"""
Base classes for the AgenticFlow Retriever System.

These classes abstract and standardize the retrieval logic that's currently
embedded within memory classes, enabling composable and pluggable retrieval strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import time

import structlog
from pydantic import BaseModel, ConfigDict

from ..memory.core import MemoryDocument

logger = structlog.get_logger(__name__)


class DistanceMetric(str, Enum):
    """Distance/similarity metrics for vector-based retrievers."""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"
    HAMMING = "hamming"
    JACCARD = "jaccard"


class RetrieverType(str, Enum):
    """Types of retrievers based on search strategy, not storage backend."""
    # Text-based search strategies
    KEYWORD = "keyword"                    # Simple keyword/text matching
    FULLTEXT = "fulltext"                  # Full-text search (PostgreSQL, Elasticsearch)
    BM25 = "bm25"                         # BM25 ranking algorithm
    FUZZY = "fuzzy"                       # Fuzzy text matching
    REGEX = "regex"                       # Regular expression search
    
    # Semantic/Vector-based search strategies  
    SEMANTIC = "semantic"                  # Dense vector semantic search
    SPARSE = "sparse"                     # Sparse vector search (e.g., SPLADE)
    HYBRID_DENSE_SPARSE = "hybrid_ds"     # Combines dense + sparse vectors
    
    # Distance/Similarity metrics for vector search
    COSINE = "cosine"                     # Cosine similarity
    EUCLIDEAN = "euclidean"               # Euclidean distance  
    DOT_PRODUCT = "dot_product"           # Dot product similarity
    MANHATTAN = "manhattan"               # Manhattan distance
    
    # Advanced composition patterns
    ENSEMBLE = "ensemble"                 # Combines multiple retrievers
    CONTEXTUAL = "contextual"             # Context-aware retrieval
    FUSION = "fusion"                     # Score fusion and reranking
    RERANK = "rerank"                     # Neural reranking
    
    # Custom extensible
    CUSTOM = "custom"                     # User-defined retriever


class RetrieverError(Exception):
    """Base exception for retriever operations."""
    pass


@dataclass
class RetrieverResult:
    """Standardized result from any retriever."""
    
    document: MemoryDocument
    score: float
    rank: int = 0
    retriever_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Add retrieval metadata to document."""
        if self.document and self.document.metadata:
            self.document.metadata.update({
                "retrieval_score": self.score,
                "retrieval_rank": self.rank,
                "retriever_type": self.retriever_type,
                **self.metadata
            })


class RetrieverConfig(BaseModel):
    """Base configuration for all retrievers."""
    
    similarity_threshold: float = 0.7
    max_results: int = 10
    enable_caching: bool = True
    cache_size: int = 100
    timeout_seconds: float = 30.0
    
    # Filtering options
    metadata_filters: Optional[Dict[str, Any]] = None
    content_filters: Optional[List[str]] = None
    
    # Scoring options
    enable_reranking: bool = False
    score_normalization: str = "minmax"  # "minmax", "zscore", "none"
    
    # Performance options
    batch_size: int = 10
    enable_parallel: bool = False
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class AsyncRetriever(ABC):
    """Abstract base class for all retrievers.
    
    Extracts and standardizes retrieval patterns from existing memory implementations.
    """
    
    def __init__(self, config: RetrieverConfig):
        """Initialize retriever with configuration."""
        self.config = config
        self.retriever_type = self._get_retriever_type()
        self.logger = logger.bind(retriever=self.retriever_type)
        
        # Simple cache implementation
        self._cache: Dict[str, List[RetrieverResult]] = {}
        self._cache_timestamps: Dict[str, float] = {}
    
    @abstractmethod
    def _get_retriever_type(self) -> str:
        """Return the retriever type string."""
        pass
    
    @abstractmethod
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement the core retrieval logic.
        
        This should be implemented by each retriever to extract the specific
        search logic from its corresponding memory class.
        """
        pass
    
    async def retrieve(
        self,
        query: str,
        limit: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        **kwargs
    ) -> List[RetrieverResult]:
        """Retrieve relevant documents for a query.
        
        Provides standardized interface with caching, filtering, and scoring.
        """
        start_time = time.time()
        
        # Use config defaults if not specified
        limit = limit or self.config.max_results
        similarity_threshold = similarity_threshold or self.config.similarity_threshold
        
        # Check cache
        cache_key = self._create_cache_key(query, limit, similarity_threshold, kwargs)
        if self.config.enable_caching and cache_key in self._cache:
            # Check if cache entry is still valid (simple time-based expiry)
            if time.time() - self._cache_timestamps[cache_key] < 300:  # 5 minutes
                self.logger.debug(f"Cache hit for query: {query[:50]}...")
                return self._cache[cache_key]
        
        try:
            # Perform retrieval
            results = await self._retrieve_impl(
                query, limit, similarity_threshold=similarity_threshold, **kwargs
            )
            
            # Apply post-processing
            results = self._apply_filters(results)
            results = self._apply_scoring(results, query)
            results = self._apply_ranking(results)
            
            # Apply final limit and threshold
            results = [r for r in results if r.score >= similarity_threshold][:limit]
            
            # Cache results
            if self.config.enable_caching:
                self._cache_result(cache_key, results)
            
            # Log metrics
            duration = time.time() - start_time
            self.logger.debug(
                f"Retrieved {len(results)} results in {duration:.3f}s for query: {query[:50]}..."
            )
            
            return results
        
        except Exception as e:
            self.logger.error(f"Retrieval failed: {e}")
            raise RetrieverError(f"Retrieval failed: {e}")
    
    def _create_cache_key(
        self, 
        query: str, 
        limit: int, 
        similarity_threshold: float, 
        kwargs: Dict[str, Any]
    ) -> str:
        """Create cache key from query parameters."""
        import hashlib
        
        key_data = f"{query}_{limit}_{similarity_threshold}_{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, results: List[RetrieverResult]):
        """Cache retrieval results with LRU eviction."""
        self._cache[cache_key] = results
        self._cache_timestamps[cache_key] = time.time()
        
        # Simple LRU eviction
        if len(self._cache) > self.config.cache_size:
            # Remove oldest entry
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=lambda k: self._cache_timestamps[k])
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]
    
    def _apply_filters(self, results: List[RetrieverResult]) -> List[RetrieverResult]:
        """Apply metadata and content filters."""
        if not self.config.metadata_filters and not self.config.content_filters:
            return results
        
        filtered = []
        for result in results:
            # Apply metadata filters
            if self.config.metadata_filters:
                if not all(
                    result.document.metadata.get(k) == v 
                    for k, v in self.config.metadata_filters.items()
                ):
                    continue
            
            # Apply content filters
            if self.config.content_filters:
                content_lower = result.document.content.lower()
                if not any(f.lower() in content_lower for f in self.config.content_filters):
                    continue
            
            filtered.append(result)
        
        return filtered
    
    def _apply_scoring(
        self, 
        results: List[RetrieverResult], 
        query: str
    ) -> List[RetrieverResult]:
        """Apply score normalization and reranking."""
        if not results:
            return results
        
        # Extract scores
        scores = [r.score for r in results]
        
        # Normalize scores
        if self.config.score_normalization == "minmax" and len(scores) > 1:
            min_score, max_score = min(scores), max(scores)
            if max_score > min_score:
                for result in results:
                    result.score = (result.score - min_score) / (max_score - min_score)
        
        elif self.config.score_normalization == "zscore" and len(scores) > 1:
            import statistics
            mean_score = statistics.mean(scores)
            stdev_score = statistics.stdev(scores) if len(scores) > 1 else 1.0
            if stdev_score > 0:
                for result in results:
                    result.score = (result.score - mean_score) / stdev_score
        
        # Apply reranking if enabled
        if self.config.enable_reranking:
            results = self._rerank_results(results, query)
        
        return results
    
    def _rerank_results(
        self, 
        results: List[RetrieverResult], 
        query: str
    ) -> List[RetrieverResult]:
        """Apply simple reranking based on content features."""
        # Simple reranking based on:
        # 1. Query term frequency in content
        # 2. Content length (prefer moderate length)
        # 3. Recency (if timestamp available)
        
        query_terms = set(query.lower().split())
        
        for result in results:
            rerank_score = result.score  # Start with original score
            content_lower = result.document.content.lower()
            content_words = set(content_lower.split())
            
            # Query term frequency boost
            term_matches = len(query_terms.intersection(content_words))
            if term_matches > 0:
                rerank_score += 0.1 * term_matches
            
            # Content length normalization (prefer 100-1000 char content)
            content_len = len(result.document.content)
            if 100 <= content_len <= 1000:
                rerank_score += 0.05
            elif content_len > 2000:
                rerank_score -= 0.05
            
            # Recency boost (if timestamp available)
            if hasattr(result.document, 'timestamp') and result.document.timestamp:
                age_hours = (time.time() - result.document.timestamp) / 3600
                if age_hours < 24:  # Recent content boost
                    rerank_score += 0.02
            
            result.score = rerank_score
        
        return results
    
    def _apply_ranking(self, results: List[RetrieverResult]) -> List[RetrieverResult]:
        """Sort results by score and assign ranks."""
        # Sort by score (descending)
        results.sort(key=lambda r: r.score, reverse=True)
        
        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        return results
    
    async def health_check(self) -> bool:
        """Check if retriever is healthy and operational."""
        try:
            # Try a simple test retrieval
            test_results = await self._retrieve_impl("test", 1)
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        return {
            "retriever_type": self.retriever_type,
            "cache_size": len(self._cache),
            "cache_hit_ratio": 0.0,  # Could track this
            "config": self.config.model_dump()
        }
    
    def clear_cache(self):
        """Clear the retriever cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        self.logger.info("Retriever cache cleared")


class DataSourceRetriever(AsyncRetriever):
    """Base class for retrievers that work with any compatible data source.
    
    Data sources can be:
    - Memory instances (BufferMemory, VectorMemory, etc.)
    - Vector stores (FAISS, Chroma, Pinecone, etc.)
    - Databases (SQLite, PostgreSQL, etc.)
    - Search engines (Elasticsearch, etc.)
    - Custom indices or data structures
    """
    
    def __init__(self, data_source: Any, config: RetrieverConfig):
        """Initialize with data source.
        
        Args:
            data_source: Any compatible data source (memory, vector store, database, etc.)
            config: Retriever configuration
        """
        super().__init__(config)
        self.data_source = data_source
        self.logger = self.logger.bind(data_source_type=type(data_source).__name__)
        
        # Detect data source capabilities
        self._capabilities = self._detect_capabilities(data_source)
    
    def _detect_capabilities(self, data_source) -> Dict[str, bool]:
        """Detect what capabilities the data source supports."""
        capabilities = {
            "has_search_method": hasattr(data_source, 'search'),
            "has_vector_search": hasattr(data_source, 'similarity_search') or hasattr(data_source, 'search'),
            "has_text_search": hasattr(data_source, 'search') or hasattr(data_source, 'query'),
            "has_embeddings": hasattr(data_source, 'embeddings') or hasattr(data_source, '_embeddings'),
            "is_memory_instance": hasattr(data_source, 'add_message'),
            "is_vector_store": hasattr(data_source, 'add_documents'),
            "is_database": hasattr(data_source, 'execute') or hasattr(data_source, 'query'),
        }
        
        self.logger.debug(f"Detected capabilities: {capabilities}")
        return capabilities
    
    async def _extract_documents_from_results(
        self, 
        raw_results: List[Any]
    ) -> List[RetrieverResult]:
        """Convert raw data source results to standardized RetrieverResult format.
        
        This handles different result formats from different data sources.
        """
        results = []
        
        for i, result in enumerate(raw_results):
            if isinstance(result, MemoryDocument):
                # Already a MemoryDocument (from memory instances)
                doc = result
                score = result.metadata.get("similarity_score", 0.5)
                
            elif hasattr(result, 'payload') and hasattr(result, 'score'):
                # Vector store result (like Qdrant)
                doc = MemoryDocument(
                    id=str(result.id) if hasattr(result, 'id') else f'doc_{i}',
                    content=result.payload.get('content', ''),
                    metadata=result.payload,
                    timestamp=result.payload.get('timestamp', time.time())
                )
                score = result.score
                
            elif hasattr(result, 'page_content') and hasattr(result, 'metadata'):
                # LangChain-style document
                doc = MemoryDocument(
                    id=result.metadata.get('id', f'doc_{i}'),
                    content=result.page_content,
                    metadata=result.metadata,
                    timestamp=result.metadata.get('timestamp', time.time())
                )
                score = result.metadata.get('score', 0.5)
                
            elif hasattr(result, 'content'):
                # Generic document with content
                doc = MemoryDocument(
                    id=getattr(result, 'id', f'doc_{i}'),
                    content=result.content,
                    metadata=getattr(result, 'metadata', {}),
                    timestamp=getattr(result, 'timestamp', time.time())
                )
                score = getattr(result, 'score', 0.5)
                
            elif isinstance(result, dict):
                # Dictionary result
                doc = MemoryDocument(
                    id=result.get('id', f'doc_{i}'),
                    content=result.get('content', ''),
                    metadata=result.get('metadata', {}),
                    timestamp=result.get('timestamp', time.time())
                )
                score = result.get('score', 0.5)
                
            elif isinstance(result, str):
                # Plain text result
                doc = MemoryDocument(
                    id=f'doc_{i}',
                    content=result,
                    metadata={},
                    timestamp=time.time()
                )
                score = 0.5
                
            else:
                # Skip unknown formats
                self.logger.warning(f"Unknown result format: {type(result)}")
                continue
            
            retriever_result = RetrieverResult(
                document=doc,
                score=score,
                rank=i + 1,
                retriever_type=self.retriever_type
            )
            results.append(retriever_result)
        
        return results
    
    async def close(self):
        """Close retriever and cleanup resources."""
        # Close data source if it has a close method
        if hasattr(self.data_source, 'close'):
            if callable(getattr(self.data_source, 'close')):
                await self.data_source.close()
        
        self.clear_cache()
