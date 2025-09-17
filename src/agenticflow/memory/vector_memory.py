"""
Vector-enabled memory backend that combines traditional memory with vector search.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

import structlog
from langchain_core.embeddings import Embeddings
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from ..config.settings import MemoryConfig
from ..vectorstores import (
    AsyncVectorStore,
    VectorStoreConfig,
    VectorStoreDocument,
    VectorStoreFactory,
    VectorStoreType,
    get_vector_store
)
from ..text.splitters import (
    SplitterManager,
    SplitterConfig,
    TextFragment,
    get_splitter_manager
)
from .core import AsyncMemory, MemoryDocument, MemoryError

logger = structlog.get_logger(__name__)


class VectorMemoryConfig:
    """Configuration for vector-enabled memory."""
    
    def __init__(
        self,
        vector_store_config: VectorStoreConfig,
        splitter_config: Optional[SplitterConfig] = None,
        enable_splitting: bool = True,
        enable_semantic_search: bool = True,
        enable_hybrid_search: bool = True,
        chunk_overlap_threshold: float = 0.8,
        max_chunks_per_message: int = 10,
        similarity_threshold: float = 0.7,
        max_retrievals: int = 5
    ):
        self.vector_store_config = vector_store_config
        self.splitter_config = splitter_config or SplitterConfig()
        self.enable_splitting = enable_splitting
        self.enable_semantic_search = enable_semantic_search
        self.enable_hybrid_search = enable_hybrid_search
        self.chunk_overlap_threshold = chunk_overlap_threshold
        self.max_chunks_per_message = max_chunks_per_message
        self.similarity_threshold = similarity_threshold
        self.max_retrievals = max_retrievals


class VectorMemory(AsyncMemory):
    """Vector-enabled memory backend with chunking and semantic search."""
    
    def __init__(
        self,
        config: MemoryConfig,
        vector_config: VectorMemoryConfig,
        embeddings: Optional[Embeddings] = None
    ):
        super().__init__(config)
        self.vector_config = vector_config
        self.embeddings = embeddings
        
        # Components
        self.vector_store: Optional[AsyncVectorStore] = None
        self.splitter_manager: Optional[SplitterManager] = None
        
        # Internal storage for non-chunked access
        self.messages: List[MemoryDocument] = []
        self.message_counter = 0
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize vector store and splitting components."""
        try:
            # Initialize splitter manager if enabled
            if self.vector_config.enable_splitting and self.embeddings:
                self.splitter_manager = get_splitter_manager()
            
            self.logger.info("Vector memory components initialized")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize vector memory components: {e}")
            raise MemoryError(f"Failed to initialize vector memory: {e}")
    
    async def _ensure_vector_store(self) -> AsyncVectorStore:
        """Ensure vector store is connected."""
        if not self.vector_store:
            self.vector_store = VectorStoreFactory.create_vector_store(
                self.vector_config.vector_store_config
            )
            await self.vector_store.connect()
            
            # Create collection if needed
            await self.vector_store.create_collection(
                dimension=self.vector_config.vector_store_config.embedding_dimension
            )
        
        return self.vector_store
    
    async def add_message(
        self, 
        message: BaseMessage, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to vector memory with chunking and embedding."""
        if not isinstance(message.content, str):
            raise MemoryError("Message content must be string")
        
        # Create document ID
        doc_id = f"msg_{self.message_counter}_{int(time.time())}"
        self.message_counter += 1
        
        # Create memory document
        doc = MemoryDocument(
            id=doc_id,
            content=message.content,
            metadata=metadata or {},
            timestamp=time.time()
        )
        
        # Add to traditional storage
        self.messages.append(doc)
        
        # Trim if exceeding limits
        await self._trim_if_needed()
        
        # Process for vector storage
        if self.embeddings:
            await self._process_message_for_vector_storage(message, doc_id, metadata)
        
        self.logger.debug(f"Added message {doc_id} to vector memory")
        return doc_id
    
    async def _process_message_for_vector_storage(
        self,
        message: BaseMessage,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Process message for vector storage with text splitting."""
        vector_store = await self._ensure_vector_store()
        content = message.content
        
        # Prepare base metadata
        base_metadata = {
            "message_id": doc_id,
            "message_type": type(message).__name__,
            "timestamp": time.time(),
            **(metadata or {})
        }
        
        vector_documents = []
        
        if self.vector_config.enable_splitting and self.splitter_manager:
            # Split the message if it's long enough
            min_chunk_size = self.vector_config.splitter_config.min_chunk_size
            
            if len(content) > min_chunk_size:
                try:
                    # Split text into fragments
                    fragments = await self.splitter_manager.split_text(
                        content,
                        source_id=doc_id,
                        metadata=base_metadata
                    )
                    
                    # Convert fragments to vector documents
                    for fragment in fragments[:self.vector_config.max_chunks_per_message]:
                        # Generate embedding for fragment if needed
                        if self.embeddings:
                            fragment_embedding = await self.embeddings.aembed_query(fragment.content)
                        else:
                            fragment_embedding = []
                        
                        fragment_metadata = {
                            **base_metadata,
                            "fragment_id": fragment.fragment_id,
                            "fragment_index": fragment.fragment_index,
                            "total_fragments": fragment.total_fragments,
                            "is_fragment": True,
                            "boundary_type": fragment.boundary_type.value,
                            "content_type": fragment.content_type.value
                        }
                        
                        vector_doc = VectorStoreDocument(
                            id=fragment.fragment_id,
                            content=fragment.content,
                            embedding=fragment_embedding,
                            metadata=fragment_metadata
                        )
                        vector_documents.append(vector_doc)
                    
                    self.logger.debug(f"Created {len(vector_documents)} fragment embeddings for message {doc_id}")
                
                except Exception as e:
                    self.logger.warning(f"Text splitting failed for message {doc_id}: {e}")
        
        # Always add the full message as well (if we have embeddings)
        if self.embeddings:
            try:
                full_message_embedding = await self.embeddings.aembed_query(content)
                
                full_doc_metadata = {
                    **base_metadata,
                    "is_full_message": True,
                    "is_chunk": False
                }
                
                full_vector_doc = VectorStoreDocument(
                    id=f"{doc_id}_full",
                    content=content,
                    embedding=full_message_embedding,
                    metadata=full_doc_metadata
                )
                vector_documents.append(full_vector_doc)
                
                self.logger.debug(f"Created full message embedding for {doc_id}")
            
            except Exception as e:
                self.logger.warning(f"Failed to create full message embedding: {e}")
        
        # Store all vector documents
        if vector_documents:
            try:
                await vector_store.add_documents(vector_documents)
                self.logger.debug(f"Stored {len(vector_documents)} vector documents for message {doc_id}")
            
            except Exception as e:
                self.logger.error(f"Failed to store vector documents: {e}")
    
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[BaseMessage]:
        """Get messages from traditional storage."""
        messages = []
        
        for doc in self.messages:
            # Filter by metadata if specified
            if filter_metadata:
                if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue
            
            # Convert to BaseMessage
            if "message_type" in doc.metadata:
                msg_type = doc.metadata["message_type"]
                if msg_type == "HumanMessage":
                    message = HumanMessage(content=doc.content)
                elif msg_type == "AIMessage":
                    message = AIMessage(content=doc.content)
                else:
                    message = SystemMessage(content=doc.content)
            else:
                message = HumanMessage(content=doc.content)
            
            messages.append(message)
            
            # Apply limit
            if limit and len(messages) >= limit:
                break
        
        return messages
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[MemoryDocument]:
        """Perform semantic search using vector store."""
        if not self.embeddings:
            # Fallback to simple text search
            return await self._simple_text_search(query, limit)
        
        try:
            vector_store = await self._ensure_vector_store()
            
            # Generate query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Search in vector store
            search_results = await vector_store.search(
                query_embedding=query_embedding,
                limit=limit * 2,  # Get more results to filter
                score_threshold=similarity_threshold
            )
            
            # Convert results and deduplicate by message
            seen_messages = set()
            memory_docs = []
            
            for result in search_results:
                # Extract original message ID
                message_id = result.document.metadata.get("message_id")
                if not message_id or message_id in seen_messages:
                    continue
                
                seen_messages.add(message_id)
                
                # Find original message content
                original_content = result.document.content
                if result.document.metadata.get("is_fragment", False):
                    # Try to find full message content
                    for msg_doc in self.messages:
                        if msg_doc.id == message_id:
                            original_content = msg_doc.content
                            break
                
                # Create memory document
                memory_doc = MemoryDocument(
                    id=message_id,
                    content=original_content,
                    metadata={
                        **result.document.metadata,
                        "similarity_score": result.score,
                        "search_rank": result.rank
                    },
                    timestamp=result.document.metadata.get("timestamp", time.time())
                )
                
                memory_docs.append(memory_doc)
                
                if len(memory_docs) >= limit:
                    break
            
            self.logger.debug(f"Vector search returned {len(memory_docs)} results for query: {query[:50]}...")
            return memory_docs
        
        except Exception as e:
            self.logger.error(f"Vector search failed: {e}")
            # Fallback to simple text search
            return await self._simple_text_search(query, limit)
    
    async def _simple_text_search(self, query: str, limit: int) -> List[MemoryDocument]:
        """Fallback simple text search."""
        results = []
        query_lower = query.lower()
        
        for doc in self.messages:
            if query_lower in doc.content.lower():
                results.append(doc)
                if len(results) >= limit:
                    break
        
        return results
    
    async def clear(self) -> None:
        """Clear all memory."""
        self.messages.clear()
        self.message_counter = 0
        
        # Clear vector store
        if self.vector_store:
            try:
                await self.vector_store.delete_collection()
                await self.vector_store.create_collection(
                    dimension=self.vector_config.vector_store_config.embedding_dimension
                )
            except Exception as e:
                self.logger.error(f"Failed to clear vector store: {e}")
        
        self.logger.info("Cleared vector memory")
    
    async def save(self, path: Optional[str] = None) -> None:
        """Save memory to file."""
        if not path:
            path = self.config.vector_store_path or "vector_memory.pkl"
        
        # Save traditional messages
        import pickle
        with open(f"{path}.messages", "wb") as f:
            pickle.dump({
                "messages": [msg.to_dict() for msg in self.messages],
                "counter": self.message_counter
            }, f)
        
        # Vector store persistence is handled by the vector store itself
        
        self.logger.info(f"Saved vector memory to {path}")
    
    async def load(self, path: str) -> None:
        """Load memory from file."""
        try:
            # Load traditional messages
            import pickle
            with open(f"{path}.messages", "rb") as f:
                data = pickle.load(f)
            
            self.messages = [MemoryDocument.from_dict(msg) for msg in data["messages"]]
            self.message_counter = data["counter"]
            
            # Vector store loading is handled by the vector store itself
            
            self.logger.info(f"Loaded vector memory from {path}")
        
        except Exception as e:
            self.logger.error(f"Failed to load vector memory: {e}")
            raise MemoryError(f"Failed to load vector memory: {e}")
    
    async def _trim_if_needed(self) -> None:
        """Trim messages if exceeding limits."""
        if self.config.max_messages and len(self.messages) > self.config.max_messages:
            # Remove oldest messages
            excess = len(self.messages) - self.config.max_messages
            removed_messages = self.messages[:excess]
            self.messages = self.messages[excess:]
            
            # Remove from vector store
            if self.vector_store:
                try:
                    # Collect all vector document IDs to remove
                    ids_to_remove = []
                    for msg in removed_messages:
                        ids_to_remove.append(f"{msg.id}_full")  # Full message
                        # Add chunk IDs (we need to query for these)
                        # This is simplified - in practice you'd track chunk IDs
                    
                    if ids_to_remove:
                        await self.vector_store.delete_documents(ids_to_remove)
                
                except Exception as e:
                    self.logger.error(f"Failed to remove old vector documents: {e}")
            
            self.logger.debug(f"Trimmed {excess} old messages from vector memory")
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        stats = {
            "total_messages": len(self.messages),
            "vector_store_connected": self.vector_store is not None,
            "embeddings_enabled": self.embeddings is not None,
            "chunking_enabled": self.vector_config.enable_chunking,
            "vector_store_type": self.vector_config.vector_store_config.store_type.value
        }
        
        if self.vector_store:
            try:
                stats["vector_documents"] = await self.vector_store.count_documents()
                stats["vector_collections"] = await self.vector_store.list_collections()
            except Exception as e:
                self.logger.error(f"Failed to get vector store stats: {e}")
                stats["vector_documents"] = 0
                stats["vector_collections"] = []
        
        return stats
    
    async def disconnect(self) -> None:
        """Disconnect from vector store."""
        if self.vector_store:
            try:
                await self.vector_store.disconnect()
                self.vector_store = None
                self.logger.info("Disconnected from vector store")
            except Exception as e:
                self.logger.error(f"Failed to disconnect from vector store: {e}")