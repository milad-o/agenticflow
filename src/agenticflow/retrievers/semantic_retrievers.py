"""
Semantic/Vector-Based Retrievers

Implements various vector-based search strategies using different distance metrics
and semantic search techniques.
"""

import math
import time
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog
from pydantic import BaseModel

from .base import DataSourceRetriever, RetrieverResult, RetrieverConfig, RetrieverType, DistanceMetric
from ..memory.core import MemoryDocument

logger = structlog.get_logger(__name__)


class SemanticRetrieverConfig(RetrieverConfig):
    """Configuration for semantic retrieval."""
    
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    embedding_dimension: Optional[int] = None
    normalize_embeddings: bool = True
    batch_search: bool = True
    embedding_cache_size: int = 1000


class VectorRetrieverConfig(RetrieverConfig):
    """Base configuration for vector-based retrievers."""
    
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    normalize_vectors: bool = True
    vector_dimension: Optional[int] = None


class CosineRetrieverConfig(SemanticRetrieverConfig):
    """Configuration for cosine similarity retrieval."""
    distance_metric: DistanceMetric = DistanceMetric.COSINE


class EuclideanRetrieverConfig(SemanticRetrieverConfig):
    """Configuration for Euclidean distance retrieval."""
    distance_metric: DistanceMetric = DistanceMetric.EUCLIDEAN


class DotProductRetrieverConfig(SemanticRetrieverConfig):
    """Configuration for dot product similarity retrieval."""
    distance_metric: DistanceMetric = DistanceMetric.DOT_PRODUCT
    normalize_embeddings: bool = False  # Usually don't normalize for dot product


class ManhattanRetrieverConfig(SemanticRetrieverConfig):
    """Configuration for Manhattan distance retrieval."""
    distance_metric: DistanceMetric = DistanceMetric.MANHATTAN


class SparseRetrieverConfig(RetrieverConfig):
    """Configuration for sparse vector retrieval."""
    
    sparsity_threshold: float = 0.01  # Values below this are considered zero
    max_features: Optional[int] = None
    idf_weighting: bool = True


