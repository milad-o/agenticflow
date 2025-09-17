"""
FAISS vector store implementation.
"""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .base import (
    AsyncVectorStore,
    VectorStoreConfig,
    VectorStoreDocument,
    SearchResult,
    VectorStoreError,
    VectorStoreConnectionError,
    DistanceMetric
)


class FAISSVectorStore(AsyncVectorStore):
    """FAISS-based vector store implementation."""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self.index = None
        self.metadata_store = {}  # Store document metadata
        self.id_to_index_map = {}  # Map document IDs to FAISS index positions
        self.index_to_id_map = {}  # Map FAISS index positions to document IDs
        self.connected = False
        
        # FAISS requires specific imports
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise VectorStoreError(
                "FAISS not installed. Install with: pip install faiss-cpu or pip install faiss-gpu"
            )
    
    async def connect(self) -> None:
        """Connect to FAISS (initialize index)."""
        try:
            if self.config.persist_path and Path(self.config.persist_path).exists():
                await self._load_index()
            else:
                await self._initialize_new_index()
            
            self.connected = True
            self.logger.info("Connected to FAISS vector store")
        
        except Exception as e:
            raise VectorStoreConnectionError(f"Failed to connect to FAISS: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from FAISS (save and cleanup)."""
        if self.connected and self.config.persist_path:
            await self._save_index()
        
        self.index = None
        self.metadata_store.clear()
        self.id_to_index_map.clear()
        self.index_to_id_map.clear()
        self.connected = False
        
        self.logger.info("Disconnected from FAISS vector store")
    
    async def create_collection(
        self, 
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None,
        distance_metric: Optional[DistanceMetric] = None
    ) -> None:
        """Create a new FAISS index (FAISS doesn't have collections per se)."""
        if not self.connected:
            await self.connect()
        
        # FAISS doesn't support multiple collections in a single index,
        # but we can reinitialize with new parameters
        if dimension:
            self.config.embedding_dimension = dimension
        
        if distance_metric:
            self.config.distance_metric = distance_metric
        
        await self._initialize_new_index()
        self.logger.debug(f"Created FAISS index with dimension {self.config.embedding_dimension}")
    
    async def delete_collection(self, collection_name: Optional[str] = None) -> None:
        """Delete the FAISS index."""
        self.index = None
        self.metadata_store.clear()
        self.id_to_index_map.clear()
        self.index_to_id_map.clear()
        
        if self.config.persist_path:
            # Remove persisted files
            persist_path = Path(self.config.persist_path)
            if persist_path.exists():
                persist_path.unlink()
            
            metadata_path = persist_path.with_suffix('.metadata.json')
            if metadata_path.exists():
                metadata_path.unlink()
        
        self.logger.debug("Deleted FAISS index")
    
    async def add_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> List[str]:
        """Add documents to the FAISS index."""
        if not self.connected:
            await self.connect()
        
        if not documents:
            return []
        
        # Validate dimensions
        for doc in documents:
            self._validate_embedding_dimension(doc.embedding)
        
        # Create embeddings matrix
        embeddings = np.array([doc.embedding for doc in documents], dtype=np.float32)
        
        # Get starting index for new documents
        start_idx = self.index.ntotal if self.index else 0
        
        # Add to FAISS index
        if self.index is None:
            await self._initialize_new_index()
        
        self.index.add(embeddings)
        
        # Update mappings and metadata
        added_ids = []
        for i, doc in enumerate(documents):
            idx = start_idx + i
            self.id_to_index_map[doc.id] = idx
            self.index_to_id_map[idx] = doc.id
            self.metadata_store[doc.id] = {
                'content': doc.content,
                'metadata': doc.metadata
            }
            added_ids.append(doc.id)
        
        self.logger.debug(f"Added {len(documents)} documents to FAISS index")
        return added_ids
    
    async def update_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> None:
        """Update documents in FAISS (requires rebuilding index)."""
        # FAISS doesn't support in-place updates, so we need to rebuild
        doc_ids_to_update = {doc.id for doc in documents}
        
        # Get all existing documents except those being updated
        existing_docs = []
        for doc_id, metadata in self.metadata_store.items():
            if doc_id not in doc_ids_to_update:
                # Reconstruct document with embedding
                idx = self.id_to_index_map[doc_id]
                embedding = self.index.reconstruct(idx).tolist()
                existing_docs.append(VectorStoreDocument(
                    id=doc_id,
                    content=metadata['content'],
                    embedding=embedding,
                    metadata=metadata['metadata']
                ))
        
        # Clear current index
        await self.delete_collection()
        await self.connect()
        
        # Add all documents (existing + updated)
        all_docs = existing_docs + documents
        await self.add_documents(all_docs)
        
        self.logger.debug(f"Updated {len(documents)} documents in FAISS index")
    
    async def delete_documents(
        self, 
        document_ids: List[str],
        collection_name: Optional[str] = None
    ) -> None:
        """Delete documents from FAISS (requires rebuilding index)."""
        if not document_ids:
            return
        
        doc_ids_to_delete = set(document_ids)
        
        # Get all documents except those being deleted
        remaining_docs = []
        for doc_id, metadata in self.metadata_store.items():
            if doc_id not in doc_ids_to_delete:
                # Reconstruct document with embedding
                idx = self.id_to_index_map[doc_id]
                embedding = self.index.reconstruct(idx).tolist()
                remaining_docs.append(VectorStoreDocument(
                    id=doc_id,
                    content=metadata['content'],
                    embedding=embedding,
                    metadata=metadata['metadata']
                ))
        
        # Rebuild index with remaining documents
        await self.delete_collection()
        if remaining_docs:
            await self.connect()
            await self.add_documents(remaining_docs)
        
        self.logger.debug(f"Deleted {len(document_ids)} documents from FAISS index")
    
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for similar documents in FAISS."""
        if not self.connected or not self.index:
            return []
        
        self._validate_embedding_dimension(query_embedding)
        
        # Convert to numpy array
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search in FAISS
        scores, indices = self.index.search(query_vector, min(limit * 2, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            # Skip invalid indices
            if idx == -1:
                continue
            
            doc_id = self.index_to_id_map.get(idx)
            if not doc_id:
                continue
            
            metadata = self.metadata_store.get(doc_id)
            if not metadata:
                continue
            
            # Apply metadata filter
            if metadata_filter:
                if not all(metadata['metadata'].get(k) == v for k, v in metadata_filter.items()):
                    continue
            
            # Convert FAISS distance to similarity score
            if self.config.distance_metric == DistanceMetric.COSINE:
                # FAISS L2 distance to cosine similarity approximation
                similarity_score = max(0.0, 1.0 - (float(score) / 2.0))
            else:
                # For other metrics, use inverse relationship
                similarity_score = 1.0 / (1.0 + float(score))
            
            # Apply score threshold
            if score_threshold and similarity_score < score_threshold:
                continue
            
            # Reconstruct document
            doc = VectorStoreDocument(
                id=doc_id,
                content=metadata['content'],
                embedding=query_embedding,  # Use query embedding as placeholder
                metadata=metadata['metadata']
            )
            
            results.append(SearchResult(document=doc, score=similarity_score))
            
            # Stop if we have enough results
            if len(results) >= limit:
                break
        
        # Add rank information
        for i, result in enumerate(results):
            result.rank = i + 1
        
        self.logger.debug(f"Found {len(results)} results in FAISS index")
        return results
    
    async def get_document(
        self, 
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[VectorStoreDocument]:
        """Get a document by ID from FAISS."""
        if not self.connected or document_id not in self.metadata_store:
            return None
        
        metadata = self.metadata_store[document_id]
        idx = self.id_to_index_map[document_id]
        
        try:
            embedding = self.index.reconstruct(idx).tolist()
            return VectorStoreDocument(
                id=document_id,
                content=metadata['content'],
                embedding=embedding,
                metadata=metadata['metadata']
            )
        except Exception as e:
            self.logger.error(f"Failed to reconstruct document {document_id}: {e}")
            return None
    
    async def count_documents(self, collection_name: Optional[str] = None) -> int:
        """Count documents in FAISS index."""
        return self.index.ntotal if self.index else 0
    
    async def list_collections(self) -> List[str]:
        """List collections (FAISS only supports one index per instance)."""
        return [self.config.collection_name] if self.connected else []
    
    async def _initialize_new_index(self) -> None:
        """Initialize a new FAISS index."""
        if not self.config.embedding_dimension:
            raise VectorStoreError("embedding_dimension must be set for FAISS")
        
        # Choose FAISS index type based on distance metric
        dimension = self.config.embedding_dimension
        
        if self.config.distance_metric == DistanceMetric.COSINE:
            # For cosine similarity, normalize vectors and use L2
            self.index = self.faiss.IndexFlatL2(dimension)
        elif self.config.distance_metric == DistanceMetric.EUCLIDEAN:
            self.index = self.faiss.IndexFlatL2(dimension)
        elif self.config.distance_metric == DistanceMetric.DOT_PRODUCT:
            self.index = self.faiss.IndexFlatIP(dimension)  # Inner product
        else:
            # Default to L2 for other metrics
            self.index = self.faiss.IndexFlatL2(dimension)
        
        # Use HNSW for better performance with large datasets
        if self.config.index_type == "hnsw":
            hnsw_index = self.faiss.IndexHNSWFlat(dimension, self.config.m)
            hnsw_index.hnsw.ef_construction = self.config.ef_construction
            self.index = hnsw_index
        
        # Clear mappings
        self.metadata_store.clear()
        self.id_to_index_map.clear()
        self.index_to_id_map.clear()
        
        self.logger.debug(f"Initialized new FAISS index with dimension {dimension}")
    
    async def _save_index(self) -> None:
        """Save FAISS index to disk."""
        if not self.index or not self.config.persist_path:
            return
        
        try:
            persist_path = Path(self.config.persist_path)
            persist_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            self.faiss.write_index(self.index, str(persist_path))
            
            # Save metadata
            metadata_path = persist_path.with_suffix('.metadata.json')
            metadata = {
                'metadata_store': self.metadata_store,
                'id_to_index_map': self.id_to_index_map,
                'index_to_id_map': self.index_to_id_map,
                'config': {
                    'embedding_dimension': self.config.embedding_dimension,
                    'distance_metric': self.config.distance_metric.value
                }
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.debug(f"Saved FAISS index to {persist_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to save FAISS index: {e}")
    
    async def _load_index(self) -> None:
        """Load FAISS index from disk."""
        try:
            persist_path = Path(self.config.persist_path)
            metadata_path = persist_path.with_suffix('.metadata.json')
            
            if not persist_path.exists() or not metadata_path.exists():
                await self._initialize_new_index()
                return
            
            # Load FAISS index
            self.index = self.faiss.read_index(str(persist_path))
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.metadata_store = metadata['metadata_store']
            self.id_to_index_map = {k: int(v) for k, v in metadata['id_to_index_map'].items()}
            self.index_to_id_map = {int(k): v for k, v in metadata['index_to_id_map'].items()}
            
            # Update config with loaded settings
            if 'config' in metadata:
                config_data = metadata['config']
                if 'embedding_dimension' in config_data:
                    self.config.embedding_dimension = config_data['embedding_dimension']
                if 'distance_metric' in config_data:
                    self.config.distance_metric = DistanceMetric(config_data['distance_metric'])
            
            self.logger.debug(f"Loaded FAISS index from {persist_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to load FAISS index: {e}")
            await self._initialize_new_index()