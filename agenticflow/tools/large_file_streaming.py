"""Advanced tools for processing huge files in slices with streaming and embedding.

These tools handle scenarios where a huge file needs to be read and processed:
- Stream-based file reading with configurable chunk sizes
- Progressive text embedding with batch processing  
- Retrieval-augmented generation (RAG) over large documents
- Flexible vector store support (Chroma, FAISS, Pinecone, etc.)
- Memory management and garbage collection
- Progress tracking and resumable processing
"""
from __future__ import annotations

import os
import gc
import json
import hashlib
import tempfile
from typing import Any, Dict, List, Optional, Iterator, Union, Type
from dataclasses import dataclass
from pathlib import Path
from langchain_core.tools import BaseTool
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import time


@dataclass
class StreamChunk:
    """A chunk of data from streaming file read."""
    content: str
    chunk_id: int
    start_byte: int
    end_byte: int
    encoding: str


@dataclass
class EmbeddingBatch:
    """A batch of documents for embedding processing."""
    documents: List[Document]
    batch_id: str
    total_chars: int
    chunk_range: tuple  # (start_chunk, end_chunk)


@dataclass
class StreamingProgress:
    """Progress tracking for large file streaming operations."""
    total_bytes: int
    processed_bytes: int
    total_chunks: int
    processed_chunks: int
    current_batch: str
    errors: List[str]
    start_time: float
    vector_store_type: Optional[str]
    index_id: Optional[str]


# Shared cache for streaming operations
_STREAMING_PROGRESS_CACHE: Dict[str, StreamingProgress] = {}
_STREAMING_CHUNK_CACHE: Dict[str, List[StreamChunk]] = {}
_VECTOR_STORE_REGISTRY: Dict[str, VectorStore] = {}