class SemanticRetriever(DataSourceRetriever):
    """Dense vector semantic search retriever."""
    
    def __init__(self, data_source: Any, config: SemanticRetrieverConfig = None):
        config = config or SemanticRetrieverConfig()
        super().__init__(data_source, config)
        self.config: SemanticRetrieverConfig = config
        
        # Cache for embeddings to avoid recomputation
        self._embedding_cache = {}
        self._embeddings_provider = None
        self._document_embeddings = {}  # Cache document embeddings
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.SEMANTIC
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement semantic retrieval."""
        
        # Get embeddings provider
        embeddings = await self._get_embeddings_provider()
        if not embeddings:
            self.logger.warning("No embeddings provider available, falling back to text search")
            return await self._fallback_text_search(query, limit)
        
        # Get query embedding
        query_embedding = await self._get_query_embedding(query, embeddings)
        if query_embedding is None:
            return []
        
        # Get documents with embeddings
        documents_with_embeddings = await self._get_documents_with_embeddings(embeddings)
        
        # Calculate similarities
        scored_results = []
        for doc, doc_embedding in documents_with_embeddings:
            similarity = self._calculate_similarity(
                query_embedding, 
                doc_embedding, 
                self.config.distance_metric
            )
            
            if similarity >= kwargs.get('similarity_threshold', self.config.similarity_threshold):
                result = RetrieverResult(
                    document=doc,
                    score=similarity,
                    retriever_type=self.retriever_type,
                    metadata={"embedding_similarity": similarity}
                )
                scored_results.append(result)
        
        # Sort by similarity and return top results
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]
    
    async def _get_embeddings_provider(self):
        """Get embeddings provider from data source."""
        if self._embeddings_provider:
            return self._embeddings_provider
        
        # Try to get from data source
        if hasattr(self.data_source, 'embeddings'):
            self._embeddings_provider = self.data_source.embeddings
        elif hasattr(self.data_source, '_embeddings'):
            self._embeddings_provider = self.data_source._embeddings
        
        return self._embeddings_provider
    
    async def _get_query_embedding(self, query: str, embeddings) -> Optional[List[float]]:
        """Get embedding for query with caching."""
        cache_key = f"query_{hash(query)}"
        
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        try:
            if hasattr(embeddings, 'aembed_query'):
                embedding = await embeddings.aembed_query(query)
            elif hasattr(embeddings, 'embed_query'):
                embedding = embeddings.embed_query(query)
            else:
                self.logger.warning("Embeddings provider has no embed_query method")
                return None
            
            # Normalize if configured
            if self.config.normalize_embeddings and embedding:
                embedding = self._normalize_vector(embedding)
            
            # Cache the result
            if len(self._embedding_cache) < self.config.embedding_cache_size:
                self._embedding_cache[cache_key] = embedding
            
            return embedding
        
        except Exception as e:
            self.logger.error(f"Failed to generate query embedding: {e}")
            return None
    
    async def _get_documents_with_embeddings(self, embeddings) -> List[Tuple[MemoryDocument, List[float]]]:
        """Get documents with their embeddings."""
        documents = await self._get_documents_from_data_source()
        documents_with_embeddings = []
        
        for doc in documents:
            # Check if document already has embedding
            doc_embedding = None
            if hasattr(doc, 'embedding') and doc.embedding:
                doc_embedding = doc.embedding
            elif doc.id in self._document_embeddings:
                doc_embedding = self._document_embeddings[doc.id]
            else:
                # Generate embedding for document
                try:
                    if hasattr(embeddings, 'aembed_query'):
                        doc_embedding = await embeddings.aembed_query(doc.content)
                    elif hasattr(embeddings, 'embed_query'):
                        doc_embedding = embeddings.embed_query(doc.content)
                    
                    if doc_embedding:
                        # Normalize if configured
                        if self.config.normalize_embeddings:
                            doc_embedding = self._normalize_vector(doc_embedding)
                        
                        # Cache the embedding
                        self._document_embeddings[doc.id] = doc_embedding
                
                except Exception as e:
                    self.logger.warning(f"Failed to generate embedding for document {doc.id}: {e}")
                    continue
            
            if doc_embedding:
                documents_with_embeddings.append((doc, doc_embedding))
        
        return documents_with_embeddings
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize vector to unit length."""
        if not vector:
            return vector
        
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude == 0:
            return vector
        
        return [x / magnitude for x in vector]
    
    def _calculate_similarity(
        self, 
        vec1: List[float], 
        vec2: List[float], 
        metric: DistanceMetric
    ) -> float:
        """Calculate similarity based on distance metric."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        if metric == DistanceMetric.COSINE:
            return self._cosine_similarity(vec1, vec2)
        elif metric == DistanceMetric.EUCLIDEAN:
            return self._euclidean_similarity(vec1, vec2)
        elif metric == DistanceMetric.DOT_PRODUCT:
            return self._dot_product_similarity(vec1, vec2)
        elif metric == DistanceMetric.MANHATTAN:
            return self._manhattan_similarity(vec1, vec2)
        else:
            return self._cosine_similarity(vec1, vec2)  # Default
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _euclidean_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Euclidean distance converted to similarity."""
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))
        # Convert distance to similarity (0 distance = 1 similarity)
        return 1.0 / (1.0 + distance)
    
    def _dot_product_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate dot product similarity."""
        return sum(a * b for a, b in zip(vec1, vec2))
    
    def _manhattan_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Manhattan distance converted to similarity."""
        distance = sum(abs(a - b) for a, b in zip(vec1, vec2))
        # Convert distance to similarity (0 distance = 1 similarity)
        return 1.0 / (1.0 + distance)
    
    async def _fallback_text_search(self, query: str, limit: int) -> List[RetrieverResult]:
        """Fallback to text search when embeddings are not available."""
        from .text_retrievers import KeywordRetriever
        
        keyword_retriever = KeywordRetriever(self.data_source)
        return await keyword_retriever._retrieve_impl(query, limit)
    
    async def _get_documents_from_data_source(self) -> List[MemoryDocument]:
        """Extract documents from data source."""
        from .text_retrievers import KeywordRetriever
        
        keyword_retriever = KeywordRetriever(self.data_source)
        return await keyword_retriever._get_documents_from_data_source()


class CosineRetriever(SemanticRetriever):
    """Cosine similarity retriever."""
    
    def __init__(self, data_source: Any, config: CosineRetrieverConfig = None):
        config = config or CosineRetrieverConfig()
        super().__init__(data_source, config)
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.COSINE


class EuclideanRetriever(SemanticRetriever):
    """Euclidean distance retriever."""
    
    def __init__(self, data_source: Any, config: EuclideanRetrieverConfig = None):
        config = config or EuclideanRetrieverConfig()
        super().__init__(data_source, config)
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.EUCLIDEAN


class DotProductRetriever(SemanticRetriever):
    """Dot product similarity retriever."""
    
    def __init__(self, data_source: Any, config: DotProductRetrieverConfig = None):
        config = config or DotProductRetrieverConfig()
        super().__init__(data_source, config)
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.DOT_PRODUCT


