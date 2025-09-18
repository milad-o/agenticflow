"""
Retriever Factory

Factory for creating retrievers from configurations, data sources, and memory instances.
Supports both standalone retrieval and memory-based retrieval patterns.
"""

from typing import Any, Dict, List, Optional, Type, Union
import structlog

from .base import AsyncRetriever, RetrieverConfig, RetrieverType
from .text_retrievers import (
    KeywordRetriever, KeywordRetrieverConfig,
    FullTextRetriever, FullTextRetrieverConfig,
    BM25Retriever, BM25RetrieverConfig,
    FuzzyRetriever, FuzzyRetrieverConfig,
    RegexRetriever, RegexRetrieverConfig
)
from .semantic_retrievers import (
    SemanticRetriever, SemanticRetrieverConfig,
    CosineRetriever, CosineRetrieverConfig,
    EuclideanRetriever, EuclideanRetrieverConfig,
    DotProductRetriever, DotProductRetrieverConfig,
    ManhattanRetriever, ManhattanRetrieverConfig,
    SparseRetriever, SparseRetrieverConfig
)
from .composite_retrievers import (
    EnsembleRetriever, EnsembleRetrieverConfig,
    HybridRetriever, HybridRetrieverConfig,
    ContextualRetriever, ContextualRetrieverConfig,
    FusionRetriever, FusionRetrieverConfig
)

logger = structlog.get_logger(__name__)