class StreamingFileReaderTool(BaseTool):
    """Stream-based file reading with configurable chunk sizes and progress tracking."""
    
    name: str = "streaming_file_reader"
    description: str = (
        "Read large files in streaming chunks to avoid memory issues. "
        "Args: file_path (str), chunk_size_kb (int, default=64), max_chunks (int, default=1000), "
        "encoding (str, default='utf-8'), resume_from (int, optional). "
        "Returns: {'stream_id': str, 'chunks': [...], 'progress': {...}}"
    )

    def _run(
        self,
        file_path: str,
        chunk_size_kb: int = 64,
        max_chunks: int = 1000,
        encoding: str = "utf-8",
        resume_from: Optional[int] = None
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Stream read a large file in configurable chunks."""
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists() or not file_path_obj.is_file():
            return {"error": f"File not found: {file_path}"}
        
        # Apply workspace guard if present
        if hasattr(self, '_path_guard') and self._path_guard:
            try:
                self._path_guard.resolve(file_path, "read")
            except Exception as e:
                return {"error": f"Workspace policy violation: {e}"}
        
        try:
            file_size = file_path_obj.stat().st_size
            chunk_size_bytes = chunk_size_kb * 1024
            
            # Generate stream ID
            stream_id = hashlib.md5(f"{file_path}_{time.time()}".encode()).hexdigest()[:16]
            
            # Initialize or resume progress
            if stream_id in _STREAMING_PROGRESS_CACHE:
                progress = _STREAMING_PROGRESS_CACHE[stream_id]
            else:
                progress = StreamingProgress(
                    total_bytes=file_size,
                    processed_bytes=resume_from or 0,
                    total_chunks=0,
                    processed_chunks=0,
                    current_batch="",
                    errors=[],
                    start_time=time.time(),
                    vector_store_type=None,
                    index_id=None
                )
                _STREAMING_PROGRESS_CACHE[stream_id] = progress
            
            chunks = []
            chunk_id = resume_from or 0
            bytes_read = resume_from or 0
            
            with open(file_path_obj, 'r', encoding=encoding, errors='ignore') as f:
                # Seek to resume position if resuming
                if resume_from:
                    f.seek(resume_from)
                
                while len(chunks) < max_chunks and bytes_read < file_size:
                    try:
                        content = f.read(chunk_size_bytes)
                        if not content:
                            break
                        
                        chunk = StreamChunk(
                            content=content,
                            chunk_id=chunk_id,
                            start_byte=bytes_read,
                            end_byte=bytes_read + len(content.encode(encoding)),
                            encoding=encoding
                        )
                        chunks.append(chunk)
                        
                        bytes_read += len(content.encode(encoding))
                        chunk_id += 1
                        
                        # Memory management - force garbage collection every 50 chunks
                        if chunk_id % 50 == 0:
                            gc.collect()
                        
                    except Exception as e:
                        progress.errors.append(f"Chunk {chunk_id} error: {e}")
                        break
            
            # Update progress
            progress.processed_bytes = bytes_read
            progress.total_chunks = chunk_id
            progress.processed_chunks = len(chunks)
            
            # Cache chunks
            _STREAMING_CHUNK_CACHE[stream_id] = chunks
            
            return {
                "stream_id": stream_id,
                "chunks": [
                    {
                        "chunk_id": c.chunk_id,
                        "size_bytes": len(c.content.encode(c.encoding)),
                        "start_byte": c.start_byte,
                        "end_byte": c.end_byte,
                        "preview": c.content[:100] + "..." if len(c.content) > 100 else c.content
                    }
                    for c in chunks[:10]  # Return first 10 chunk previews
                ],
                "progress": {
                    "total_size_mb": progress.total_bytes / (1024*1024),
                    "processed_mb": progress.processed_bytes / (1024*1024),
                    "progress_pct": (progress.processed_bytes / progress.total_bytes) * 100,
                    "total_chunks": progress.processed_chunks,
                    "errors": len(progress.errors),
                    "elapsed_time": time.time() - progress.start_time,
                    "is_complete": bytes_read >= file_size
                }
            }
            
        except Exception as e:
            return {"error": f"Streaming failed: {e}"}


class ProgressiveEmbeddingTool(BaseTool):
    """Progressive text embedding with batch processing and flexible vector store support."""
    
    name: str = "progressive_embedding"
    description: str = (
        "Create embeddings from streaming chunks with flexible vector store support. "
        "Args: stream_id (str), vector_store_type (str: 'chroma'|'faiss'|'pinecone'), "
        "batch_size (int, default=10), chunk_size (int, default=1000), "
        "collection_name (str, optional). "
        "Returns: {'index_id': str, 'embedded_chunks': int, 'vector_store': str}"
    )

    def _run(
        self,
        stream_id: str,
        vector_store_type: str = "chroma",
        batch_size: int = 10,
        chunk_size: int = 1000,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Create progressive embeddings with flexible vector store support."""
        
        try:
            # Get streaming chunks
            if stream_id not in _STREAMING_CHUNK_CACHE:
                return {"error": f"Stream {stream_id} not found. Run streaming_file_reader first."}
            
            chunks = _STREAMING_CHUNK_CACHE[stream_id]
            if not chunks:
                return {"error": "No chunks available for embedding"}
            
            # Initialize text splitter for semantic chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=200
            )
            
            # Process chunks into documents
            all_documents = []
            for chunk in chunks:
                # Split each chunk into semantic sub-chunks
                texts = text_splitter.split_text(chunk.content)
                for i, text in enumerate(texts):
                    doc = Document(
                        page_content=text,
                        metadata={
                            "stream_id": stream_id,
                            "original_chunk_id": chunk.chunk_id,
                            "sub_chunk_id": i,
                            "start_byte": chunk.start_byte,
                            "encoding": chunk.encoding
                        }
                    )
                    all_documents.append(doc)
            
            # Create vector store based on type
            vector_store = self._create_vector_store(
                vector_store_type, 
                collection_name or f"{stream_id}_{vector_store_type}"
            )
            
            # Batch embedding to manage memory
            embedded_count = 0
            batch_count = 0
            
            for i in range(0, len(all_documents), batch_size):
                batch_docs = all_documents[i:i + batch_size]
                
                try:
                    # Add documents to vector store
                    if hasattr(vector_store, 'add_documents'):
                        vector_store.add_documents(batch_docs)
                    else:
                        # Fallback for stores that only support add_texts
                        texts = [doc.page_content for doc in batch_docs]
                        metadatas = [doc.metadata for doc in batch_docs]
                        vector_store.add_texts(texts, metadatas)
                    
                    embedded_count += len(batch_docs)
                    batch_count += 1
                    
                    # Memory management
                    if batch_count % 10 == 0:
                        gc.collect()
                        
                except Exception as e:
                    progress = _STREAMING_PROGRESS_CACHE.get(stream_id)
                    if progress:
                        progress.errors.append(f"Embedding batch {batch_count} error: {e}")
                    continue
            
            # Register vector store for future use
            index_id = f"{stream_id}_{vector_store_type}_{int(time.time())}"
            _VECTOR_STORE_REGISTRY[index_id] = vector_store
            
            # Update progress
            progress = _STREAMING_PROGRESS_CACHE.get(stream_id)
            if progress:
                progress.vector_store_type = vector_store_type
                progress.index_id = index_id
            
            return {
                "index_id": index_id,
                "embedded_chunks": embedded_count,
                "vector_store": vector_store_type,
                "batch_count": batch_count,
                "collection_name": collection_name or f"{stream_id}_{vector_store_type}"
            }
            
        except Exception as e:
            return {"error": f"Progressive embedding failed: {e}"}
    
    def _create_vector_store(self, store_type: str, collection_name: str) -> VectorStore:
        """Create vector store based on type with fallbacks."""
        
        # Get embeddings (try multiple providers)
        embeddings = self._get_embeddings()
        
        if store_type.lower() == "chroma":
            try:
                from langchain_community.vectorstores import Chroma
                return Chroma(
                    collection_name=collection_name,
                    embedding_function=embeddings
                )
            except ImportError:
                # Fallback to existing ephemeral chroma
                from agenticflow.tools.ephemeral_chroma import BuildEphemeralChromaTool
                builder = BuildEphemeralChromaTool()
                return builder  # Return builder as proxy
        
        elif store_type.lower() == "faiss":
            try:
                from langchain_community.vectorstores import FAISS
                # Initialize empty FAISS index
                return FAISS.from_texts(["init"], embeddings)
            except ImportError:
                raise ValueError(f"FAISS not available. Install with: pip install faiss-cpu")
        
        elif store_type.lower() == "pinecone":
            try:
                from langchain_pinecone import PineconeVectorStore
                # Note: Requires pinecone API key and index setup
                return PineconeVectorStore(
                    index_name=collection_name,
                    embedding=embeddings
                )
            except ImportError:
                raise ValueError(f"Pinecone not available. Install with: pip install pinecone-client")
        
        else:
            # Default to Chroma as fallback
            try:
                from langchain_community.vectorstores import Chroma
                return Chroma(
                    collection_name=collection_name,
                    embedding_function=embeddings
                )
            except ImportError:
                raise ValueError(f"No vector store available. Install Chroma: pip install chromadb")
    
    def _get_embeddings(self) -> Embeddings:
        """Get embeddings with multiple fallbacks."""
        try:
            # Try Ollama first (local)
            from agenticflow.core.models import get_ollama_embeddings
            return get_ollama_embeddings()
        except Exception:
            try:
                # Try OpenAI as fallback
                from langchain_openai import OpenAIEmbeddings
                return OpenAIEmbeddings()
            except Exception:
                try:
                    # Try HuggingFace as final fallback
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    return HuggingFaceEmbeddings()
                except Exception:
                    raise ValueError("No embedding provider available. Install Ollama, OpenAI, or HuggingFace.")