class ManhattanRetriever(SemanticRetriever):
    """Manhattan distance retriever."""
    
    def __init__(self, data_source: Any, config: ManhattanRetrieverConfig = None):
        config = config or ManhattanRetrieverConfig()
        super().__init__(data_source, config)
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.MANHATTAN


class SparseRetriever(DataSourceRetriever):
    """Sparse vector retrieval (e.g., SPLADE, TF-IDF vectors)."""
    
    def __init__(self, data_source: Any, config: SparseRetrieverConfig = None):
        config = config or SparseRetrieverConfig()
        super().__init__(data_source, config)
        self.config: SparseRetrieverConfig = config
        
        # Vocabulary and IDF weights
        self.vocabulary = {}
        self.idf_weights = {}
        self._corpus_built = False
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.SPARSE
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement sparse vector retrieval."""
        
        # Build corpus if needed
        if not self._corpus_built:
            await self._build_sparse_corpus()
        
        # Convert query to sparse vector
        query_vector = self._text_to_sparse_vector(query)
        if not query_vector:
            return []
        
        # Get documents and convert to sparse vectors
        documents = await self._get_documents_from_data_source()
        scored_results = []
        
        for doc in documents:
            doc_vector = self._text_to_sparse_vector(doc.content)
            if doc_vector:
                similarity = self._sparse_cosine_similarity(query_vector, doc_vector)
                
                if similarity >= kwargs.get('similarity_threshold', self.config.similarity_threshold):
                    result = RetrieverResult(
                        document=doc,
                        score=similarity,
                        retriever_type=self.retriever_type,
                        metadata={"sparse_similarity": similarity}
                    )
                    scored_results.append(result)
        
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]
    
    async def _build_sparse_corpus(self):
        """Build vocabulary and IDF weights from corpus."""
        documents = await self._get_documents_from_data_source()
        
        # Build vocabulary
        word_doc_count = {}
        total_docs = len(documents)
        
        for doc in documents:
            words = set(self._tokenize_text(doc.content))
            for word in words:
                word_doc_count[word] = word_doc_count.get(word, 0) + 1
        
        # Create vocabulary index
        self.vocabulary = {word: idx for idx, word in enumerate(word_doc_count.keys())}
        
        # Calculate IDF weights
        if self.config.idf_weighting:
            self.idf_weights = {}
            for word, doc_freq in word_doc_count.items():
                self.idf_weights[word] = math.log(total_docs / (doc_freq + 1))
        
        # Limit vocabulary size if specified
        if self.config.max_features and len(self.vocabulary) > self.config.max_features:
            # Keep most frequent terms
            sorted_words = sorted(word_doc_count.items(), key=lambda x: x[1], reverse=True)
            self.vocabulary = {word: idx for idx, (word, _) in enumerate(sorted_words[:self.config.max_features])}
        
        self._corpus_built = True
        self.logger.debug(f"Built sparse corpus with {len(self.vocabulary)} terms")
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Simple tokenization."""
        import re
        return re.findall(r'\b\w+\b', text.lower())
    
    def _text_to_sparse_vector(self, text: str) -> Dict[int, float]:
        """Convert text to sparse vector representation."""
        words = self._tokenize_text(text)
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Convert to sparse vector with TF-IDF weighting
        sparse_vector = {}
        total_words = len(words)
        
        for word, count in word_counts.items():
            if word in self.vocabulary:
                idx = self.vocabulary[word]
                tf = count / total_words  # Term frequency
                
                if self.config.idf_weighting and word in self.idf_weights:
                    weight = tf * self.idf_weights[word]  # TF-IDF
                else:
                    weight = tf
                
                # Apply sparsity threshold
                if weight >= self.config.sparsity_threshold:
                    sparse_vector[idx] = weight
        
        return sparse_vector
    
    def _sparse_cosine_similarity(self, vec1: Dict[int, float], vec2: Dict[int, float]) -> float:
        """Calculate cosine similarity between sparse vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        # Calculate dot product
        common_indices = set(vec1.keys()) & set(vec2.keys())
        dot_product = sum(vec1[idx] * vec2[idx] for idx in common_indices)
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
        mag2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    async def _get_documents_from_data_source(self) -> List[MemoryDocument]:
        """Extract documents from data source."""
        from .text_retrievers import KeywordRetriever
        
        keyword_retriever = KeywordRetriever(self.data_source)
        return await keyword_retriever._get_documents_from_data_source()