class RetrieverFactory:
    """Factory for creating retrievers from various configurations."""
    
    # Registry of retriever classes
    _retriever_registry: Dict[str, Type[AsyncRetriever]] = {
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
        RetrieverType.SPARSE: SparseRetriever,
        RetrieverType.ENSEMBLE: EnsembleRetriever,
        RetrieverType.HYBRID_DENSE_SPARSE: HybridRetriever,
        RetrieverType.CONTEXTUAL: ContextualRetriever,
        RetrieverType.FUSION: FusionRetriever,
    }
    
    # Registry of config classes
    _config_registry: Dict[str, Type[RetrieverConfig]] = {
        RetrieverType.KEYWORD: KeywordRetrieverConfig,
        RetrieverType.FULLTEXT: FullTextRetrieverConfig,
        RetrieverType.BM25: BM25RetrieverConfig,
        RetrieverType.FUZZY: FuzzyRetrieverConfig,
        RetrieverType.REGEX: RegexRetrieverConfig,
        RetrieverType.SEMANTIC: SemanticRetrieverConfig,
        RetrieverType.COSINE: CosineRetrieverConfig,
        RetrieverType.EUCLIDEAN: EuclideanRetrieverConfig,
        RetrieverType.DOT_PRODUCT: DotProductRetrieverConfig,
        RetrieverType.MANHATTAN: ManhattanRetrieverConfig,
        RetrieverType.SPARSE: SparseRetrieverConfig,
        RetrieverType.ENSEMBLE: EnsembleRetrieverConfig,
        RetrieverType.HYBRID_DENSE_SPARSE: HybridRetrieverConfig,
        RetrieverType.CONTEXTUAL: ContextualRetrieverConfig,
        RetrieverType.FUSION: FusionRetrieverConfig,
    }
    
    @classmethod
    def create_retriever(
        cls,
        retriever_type: str,
        data_source: Any = None,
        config: Optional[RetrieverConfig] = None,
        **kwargs
    ) -> AsyncRetriever:
        """Create a retriever instance.
        
        Args:
            retriever_type: Type of retriever to create
            data_source: Data source (memory, vector store, etc.)
            config: Retriever configuration
            **kwargs: Additional arguments for specific retriever types
            
        Returns:
            Configured retriever instance
            
        Raises:
            ValueError: If retriever type is not supported
        """
        if retriever_type not in cls._retriever_registry:
            raise ValueError(f"Unsupported retriever type: {retriever_type}")
        
        retriever_class = cls._retriever_registry[retriever_type]
        
        # Create default config if not provided
        if config is None:
            config_class = cls._config_registry.get(retriever_type, RetrieverConfig)
            config = config_class()
        
        # Handle composite retrievers that need multiple components
        if retriever_type == RetrieverType.ENSEMBLE:
            retrievers = kwargs.get('retrievers', [])
            if not retrievers:
                raise ValueError("EnsembleRetriever requires 'retrievers' parameter")
            return retriever_class(retrievers, config)
        
        elif retriever_type == RetrieverType.HYBRID_DENSE_SPARSE:
            dense_retriever = kwargs.get('dense_retriever')
            sparse_retriever = kwargs.get('sparse_retriever')
            if not dense_retriever or not sparse_retriever:
                raise ValueError("HybridRetriever requires 'dense_retriever' and 'sparse_retriever' parameters")
            return retriever_class(dense_retriever, sparse_retriever, config)
        
        elif retriever_type == RetrieverType.CONTEXTUAL:
            base_retriever = kwargs.get('base_retriever')
            if not base_retriever:
                raise ValueError("ContextualRetriever requires 'base_retriever' parameter")
            return retriever_class(base_retriever, config)
        
        elif retriever_type == RetrieverType.FUSION:
            retrievers = kwargs.get('retrievers', [])
            if not retrievers:
                raise ValueError("FusionRetriever requires 'retrievers' parameter")
            return retriever_class(retrievers, config)
        
        else:
            # Standard data source retrievers
            if data_source is None:
                raise ValueError(f"Retriever type {retriever_type} requires a data_source")
            return retriever_class(data_source, config)
    
    @classmethod
    def create_from_memory(
        cls,
        memory_instance: Any,
        retriever_type: Optional[str] = None,
        config: Optional[RetrieverConfig] = None
    ) -> AsyncRetriever:
        """Create retriever from a memory instance.
        
        Args:
            memory_instance: Memory instance (BufferMemory, VectorMemory, etc.)
            retriever_type: Specific retriever type, auto-detected if None
            config: Retriever configuration
            
        Returns:
            Configured retriever instance
        """
        # Auto-detect retriever type if not specified
        if retriever_type is None:
            retriever_type = cls._detect_optimal_retriever_type(memory_instance)
        
        logger.debug(f"Creating {retriever_type} retriever from {type(memory_instance).__name__}")
        
        return cls.create_retriever(retriever_type, memory_instance, config)
    
    @classmethod
    def create_hybrid_from_memory(
        cls,
        memory_instance: Any,
        dense_type: str = RetrieverType.SEMANTIC,
        sparse_type: str = RetrieverType.SPARSE,
        config: Optional[HybridRetrieverConfig] = None
    ) -> HybridRetriever:
        """Create hybrid dense-sparse retriever from memory.
        
        Args:
            memory_instance: Memory instance that supports both dense and sparse retrieval
            dense_type: Dense retriever type
            sparse_type: Sparse retriever type
            config: Hybrid retriever configuration
            
        Returns:
            Configured hybrid retriever
        """
        dense_retriever = cls.create_retriever(dense_type, memory_instance)
        sparse_retriever = cls.create_retriever(sparse_type, memory_instance)
        
        return cls.create_retriever(
            RetrieverType.HYBRID_DENSE_SPARSE,
            dense_retriever=dense_retriever,
            sparse_retriever=sparse_retriever,
            config=config
        )
    
    @classmethod
    def create_ensemble_from_memory(
        cls,
        memory_instance: Any,
        retriever_types: List[str],
        config: Optional[EnsembleRetrieverConfig] = None
    ) -> EnsembleRetriever:
        """Create ensemble retriever from memory with multiple strategies.
        
        Args:
            memory_instance: Memory instance
            retriever_types: List of retriever types to combine
            config: Ensemble retriever configuration
            
        Returns:
            Configured ensemble retriever
        """
        retrievers = []
        for retriever_type in retriever_types:
            try:
                retriever = cls.create_retriever(retriever_type, memory_instance)
                retrievers.append(retriever)
            except Exception as e:
                logger.warning(f"Failed to create {retriever_type} retriever: {e}")
        
        if not retrievers:
            raise ValueError("No retrievers could be created from the specified types")
        
        return cls.create_retriever(
            RetrieverType.ENSEMBLE,
            retrievers=retrievers,
            config=config
        )
    
    @classmethod
    def _detect_optimal_retriever_type(cls, data_source: Any) -> str:
        """Detect the optimal retriever type for a data source.
        
        Args:
            data_source: Data source to analyze
            
        Returns:
            Recommended retriever type
        """
        # Check for vector capabilities
        if hasattr(data_source, 'embeddings') or hasattr(data_source, '_embeddings'):
            return RetrieverType.SEMANTIC
        
        # Check for full-text search capabilities
        if hasattr(data_source, 'similarity_search'):
            return RetrieverType.SEMANTIC
        
        # Check for database-like capabilities
        if hasattr(data_source, 'execute') or hasattr(data_source, 'query'):
            return RetrieverType.FULLTEXT
        
        # Check for search method
        if hasattr(data_source, 'search'):
            return RetrieverType.KEYWORD
        
        # Default to keyword search
        return RetrieverType.KEYWORD
    
    @classmethod
    def register_retriever(
        cls,
        retriever_type: str,
        retriever_class: Type[AsyncRetriever],
        config_class: Type[RetrieverConfig]
    ):
        """Register a custom retriever type.
        
        Args:
            retriever_type: Unique identifier for the retriever
            retriever_class: Retriever implementation class
            config_class: Configuration class for the retriever
        """
        cls._retriever_registry[retriever_type] = retriever_class
        cls._config_registry[retriever_type] = config_class
        
        logger.info(f"Registered custom retriever type: {retriever_type}")
    
    @classmethod
    def list_supported_types(cls) -> List[str]:
        """List all supported retriever types.
        
        Returns:
            List of supported retriever type strings
        """
        return list(cls._retriever_registry.keys())
    
    @classmethod
    def get_config_class(cls, retriever_type: str) -> Type[RetrieverConfig]:
        """Get the configuration class for a retriever type.
        
        Args:
            retriever_type: Retriever type
            
        Returns:
            Configuration class for the retriever
            
        Raises:
            ValueError: If retriever type is not supported
        """
        if retriever_type not in cls._config_registry:
            raise ValueError(f"Unsupported retriever type: {retriever_type}")
        
        return cls._config_registry[retriever_type]


