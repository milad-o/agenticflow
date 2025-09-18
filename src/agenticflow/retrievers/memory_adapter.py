"""
Memory Retriever Adapter

Provides utilities to create retrievers from existing memory instances while maintaining
the modular retriever architecture. This allows users to leverage existing memory
systems with the new retriever capabilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING
import structlog

from .base import AsyncRetriever, RetrieverConfig, RetrieverType, DataSourceRetriever
from ..memory.core import AsyncMemory

if TYPE_CHECKING:
    from .composite_retrievers import EnsembleRetriever

logger = structlog.get_logger(__name__)


class MemoryRetrieverAdapter:
    """Adapter to create retrievers from memory instances."""
    
    @classmethod
    def from_memory(
        cls,
        memory: AsyncMemory,
        retriever_type: Optional[RetrieverType] = None,
        config: Optional[RetrieverConfig] = None
    ) -> AsyncRetriever:
        """Create a retriever from an existing memory instance.
        
        Args:
            memory: Existing memory instance (BufferMemory, VectorMemory, etc.)
            retriever_type: Specific retriever type to use (auto-detected if None)
            config: Retriever configuration (uses defaults if None)
            
        Returns:
            Appropriate retriever instance
            
        Usage:
            # Auto-detect best retriever for memory type
            retriever = MemoryRetrieverAdapter.from_memory(vector_memory)
            
            # Force specific retriever type
            retriever = MemoryRetrieverAdapter.from_memory(
                sqlite_memory,
                retriever_type=RetrieverType.BM25,
                config=BM25RetrieverConfig(k1=1.2, b=0.75)
            )
        """
        config = config or RetrieverConfig()
        
        # Auto-detect retriever type if not specified
        if retriever_type is None:
            retriever_type = cls._detect_best_retriever_type(memory)
        
        # Create appropriate retriever
        return cls._create_retriever_for_memory(memory, retriever_type, config)
    
    @classmethod
    def _detect_best_retriever_type(cls, memory: AsyncMemory) -> RetrieverType:
        """Detect the best retriever type for a memory instance."""
        memory_type = type(memory).__name__
        
        # Map memory types to best retriever strategies
        memory_retriever_map = {
            'BufferMemory': RetrieverType.KEYWORD,
            'SQLiteMemory': RetrieverType.FULLTEXT,  # Can also use BM25
            'PostgreSQLMemory': RetrieverType.FULLTEXT,  # Has full-text search
            'VectorMemory': RetrieverType.SEMANTIC,
            'EnhancedMemory': RetrieverType.SEMANTIC,  # Has embeddings and fragments
            'RetrievalMemory': RetrieverType.SEMANTIC,
            'HybridMemory': RetrieverType.ENSEMBLE,  # Combines multiple strategies
        }
        
        detected_type = memory_retriever_map.get(memory_type, RetrieverType.KEYWORD)
        logger.info(f"Auto-detected retriever type {detected_type} for memory {memory_type}")
        
        return detected_type
    
    @classmethod
    def _create_retriever_for_memory(
        cls,
        memory: AsyncMemory,
        retriever_type: RetrieverType,
        config: RetrieverConfig
    ) -> AsyncRetriever:
        """Create specific retriever for memory instance."""
        from .text_retrievers import KeywordRetriever, FullTextRetriever, BM25Retriever, FuzzyRetriever, RegexRetriever
        from .semantic_retrievers import SemanticRetriever, CosineRetriever, EuclideanRetriever, DotProductRetriever, ManhattanRetriever
        from .composite_retrievers import EnsembleRetriever, FusionRetriever
        
        # Map retriever types to classes
        retriever_classes = {
            RetrieverType.KEYWORD: KeywordRetriever,
            RetrieverType.FULLTEXT: FullTextRetriever,
            RetrieverType.BM25: BM25Retriever,
            RetrieverType.FUZZY: FuzzyRetriever,
            RetrieverType.REGEX: RegexRetriever,
            RetrieverType.SEMANTIC: SemanticRetriever,
            RetrieverType.COSINE: CosineRetriever,
            RetrieverType.EUCLIDEAN: EuclideanRetriever,
            RetrieverType.DOT_PRODUCT: DotProductRetriever,
            RetrieverType.MANHATTAN: ManhattanRetriever,
            RetrieverType.ENSEMBLE: EnsembleRetriever,
            RetrieverType.FUSION: FusionRetriever,
        }
        
        retriever_class = retriever_classes.get(retriever_type)
        if not retriever_class:
            logger.warning(f"Retriever type {retriever_type} not implemented, using KeywordRetriever")
            retriever_class = KeywordRetriever
        
        # Create retriever with memory as data source
        return retriever_class(data_source=memory, config=config)
    
    @classmethod
    def get_compatible_retrievers(cls, memory: AsyncMemory) -> List[RetrieverType]:
        """Get list of retriever types compatible with a memory instance.
        
        Args:
            memory: Memory instance to check
            
        Returns:
            List of compatible retriever types
        """
        memory_type = type(memory).__name__
        
        # Define compatibility matrix
        compatibility_matrix = {
            'BufferMemory': [
                RetrieverType.KEYWORD,
                RetrieverType.FUZZY,
                RetrieverType.REGEX,
            ],
            'SQLiteMemory': [
                RetrieverType.KEYWORD,
                RetrieverType.FULLTEXT,
                RetrieverType.BM25,
                RetrieverType.FUZZY,
                RetrieverType.REGEX,
            ],
            'PostgreSQLMemory': [
                RetrieverType.KEYWORD,
                RetrieverType.FULLTEXT,
                RetrieverType.BM25,
                RetrieverType.FUZZY,
                RetrieverType.REGEX,
            ],
            'VectorMemory': [
                RetrieverType.KEYWORD,  # Fallback text search
                RetrieverType.SEMANTIC,
                RetrieverType.COSINE,
                RetrieverType.EUCLIDEAN,
                RetrieverType.DOT_PRODUCT,
                RetrieverType.MANHATTAN,
            ],
            'EnhancedMemory': [
                RetrieverType.KEYWORD,
                RetrieverType.SEMANTIC,
                RetrieverType.COSINE,
                RetrieverType.EUCLIDEAN,
                RetrieverType.DOT_PRODUCT,
                RetrieverType.MANHATTAN,
            ],
            'RetrievalMemory': [
                RetrieverType.SEMANTIC,
                RetrieverType.COSINE,
                RetrieverType.EUCLIDEAN,
                RetrieverType.DOT_PRODUCT,
                RetrieverType.MANHATTAN,
            ],
            'HybridMemory': [
                RetrieverType.KEYWORD,
                RetrieverType.SEMANTIC,
                RetrieverType.ENSEMBLE,
                RetrieverType.FUSION,
            ],
        }
        
        compatible = compatibility_matrix.get(memory_type, [RetrieverType.KEYWORD])
        logger.debug(f"Compatible retrievers for {memory_type}: {compatible}")
        
        return compatible
    
    @classmethod
    def create_ensemble_from_memory(
        cls,
        memory: AsyncMemory,
        retriever_types: Optional[List[RetrieverType]] = None,
        config: Optional[RetrieverConfig] = None
    ) -> EnsembleRetriever:
        """Create an ensemble retriever using multiple strategies on the same memory.
        
        Args:
            memory: Memory instance to create ensemble for
            retriever_types: List of retriever types to combine (auto-selects if None)
            config: Base configuration for all retrievers
            
        Returns:
            EnsembleRetriever instance
            
        Usage:
            # Auto-create ensemble with best strategies
            ensemble = MemoryRetrieverAdapter.create_ensemble_from_memory(vector_memory)
            
            # Custom ensemble
            ensemble = MemoryRetrieverAdapter.create_ensemble_from_memory(
                sqlite_memory,
                retriever_types=[RetrieverType.KEYWORD, RetrieverType.BM25, RetrieverType.FULLTEXT]
            )
        """
        from .composite_retrievers import EnsembleRetriever
        
        config = config or RetrieverConfig()
        
        # Auto-select retriever types if not provided
        if retriever_types is None:
            compatible_types = cls.get_compatible_retrievers(memory)
            # Select a good mix of retriever types
            retriever_types = compatible_types[:3]  # Take first 3 compatible types
        
        # Create individual retrievers
        retrievers = []
        for retriever_type in retriever_types:
            try:
                retriever = cls._create_retriever_for_memory(memory, retriever_type, config)
                retrievers.append(retriever)
            except Exception as e:
                logger.warning(f"Failed to create {retriever_type} retriever: {e}")
                continue
        
        if not retrievers:
            # Fallback to keyword retriever
            retriever = cls._create_retriever_for_memory(memory, RetrieverType.KEYWORD, config)
            retrievers.append(retriever)
        
        return EnsembleRetriever(retrievers, config)


# Convenience functions for common use cases
async def create_retriever_from_memory(
    memory: AsyncMemory,
    retriever_type: Optional[RetrieverType] = None,
    **config_kwargs
) -> AsyncRetriever:
    """Convenience function to create retriever from memory.
    
    Usage:
        retriever = await create_retriever_from_memory(
            vector_memory,
            retriever_type=RetrieverType.SEMANTIC,
            similarity_threshold=0.8
        )
    """
    config = RetrieverConfig(**config_kwargs)
    return MemoryRetrieverAdapter.from_memory(memory, retriever_type, config)


async def create_smart_retriever_from_memory(
    memory: AsyncMemory,
    **config_kwargs
) -> AsyncRetriever:
    """Create the best retriever for a memory instance with smart defaults.
    
    For vector-enabled memories, creates ensemble of semantic + keyword search.
    For text memories, creates ensemble of full-text + keyword search.
    
    Usage:
        retriever = await create_smart_retriever_from_memory(
            memory,
            similarity_threshold=0.7,
            max_results=10
        )
    """
    config = RetrieverConfig(**config_kwargs)
    
    # Check if memory supports semantic search
    has_embeddings = (
        hasattr(memory, 'embeddings') or
        hasattr(memory, '_embeddings') or
        'Vector' in type(memory).__name__ or
        'Enhanced' in type(memory).__name__
    )
    
    if has_embeddings:
        # Create ensemble with semantic + keyword for vector memories
        return MemoryRetrieverAdapter.create_ensemble_from_memory(
            memory,
            retriever_types=[RetrieverType.SEMANTIC, RetrieverType.KEYWORD],
            config=config
        )
    else:
        # Create ensemble with text-based strategies for non-vector memories
        compatible_types = MemoryRetrieverAdapter.get_compatible_retrievers(memory)
        text_types = [t for t in compatible_types if t in [
            RetrieverType.FULLTEXT, RetrieverType.BM25, RetrieverType.KEYWORD
        ]]
        
        return MemoryRetrieverAdapter.create_ensemble_from_memory(
            memory,
            retriever_types=text_types[:2],  # Use best 2 text strategies
            config=config
        )