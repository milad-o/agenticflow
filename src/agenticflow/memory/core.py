"""
Memory systems for AgenticFlow agents.

Provides various memory implementations including buffer memory and retrieval-based
memory using embeddings and vector stores for long-term context storage.
"""

import asyncio
import json
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import faiss
import numpy as np
import structlog
from langchain_core.embeddings import Embeddings
from langchain_core.memory import BaseMemory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from ..config.settings import MemoryConfig
from ..llm_providers import EmbeddingProviderFactory, get_llm_manager

logger = structlog.get_logger(__name__)


class MemoryError(Exception):
    """Base exception for memory-related errors."""
    pass


class VectorStoreError(MemoryError):
    """Raised when vector store operations fail."""
    pass


class MemoryDocument(BaseModel):
    """Document stored in memory with metadata."""
    
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: float
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "embedding": self.embedding,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryDocument":
        """Create from dictionary."""
        return cls(**data)


class AsyncMemory(ABC):
    """Abstract base class for async memory implementations."""
    
    def __init__(self, config: MemoryConfig) -> None:
        """Initialize memory with configuration."""
        self.config = config
        self.logger = logger.bind(memory_type=config.type)
    
    @abstractmethod
    async def add_message(self, message: BaseMessage, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to memory and return document ID."""
        pass
    
    @abstractmethod
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[BaseMessage]:
        """Get messages from memory."""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[MemoryDocument]:
        """Search for relevant documents."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory."""
        pass
    
    @abstractmethod
    async def save(self, path: Optional[str] = None) -> None:
        """Save memory to file."""
        pass
    
    @abstractmethod
    async def load(self, path: str) -> None:
        """Load memory from file."""
        pass


class BufferMemory(AsyncMemory):
    """Simple buffer memory that stores messages in order."""
    
    def __init__(self, config: MemoryConfig) -> None:
        """Initialize buffer memory."""
        super().__init__(config)
        self._messages: List[Tuple[BaseMessage, Dict[str, Any], str]] = []
        self._message_counter = 0
    
    async def add_message(self, message: BaseMessage, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to the buffer."""
        if metadata is None:
            metadata = {}
        
        doc_id = f"msg_{self._message_counter}"
        self._message_counter += 1
        
        self._messages.append((message, metadata, doc_id))
        
        # Trim if we exceed limits
        await self._trim_if_needed()
        
        self.logger.debug(f"Added message {doc_id} to buffer")
        return doc_id
    
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[BaseMessage]:
        """Get messages from buffer."""
        messages = []
        
        for message, metadata, _ in self._messages:
            # Filter by metadata if specified
            if filter_metadata:
                if not all(metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue
            
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
        """Search messages by content similarity (simple text matching)."""
        results = []
        query_lower = query.lower()
        
        for message, metadata, doc_id in self._messages:
            content = message.content
            if isinstance(content, str) and query_lower in content.lower():
                doc = MemoryDocument(
                    id=doc_id,
                    content=content,
                    metadata=metadata,
                    timestamp=metadata.get("timestamp", 0.0)
                )
                results.append(doc)
                
                if len(results) >= limit:
                    break
        
        return results
    
    async def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._message_counter = 0
        self.logger.info("Cleared buffer memory")
    
    async def save(self, path: Optional[str] = None) -> None:
        """Save buffer to file."""
        if not path:
            path = "buffer_memory.pkl"
        
        data = {
            "messages": [(msg.dict(), metadata, doc_id) for msg, metadata, doc_id in self._messages],
            "counter": self._message_counter,
        }
        
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        self.logger.info(f"Saved buffer memory to {path}")
    
    async def load(self, path: str) -> None:
        """Load buffer from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self._messages = []
        for msg_data, metadata, doc_id in data["messages"]:
            # Reconstruct message from dict
            if msg_data["type"] == "human":
                message = HumanMessage(content=msg_data["content"])
            elif msg_data["type"] == "ai":
                message = AIMessage(content=msg_data["content"])
            elif msg_data["type"] == "system":
                message = SystemMessage(content=msg_data["content"])
            else:
                continue
            
            self._messages.append((message, metadata, doc_id))
        
        self._message_counter = data["counter"]
        self.logger.info(f"Loaded buffer memory from {path}")
    
    async def _trim_if_needed(self) -> None:
        """Trim buffer if it exceeds configured limits."""
        # Trim by message count
        if self.config.max_messages and len(self._messages) > self.config.max_messages:
            excess = len(self._messages) - self.config.max_messages
            self._messages = self._messages[excess:]
            self.logger.debug(f"Trimmed {excess} messages from buffer")
        
        # Trim by token count (approximate)
        if self.config.max_tokens:
            total_tokens = sum(len(msg.content.split()) for msg, _, _ in self._messages if isinstance(msg.content, str))
            while total_tokens > self.config.max_tokens and self._messages:
                removed_msg, _, _ = self._messages.pop(0)
                if isinstance(removed_msg.content, str):
                    total_tokens -= len(removed_msg.content.split())


class RetrievalMemory(AsyncMemory):
    """Retrieval-based memory using embeddings and vector search."""
    
    def __init__(self, config: MemoryConfig, embeddings: Optional[Embeddings] = None) -> None:
        """Initialize retrieval memory."""
        super().__init__(config)
        self._embeddings = embeddings
        self._documents: Dict[str, MemoryDocument] = {}
        self._vector_store: Optional[faiss.IndexFlatIP] = None
        self._id_to_index: Dict[str, int] = {}
        self._index_to_id: Dict[int, str] = {}
        self._next_index = 0
        self._dimension: Optional[int] = None
        
        # Initialize vector store if path exists
        if config.vector_store_path and Path(config.vector_store_path).exists():
            asyncio.create_task(self._load_vector_store())
    
    async def _ensure_embeddings(self) -> Embeddings:
        """Ensure embeddings are available."""
        if not self._embeddings:
            # Try to get embeddings from LLM manager
            llm_manager = get_llm_manager()
            providers = [name for name, info in llm_manager.list_providers().items() if info["supports_embeddings"]]
            
            if providers:
                provider = llm_manager.get_provider(providers[0])
                self._embeddings = provider.embeddings
            
            if not self._embeddings:
                raise MemoryError("No embedding provider available for retrieval memory")
        
        return self._embeddings
    
    async def _ensure_vector_store(self, dimension: int) -> faiss.IndexFlatIP:
        """Ensure vector store is initialized."""
        if self._vector_store is None or self._dimension != dimension:
            self._vector_store = faiss.IndexFlatIP(dimension)
            self._dimension = dimension
            self.logger.debug(f"Initialized vector store with dimension {dimension}")
        
        return self._vector_store
    
    async def add_message(self, message: BaseMessage, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to retrieval memory."""
        if not isinstance(message.content, str):
            raise MemoryError("Message content must be string for retrieval memory")
        
        embeddings = await self._ensure_embeddings()
        
        # Generate embedding
        try:
            embedding = await embeddings.aembed_query(message.content)
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            raise MemoryError(f"Failed to generate embedding: {e}")
        
        # Create document
        doc_id = f"doc_{len(self._documents)}"
        doc = MemoryDocument(
            id=doc_id,
            content=message.content,
            metadata=metadata or {},
            timestamp=asyncio.get_event_loop().time(),
            embedding=embedding
        )
        
        # Store document
        self._documents[doc_id] = doc
        
        # Add to vector store
        vector_store = await self._ensure_vector_store(len(embedding))
        vector_store.add(np.array([embedding], dtype=np.float32))
        
        # Update index mappings
        self._id_to_index[doc_id] = self._next_index
        self._index_to_id[self._next_index] = doc_id
        self._next_index += 1
        
        self.logger.debug(f"Added document {doc_id} to retrieval memory")
        return doc_id
    
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[BaseMessage]:
        """Get recent messages from memory."""
        # Sort documents by timestamp
        sorted_docs = sorted(self._documents.values(), key=lambda d: d.timestamp, reverse=True)
        
        messages = []
        for doc in sorted_docs:
            # Filter by metadata if specified
            if filter_metadata:
                if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue
            
            # Create message (assume human message for simplicity)
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
        """Search for relevant documents using vector similarity."""
        if not self._documents or not self._vector_store:
            return []
        
        embeddings = await self._ensure_embeddings()
        
        try:
            # Generate query embedding
            query_embedding = await embeddings.aembed_query(query)
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Search vector store
            scores, indices = self._vector_store.search(query_vector, min(limit * 2, len(self._documents)))
            
            results = []
            for score, index in zip(scores[0], indices[0]):
                # Apply similarity threshold
                if score < similarity_threshold:
                    continue
                
                doc_id = self._index_to_id.get(index)
                if doc_id and doc_id in self._documents:
                    doc = self._documents[doc_id]
                    results.append(doc)
                
                if len(results) >= limit:
                    break
            
            self.logger.debug(f"Found {len(results)} relevant documents for query")
            return results
        
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    async def clear(self) -> None:
        """Clear all memory."""
        self._documents.clear()
        self._id_to_index.clear()
        self._index_to_id.clear()
        self._next_index = 0
        
        # Reinitialize vector store
        if self._dimension:
            self._vector_store = faiss.IndexFlatIP(self._dimension)
        
        self.logger.info("Cleared retrieval memory")
    
    async def save(self, path: Optional[str] = None) -> None:
        """Save retrieval memory to files."""
        if not path:
            path = self.config.vector_store_path or "retrieval_memory"
        
        # Save documents as JSON
        docs_path = f"{path}_docs.json"
        with open(docs_path, 'w') as f:
            json.dump({doc_id: doc.to_dict() for doc_id, doc in self._documents.items()}, f)
        
        # Save vector store
        if self._vector_store and self._documents:
            vector_path = f"{path}_vectors.index"
            faiss.write_index(self._vector_store, vector_path)
        
        # Save index mappings
        mappings_path = f"{path}_mappings.json"
        with open(mappings_path, 'w') as f:
            json.dump({
                "id_to_index": self._id_to_index,
                "index_to_id": {str(k): v for k, v in self._index_to_id.items()},
                "next_index": self._next_index,
                "dimension": self._dimension,
            }, f)
        
        self.logger.info(f"Saved retrieval memory to {path}")
    
    async def load(self, path: str) -> None:
        """Load retrieval memory from files."""
        try:
            # Load documents
            docs_path = f"{path}_docs.json"
            if Path(docs_path).exists():
                with open(docs_path, 'r') as f:
                    docs_data = json.load(f)
                    self._documents = {
                        doc_id: MemoryDocument.from_dict(doc_data)
                        for doc_id, doc_data in docs_data.items()
                    }
            
            # Load index mappings
            mappings_path = f"{path}_mappings.json"
            if Path(mappings_path).exists():
                with open(mappings_path, 'r') as f:
                    mappings = json.load(f)
                    self._id_to_index = mappings["id_to_index"]
                    self._index_to_id = {int(k): v for k, v in mappings["index_to_id"].items()}
                    self._next_index = mappings["next_index"]
                    self._dimension = mappings["dimension"]
            
            # Load vector store
            vector_path = f"{path}_vectors.index"
            if Path(vector_path).exists() and self._dimension:
                self._vector_store = faiss.read_index(vector_path)
            
            self.logger.info(f"Loaded retrieval memory from {path}")
        
        except Exception as e:
            self.logger.error(f"Failed to load retrieval memory: {e}")
            raise MemoryError(f"Failed to load retrieval memory: {e}")
    
    async def _load_vector_store(self) -> None:
        """Load vector store from configured path."""
        if self.config.vector_store_path:
            try:
                await self.load(self.config.vector_store_path)
            except Exception as e:
                self.logger.warning(f"Failed to load vector store from {self.config.vector_store_path}: {e}")


class HybridMemory(AsyncMemory):
    """Hybrid memory combining buffer and retrieval memory."""
    
    def __init__(self, config: MemoryConfig, embeddings: Optional[Embeddings] = None) -> None:
        """Initialize hybrid memory."""
        super().__init__(config)
        
        # Create buffer memory for recent messages
        buffer_config = MemoryConfig(
            type="buffer",
            max_messages=config.max_messages or 50,
            max_tokens=config.max_tokens
        )
        self._buffer_memory = BufferMemory(buffer_config)
        
        # Create retrieval memory for long-term storage
        self._retrieval_memory = RetrievalMemory(config, embeddings)
    
    async def add_message(self, message: BaseMessage, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add message to both buffer and retrieval memory."""
        # Add to buffer for quick access
        buffer_id = await self._buffer_memory.add_message(message, metadata)
        
        # Add to retrieval memory for long-term storage
        try:
            retrieval_id = await self._retrieval_memory.add_message(message, metadata)
            return retrieval_id
        except Exception as e:
            self.logger.warning(f"Failed to add to retrieval memory: {e}")
            return buffer_id
    
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[BaseMessage]:
        """Get messages from buffer memory (most recent)."""
        return await self._buffer_memory.get_messages(limit, filter_metadata)
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[MemoryDocument]:
        """Search using retrieval memory."""
        return await self._retrieval_memory.search(query, limit, similarity_threshold)
    
    async def clear(self) -> None:
        """Clear both buffer and retrieval memory."""
        await self._buffer_memory.clear()
        await self._retrieval_memory.clear()
    
    async def save(self, path: Optional[str] = None) -> None:
        """Save both memory types."""
        if not path:
            path = "hybrid_memory"
        
        await self._buffer_memory.save(f"{path}_buffer.pkl")
        await self._retrieval_memory.save(path)
    
    async def load(self, path: str) -> None:
        """Load both memory types."""
        await self._buffer_memory.load(f"{path}_buffer.pkl")
        await self._retrieval_memory.load(path)


class MemoryFactory:
    """Factory for creating memory instances."""
    
    @classmethod
    async def create_memory(
        self, 
        config: MemoryConfig, 
        embeddings: Optional[Embeddings] = None
    ) -> AsyncMemory:
        """Create memory instance based on configuration."""
        if config.type == "buffer":
            return BufferMemory(config)
        elif config.type == "retrieval":
            return RetrievalMemory(config, embeddings)
        elif config.type == "hybrid":
            return HybridMemory(config, embeddings)
        else:
            raise MemoryError(f"Unknown memory type: {config.type}")