# Convenience functions
def create_retriever(
    retriever_type: str,
    data_source: Any = None,
    config: Optional[RetrieverConfig] = None,
    **kwargs
) -> AsyncRetriever:
    """Convenience function to create a retriever."""
    return RetrieverFactory.create_retriever(retriever_type, data_source, config, **kwargs)


def create_from_memory(
    memory_instance: Any,
    retriever_type: Optional[str] = None,
    config: Optional[RetrieverConfig] = None
) -> AsyncRetriever:
    """Convenience function to create retriever from memory."""
    return RetrieverFactory.create_from_memory(memory_instance, retriever_type, config)


def create_hybrid_retriever(
    memory_instance: Any,
    dense_type: str = RetrieverType.SEMANTIC,
    sparse_type: str = RetrieverType.SPARSE,
    config: Optional[HybridRetrieverConfig] = None
) -> HybridRetriever:
    """Convenience function to create hybrid retriever."""
    return RetrieverFactory.create_hybrid_from_memory(memory_instance, dense_type, sparse_type, config)


def create_ensemble_retriever(
    memory_instance: Any,
    retriever_types: List[str],
    config: Optional[EnsembleRetrieverConfig] = None
) -> EnsembleRetriever:
    """Convenience function to create ensemble retriever."""
    return RetrieverFactory.create_ensemble_from_memory(memory_instance, retriever_types, config)