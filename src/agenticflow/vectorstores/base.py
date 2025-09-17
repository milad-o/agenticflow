"""
Base classes and interfaces for vector stores.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog

logger = structlog.get_logger(__name__)


class VectorStoreType(str, Enum):
    """Supported vector store types."""
    FAISS = "faiss"
    CHROMA = "chroma"
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"
    MILVUS = "milvus"
    MEMORY = "memory"  # In-memory vector store


class DistanceMetric(str, Enum):
    """Distance metrics for vector similarity."""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"


@dataclass
class VectorStoreDocument:
    """Document stored in vector store with metadata."""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """Search result from vector store."""
    document: VectorStoreDocument
    score: float
    rank: int = 0


@dataclass
class VectorStoreConfig:
    """Configuration for vector stores."""
    store_type: VectorStoreType
    collection_name: str = "default"
    persist_path: Optional[str] = None
    embedding_dimension: Optional[int] = None
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    
    # Performance settings
    index_type: Optional[str] = None
    ef_construction: int = 200  # HNSW parameter
    m: int = 16  # HNSW parameter
    
    # Connection settings (for remote stores)
    host: Optional[str] = None
    port: Optional[int] = None
    api_key: Optional[str] = None
    environment: Optional[str] = None
    
    # Additional provider-specific settings
    extra_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_config is None:
            self.extra_config = {}


class VectorStoreError(Exception):
    """Base exception for vector store operations."""
    pass


class VectorStoreConnectionError(VectorStoreError):
    """Raised when vector store connection fails."""
    pass


class VectorStoreIndexError(VectorStoreError):
    """Raised when vector store indexing fails."""
    pass


class AsyncVectorStore(ABC):
    """Abstract base class for async vector stores."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize vector store with configuration."""
        self.config = config
        self.logger = logger.bind(
            vector_store=config.store_type.value,
            collection=config.collection_name
        )
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the vector store."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the vector store."""
        pass
    
    @abstractmethod
    async def create_collection(
        self, 
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None,
        distance_metric: Optional[DistanceMetric] = None
    ) -> None:
        """Create a new collection/index."""
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: Optional[str] = None) -> None:
        """Delete a collection/index."""
        pass
    
    @abstractmethod
    async def add_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> List[str]:
        """Add documents to the vector store."""
        pass
    
    @abstractmethod
    async def update_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> None:
        """Update existing documents in the vector store."""
        pass
    
    @abstractmethod
    async def delete_documents(
        self, 
        document_ids: List[str],
        collection_name: Optional[str] = None
    ) -> None:
        """Delete documents from the vector store."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    async def get_document(
        self, 
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[VectorStoreDocument]:
        """Get a document by ID."""
        pass
    
    @abstractmethod
    async def count_documents(self, collection_name: Optional[str] = None) -> int:
        """Count documents in the collection."""
        pass
    
    @abstractmethod
    async def list_collections(self) -> List[str]:
        """List all available collections."""
        pass
    
    # Optional methods that can be overridden
    async def health_check(self) -> bool:
        """Check if the vector store is healthy."""
        try:
            await self.count_documents()
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def get_collection_info(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a collection."""
        collection = collection_name or self.config.collection_name
        return {
            "collection_name": collection,
            "document_count": await self.count_documents(collection),
            "store_type": self.config.store_type.value,
            "distance_metric": self.config.distance_metric.value
        }
    
    async def bulk_search(
        self,
        query_embeddings: List[List[float]],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> List[List[SearchResult]]:
        """Perform bulk search operations."""
        results = []
        for embedding in query_embeddings:
            search_results = await self.search(
                embedding, limit, score_threshold, metadata_filter, collection_name
            )
            results.append(search_results)
        return results
    
    def _get_collection_name(self, collection_name: Optional[str] = None) -> str:
        """Get collection name, using default if not provided."""
        return collection_name or self.config.collection_name
    
    def _validate_embedding_dimension(self, embedding: List[float]) -> None:
        """Validate embedding dimension matches configuration."""
        if self.config.embedding_dimension and len(embedding) != self.config.embedding_dimension:
            raise VectorStoreError(
                f"Embedding dimension {len(embedding)} doesn't match configured dimension {self.config.embedding_dimension}"
            )
    
    def _calculate_distance(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """Calculate distance between two embeddings."""
        import math
        
        if self.config.distance_metric == DistanceMetric.COSINE:
            # Cosine similarity (converted to distance)
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            magnitude1 = math.sqrt(sum(a * a for a in embedding1))
            magnitude2 = math.sqrt(sum(b * b for b in embedding2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 1.0  # Maximum distance
            
            cosine_sim = dot_product / (magnitude1 * magnitude2)
            return 1.0 - cosine_sim  # Convert similarity to distance
        
        elif self.config.distance_metric == DistanceMetric.EUCLIDEAN:
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(embedding1, embedding2)))
        
        elif self.config.distance_metric == DistanceMetric.DOT_PRODUCT:
            return -sum(a * b for a, b in zip(embedding1, embedding2))  # Negative for distance
        
        elif self.config.distance_metric == DistanceMetric.MANHATTAN:
            return sum(abs(a - b) for a, b in zip(embedding1, embedding2))
        
        else:
            raise VectorStoreError(f"Unsupported distance metric: {self.config.distance_metric}")


class EphemeralVectorStore(AsyncVectorStore):
    """In-memory vector store implementation for testing and development."""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self.collections: Dict[str, List[VectorStoreDocument]] = {}
        self.connected = False
    
    async def connect(self) -> None:
        """Connect to the in-memory store."""
        self.connected = True
        self.logger.info("Connected to ephemeral vector store")
    
    async def disconnect(self) -> None:
        """Disconnect from the in-memory store."""
        self.connected = False
        self.collections.clear()
        self.logger.info("Disconnected from ephemeral vector store")
    
    async def create_collection(
        self, 
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None,
        distance_metric: Optional[DistanceMetric] = None
    ) -> None:
        """Create a new collection."""
        collection = self._get_collection_name(collection_name)
        if collection not in self.collections:
            self.collections[collection] = []
            self.logger.debug(f"Created collection: {collection}")
    
    async def delete_collection(self, collection_name: Optional[str] = None) -> None:
        """Delete a collection."""
        collection = self._get_collection_name(collection_name)
        if collection in self.collections:
            del self.collections[collection]
            self.logger.debug(f"Deleted collection: {collection}")
    
    async def add_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> List[str]:
        """Add documents to the collection."""
        collection = self._get_collection_name(collection_name)
        await self.create_collection(collection)
        
        for doc in documents:
            self._validate_embedding_dimension(doc.embedding)
            self.collections[collection].append(doc)
        
        self.logger.debug(f"Added {len(documents)} documents to {collection}")
        return [doc.id for doc in documents]
    
    async def update_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> None:
        """Update existing documents."""
        collection = self._get_collection_name(collection_name)
        if collection not in self.collections:
            return
        
        doc_map = {doc.id: doc for doc in documents}
        
        for i, existing_doc in enumerate(self.collections[collection]):
            if existing_doc.id in doc_map:
                self.collections[collection][i] = doc_map[existing_doc.id]
        
        self.logger.debug(f"Updated {len(documents)} documents in {collection}")
    
    async def delete_documents(
        self, 
        document_ids: List[str],
        collection_name: Optional[str] = None
    ) -> None:
        """Delete documents by ID."""
        collection = self._get_collection_name(collection_name)
        if collection not in self.collections:
            return
        
        id_set = set(document_ids)
        self.collections[collection] = [
            doc for doc in self.collections[collection]
            if doc.id not in id_set
        ]
        
        self.logger.debug(f"Deleted {len(document_ids)} documents from {collection}")
    
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for similar documents."""
        collection = self._get_collection_name(collection_name)
        if collection not in self.collections:
            return []
        
        self._validate_embedding_dimension(query_embedding)
        
        # Calculate similarities
        results = []
        for doc in self.collections[collection]:
            # Apply metadata filter if specified
            if metadata_filter:
                if not all(doc.metadata.get(k) == v for k, v in metadata_filter.items()):
                    continue
            
            distance = self._calculate_distance(query_embedding, doc.embedding)
            
            # Convert distance to similarity score (higher is better)
            if self.config.distance_metric == DistanceMetric.COSINE:
                score = 1.0 - distance  # Convert distance back to similarity
            elif self.config.distance_metric == DistanceMetric.DOT_PRODUCT:
                # For dot product, negative values are distances, so invert
                score = max(0.0, -distance)  # Convert negative distance to positive score
            else:
                score = 1.0 / (1.0 + abs(distance))  # Inverse relationship with abs to avoid division by zero
            
            # Apply score threshold
            if score_threshold and score < score_threshold:
                continue
            
            results.append(SearchResult(document=doc, score=score))
        
        # Sort by score (descending) and limit
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:limit]
        
        # Add rank information
        for i, result in enumerate(results):
            result.rank = i + 1
        
        self.logger.debug(f"Found {len(results)} results in {collection}")
        return results
    
    async def get_document(
        self, 
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[VectorStoreDocument]:
        """Get a document by ID."""
        collection = self._get_collection_name(collection_name)
        if collection not in self.collections:
            return None
        
        for doc in self.collections[collection]:
            if doc.id == document_id:
                return doc
        
        return None
    
    async def count_documents(self, collection_name: Optional[str] = None) -> int:
        """Count documents in the collection."""
        collection = self._get_collection_name(collection_name)
        return len(self.collections.get(collection, []))
    
    async def list_collections(self) -> List[str]:
        """List all available collections."""
        return list(self.collections.keys())