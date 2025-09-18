"""
AgenticFlow Retriever System
============================

Modular, scalable retrieval system organized by search strategy, not storage backend.
Enables mixing and matching any retrieval algorithm with any data source.

🎯 Core Philosophy: Search Strategy > Storage Type

Text-Based Retrievers:
• KeywordRetriever: Simple text matching (works on any text corpus)
• FullTextRetriever: Advanced text search (PostgreSQL, Elasticsearch, etc.)
• BM25Retriever: BM25 ranking algorithm (any indexed corpus)
• FuzzyRetriever: Fuzzy text matching with edit distance

Semantic/Vector Retrievers:
• SemanticRetriever: Dense vector search with configurable distance metrics
• SparseRetriever: Sparse vector search (SPLADE, etc.)
• HybridRetriever: Dense + Sparse vector combination

Distance Metrics (for vector retrievers):
• CosineRetriever: Cosine similarity search
• EuclideanRetriever: Euclidean distance search  
• DotProductRetriever: Dot product similarity
• ManhattanRetriever: Manhattan distance search

Composite Patterns:
• EnsembleRetriever: Combines multiple search strategies
• HybridRetriever: Dense + sparse vector combination 
• ContextualRetriever: Context-aware search with conversation history
• FusionRetriever: Advanced score fusion and reranking

🚀 Key Benefits:
• Any retriever can work with any compatible data source
• SQLite can use KeywordRetriever, BM25Retriever, or SemanticRetriever
• Vector stores can use multiple distance metrics and algorithms
• Easy to add custom retrievers and distance functions
• Modular composition and A/B testing

Usage Examples:
    # Semantic search on any vector-enabled data source
    semantic_retriever = SemanticRetriever(
        data_source=vector_store,  # or vector_memory, or custom_index
        distance_metric=DistanceMetric.COSINE,
        similarity_threshold=0.7
    )
    
    # BM25 search on any text corpus
    bm25_retriever = BM25Retriever(
        data_source=sqlite_memory,  # or postgres_memory, or text_index
        k1=1.2, b=0.75
    )
    
    # Combine different strategies
    ensemble = EnsembleRetriever([
        semantic_retriever,  # For semantic similarity
        bm25_retriever,     # For keyword relevance
        keyword_retriever   # For exact matches
    ])
    
    results = await ensemble.retrieve("machine learning concepts")
"""

from .base import (
    AsyncRetriever,
    DataSourceRetriever,
    RetrieverResult,
    RetrieverConfig,
    RetrieverError,
    RetrieverType,
    DistanceMetric
)

# Text-based retrievers
from .text_retrievers import (
    KeywordRetriever,
    KeywordRetrieverConfig,
    FullTextRetriever,
    FullTextRetrieverConfig,
    BM25Retriever,
    BM25RetrieverConfig,
    FuzzyRetriever,
    FuzzyRetrieverConfig,
    RegexRetriever,
    RegexRetrieverConfig
)

# Semantic/Vector retrievers
from .semantic_retrievers import (
    SemanticRetriever,
    SemanticRetrieverConfig,
    CosineRetriever,
    CosineRetrieverConfig,
    EuclideanRetriever,
    EuclideanRetrieverConfig,
    DotProductRetriever,
    DotProductRetrieverConfig,
    ManhattanRetriever,
    ManhattanRetrieverConfig,
    SparseRetriever,
    SparseRetrieverConfig
)

# Composite retrievers
from .composite_retrievers import (
    EnsembleRetriever,
    EnsembleRetrieverConfig,
    HybridRetriever,
    HybridRetrieverConfig,
    ContextualRetriever,
    ContextualRetrieverConfig,
    FusionRetriever,
    FusionRetrieverConfig
)

# Factory and convenience functions
from .factory import (
    RetrieverFactory,
    create_retriever,
    create_from_memory,
    create_hybrid_retriever,
    create_ensemble_retriever
)

# Memory adapter utilities
from .memory_adapter import (
    MemoryRetrieverAdapter,
    create_retriever_from_memory,
    create_smart_retriever_from_memory
)

__all__ = [
    # Base classes
    "AsyncRetriever",
    "DataSourceRetriever",
    "RetrieverResult", 
    "RetrieverConfig",
    "RetrieverError",
    "RetrieverType",
    "DistanceMetric",
    
    # Text-based retrievers
    "KeywordRetriever",
    "KeywordRetrieverConfig",
    "FullTextRetriever",
    "FullTextRetrieverConfig",
    "BM25Retriever",
    "BM25RetrieverConfig",
    "FuzzyRetriever",
    "FuzzyRetrieverConfig",
    "RegexRetriever",
    "RegexRetrieverConfig",
    
    # Semantic/Vector retrievers
    "SemanticRetriever",
    "SemanticRetrieverConfig",
    "CosineRetriever",
    "CosineRetrieverConfig",
    "EuclideanRetriever",
    "EuclideanRetrieverConfig",
    "DotProductRetriever",
    "DotProductRetrieverConfig",
    "ManhattanRetriever",
    "ManhattanRetrieverConfig",
    "SparseRetriever", 
    "SparseRetrieverConfig",
    
    # Composite retrievers
    "EnsembleRetriever",
    "EnsembleRetrieverConfig",
    "HybridRetriever",
    "HybridRetrieverConfig",
    "ContextualRetriever",
    "ContextualRetrieverConfig",
    "FusionRetriever",
    "FusionRetrieverConfig",
    
    # Factory and convenience functions
    "RetrieverFactory",
    "create_retriever",
    "create_from_memory",
    "create_hybrid_retriever",
    "create_ensemble_retriever",
    
    # Memory adapter utilities
    "MemoryRetrieverAdapter",
    "create_retriever_from_memory",
    "create_smart_retriever_from_memory",
]

# Version info
__version__ = "0.1.0"