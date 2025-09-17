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

# LangChain integration (if available)
try:
    from .langchain_adapter import (
        LangChainVectorStoreAdapter,
        create_langchain_adapter,
        create_chroma_adapter,
        create_faiss_adapter,
        create_pinecone_adapter
    )
except ImportError:
    LangChainVectorStoreAdapter = None
    create_langchain_adapter = None
    create_chroma_adapter = None
    create_faiss_adapter = None
    create_pinecone_adapter = None

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
    
    # LangChain integration (if available)
    'LangChainVectorStoreAdapter',
    'create_langchain_adapter',
    'create_chroma_adapter',
    'create_faiss_adapter',
    'create_pinecone_adapter',
    
    # Factory and management
    'VectorStoreFactory',
    'get_vector_store',
    'cleanup_vector_stores',
    'list_vector_stores'
]
