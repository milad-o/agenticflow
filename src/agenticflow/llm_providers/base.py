"""
Base classes and exceptions for LLM providers.

Provides the abstract base class and error types used by all LLM provider implementations.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import httpx
import structlog
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config.settings import LLMProviderConfig

logger = structlog.get_logger(__name__)


class AgenticFlowLLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class ProviderNotAvailableError(AgenticFlowLLMError):
    """Raised when an LLM provider is not available."""
    pass


class EmbeddingNotSupportedError(AgenticFlowLLMError):
    """Raised when embedding is not supported by the provider."""
    pass


class AsyncLLMProvider(ABC):
    """Abstract base class for async LLM providers."""
    
    def __init__(self, config: LLMProviderConfig) -> None:
        """Initialize the provider with configuration."""
        self.config = config
        self.logger = logger.bind(provider=config.provider.value, model=config.model)
        self._llm: Optional[BaseLanguageModel] = None
        self._embeddings: Optional[Embeddings] = None
    
    @property
    def llm(self) -> BaseLanguageModel:
        """Get the LLM instance."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm
    
    @property
    def embeddings(self) -> Optional[Embeddings]:
        """Get the embeddings instance if supported."""
        if self._embeddings is None and self.supports_embeddings:
            try:
                self._embeddings = self._create_embeddings()
            except Exception as e:
                self.logger.warning(f"Failed to create embeddings: {e}")
        return self._embeddings
    
    @property
    @abstractmethod
    def supports_embeddings(self) -> bool:
        """Check if the provider supports embeddings."""
        pass
    
    @abstractmethod
    def _create_llm(self) -> BaseLanguageModel:
        """Create the LLM instance."""
        pass
    
    def _create_embeddings(self) -> Optional[Embeddings]:
        """Create the embeddings instance if supported."""
        raise EmbeddingNotSupportedError(f"Embeddings not supported by {self.config.provider}")
    
    async def agenerate(
        self, 
        messages: List[BaseMessage], 
        **kwargs: Any
    ) -> str:
        """Generate text asynchronously with retry logic."""
        retry_config = AsyncRetrying(
            stop=stop_after_attempt(self.config.max_retries + 1),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        )
        
        async for attempt in retry_config:
            with attempt:
                try:
                    result = await self.llm.agenerate([messages], **kwargs)
                    return result.generations[0][0].text
                except Exception as e:
                    self.logger.warning(f"LLM generation attempt failed: {e}")
                    raise
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents asynchronously."""
        if not self.embeddings:
            raise EmbeddingNotSupportedError(f"Embeddings not available for {self.config.provider}")
        
        return await self.embeddings.aembed_documents(texts)
    
    async def aembed_query(self, text: str) -> List[float]:
        """Embed a query asynchronously."""
        if not self.embeddings:
            raise EmbeddingNotSupportedError(f"Embeddings not available for {self.config.provider}")
        
        return await self.embeddings.aembed_query(text)