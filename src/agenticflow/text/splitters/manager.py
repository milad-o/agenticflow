"""
Text Splitter Management System
==============================

Provides centralized management for text splitters with caching, performance monitoring,
and advanced features like batch processing and async management.
"""

import asyncio
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import structlog
import threading
from functools import lru_cache

from .base import (
    TextSplitter,
    TextFragment,
    SplitterConfig,
    SplitterType,
    ContentType,
    BoundaryType,
    LanguageType
)
from .factory import SplitterFactory

logger = structlog.get_logger(__name__)


class SplitterPerformanceMetrics:
    """Performance metrics for splitter operations."""
    
    def __init__(self):
        self.total_splits = 0
        self.total_processing_time = 0.0
        self.total_fragments_created = 0
        self.average_fragment_size = 0.0
        self.errors = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_reset = time.time()
    
    def record_split(self, processing_time: float, fragment_count: int, average_size: float):
        """Record a successful split operation."""
        self.total_splits += 1
        self.total_processing_time += processing_time
        self.total_fragments_created += fragment_count
        self.average_fragment_size = (
            (self.average_fragment_size * (self.total_splits - 1) + average_size) 
            / self.total_splits
        )
    
    def record_error(self):
        """Record an error."""
        self.errors += 1
    
    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_misses += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        avg_time = (
            self.total_processing_time / self.total_splits 
            if self.total_splits > 0 else 0
        )
        
        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            self.cache_hits / cache_total 
            if cache_total > 0 else 0
        )
        
        return {
            "total_splits": self.total_splits,
            "total_processing_time": self.total_processing_time,
            "average_processing_time": avg_time,
            "total_fragments_created": self.total_fragments_created,
            "average_fragment_size": self.average_fragment_size,
            "errors": self.errors,
            "error_rate": self.errors / max(self.total_splits, 1),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "uptime": time.time() - self.last_reset
        }
    
    def reset(self):
        """Reset all metrics."""
        self.__init__()


class SplitterCache:
    """Intelligent caching system for split results."""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[float] = 3600):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self._cache: Dict[str, Tuple[List[TextFragment], float]] = {}
        self._access_order: List[str] = []
        self._lock = threading.RLock()
    
    def _generate_key(self, text: str, config: SplitterConfig, source_id: Optional[str]) -> str:
        """Generate cache key for text and config."""
        import hashlib
        
        # Create a hash of the text content
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:16]
        
        # Create a hash of the config
        config_str = f"{config.splitter_type.value}_{config.chunk_size}_{config.chunk_overlap}"
        config_hash = hashlib.md5(config_str.encode('utf-8')).hexdigest()[:16]
        
        return f"{text_hash}_{config_hash}_{source_id or 'none'}"
    
    def get(self, text: str, config: SplitterConfig, source_id: Optional[str]) -> Optional[List[TextFragment]]:
        """Get cached split result."""
        key = self._generate_key(text, config, source_id)
        
        with self._lock:
            if key in self._cache:
                fragments, timestamp = self._cache[key]
                
                # Check if expired
                if self.ttl and time.time() - timestamp > self.ttl:
                    del self._cache[key]
                    self._access_order.remove(key)
                    return None
                
                # Move to end (most recently used)
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                
                return fragments
        
        return None
    
    def put(self, text: str, config: SplitterConfig, source_id: Optional[str], fragments: List[TextFragment]):
        """Cache split result."""
        key = self._generate_key(text, config, source_id)
        
        with self._lock:
            # Remove oldest entries if cache is full
            while len(self._cache) >= self.max_size and self._access_order:
                oldest_key = self._access_order.pop(0)
                if oldest_key in self._cache:
                    del self._cache[oldest_key]
            
            # Store with timestamp
            self._cache[key] = (fragments, time.time())
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
    
    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "utilization": len(self._cache) / self.max_size,
            "ttl": self.ttl
        }


