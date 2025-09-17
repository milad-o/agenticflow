"""Vector stores for AgenticFlow."""

# Import core components
from .base import (
    AsyncVectorStore,
    VectorStoreType,
    DistanceMetric,
    VectorStoreConfig,
    VectorStoreDocument,
    SearchResult,
    VectorStoreError,
    VectorStoreConnectionError,
    VectorStoreIndexError,
    EphemeralVectorStore
)

# Import factory and management
from .factory import (
    VectorStoreFactory,
    get_vector_store,
    cleanup_vector_stores,
    list_vector_stores
)

# Import specific implementations (with graceful fallbacks)
try:
    from .faiss_store import FAISSVectorStore
except ImportError:
    FAISSVectorStore = None

try:
    from .chroma_store import ChromaVectorStore
except ImportError:
    ChromaVectorStore = None

__all__ = [
    # Core types
    'AsyncVectorStore',
    'VectorStoreType',
    'DistanceMetric',
    'VectorStoreConfig',
    'VectorStoreDocument',
    'SearchResult',
    
    # Exceptions
    'VectorStoreError',
    'VectorStoreConnectionError',
    'VectorStoreIndexError',
    
    # Base implementations
    'EphemeralVectorStore',
    
    # Specific implementations (if available)
    'FAISSVectorStore',
    'ChromaVectorStore',
    
    # Factory and management
    'VectorStoreFactory',
    'get_vector_store',
    'cleanup_vector_stores',
    'list_vector_stores'
]