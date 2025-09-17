"""
OpenAI Embedding Provider
========================

Implementation of OpenAI's embedding models including text-embedding-ada-002, 
text-embedding-3-small, and text-embedding-3-large.
"""

import os
from typing import Any, Dict, List, Optional

import httpx
import structlog
from openai import AsyncOpenAI

from .base import (
    AsyncEmbeddingProvider,
    EmbeddingConfig,
    EmbeddingProvider,
    EmbeddingTaskType,
    EmbeddingRateLimitError,
    EmbeddingModelNotFoundError,
)

logger = structlog.get_logger(__name__)


class OpenAIEmbeddingProvider(AsyncEmbeddingProvider):
    """OpenAI embedding provider with support for all OpenAI embedding models."""
    
    # Model configurations
    MODEL_INFO = {
        "text-embedding-ada-002": {
            "dimension": 1536,
            "max_input_tokens": 8191,
            "cost_per_1k_tokens": 0.0001,
        },
        "text-embedding-3-small": {
            "dimension": 1536,
            "max_input_tokens": 8191,
            "cost_per_1k_tokens": 0.00002,
        },
        "text-embedding-3-large": {
            "dimension": 3072,
            "max_input_tokens": 8191,
            "cost_per_1k_tokens": 0.00013,
        }
    }
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        
        # Initialize OpenAI client
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=config.api_base or None,
            organization=config.organization,
            timeout=config.request_timeout,
            max_retries=0,  # We handle retries ourselves
        )
        
        # Validate model
        if config.model not in self.MODEL_INFO:
            available_models = list(self.MODEL_INFO.keys())
            raise EmbeddingModelNotFoundError(
                f"Model '{config.model}' not found. Available models: {available_models}"
            )
        
        self.model_info = self.MODEL_INFO[config.model]
        
        # Set dimension if not specified
        if config.dimensions is None:
            self._dimension = self.model_info["dimension"]
        else:
            self._dimension = config.dimensions
    
    @property
    def supports_batch(self) -> bool:
        """OpenAI supports batch embedding."""
        return True
    
    @property
    def max_batch_size(self) -> int:
        """OpenAI maximum batch size."""
        return 2048
    
    @property
    def max_text_length(self) -> int:
        """Maximum text length for OpenAI models."""
        # Approximate: 4 chars per token
        return self.model_info["max_input_tokens"] * 4
    
    async def _embed_texts_impl(
        self, 
        texts: List[str],
        task_type: Optional[EmbeddingTaskType] = None
    ) -> List[List[float]]:
        """Implementation-specific embedding method."""
        try:
            # Prepare request parameters
            kwargs = {
                "input": texts,
                "model": self.config.model,
            }
            
            # Add optional parameters
            if self.config.dimensions:
                kwargs["dimensions"] = self.config.dimensions
            
            if self.config.encoding_format:
                kwargs["encoding_format"] = self.config.encoding_format
            
            if self.config.user:
                kwargs["user"] = self.config.user
            
            # Make API request
            response = await self.client.embeddings.create(**kwargs)
            
            # Extract embeddings
            embeddings = []
            for embedding_data in response.data:
                embeddings.append(embedding_data.embedding)
            
            # Update cost metrics
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens
                cost_per_token = self.model_info["cost_per_1k_tokens"] / 1000
                cost = tokens_used * cost_per_token
                self._metrics.total_cost += cost
                self.logger.debug(f"OpenAI embedding cost: ${cost:.6f} for {tokens_used} tokens")
            
            return embeddings
        
        except Exception as e:
            # Handle specific OpenAI errors
            if "rate_limit" in str(e).lower():
                raise EmbeddingRateLimitError(f"OpenAI rate limit exceeded: {e}")
            elif "model" in str(e).lower() and "not found" in str(e).lower():
                raise EmbeddingModelNotFoundError(f"OpenAI model not found: {e}")
            else:
                self.logger.error(f"OpenAI embedding error: {e}")
                raise
    
    async def get_dimension(self) -> int:
        """Get the embedding dimension."""
        if self._dimension is None:
            # Try to get dimension from a test embedding
            try:
                test_embedding = await self._embed_texts_impl(["test"])
                self._dimension = len(test_embedding[0])
            except Exception:
                # Fallback to model default
                self._dimension = self.model_info["dimension"]
        
        return self._dimension
    
    async def is_available(self) -> bool:
        """Check if the OpenAI embedding service is available."""
        try:
            # Test with a simple embedding
            await self._embed_texts_impl(["test"])
            return True
        except Exception as e:
            self.logger.warning(f"OpenAI embedding service not available: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the OpenAI embedding model."""
        return {
            "provider": EmbeddingProvider.OPENAI.value,
            "model": self.config.model,
            "dimension": self._dimension or self.model_info["dimension"],
            "max_input_tokens": self.model_info["max_input_tokens"],
            "cost_per_1k_tokens": self.model_info["cost_per_1k_tokens"],
            "supports_batch": self.supports_batch,
            "max_batch_size": self.max_batch_size,
            "max_text_length": self.max_text_length,
            "supports_task_types": False,  # OpenAI doesn't support task types yet
        }


def create_openai_embedding_provider(
    model: str = "text-embedding-3-small",
    api_key: Optional[str] = None,
    dimensions: Optional[int] = None,
    **kwargs
) -> OpenAIEmbeddingProvider:
    """
    Create an OpenAI embedding provider.
    
    Args:
        model: OpenAI embedding model name
        api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        dimensions: Embedding dimensions (uses model default if not provided)
        **kwargs: Additional configuration options
        
    Returns:
        Configured OpenAI embedding provider
    """
    config = EmbeddingConfig(
        provider=EmbeddingProvider.OPENAI,
        model=model,
        api_key=api_key,
        dimensions=dimensions,
        **kwargs
    )
    
    return OpenAIEmbeddingProvider(config)