class RAGQueryTool(BaseTool):
    """Retrieval-augmented generation over large documents using any vector store."""
    
    name: str = "rag_query"
    description: str = (
        "Query large documents using RAG with flexible vector store support. "
        "Args: index_id (str), query (str), k (int, default=5), "
        "include_metadata (bool, default=True). "
        "Returns: {'answer': str, 'sources': [...], 'similarity_scores': [...]}"
    )

    def _run(
        self,
        index_id: str,
        query: str,
        k: int = 5,
        include_metadata: bool = True
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Query the vector index with RAG."""
        
        try:
            # Get vector store
            if index_id not in _VECTOR_STORE_REGISTRY:
                return {"error": f"Index {index_id} not found. Run progressive_embedding first."}
            
            vector_store = _VECTOR_STORE_REGISTRY[index_id]
            
            # Perform similarity search
            if hasattr(vector_store, 'similarity_search_with_score'):
                # Get results with similarity scores
                results = vector_store.similarity_search_with_score(query, k=k)
                documents = [doc for doc, score in results]
                scores = [float(score) for doc, score in results]
            else:
                # Fallback to regular similarity search
                documents = vector_store.similarity_search(query, k=k)
                scores = [1.0] * len(documents)  # Dummy scores
            
            if not documents:
                return {"error": "No relevant documents found"}
            
            # Build context from retrieved documents
            context_parts = []
            sources = []
            
            for i, doc in enumerate(documents):
                context_parts.append(doc.page_content)
                
                if include_metadata:
                    source_info = {
                        "chunk_id": doc.metadata.get("original_chunk_id", i),
                        "sub_chunk_id": doc.metadata.get("sub_chunk_id", 0),
                        "start_byte": doc.metadata.get("start_byte", 0),
                        "similarity_score": scores[i],
                        "preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                    }
                else:
                    source_info = {"chunk_id": i, "similarity_score": scores[i]}
                
                sources.append(source_info)
            
            # Simple context-based answer (in real implementation, use LLM)
            context = "\n\n".join(context_parts)
            answer = f"Based on the document content, here are the most relevant sections for '{query}':\n\n{context[:1000]}..."
            
            return {
                "answer": answer,
                "sources": sources,
                "similarity_scores": scores,
                "context_length": len(context),
                "retrieved_chunks": len(documents)
            }
            
        except Exception as e:
            return {"error": f"RAG query failed: {e}"}


class StreamingMemoryManagerTool(BaseTool):
    """Memory management and cleanup for streaming operations."""
    
    name: str = "streaming_memory_manager"
    description: str = (
        "Manage memory usage and cleanup streaming operations. "
        "Args: action (str: 'status'|'cleanup'|'gc'), stream_id (str, optional). "
        "Returns: {'memory_usage': {...}, 'cleaned_items': int}"
    )

    def _run(
        self,
        action: str = "status",
        stream_id: Optional[str] = None
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Manage streaming operation memory."""
        
        try:
            if action == "status":
                return {
                    "memory_usage": {
                        "active_streams": len(_STREAMING_PROGRESS_CACHE),
                        "cached_chunks": sum(len(chunks) for chunks in _STREAMING_CHUNK_CACHE.values()),
                        "vector_stores": len(_VECTOR_STORE_REGISTRY),
                        "total_cache_entries": len(_STREAMING_PROGRESS_CACHE) + len(_STREAMING_CHUNK_CACHE) + len(_VECTOR_STORE_REGISTRY)
                    }
                }
            
            elif action == "cleanup":
                cleaned = 0
                
                if stream_id:
                    # Clean specific stream
                    if stream_id in _STREAMING_PROGRESS_CACHE:
                        del _STREAMING_PROGRESS_CACHE[stream_id]
                        cleaned += 1
                    if stream_id in _STREAMING_CHUNK_CACHE:
                        del _STREAMING_CHUNK_CACHE[stream_id]
                        cleaned += 1
                    
                    # Clean related vector stores
                    to_remove = [k for k in _VECTOR_STORE_REGISTRY.keys() if k.startswith(stream_id)]
                    for k in to_remove:
                        del _VECTOR_STORE_REGISTRY[k]
                        cleaned += 1
                else:
                    # Clean all
                    cleaned += len(_STREAMING_PROGRESS_CACHE)
                    cleaned += len(_STREAMING_CHUNK_CACHE)
                    cleaned += len(_VECTOR_STORE_REGISTRY)
                    
                    _STREAMING_PROGRESS_CACHE.clear()
                    _STREAMING_CHUNK_CACHE.clear()
                    _VECTOR_STORE_REGISTRY.clear()
                
                return {"cleaned_items": cleaned}
            
            elif action == "gc":
                # Force garbage collection
                import gc
                collected = gc.collect()
                return {"collected_objects": collected}
            
            else:
                return {"error": f"Unknown action: {action}"}
        
        except Exception as e:
            return {"error": f"Memory management failed: {e}"}