class SplitterManager:
    """
    Centralized manager for text splitters.
    
    Provides caching, performance monitoring, batch processing,
    and intelligent splitter selection and management.
    """
    
    def __init__(
        self,
        cache_size: int = 1000,
        cache_ttl: Optional[float] = 3600,
        enable_metrics: bool = True,
        max_workers: int = 4
    ):
        self.cache = SplitterCache(cache_size, cache_ttl)
        self.metrics = SplitterPerformanceMetrics() if enable_metrics else None
        self.max_workers = max_workers
        
        # Splitter registry and pools
        self._splitters: Dict[str, TextSplitter] = {}
        self._splitter_configs: Dict[str, SplitterConfig] = {}
        self._default_splitter_id = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        self.logger = logger.bind(manager="SplitterManager")
        self.logger.info("Initialized SplitterManager")
    
    def register_splitter(
        self,
        splitter_id: str,
        config: SplitterConfig,
        set_as_default: bool = False
    ) -> TextSplitter:
        """
        Register a splitter with the manager.
        
        Args:
            splitter_id: Unique identifier for the splitter
            config: Splitter configuration
            set_as_default: Whether to set as default splitter
            
        Returns:
            Created splitter instance
        """
        with self._lock:
            splitter = SplitterFactory.create_splitter(config)
            self._splitters[splitter_id] = splitter
            self._splitter_configs[splitter_id] = config
            
            if set_as_default or self._default_splitter_id is None:
                self._default_splitter_id = splitter_id
            
            self.logger.info(f"Registered splitter: {splitter_id}")
            return splitter
    
    def get_splitter(self, splitter_id: Optional[str] = None) -> Optional[TextSplitter]:
        """
        Get a registered splitter.
        
        Args:
            splitter_id: Splitter ID, or None for default
            
        Returns:
            Splitter instance or None if not found
        """
        with self._lock:
            if splitter_id is None:
                splitter_id = self._default_splitter_id
            
            if splitter_id is None:
                return None
            
            return self._splitters.get(splitter_id)
    
    def remove_splitter(self, splitter_id: str):
        """Remove a registered splitter."""
        with self._lock:
            if splitter_id in self._splitters:
                del self._splitters[splitter_id]
                del self._splitter_configs[splitter_id]
                
                # Update default if necessary
                if self._default_splitter_id == splitter_id:
                    self._default_splitter_id = next(iter(self._splitters.keys()), None)
                
                self.logger.info(f"Removed splitter: {splitter_id}")
    
    def list_splitters(self) -> List[Dict[str, Any]]:
        """List all registered splitters."""
        with self._lock:
            result = []
            for splitter_id, config in self._splitter_configs.items():
                result.append({
                    "id": splitter_id,
                    "type": config.splitter_type.value,
                    "content_type": config.content_type.value,
                    "chunk_size": config.chunk_size,
                    "chunk_overlap": config.chunk_overlap,
                    "is_default": splitter_id == self._default_splitter_id
                })
            return result
    
    async def split_text(
        self,
        text: str,
        splitter_id: Optional[str] = None,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> List[TextFragment]:
        """
        Split text using a registered splitter.
        
        Args:
            text: Text to split
            splitter_id: Splitter to use (None for default)
            source_id: Optional source identifier
            metadata: Optional metadata
            use_cache: Whether to use caching
            
        Returns:
            List of text fragments
        """
        start_time = time.time()
        
        # Get splitter
        splitter = self.get_splitter(splitter_id)
        if splitter is None:
            if self.metrics:
                self.metrics.record_error()
            raise ValueError(f"Splitter not found: {splitter_id}")
        
        config = self._splitter_configs[splitter_id or self._default_splitter_id]
        
        # Check cache first
        if use_cache:
            cached_result = self.cache.get(text, config, source_id)
            if cached_result is not None:
                if self.metrics:
                    self.metrics.record_cache_hit()
                return cached_result
        
        if self.metrics:
            self.metrics.record_cache_miss()
        
        try:
            # Perform splitting
            fragments = await splitter.split_text(text, source_id, metadata)
            
            # Cache result
            if use_cache:
                self.cache.put(text, config, source_id, fragments)
            
            # Record metrics
            if self.metrics:
                processing_time = time.time() - start_time
                avg_size = sum(len(f.content) for f in fragments) / len(fragments) if fragments else 0
                self.metrics.record_split(processing_time, len(fragments), avg_size)
            
            return fragments
        
        except Exception as e:
            if self.metrics:
                self.metrics.record_error()
            self.logger.error(f"Split failed: {e}")
            raise
    
    async def split_documents(
        self,
        documents: List[Dict[str, Any]],
        splitter_id: Optional[str] = None,
        use_cache: bool = True,
        max_concurrency: Optional[int] = None
    ) -> List[List[TextFragment]]:
        """
        Split multiple documents concurrently.
        
        Args:
            documents: List of documents with 'content' and optional metadata
            splitter_id: Splitter to use
            use_cache: Whether to use caching
            max_concurrency: Max concurrent operations (None for manager default)
            
        Returns:
            List of fragment lists, one per document
        """
        if max_concurrency is None:
            max_concurrency = self.max_workers
        
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def split_single(doc: Dict[str, Any]) -> List[TextFragment]:
            async with semaphore:
                return await self.split_text(
                    text=doc.get("content", ""),
                    splitter_id=splitter_id,
                    source_id=doc.get("id"),
                    metadata=doc.get("metadata", {}),
                    use_cache=use_cache
                )
        
        # Process documents concurrently
        tasks = [split_single(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results and exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to split document {i}: {result}")
                processed_results.append([])  # Empty result for failed document
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def smart_split(
        self,
        text: str,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        use_cache: bool = True
    ) -> List[TextFragment]:
        """
        Intelligently split text by analyzing content and choosing best splitter.
        
        Args:
            text: Text to split
            source_id: Optional source identifier
            metadata: Optional metadata
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            use_cache: Whether to use caching
            
        Returns:
            List of text fragments
        """
        # Create smart splitter
        smart_splitter = SplitterFactory.create_smart_splitter(
            text_sample=text[:2000],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Register temporarily
        temp_id = f"smart_temp_{int(time.time() * 1000000)}"
        self._splitters[temp_id] = smart_splitter
        self._splitter_configs[temp_id] = smart_splitter.config
        
        try:
            result = await self.split_text(
                text=text,
                splitter_id=temp_id,
                source_id=source_id,
                metadata=metadata,
                use_cache=use_cache
            )
            return result
        finally:
            # Clean up temporary splitter
            if temp_id in self._splitters:
                del self._splitters[temp_id]
                del self._splitter_configs[temp_id]
    
    def get_performance_stats(self) -> Optional[Dict[str, Any]]:
        """Get performance statistics."""
        if not self.metrics:
            return None
        
        stats = self.metrics.get_stats()
        stats["cache"] = self.cache.get_stats()
        stats["registered_splitters"] = len(self._splitters)
        
        return stats
    
    def reset_metrics(self):
        """Reset performance metrics."""
        if self.metrics:
            self.metrics.reset()
        self.logger.info("Reset performance metrics")
    
    def clear_cache(self):
        """Clear all cached results."""
        self.cache.clear()
        self.logger.info("Cleared cache")
    
    async def start(self):
        """Start the manager and background tasks."""
        self._is_running = True
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())
        
        self.logger.info("Started SplitterManager")
    
    async def stop(self):
        """Stop the manager and background tasks."""
        self._is_running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped SplitterManager")
    
    async def _cleanup_worker(self):
        """Background worker for periodic cleanup tasks."""
        while self._is_running:
            try:
                # Periodic cache cleanup can be added here if needed
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup worker error: {e}")
                await asyncio.sleep(60)  # Wait before retrying


# Global manager instance
_global_manager: Optional[SplitterManager] = None
_manager_lock = threading.Lock()


def get_splitter_manager() -> SplitterManager:
    """
    Get the global splitter manager instance.
    
    Returns:
        Global SplitterManager instance
    """
    global _global_manager
    
    with _manager_lock:
        if _global_manager is None:
            _global_manager = SplitterManager()
            
            # Register default splitters
            _global_manager.register_splitter(
                "default_recursive",
                SplitterConfig(
                    splitter_type=SplitterType.RECURSIVE,
                    chunk_size=1000,
                    chunk_overlap=200
                ),
                set_as_default=True
            )
            
            _global_manager.register_splitter(
                "sentence",
                SplitterConfig(
                    splitter_type=SplitterType.SENTENCE,
                    chunk_size=1000,
                    chunk_overlap=100
                )
            )
            
            _global_manager.register_splitter(
                "markdown",
                SplitterConfig(
                    splitter_type=SplitterType.MARKDOWN,
                    content_type=ContentType.MARKDOWN,
                    chunk_size=1500,
                    chunk_overlap=200
                )
            )
    
    return _global_manager


async def initialize_manager() -> SplitterManager:
    """
    Initialize and start the global splitter manager.
    
    Returns:
        Started SplitterManager instance
    """
    manager = get_splitter_manager()
    await manager.start()
    return manager


# Convenience functions using the global manager
async def split_text(
    text: str,
    splitter_type: SplitterType = SplitterType.RECURSIVE,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    source_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    use_cache: bool = True
) -> List[TextFragment]:
    """
    Split text using the global manager.
    
    Args:
        text: Text to split
        splitter_type: Type of splitter to use
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        source_id: Optional source identifier
        metadata: Optional metadata
        use_cache: Whether to use caching
        
    Returns:
        List of text fragments
    """
    manager = get_splitter_manager()
    
    # Find or create appropriate splitter
    splitter_id = None
    for registered in manager.list_splitters():
        if registered["type"] == splitter_type.value:
            splitter_id = registered["id"]
            break
    
    if splitter_id is None:
        # Register new splitter
        config = SplitterConfig(
            splitter_type=splitter_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        splitter_id = f"{splitter_type.value}_{chunk_size}_{chunk_overlap}"
        manager.register_splitter(splitter_id, config)
    
    return await manager.split_text(
        text=text,
        splitter_id=splitter_id,
        source_id=source_id,
        metadata=metadata,
        use_cache=use_cache
    )


async def smart_split_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    source_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    use_cache: bool = True
) -> List[TextFragment]:
    """
    Intelligently split text using the global manager.
    
    Args:
        text: Text to split
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        source_id: Optional source identifier
        metadata: Optional metadata
        use_cache: Whether to use caching
        
    Returns:
        List of text fragments
    """
    manager = get_splitter_manager()
    return await manager.smart_split(
        text=text,
        source_id=source_id,
        metadata=metadata,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        use_cache=use_cache
    )


def get_manager_stats() -> Optional[Dict[str, Any]]:
    """Get performance statistics from the global manager."""
    manager = get_splitter_manager()
    return manager.get_performance_stats()


def clear_manager_cache():
    """Clear cache from the global manager."""
    manager = get_splitter_manager()
    manager.clear_cache()