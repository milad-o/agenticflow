"""
Chroma vector store implementation.
"""

from typing import Any, Dict, List, Optional
import uuid

from .base import (
    AsyncVectorStore,
    VectorStoreConfig,
    VectorStoreDocument,
    SearchResult,
    VectorStoreError,
    VectorStoreConnectionError,
    DistanceMetric
)


class ChromaVectorStore(AsyncVectorStore):
    """Chroma-based vector store implementation."""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self.client = None
        self.collection = None
        self.connected = False
        
        # Chroma requires specific imports
        try:
            import chromadb
            from chromadb.config import Settings
            self.chromadb = chromadb
            self.Settings = Settings
        except ImportError:
            raise VectorStoreError(
                "Chroma not installed. Install with: pip install chromadb"
            )
    
    async def connect(self) -> None:
        """Connect to Chroma."""
        try:
            # Create client based on configuration
            if self.config.persist_path:
                # Persistent client
                self.client = self.chromadb.PersistentClient(
                    path=self.config.persist_path,
                    settings=self.Settings(anonymized_telemetry=False)
                )
            elif self.config.host:
                # Remote client
                self.client = self.chromadb.HttpClient(
                    host=self.config.host,
                    port=self.config.port or 8000,
                    settings=self.Settings(anonymized_telemetry=False)
                )
            else:
                # In-memory client
                self.client = self.chromadb.Client(
                    settings=self.Settings(anonymized_telemetry=False)
                )
            
            # Get or create collection
            await self._ensure_collection()
            
            self.connected = True
            self.logger.info("Connected to Chroma vector store")
        
        except Exception as e:
            raise VectorStoreConnectionError(f"Failed to connect to Chroma: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Chroma."""
        self.client = None
        self.collection = None
        self.connected = False
        self.logger.info("Disconnected from Chroma vector store")
    
    async def create_collection(
        self, 
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None,
        distance_metric: Optional[DistanceMetric] = None
    ) -> None:
        """Create a new collection in Chroma."""
        if not self.connected:
            await self.connect()
        
        collection_name = collection_name or self.config.collection_name
        
        # Map distance metric to Chroma metric
        distance_function = self._map_distance_metric(distance_metric or self.config.distance_metric)
        
        try:
            # Delete existing collection if it exists
            try:
                self.client.delete_collection(name=collection_name)
            except:
                pass  # Collection doesn't exist, which is fine
            
            # Create new collection
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": distance_function}
            )
            
            self.logger.debug(f"Created Chroma collection: {collection_name}")
        
        except Exception as e:
            raise VectorStoreError(f"Failed to create Chroma collection: {e}")
    
    async def delete_collection(self, collection_name: Optional[str] = None) -> None:
        """Delete a collection from Chroma."""
        if not self.connected:
            return
        
        collection_name = collection_name or self.config.collection_name
        
        try:
            self.client.delete_collection(name=collection_name)
            self.collection = None
            self.logger.debug(f"Deleted Chroma collection: {collection_name}")
        
        except Exception as e:
            self.logger.error(f"Failed to delete Chroma collection: {e}")
    
    async def add_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> List[str]:
        """Add documents to Chroma."""
        if not self.connected:
            await self.connect()
        
        if not documents:
            return []
        
        # Ensure we have the right collection
        if collection_name and collection_name != self.config.collection_name:
            await self._get_collection(collection_name)
        
        # Validate dimensions
        for doc in documents:
            self._validate_embedding_dimension(doc.embedding)
        
        # Prepare data for Chroma
        ids = [doc.id for doc in documents]
        embeddings = [doc.embedding for doc in documents]
        documents_content = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents_content,
                metadatas=metadatas
            )
            
            self.logger.debug(f"Added {len(documents)} documents to Chroma")
            return ids
        
        except Exception as e:
            raise VectorStoreError(f"Failed to add documents to Chroma: {e}")
    
    async def update_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> None:
        """Update documents in Chroma."""
        if not self.connected:
            await self.connect()
        
        if not documents:
            return
        
        # Ensure we have the right collection
        if collection_name and collection_name != self.config.collection_name:
            await self._get_collection(collection_name)
        
        # Prepare data for Chroma
        ids = [doc.id for doc in documents]
        embeddings = [doc.embedding for doc in documents]
        documents_content = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        try:
            self.collection.update(
                ids=ids,
                embeddings=embeddings,
                documents=documents_content,
                metadatas=metadatas
            )
            
            self.logger.debug(f"Updated {len(documents)} documents in Chroma")
        
        except Exception as e:
            raise VectorStoreError(f"Failed to update documents in Chroma: {e}")
    
    async def delete_documents(
        self, 
        document_ids: List[str],
        collection_name: Optional[str] = None
    ) -> None:
        """Delete documents from Chroma."""
        if not self.connected or not document_ids:
            return
        
        # Ensure we have the right collection
        if collection_name and collection_name != self.config.collection_name:
            await self._get_collection(collection_name)
        
        try:
            self.collection.delete(ids=document_ids)
            self.logger.debug(f"Deleted {len(document_ids)} documents from Chroma")
        
        except Exception as e:
            raise VectorStoreError(f"Failed to delete documents from Chroma: {e}")
    
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for similar documents in Chroma."""
        if not self.connected:
            return []
        
        # Ensure we have the right collection
        if collection_name and collection_name != self.config.collection_name:
            await self._get_collection(collection_name)
        
        self._validate_embedding_dimension(query_embedding)
        
        try:
            # Build query parameters
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": limit
            }
            
            # Add metadata filter if specified
            if metadata_filter:
                query_params["where"] = metadata_filter
            
            # Execute search
            results = self.collection.query(**query_params)
            
            # Process results
            search_results = []
            
            if results["ids"] and results["ids"][0]:  # Check if we have results
                ids = results["ids"][0]
                distances = results["distances"][0] if results["distances"] else [0] * len(ids)
                documents_content = results["documents"][0] if results["documents"] else [""] * len(ids)
                metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
                
                for i, (doc_id, distance, content, metadata) in enumerate(zip(ids, distances, documents_content, metadatas)):
                    # Convert distance to similarity score
                    if self.config.distance_metric == DistanceMetric.COSINE:
                        # Chroma returns distances, convert to similarity
                        score = max(0.0, 1.0 - distance)
                    else:
                        # For other metrics, use inverse relationship
                        score = 1.0 / (1.0 + distance)
                    
                    # Apply score threshold
                    if score_threshold and score < score_threshold:
                        continue
                    
                    # Create document
                    doc = VectorStoreDocument(
                        id=doc_id,
                        content=content,
                        embedding=query_embedding,  # Use query embedding as placeholder
                        metadata=metadata or {}
                    )
                    
                    search_results.append(SearchResult(
                        document=doc,
                        score=score,
                        rank=i + 1
                    ))
            
            self.logger.debug(f"Found {len(search_results)} results in Chroma")
            return search_results
        
        except Exception as e:
            self.logger.error(f"Search failed in Chroma: {e}")
            return []
    
    async def get_document(
        self, 
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[VectorStoreDocument]:
        """Get a document by ID from Chroma."""
        if not self.connected:
            return None
        
        # Ensure we have the right collection
        if collection_name and collection_name != self.config.collection_name:
            await self._get_collection(collection_name)
        
        try:
            results = self.collection.get(
                ids=[document_id],
                include=["documents", "metadatas", "embeddings"]
            )
            
            if results["ids"] and results["ids"][0] == document_id:
                content = results["documents"][0] if results["documents"] else ""
                metadata = results["metadatas"][0] if results["metadatas"] else {}
                embedding = results["embeddings"][0] if results["embeddings"] else []
                
                return VectorStoreDocument(
                    id=document_id,
                    content=content,
                    embedding=embedding,
                    metadata=metadata
                )
        
        except Exception as e:
            self.logger.error(f"Failed to get document {document_id} from Chroma: {e}")
        
        return None
    
    async def count_documents(self, collection_name: Optional[str] = None) -> int:
        """Count documents in Chroma collection."""
        if not self.connected:
            return 0
        
        # Ensure we have the right collection
        if collection_name and collection_name != self.config.collection_name:
            await self._get_collection(collection_name)
        
        try:
            return self.collection.count()
        except Exception as e:
            self.logger.error(f"Failed to count documents in Chroma: {e}")
            return 0
    
    async def list_collections(self) -> List[str]:
        """List all collections in Chroma."""
        if not self.connected:
            return []
        
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            self.logger.error(f"Failed to list Chroma collections: {e}")
            return []
    
    async def _ensure_collection(self) -> None:
        """Ensure the collection exists, create if it doesn't."""
        try:
            self.collection = self.client.get_collection(name=self.config.collection_name)
        except:
            # Collection doesn't exist, create it
            await self.create_collection()
    
    async def _get_collection(self, collection_name: str) -> None:
        """Get a specific collection."""
        try:
            self.collection = self.client.get_collection(name=collection_name)
            self.config.collection_name = collection_name
        except Exception as e:
            raise VectorStoreError(f"Failed to get Chroma collection {collection_name}: {e}")
    
    def _map_distance_metric(self, metric: DistanceMetric) -> str:
        """Map DistanceMetric to Chroma distance function."""
        mapping = {
            DistanceMetric.COSINE: "cosine",
            DistanceMetric.EUCLIDEAN: "l2",
            DistanceMetric.DOT_PRODUCT: "ip",  # inner product
            DistanceMetric.MANHATTAN: "l1"
        }
        
        return mapping.get(metric, "cosine")