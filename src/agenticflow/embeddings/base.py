"""
Base classes and exceptions for embedding providers.

Provides the abstract base class and error types used by all embedding provider implementations.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

import httpx
import structlog
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    OLLAMA = "ollama"
    LOCAL = "local"
    CUSTOM = "custom"


class EmbeddingTaskType(str, Enum):
    """Types of embedding tasks."""
    SEARCH_DOCUMENT = "search_document"
    SEARCH_QUERY = "search_query"
    RETRIEVAL_DOCUMENT = "retrieval.document"
    RETRIEVAL_QUERY = "retrieval.query"
    SIMILARITY = "similarity"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    

# Exceptions
class AgenticFlowEmbeddingError(Exception):
    """Base exception for embedding-related errors."""
    pass


class EmbeddingProviderNotAvailableError(AgenticFlowEmbeddingError):
    """Raised when an embedding provider is not available."""
    pass


class EmbeddingModelNotFoundError(AgenticFlowEmbeddingError):
    """Raised when an embedding model is not found."""
    pass


class EmbeddingDimensionMismatchError(AgenticFlowEmbeddingError):
    """Raised when embedding dimensions don't match expected values."""
    pass


class EmbeddingRateLimitError(AgenticFlowEmbeddingError):
    """Raised when embedding API rate limit is exceeded."""
    pass


@dataclass
class EmbeddingConfig:
    """Configuration for embedding providers."""
    provider: EmbeddingProvider
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    organization: Optional[str] = None
    dimensions: Optional[int] = None
    max_retries: int = 3
    request_timeout: float = 60.0
    batch_size: int = 100
    task_type: Optional[EmbeddingTaskType] = None
    
    # Model-specific parameters
    truncate: Optional[str] = None  # Cohere
    encoding_format: Optional[str] = None  # OpenAI
    user: Optional[str] = None  # OpenAI
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl: int = 3600  # seconds
    enable_batching: bool = True
    
    # Advanced settings
    custom_headers: Optional[Dict[str, str]] = None
    proxy: Optional[str] = None
    verify_ssl: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if isinstance(self.provider, str):
            self.provider = EmbeddingProvider(self.provider)
        
        if self.max_retries < 0:
            self.max_retries = 0
        
        if self.request_timeout <= 0:
            self.request_timeout = 60.0


@dataclass
class EmbeddingMetrics:
    """Metrics for embedding operations."""
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_latency: float = 0.0
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_reset: float = 0.0
    
    def __post_init__(self):
        if self.last_reset == 0.0:
            self.last_reset = time.time()


class AsyncEmbeddingProvider(ABC):
    """Abstract base class for async embedding providers."""
    
    def __init__(self, config: EmbeddingConfig):
        """Initialize the provider with configuration."""
        self.config = config
        self.logger = logger.bind(
            provider=config.provider.value,
            model=config.model
        )
        self._dimension: Optional[int] = None
        self._metrics = EmbeddingMetrics()
        self._cache: Dict[str, Tuple[List[float], float]] = {}
    
    @property
    def metrics(self) -> EmbeddingMetrics:
        """Get embedding metrics."""
        return self._metrics
    
    @property
    @abstractmethod
    def supports_batch(self) -> bool:
        """Check if the provider supports batch embedding."""
        pass
    
    @property
    @abstractmethod
    def max_batch_size(self) -> int:
        """Get maximum batch size for this provider."""
        pass
    
    @property
    @abstractmethod
    def max_text_length(self) -> int:
        """Get maximum text length for this provider."""
        pass
    
    @abstractmethod
    async def _embed_texts_impl(
        self, 
        texts: List[str],
        task_type: Optional[EmbeddingTaskType] = None
    ) -> List[List[float]]:
        """Implementation-specific embedding method."""
        pass
    
    @abstractmethod
    async def get_dimension(self) -> int:
        """Get the embedding dimension."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the embedding model is available."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        pass
    
    async def embed_text(
        self, 
        text: str,
        task_type: Optional[EmbeddingTaskType] = None
    ) -> List[float]:
        """Embed a single text with caching and error handling."""
        if not text.strip():
            dimension = await self.get_dimension()
            return [0.0] * dimension
        
        # Check cache
        cache_key = f"{hash(text)}_{task_type}"
        if self.config.enable_caching and cache_key in self._cache:
            cached_embedding, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                self._metrics.cache_hits += 1
                return cached_embedding
        
        self._metrics.cache_misses += 1
        
        try:
            embeddings = await self._embed_with_retry([text], task_type)
            embedding = embeddings[0]
            
            # Cache result
            if self.config.enable_caching:
                self._cache[cache_key] = (embedding, time.time())
                # Simple cache cleanup
                if len(self._cache) > 1000:
                    oldest_key = min(self._cache.keys(), 
                                   key=lambda k: self._cache[k][1])
                    del self._cache[oldest_key]
            
            return embedding
            
        except Exception as e:
            self._metrics.error_count += 1
            self.logger.error(f"Failed to embed text: {e}")
            raise
    
    async def embed_texts(
        self, 
        texts: List[str],
        task_type: Optional[EmbeddingTaskType] = None
    ) -> List[List[float]]:
        """Embed multiple texts with batching support."""
        if not texts:
            return []
        
        if not self.supports_batch or not self.config.enable_batching:
            # Process one by one
            results = []
            for text in texts:
                embedding = await self.embed_text(text, task_type)
                results.append(embedding)
            return results
        
        # Batch processing
        results = []
        batch_size = min(self.config.batch_size, self.max_batch_size)
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._embed_with_retry(batch, task_type)
            results.extend(batch_embeddings)
        
        return results
    
    async def _embed_with_retry(
        self,
        texts: List[str],
        task_type: Optional[EmbeddingTaskType] = None
    ) -> List[List[float]]:
        """Embed texts with retry logic."""
        retry_config = AsyncRetrying(
            stop=stop_after_attempt(self.config.max_retries + 1),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            retry=retry_if_exception_type((
                httpx.RequestError, 
                httpx.HTTPStatusError,
                EmbeddingRateLimitError
            )),
        )
        
        start_time = time.time()
        
        async for attempt in retry_config:
            with attempt:
                try:
                    embeddings = await self._embed_texts_impl(texts, task_type)
                    
                    # Update metrics
                    self._metrics.total_requests += 1
                    self._metrics.total_tokens += sum(len(text.split()) for text in texts)
                    latency = time.time() - start_time
                    
                    # Update average latency
                    total_time = (self._metrics.average_latency * 
                                (self._metrics.total_requests - 1) + latency)
                    self._metrics.average_latency = total_time / self._metrics.total_requests
                    
                    return embeddings
                    
                except Exception as e:
                    self.logger.warning(f"Embedding attempt failed: {e}")
                    raise
    
    def reset_metrics(self):
        """Reset embedding metrics."""
        self._metrics = EmbeddingMetrics()
    
    def clear_cache(self):
        """Clear embedding cache."""
        self._cache.clear()
        self.logger.info("Cleared embedding cache")
