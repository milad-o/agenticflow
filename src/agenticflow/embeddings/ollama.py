"""
Ollama Embedding Provider
=========================

Implementation of Ollama's embedding API for local text embeddings.
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


class OllamaEmbeddingProvider(AsyncEmbeddingProvider):
    """Ollama embedding provider for local text embeddings."""
    
    # Popular Ollama embedding models
    MODEL_INFO = {
        "mxbai-embed-large": {
            "dimension": 1024,
            "max_input_length": 512,
            "supports_task_types": False,
        },
        "nomic-embed-text": {
            "dimension": 768,
            "max_input_length": 2048,
            "supports_task_types": True,
        },
        "all-minilm": {
            "dimension": 384,
            "max_input_length": 256,
            "supports_task_types": False,
        },
        "snowflake-arctic-embed": {
            "dimension": 1024,
            "max_input_length": 512,
            "supports_task_types": True,
        },
    }
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        
        self.base_url = config.api_base or "http://localhost:11434"
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "agenticflow-ollama-client",
            },
            timeout=config.request_timeout,
        )
    
    @property
    def supports_batch(self) -> bool:
        """Ollama doesn't natively support batch embedding, but we can simulate it."""
        return True
    
    @property
    def max_batch_size(self) -> int:
        """Ollama batch size (processed sequentially)."""
        return min(self.config.batch_size, 20)  # Reasonable limit for local processing
    
    @property
    def max_text_length(self) -> int:
        """Maximum text length for Ollama models."""
        model_info = self.MODEL_INFO.get(self.config.model, {})
        return model_info.get("max_input_length", 512) * 4  # approx chars per token
    
    async def _embed_texts_impl(
        self, 
        texts: List[str],
        task_type: Optional[EmbeddingTaskType] = None
    ) -> List[List[float]]:
        """Implementation-specific embedding method."""
        
        if not texts:
            return []
        
        embeddings = []
        
        for text in texts:
            try:
                # Prepare request payload
                payload = {
                    "model": self.config.model,
                    "prompt": text,
                }
                
                # Add task type if supported by the model
                model_info = self.MODEL_INFO.get(self.config.model, {})
                if model_info.get("supports_task_types", False) and task_type:
                    # Map our task types to Ollama's format
                    if task_type in [EmbeddingTaskType.SEARCH_DOCUMENT, EmbeddingTaskType.RETRIEVAL_DOCUMENT]:
                        payload["options"] = {"embedding_only": True, "task": "document"}
                    elif task_type in [EmbeddingTaskType.SEARCH_QUERY, EmbeddingTaskType.RETRIEVAL_QUERY]:
                        payload["options"] = {"embedding_only": True, "task": "query"}
                
                # Make API request with retry logic
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self.config.max_retries + 1),
                    wait=wait_exponential(multiplier=1, min=1, max=10),
                    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
                    reraise=True,
                ):
                    with attempt:
                        response = await self.client.post("/api/embeddings", json=payload)
                        
                        if response.status_code == 404:
                            raise EmbeddingModelNotFoundError(
                                f"Model {self.config.model} not found. "
                                f"Install it with: ollama pull {self.config.model}"
                            )
                        elif response.status_code == 500:
                            error_text = response.text
                            if "model not found" in error_text.lower():
                                raise EmbeddingModelNotFoundError(
                                    f"Model {self.config.model} not found. "
                                    f"Install it with: ollama pull {self.config.model}"
                                )
                        
                        response.raise_for_status()
                        result = response.json()
                        
                        # Extract embedding from response
                        if "embedding" in result:
                            embeddings.append(result["embedding"])
                        else:
                            raise ValueError(f"Invalid response format: {result}")
            
            except httpx.ConnectError:
                raise EmbeddingProviderNotAvailableError(
                    "Cannot connect to Ollama server. "
                    "Make sure Ollama is running on the specified URL."
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise EmbeddingModelNotFoundError(
                        f"Model {self.config.model} not found. "
                        f"Install it with: ollama pull {self.config.model}"
                    )
                else:
                    self.logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
                    raise
            except Exception as e:
                self.logger.error(f"Ollama embedding error: {e}")
                raise
        
        return embeddings
    
    async def get_dimension(self) -> int:
        """Get the embedding dimension."""
        if self._dimension is None:
            # Get from model info or test embedding
            model_info = self.MODEL_INFO.get(self.config.model)
            if model_info:
                self._dimension = model_info["dimension"]
            else:
                # Get dimension from test embedding
                try:
                    test_embeddings = await self._embed_texts_impl(["test"])
                    self._dimension = len(test_embeddings[0])
                except Exception:
                    # Fallback to common dimension
                    self._dimension = 768
        
        return self._dimension
    
    async def is_available(self) -> bool:
        """Check if the Ollama model is available."""
        try:
            # First check if Ollama server is running
            response = await self.client.get("/api/tags")
            if response.status_code != 200:
                return False
            
            # Check if our model is available
            models = response.json()
            available_models = [model["name"].split(":")[0] for model in models.get("models", [])]
            
            if self.config.model not in available_models:
                # Try a simple embedding to see if the model works anyway
                try:
                    await self._embed_texts_impl(["test"])
                    return True
                except EmbeddingModelNotFoundError:
                    return False
            
            # Test with a simple embedding request
            await self._embed_texts_impl(["test"])
            return True
            
        except Exception as e:
            self.logger.warning(f"Ollama model not available: {e}")
            return False
    
    async def list_available_models(self) -> List[str]:
        """List available models on the Ollama server."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            
            models = response.json()
            return [model["name"] for model in models.get("models", [])]
            
        except Exception as e:
            self.logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Ollama model."""
        model_info = self.MODEL_INFO.get(self.config.model, {})
        
        return {
            "provider": EmbeddingProvider.OLLAMA.value,
            "model": self.config.model,
            "dimension": self._dimension or model_info.get("dimension", "unknown"),
            "max_input_length": model_info.get("max_input_length", 512),
            "supports_batch": self.supports_batch,
            "max_batch_size": self.max_batch_size,
            "max_text_length": self.max_text_length,
            "supports_task_types": model_info.get("supports_task_types", False),
            "local_model": True,
            "cost_per_1k_tokens": 0.0,  # Local models are free
            "base_url": self.base_url,
        }
    
    async def close(self):
        """Close the HTTP client."""
        if hasattr(self, 'client'):
            await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def create_ollama_embedding_provider(
    model: str = "mxbai-embed-large",
    api_base: Optional[str] = None,
    **kwargs
) -> OllamaEmbeddingProvider:
    """
    Create an Ollama embedding provider.
    
    Args:
        model: Ollama model name (must be installed via 'ollama pull')
        api_base: Ollama server URL (default: http://localhost:11434)
        **kwargs: Additional configuration options
        
    Returns:
        Configured Ollama embedding provider
    """
    config = EmbeddingConfig(
        provider=EmbeddingProvider.OLLAMA,
        model=model,
        api_base=api_base,
        **kwargs
    )
    
    return OllamaEmbeddingProvider(config)