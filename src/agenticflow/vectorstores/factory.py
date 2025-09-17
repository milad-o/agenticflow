"""
Factory for creating vector store instances.
"""

from typing import Optional, Dict, Any
import structlog

from .base import (
    AsyncVectorStore,
    VectorStoreConfig,
    VectorStoreType,
    VectorStoreError,
    EphemeralVectorStore
)

logger = structlog.get_logger(__name__)


class VectorStoreFactory:
    """Factory for creating vector store instances."""
    
    @staticmethod
    def create_vector_store(config: VectorStoreConfig) -> AsyncVectorStore:
        """Create a vector store instance based on configuration."""
        
        try:
            if config.store_type == VectorStoreType.MEMORY:
                return EphemeralVectorStore(config)
            
            elif config.store_type == VectorStoreType.FAISS:
                from .faiss_store import FAISSVectorStore
                return FAISSVectorStore(config)
            
            elif config.store_type == VectorStoreType.CHROMA:
                from .chroma_store import ChromaVectorStore
                return ChromaVectorStore(config)
            
            elif config.store_type == VectorStoreType.PINECONE:
                from .pinecone_store import PineconeVectorStore
                return PineconeVectorStore(config)
            
            elif config.store_type == VectorStoreType.QDRANT:
                from .qdrant_store import QdrantVectorStore
                return QdrantVectorStore(config)
            
            else:
                raise VectorStoreError(f"Unsupported vector store type: {config.store_type}")
        
        except ImportError as e:
            # Fallback to ephemeral store if specific implementation not available
            logger.warning(f"Failed to import {config.store_type} implementation: {e}")
            logger.info("Falling back to ephemeral vector store")
            ephemeral_config = VectorStoreConfig(
                store_type=VectorStoreType.MEMORY,
                collection_name=config.collection_name,
                embedding_dimension=config.embedding_dimension,
                distance_metric=config.distance_metric
            )
            return EphemeralVectorStore(ephemeral_config)
    
    @staticmethod
    def get_supported_stores() -> list[VectorStoreType]:
        """Get list of supported vector store types."""
        return list(VectorStoreType)
    
    @staticmethod
    def get_store_description(store_type: VectorStoreType) -> str:
        """Get description of a vector store type."""
        descriptions = {
            VectorStoreType.MEMORY: "In-memory ephemeral vector store for development and testing",
            VectorStoreType.FAISS: "Facebook AI Similarity Search - fast local vector search with persistence",
            VectorStoreType.CHROMA: "Open-source embedding database with local and remote options",
            VectorStoreType.PINECONE: "Managed vector database service with enterprise features",
            VectorStoreType.QDRANT: "Open-source vector database with advanced filtering",
            VectorStoreType.WEAVIATE: "Open-source vector database with semantic search capabilities",
            VectorStoreType.MILVUS: "Open-source vector database built for scalable similarity search"
        }
        
        return descriptions.get(store_type, "Unknown vector store")
    
    @staticmethod
    def create_faiss_config(
        collection_name: str = "default",
        persist_path: Optional[str] = None,
        embedding_dimension: int = 1536,
        index_type: str = "flat",
        **kwargs
    ) -> VectorStoreConfig:
        """Create FAISS vector store configuration."""
        return VectorStoreConfig(
            store_type=VectorStoreType.FAISS,
            collection_name=collection_name,
            persist_path=persist_path,
            embedding_dimension=embedding_dimension,
            index_type=index_type,
            **kwargs
        )
    
    @staticmethod
    def create_chroma_config(
        collection_name: str = "default",
        persist_path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        embedding_dimension: Optional[int] = None,
        **kwargs
    ) -> VectorStoreConfig:
        """Create Chroma vector store configuration."""
        return VectorStoreConfig(
            store_type=VectorStoreType.CHROMA,
            collection_name=collection_name,
            persist_path=persist_path,
            host=host,
            port=port,
            embedding_dimension=embedding_dimension,
            **kwargs
        )
    
    @staticmethod
    def create_pinecone_config(
        collection_name: str = "default",
        api_key: str = None,
        environment: str = None,
        embedding_dimension: int = 1536,
        **kwargs
    ) -> VectorStoreConfig:
        """Create Pinecone vector store configuration."""
        return VectorStoreConfig(
            store_type=VectorStoreType.PINECONE,
            collection_name=collection_name,
            api_key=api_key,
            environment=environment,
            embedding_dimension=embedding_dimension,
            **kwargs
        )
    
    @staticmethod
    def create_ephemeral_config(
        collection_name: str = "default",
        embedding_dimension: Optional[int] = None,
        **kwargs
    ) -> VectorStoreConfig:
        """Create ephemeral/memory vector store configuration."""
        return VectorStoreConfig(
            store_type=VectorStoreType.MEMORY,
            collection_name=collection_name,
            embedding_dimension=embedding_dimension,
            **kwargs
        )
    
    @staticmethod
    def auto_select_store(
        requirements: Dict[str, Any]
    ) -> VectorStoreType:
        """Auto-select best vector store type based on requirements."""
        
        # Check if persistence is required
        needs_persistence = requirements.get("persistence", False)
        
        # Check scale requirements
        expected_documents = requirements.get("expected_documents", 1000)
        
        # Check deployment preference
        deployment = requirements.get("deployment", "local")  # local, remote, cloud
        
        # Check budget considerations
        budget = requirements.get("budget", "free")  # free, low, medium, high
        
        # Auto-selection logic
        if not needs_persistence and expected_documents < 10000:
            return VectorStoreType.MEMORY
        
        elif deployment == "local" and expected_documents < 100000:
            return VectorStoreType.FAISS
        
        elif deployment == "local" and budget in ["free", "low"]:
            return VectorStoreType.CHROMA
        
        elif deployment == "cloud" and budget in ["medium", "high"]:
            return VectorStoreType.PINECONE
        
        elif expected_documents > 1000000:
            return VectorStoreType.QDRANT
        
        else:
            # Default to Chroma as it's versatile
            return VectorStoreType.CHROMA


# Global vector store manager
_global_vector_stores: Dict[str, AsyncVectorStore] = {}


async def get_vector_store(
    name: str,
    config: Optional[VectorStoreConfig] = None
) -> AsyncVectorStore:
    """Get or create a named vector store instance."""
    global _global_vector_stores
    
    if name in _global_vector_stores:
        return _global_vector_stores[name]
    
    if not config:
        # Create default ephemeral config
        config = VectorStoreFactory.create_ephemeral_config(collection_name=name)
    
    # Create and connect vector store
    store = VectorStoreFactory.create_vector_store(config)
    await store.connect()
    
    # Cache for future use
    _global_vector_stores[name] = store
    
    logger.info(f"Created vector store '{name}' of type {config.store_type.value}")
    return store


async def cleanup_vector_stores():
    """Cleanup all managed vector stores."""
    global _global_vector_stores
    
    for name, store in _global_vector_stores.items():
        try:
            await store.disconnect()
            logger.debug(f"Cleaned up vector store '{name}'")
        except Exception as e:
            logger.error(f"Error cleaning up vector store '{name}': {e}")
    
    _global_vector_stores.clear()


def list_vector_stores() -> list[str]:
    """List all active vector store names."""
    return list(_global_vector_stores.keys())