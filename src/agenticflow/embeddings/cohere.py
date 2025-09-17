"""
Cohere Embedding Provider
=========================

Implementation of Cohere's embedding API for text embeddings.
"""

import asyncio
from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from .base import (
    AsyncEmbeddingProvider,
    EmbeddingConfig,
    EmbeddingProvider,
    EmbeddingTaskType,
    EmbeddingModelNotFoundError,
    EmbeddingProviderNotAvailableError,
    EmbeddingRateLimitError,
)

logger = structlog.get_logger(__name__)


class CohereEmbeddingProvider(AsyncEmbeddingProvider):
    """Cohere embedding provider for text embeddings."""
    
    # Cohere model configurations
    MODEL_INFO = {
        "embed-english-v3.0": {
            "dimension": 1024,
            "max_input_length": 512,
            "supports_task_types": True,
            "cost_per_1k_tokens": 0.0001,
        },
        "embed-multilingual-v3.0": {
            "dimension": 1024,
            "max_input_length": 512,
            "supports_task_types": True,
            "cost_per_1k_tokens": 0.0001,
        },
        "embed-english-light-v3.0": {
            "dimension": 384,
            "max_input_length": 512,
            "supports_task_types": True,
            "cost_per_1k_tokens": 0.0001,
        },
        "embed-multilingual-light-v3.0": {
            "dimension": 384,
            "max_input_length": 512,
            "supports_task_types": True,
            "cost_per_1k_tokens": 0.0001,
        },
        "embed-english-v2.0": {
            "dimension": 4096,
            "max_input_length": 512,
            "supports_task_types": False,
            "cost_per_1k_tokens": 0.0001,
        },
        "embed-multilingual-v2.0": {
            "dimension": 768,
            "max_input_length": 512,
            "supports_task_types": False,
            "cost_per_1k_tokens": 0.0001,
        },
    }
    
    # Task type mapping to Cohere's input types
    TASK_TYPE_MAPPING = {
        EmbeddingTaskType.SEARCH_DOCUMENT: "search_document",
        EmbeddingTaskType.SEARCH_QUERY: "search_query",
        EmbeddingTaskType.CLASSIFICATION: "classification",
        EmbeddingTaskType.CLUSTERING: "clustering",
    }
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        
        self.api_key = config.api_key or self._get_api_key()
        if not self.api_key:
            raise EmbeddingProviderNotAvailableError(
                "Cohere API key not provided. Set COHERE_API_KEY environment variable "
                "or pass api_key in config."
            )
        
        self.client = httpx.AsyncClient(
            base_url=config.api_base or "https://api.cohere.ai/v1",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Client-Name": "agenticflow",
            },
            timeout=config.request_timeout,
        )
    
    def _get_api_key(self) -> Optional[str]:
        """Get Cohere API key from environment variables."""
        import os
        return os.getenv("COHERE_API_KEY") or os.getenv("CO_API_KEY")
    
    @property
    def supports_batch(self) -> bool:
        """Cohere supports batch embedding."""
        return True
    
    @property
    def max_batch_size(self) -> int:
        """Cohere batch size limit."""
        return min(self.config.batch_size, 96)  # Cohere's limit
    
    @property
    def max_text_length(self) -> int:
        """Maximum text length for Cohere models."""
        model_info = self.MODEL_INFO.get(self.config.model, {})
        return model_info.get("max_input_length", 512) * 4  # approx chars per token
    
    async def _embed_texts_impl(
        self, 
        texts: List[str],
        task_type: Optional[EmbeddingTaskType] = None
    ) -> List[List[float]]:
        """Implementation-specific embedding method."""
        
        # Prepare request payload
        payload = {
            "texts": texts,
            "model": self.config.model,
        }
        
        # Add input type for v3 models that support task types
        model_info = self.MODEL_INFO.get(self.config.model, {})
        if model_info.get("supports_task_types", False):
            cohere_task = self.TASK_TYPE_MAPPING.get(
                task_type or self.config.task_type,
                "search_document"  # Default
            )
            payload["input_type"] = cohere_task
        
        # Add truncate option if configured
        if self.config.truncate:
            payload["truncate"] = self.config.truncate
        
        try:
            # Make API request with retry logic
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.config.max_retries + 1),
                wait=wait_exponential(multiplier=1, min=1, max=60),
                retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
                reraise=True,
            ):
                with attempt:
                    response = await self.client.post("/embed", json=payload)
                    
                    if response.status_code == 429:
                        raise EmbeddingRateLimitError("Cohere API rate limit exceeded")
                    elif response.status_code == 404:
                        raise EmbeddingModelNotFoundError(f"Model {self.config.model} not found")
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    return result["embeddings"]
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise EmbeddingRateLimitError("Cohere API rate limit exceeded")
            elif e.response.status_code == 404:
                raise EmbeddingModelNotFoundError(f"Model {self.config.model} not found")
            else:
                self.logger.error(f"Cohere API error: {e.response.status_code} - {e.response.text}")
                raise
        except Exception as e:
            self.logger.error(f"Cohere embedding error: {e}")
            raise
    
    async def get_dimension(self) -> int:
        """Get the embedding dimension."""
        if self._dimension is None:
            # Get from model info or test embedding
            model_info = self.MODEL_INFO.get(self.config.model)
            if model_info:
                self._dimension = model_info["dimension"]
            else:
                # Get dimension from test embedding
                test_embeddings = await self._embed_texts_impl(["test"])
                self._dimension = len(test_embeddings[0])
        
        return self._dimension
    
    async def is_available(self) -> bool:
        """Check if the Cohere model is available."""
        try:
            # Test with a simple embedding request
            await self._embed_texts_impl(["test"])
            return True
        except Exception as e:
            self.logger.warning(f"Cohere model not available: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Cohere model."""
        model_info = self.MODEL_INFO.get(self.config.model, {})
        
        return {
            "provider": EmbeddingProvider.COHERE.value,
            "model": self.config.model,
            "dimension": self._dimension or model_info.get("dimension", "unknown"),
            "max_input_length": model_info.get("max_input_length", 512),
            "supports_batch": self.supports_batch,
            "max_batch_size": self.max_batch_size,
            "max_text_length": self.max_text_length,
            "supports_task_types": model_info.get("supports_task_types", False),
            "local_model": False,
            "cost_per_1k_tokens": model_info.get("cost_per_1k_tokens", 0.0),
        }
    
    async def close(self):
        """Close the HTTP client."""
        if hasattr(self, 'client'):
            await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def create_cohere_embedding_provider(
    model: str = "embed-english-v3.0",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    **kwargs
) -> CohereEmbeddingProvider:
    """
    Create a Cohere embedding provider.
    
    Args:
        model: Cohere model name
        api_key: Cohere API key (if not set in environment)
        api_base: Custom API base URL
        **kwargs: Additional configuration options
        
    Returns:
        Configured Cohere embedding provider
    """
    config = EmbeddingConfig(
        provider=EmbeddingProvider.COHERE,
        model=model,
        api_key=api_key,
        api_base=api_base,
        **kwargs
    )
    
    return CohereEmbeddingProvider(config)