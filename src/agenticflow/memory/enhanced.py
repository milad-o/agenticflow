"""
Enhanced memory systems with advanced chunking, compression, and long-term management.

Provides intelligent memory management with automatic chunking, embedding-based
retrieval, memory compression, lifecycle management, and advanced analytics.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path
import math

import structlog
from langchain_core.embeddings import Embeddings
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from .core import AsyncMemory, MemoryDocument, MemoryError
from ..config.settings import MemoryConfig
from ..text.chunking import (
    ChunkingManager, ChunkingConfig, ChunkingStrategy, 
    TextChunk, get_chunking_manager
)
from ..llm_providers import get_llm_manager

logger = structlog.get_logger(__name__)


@dataclass
class MemoryStats:
    """Memory usage and performance statistics."""
    total_messages: int = 0
    total_chunks: int = 0
    total_characters: int = 0
    total_tokens: int = 0
    memory_size_mb: float = 0.0
    
    # Time-based stats
    oldest_message: Optional[datetime] = None
    newest_message: Optional[datetime] = None
    average_message_length: float = 0.0
    
    # Compression stats
    compression_ratio: float = 0.0
    compressed_messages: int = 0
    
    # Search stats
    search_count: int = 0
    average_search_time: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Health metrics
    fragmentation_ratio: float = 0.0
    embedding_coverage: float = 0.0


@dataclass
class MemoryConfiguration:
    """Enhanced memory configuration."""
    # Basic settings
    max_messages: Optional[int] = None
    max_total_tokens: Optional[int] = None
    max_memory_mb: Optional[float] = None
    
    # Chunking settings
    enable_chunking: bool = True
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    
    # Compression settings  
    enable_compression: bool = True
    compression_threshold: int = 50  # Messages before compression
    compression_ratio_target: float = 0.3  # Target 30% of original size
    preserve_recent_messages: int = 10  # Never compress last N messages
    
    # Embedding settings
    generate_embeddings: bool = True
    embedding_batch_size: int = 10
    similarity_threshold: float = 0.8
    
    # Lifecycle management
    enable_archiving: bool = True
    archive_after_days: int = 30
    cleanup_interval: int = 3600  # seconds
    max_archive_size_mb: float = 100.0
    
    # Performance settings
    enable_caching: bool = True
    cache_size: int = 100
    index_rebuild_threshold: int = 1000
    
    # Analytics
    enable_analytics: bool = True
    analytics_retention_days: int = 90


class MemoryCompressionError(MemoryError):
    """Raised when memory compression fails."""
    pass


class MemoryLifecycleError(MemoryError):
    """Raised when memory lifecycle operations fail."""
    pass


class MemoryCompressor:
    """Handles memory compression using LLM summarization."""
    
    def __init__(self, llm_manager=None):
        """Initialize memory compressor."""
        self.llm_manager = llm_manager or get_llm_manager()
        self.logger = logger.bind(component="memory_compressor")
    
    async def compress_messages(
        self,
        messages: List[BaseMessage],
        target_ratio: float = 0.3,
        preserve_context: bool = True
    ) -> List[BaseMessage]:
        """Compress messages using LLM summarization."""
        if not messages:
            return messages
        
        try:
            # Group messages by type and context
            message_groups = self._group_messages(messages)
            compressed_messages = []
            
            for group in message_groups:
                if len(group) <= 2:  # Don't compress very small groups
                    compressed_messages.extend(group)
                    continue
                
                # Create summarization prompt
                summary_prompt = self._create_summary_prompt(group, target_ratio)
                
                # Get LLM summarization
                provider = self.llm_manager.get_provider()
                summary_response = await provider.agenerate([summary_prompt])
                
                # Create compressed message
                compressed_msg = SystemMessage(
                    content=f"[COMPRESSED SUMMARY] {summary_response}"
                )
                compressed_messages.append(compressed_msg)
            
            self.logger.info(f"Compressed {len(messages)} messages to {len(compressed_messages)}")
            return compressed_messages
        
        except Exception as e:
            self.logger.error(f"Memory compression failed: {e}")
            raise MemoryCompressionError(f"Failed to compress messages: {e}")
    
    def _group_messages(self, messages: List[BaseMessage]) -> List[List[BaseMessage]]:
        """Group related messages for compression."""
        groups = []
        current_group = []
        
        for message in messages:
            # Simple grouping by message type and time proximity
            if (not current_group or 
                type(message) == type(current_group[-1]) or 
                len(current_group) >= 5):
                
                if current_group:
                    groups.append(current_group)
                current_group = [message]
            else:
                current_group.append(message)
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _create_summary_prompt(
        self,
        messages: List[BaseMessage], 
        target_ratio: float
    ) -> SystemMessage:
        """Create prompt for message summarization."""
        content = "Please summarize the following conversation messages, "
        content += f"preserving key information while reducing length by approximately {(1-target_ratio)*100:.0f}%:\n\n"
        
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__.replace("Message", "")
            content += f"{msg_type}: {msg.content}\n"
        
        content += "\nProvide a concise summary that captures the main points and context."
        
        return SystemMessage(content=content)


class MemoryLifecycleManager:
    """Manages memory lifecycle including archiving and cleanup."""
    
    def __init__(self, config: MemoryConfiguration):
        """Initialize lifecycle manager."""
        self.config = config
        self.logger = logger.bind(component="memory_lifecycle")
    
    async def archive_old_messages(
        self,
        messages: List[MemoryDocument],
        archive_path: str
    ) -> Tuple[List[MemoryDocument], List[MemoryDocument]]:
        """Archive old messages and return active/archived lists."""
        if not self.config.enable_archiving:
            return messages, []
        
        cutoff_time = time.time() - (self.config.archive_after_days * 24 * 3600)
        active_messages = []
        archived_messages = []
        
        for msg in messages:
            if msg.timestamp < cutoff_time:
                archived_messages.append(msg)
            else:
                active_messages.append(msg)
        
        if archived_messages:
            await self._write_archive(archived_messages, archive_path)
            self.logger.info(f"Archived {len(archived_messages)} old messages")
        
        return active_messages, archived_messages
    
    async def cleanup_memory(self, memory_path: str) -> Dict[str, int]:
        """Perform memory cleanup and return statistics."""
        cleanup_stats = {
            "files_cleaned": 0,
            "space_freed_mb": 0,
            "fragments_merged": 0
        }
        
        try:
            # Cleanup temporary files
            temp_files = Path(memory_path).glob("*.tmp")
            for temp_file in temp_files:
                size_mb = temp_file.stat().st_size / (1024 * 1024)
                temp_file.unlink()
                cleanup_stats["files_cleaned"] += 1
                cleanup_stats["space_freed_mb"] += size_mb
            
            # Merge fragmented index files (placeholder logic)
            cleanup_stats["fragments_merged"] = await self._merge_fragments(memory_path)
            
            self.logger.info(f"Memory cleanup completed: {cleanup_stats}")
            return cleanup_stats
        
        except Exception as e:
            self.logger.error(f"Memory cleanup failed: {e}")
            raise MemoryLifecycleError(f"Cleanup failed: {e}")
    
    async def _write_archive(self, messages: List[MemoryDocument], archive_path: str):
        """Write messages to archive."""
        archive_file = Path(f"{archive_path}_archive_{int(time.time())}.json")
        archive_data = {
            "timestamp": time.time(),
            "message_count": len(messages),
            "messages": [msg.to_dict() for msg in messages]
        }
        
        with open(archive_file, 'w') as f:
            json.dump(archive_data, f, indent=2)
    
    async def _merge_fragments(self, memory_path: str) -> int:
        """Merge fragmented memory files."""
        # Placeholder implementation
        return 0


class MemoryAnalytics:
    """Provides memory analytics and insights."""
    
    def __init__(self):
        """Initialize memory analytics."""
        self.search_times = []
        self.search_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.logger = logger.bind(component="memory_analytics")
    
    def record_search(self, search_time: float, cache_hit: bool = False):
        """Record a search operation."""
        self.search_times.append(search_time)
        self.search_count += 1
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def calculate_memory_stats(
        self,
        messages: List[MemoryDocument],
        chunks: List[TextChunk]
    ) -> MemoryStats:
        """Calculate comprehensive memory statistics."""
        if not messages:
            return MemoryStats()
        
        # Basic stats
        total_chars = sum(len(msg.content) for msg in messages)
        total_tokens = sum(len(msg.content.split()) for msg in messages) * 1.3  # Rough estimate
        
        # Time-based stats
        timestamps = [msg.timestamp for msg in messages if msg.timestamp]
        oldest = min(timestamps) if timestamps else None
        newest = max(timestamps) if timestamps else None
        
        # Search stats
        avg_search_time = sum(self.search_times) / len(self.search_times) if self.search_times else 0
        cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        # Embedding coverage
        embedded_count = sum(1 for chunk in chunks if chunk.embedding is not None)
        embedding_coverage = embedded_count / len(chunks) if chunks else 0
        
        return MemoryStats(
            total_messages=len(messages),
            total_chunks=len(chunks),
            total_characters=total_chars,
            total_tokens=int(total_tokens),
            memory_size_mb=total_chars / (1024 * 1024),
            oldest_message=datetime.fromtimestamp(oldest) if oldest else None,
            newest_message=datetime.fromtimestamp(newest) if newest else None,
            average_message_length=total_chars / len(messages),
            search_count=self.search_count,
            average_search_time=avg_search_time,
            cache_hit_rate=cache_hit_rate,
            embedding_coverage=embedding_coverage
        )
    
    def generate_insights(self, stats: MemoryStats) -> Dict[str, Any]:
        """Generate insights and recommendations."""
        insights = {
            "recommendations": [],
            "health_score": 0.0,
            "performance_score": 0.0,
            "efficiency_score": 0.0
        }
        
        # Health recommendations
        if stats.memory_size_mb > 50:
            insights["recommendations"].append("Consider memory compression - size exceeds 50MB")
        
        if stats.embedding_coverage < 0.8:
            insights["recommendations"].append("Low embedding coverage - consider regenerating embeddings")
        
        if stats.cache_hit_rate < 0.5:
            insights["recommendations"].append("Low cache hit rate - consider increasing cache size")
        
        # Calculate scores
        health_factors = [
            min(1.0, 100 / max(1, stats.memory_size_mb)),  # Size efficiency
            stats.embedding_coverage,  # Embedding coverage
            min(1.0, stats.cache_hit_rate * 2)  # Cache performance
        ]
        insights["health_score"] = sum(health_factors) / len(health_factors)
        
        performance_factors = [
            max(0.0, 1.0 - stats.average_search_time / 1000),  # Search speed
            stats.cache_hit_rate,  # Cache efficiency
            min(1.0, stats.total_chunks / max(1, stats.total_messages))  # Chunking efficiency
        ]
        insights["performance_score"] = sum(performance_factors) / len(performance_factors)
        
        insights["efficiency_score"] = (insights["health_score"] + insights["performance_score"]) / 2
        
        return insights


class EnhancedMemory(AsyncMemory):
    """Enhanced memory system with chunking, compression, and lifecycle management."""
    
    def __init__(
        self,
        config: MemoryConfig,
        enhanced_config: Optional[MemoryConfiguration] = None,
        embeddings: Optional[Embeddings] = None
    ):
        """Initialize enhanced memory."""
        super().__init__(config)
        self.enhanced_config = enhanced_config or MemoryConfiguration()
        self.embeddings = embeddings
        
        # Core components
        self.chunking_manager = None
        self.compressor = None
        self.lifecycle_manager = MemoryLifecycleManager(self.enhanced_config)
        self.analytics = MemoryAnalytics()
        
        # Storage
        self.messages: List[MemoryDocument] = []
        self.chunks: List[TextChunk] = []
        self.search_cache: Dict[str, List[MemoryDocument]] = {}
        
        # Performance tracking
        self.last_cleanup = time.time()
        self.last_compression = time.time()
        
        # Initialize components
        asyncio.create_task(self._initialize_components())
    
    async def _initialize_components(self):
        """Initialize memory components."""
        try:
            # Initialize chunking
            if self.enhanced_config.enable_chunking:
                chunking_config = ChunkingConfig(
                    strategy=self.enhanced_config.chunking_strategy,
                    chunk_size=self.enhanced_config.chunk_size,
                    chunk_overlap=self.enhanced_config.chunk_overlap,
                    min_chunk_size=self.enhanced_config.min_chunk_size,
                    max_chunk_size=self.enhanced_config.max_chunk_size
                )
                self.chunking_manager = get_chunking_manager(chunking_config, self.embeddings)
            
            # Initialize compression
            if self.enhanced_config.enable_compression:
                self.compressor = MemoryCompressor()
            
            self.logger.info("Enhanced memory components initialized")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced memory components: {e}")
    
    async def add_message(self, message: BaseMessage, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add message with intelligent chunking and processing."""
        if not isinstance(message.content, str):
            raise MemoryError("Message content must be string")
        
        # Create memory document
        doc_id = f"msg_{len(self.messages)}_{int(time.time())}"
        doc = MemoryDocument(
            id=doc_id,
            content=message.content,
            metadata=metadata or {},
            timestamp=time.time()
        )
        
        # Add to messages
        self.messages.append(doc)
        
        # Chunk the message if enabled and content is long enough
        if (self.enhanced_config.enable_chunking and 
            self.chunking_manager and 
            len(message.content) > self.enhanced_config.min_chunk_size):
            
            chunks = await self.chunking_manager.chunk_with_embeddings(
                message.content,
                text_id=doc_id,
                metadata={"source_message_id": doc_id, "message_type": type(message).__name__}
            )
            self.chunks.extend(chunks)
            self.logger.debug(f"Created {len(chunks)} chunks for message {doc_id}")
        
        # Generate embedding for the full message if enabled
        if self.enhanced_config.generate_embeddings and self.embeddings:
            try:
                doc.embedding = await self.embeddings.aembed_query(message.content)
            except Exception as e:
                self.logger.warning(f"Failed to generate embedding for message: {e}")
        
        # Clear cache
        self.search_cache.clear()
        
        # Check if maintenance is needed
        await self._check_maintenance()
        
        self.logger.debug(f"Added message {doc_id} to enhanced memory")
        return doc_id
    
    async def get_messages(
        self,
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[BaseMessage]:
        """Get messages from memory."""
        filtered_messages = []
        
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
                message = HumanMessage(content=doc.content)  # Default
            
            filtered_messages.append(message)
            
            # Apply limit
            if limit and len(filtered_messages) >= limit:
                break
        
        return filtered_messages
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[MemoryDocument]:
        """Enhanced semantic search across messages and chunks."""
        start_time = time.time()
        cache_key = f"{query}_{limit}_{similarity_threshold}"
        
        # Check cache
        if cache_key in self.search_cache and self.enhanced_config.enable_caching:
            self.analytics.record_search(time.time() - start_time, cache_hit=True)
            return self.search_cache[cache_key]
        
        results = []
        
        try:
            # Search in chunks if available and embeddings enabled
            if self.chunks and self.embeddings:
                query_embedding = await self.embeddings.aembed_query(query)
                
                # Calculate similarities with chunks
                chunk_similarities = []
                for chunk in self.chunks:
                    if chunk.embedding:
                        similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                        if similarity >= similarity_threshold:
                            chunk_similarities.append((chunk, similarity))
                
                # Sort by similarity and get top results
                chunk_similarities.sort(key=lambda x: x[1], reverse=True)
                
                # Convert chunks to memory documents
                for chunk, similarity in chunk_similarities[:limit]:
                    doc = MemoryDocument(
                        id=chunk.metadata.chunk_id,
                        content=chunk.content,
                        metadata={
                            **(chunk.metadata.custom_metadata or {}),
                            "similarity_score": similarity,
                            "chunk_index": chunk.metadata.chunk_index,
                            "source_text_id": chunk.metadata.source_text_id
                        },
                        timestamp=time.time()
                    )
                    results.append(doc)
            
            # Fallback to simple text search if no embeddings
            if not results:
                query_lower = query.lower()
                for doc in self.messages:
                    if query_lower in doc.content.lower():
                        results.append(doc)
                        if len(results) >= limit:
                            break
        
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            # Fallback to simple search
            query_lower = query.lower()
            for doc in self.messages:
                if query_lower in doc.content.lower():
                    results.append(doc)
                    if len(results) >= limit:
                        break
        
        # Cache results
        if self.enhanced_config.enable_caching:
            self.search_cache[cache_key] = results
            if len(self.search_cache) > self.enhanced_config.cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self.search_cache))
                del self.search_cache[oldest_key]
        
        # Record analytics
        self.analytics.record_search(time.time() - start_time, cache_hit=False)
        
        self.logger.debug(f"Search returned {len(results)} results for query: {query[:50]}...")
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def _check_maintenance(self):
        """Check if memory maintenance is needed."""
        current_time = time.time()
        
        # Check compression
        if (self.enhanced_config.enable_compression and 
            len(self.messages) >= self.enhanced_config.compression_threshold and
            current_time - self.last_compression > 3600):  # Every hour
            
            await self._compress_old_messages()
        
        # Check cleanup
        if current_time - self.last_cleanup > self.enhanced_config.cleanup_interval:
            await self._perform_cleanup()
    
    async def _compress_old_messages(self):
        """Compress old messages using LLM summarization."""
        if not self.compressor:
            return
        
        # Keep recent messages, compress older ones
        preserve_count = self.enhanced_config.preserve_recent_messages
        if len(self.messages) <= preserve_count:
            return
        
        messages_to_compress = self.messages[:-preserve_count]
        recent_messages = self.messages[-preserve_count:]
        
        try:
            # Convert to BaseMessages for compression
            base_messages = []
            for doc in messages_to_compress:
                base_messages.append(HumanMessage(content=doc.content))
            
            # Compress messages
            compressed = await self.compressor.compress_messages(
                base_messages,
                self.enhanced_config.compression_ratio_target
            )
            
            # Convert back to MemoryDocuments
            compressed_docs = []
            for i, msg in enumerate(compressed):
                doc = MemoryDocument(
                    id=f"compressed_{int(time.time())}_{i}",
                    content=msg.content,
                    metadata={"compressed": True},
                    timestamp=time.time()
                )
                compressed_docs.append(doc)
            
            # Update messages list
            self.messages = compressed_docs + recent_messages
            self.last_compression = time.time()
            
            self.logger.info(f"Compressed {len(messages_to_compress)} messages to {len(compressed)}")
        
        except Exception as e:
            self.logger.error(f"Message compression failed: {e}")
    
    async def _perform_cleanup(self):
        """Perform memory cleanup and maintenance."""
        try:
            # Archive old messages if enabled
            if self.enhanced_config.enable_archiving:
                active, archived = await self.lifecycle_manager.archive_old_messages(
                    self.messages, 
                    self.config.vector_store_path or "memory"
                )
                self.messages = active
            
            # Clear old cache entries
            self.search_cache.clear()
            
            # Remove old chunks for archived messages
            if self.enhanced_config.enable_archiving:
                archived_msg_ids = {doc.id for doc in archived} if 'archived' in locals() else set()
                self.chunks = [
                    chunk for chunk in self.chunks 
                    if chunk.metadata.source_text_id not in archived_msg_ids
                ]
            
            self.last_cleanup = time.time()
            self.logger.debug("Memory cleanup completed")
        
        except Exception as e:
            self.logger.error(f"Memory cleanup failed: {e}")
    
    async def get_memory_stats(self) -> MemoryStats:
        """Get comprehensive memory statistics."""
        return self.analytics.calculate_memory_stats(self.messages, self.chunks)
    
    async def get_memory_insights(self) -> Dict[str, Any]:
        """Get memory insights and recommendations."""
        stats = await self.get_memory_stats()
        return self.analytics.generate_insights(stats)
    
    async def clear(self):
        """Clear all memory."""
        self.messages.clear()
        self.chunks.clear()
        self.search_cache.clear()
        self.logger.info("Cleared enhanced memory")
    
    async def save(self, path: Optional[str] = None):
        """Save enhanced memory to files."""
        if not path:
            path = self.config.vector_store_path or "enhanced_memory"
        
        # Save messages
        messages_data = {
            "messages": [msg.to_dict() for msg in self.messages],
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "config": asdict(self.enhanced_config),
            "timestamp": time.time()
        }
        
        messages_file = f"{path}_enhanced.json"
        with open(messages_file, 'w') as f:
            json.dump(messages_data, f, indent=2)
        
        self.logger.info(f"Saved enhanced memory to {path}")
    
    async def load(self, path: str):
        """Load enhanced memory from files."""
        try:
            messages_file = f"{path}_enhanced.json"
            if not Path(messages_file).exists():
                self.logger.warning(f"Enhanced memory file not found: {messages_file}")
                return
            
            with open(messages_file, 'r') as f:
                data = json.load(f)
            
            # Load messages
            self.messages = [
                MemoryDocument.from_dict(msg_data) 
                for msg_data in data.get("messages", [])
            ]
            
            # Load chunks
            self.chunks = [
                TextChunk.from_dict(chunk_data)
                for chunk_data in data.get("chunks", [])
            ]
            
            self.logger.info(f"Loaded enhanced memory from {path}")
        
        except Exception as e:
            self.logger.error(f"Failed to load enhanced memory: {e}")
            raise MemoryError(f"Failed to load enhanced memory: {e}")


# Convenience functions
async def create_enhanced_memory(
    config: MemoryConfig,
    enhanced_config: Optional[MemoryConfiguration] = None,
    embeddings: Optional[Embeddings] = None
) -> EnhancedMemory:
    """Create an enhanced memory instance."""
    memory = EnhancedMemory(config, enhanced_config, embeddings)
    await memory._initialize_components()  # Ensure components are initialized
    return memory