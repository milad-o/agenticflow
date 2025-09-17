"""
LLM providers integration for AgenticFlow.

Provides wrapper classes for OpenAI, Groq, and Ollama with async support,
configurable switching, and embedding support for memory/retrieval.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import httpx
import structlog
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config.settings import EmbeddingConfig, LLMProvider, LLMProviderConfig

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


class OpenAIProvider(AsyncLLMProvider):
    """OpenAI provider implementation."""
    
    @property
    def supports_embeddings(self) -> bool:
        """OpenAI supports embeddings."""
        return True
    
    def _create_llm(self) -> BaseLanguageModel:
        """Create OpenAI LLM instance."""
        kwargs = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
        }
        
        if self.config.api_key:
            kwargs["openai_api_key"] = self.config.api_key.get_secret_value()
        
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        
        if self.config.max_tokens:
            kwargs["max_tokens"] = self.config.max_tokens
        
        return ChatOpenAI(**kwargs)
    
    def _create_embeddings(self) -> Embeddings:
        """Create OpenAI embeddings instance."""
        kwargs = {}
        
        if self.config.api_key:
            kwargs["openai_api_key"] = self.config.api_key.get_secret_value()
        
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        
        # Use a default embedding model if not specified
        model = "text-embedding-3-small"
        
        return OpenAIEmbeddings(model=model, **kwargs)


class GroqProvider(AsyncLLMProvider):
    """Groq provider implementation."""
    
    @property
    def supports_embeddings(self) -> bool:
        """Groq doesn't support embeddings currently."""
        return False
    
    def _create_llm(self) -> BaseLanguageModel:
        """Create Groq LLM instance."""
        kwargs = {
            "model": self.config.model,
            "temperature": self.config.temperature,
        }
        
        if self.config.api_key:
            kwargs["groq_api_key"] = self.config.api_key.get_secret_value()
        
        if self.config.max_tokens:
            kwargs["max_tokens"] = self.config.max_tokens
        
        return ChatGroq(**kwargs)


class OllamaProvider(AsyncLLMProvider):
    """Ollama provider implementation."""
    
    @property
    def supports_embeddings(self) -> bool:
        """Ollama supports embeddings through some models."""
        return True
    
    def _create_llm(self) -> BaseLanguageModel:
        """Create Ollama LLM instance."""
        kwargs = {
            "model": self.config.model,
            "temperature": self.config.temperature,
        }
        
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        
        return ChatOllama(**kwargs)
    
    def _create_embeddings(self) -> Embeddings:
        """Create Ollama embeddings instance."""
        # Ollama embeddings would need a custom implementation
        # For now, we'll raise an error
        raise EmbeddingNotSupportedError("Ollama embeddings not yet implemented")


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers = {
        LLMProvider.OPENAI: OpenAIProvider,
        LLMProvider.GROQ: GroqProvider,
        LLMProvider.OLLAMA: OllamaProvider,
    }
    
    @classmethod
    def create_provider(cls, config: LLMProviderConfig) -> AsyncLLMProvider:
        """Create a provider instance based on configuration."""
        provider_class = cls._providers.get(config.provider)
        if not provider_class:
            raise ProviderNotAvailableError(f"Provider {config.provider} is not supported")
        
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> List[LLMProvider]:
        """Get list of available providers."""
        return list(cls._providers.keys())


class EmbeddingProviderFactory:
    """Factory for creating embedding providers."""
    
    @classmethod
    async def create_embeddings(cls, config: EmbeddingConfig) -> Embeddings:
        """Create embeddings instance based on configuration."""
        if config.provider == LLMProvider.OPENAI:
            kwargs = {
                "model": config.model,
            }
            
            if config.api_key:
                kwargs["openai_api_key"] = config.api_key.get_secret_value()
            
            if config.dimensions:
                kwargs["dimensions"] = config.dimensions
                
            return OpenAIEmbeddings(**kwargs)
        
        elif config.provider == LLMProvider.GROQ:
            raise EmbeddingNotSupportedError("Groq doesn't support embeddings")
        
        elif config.provider == LLMProvider.OLLAMA:
            raise EmbeddingNotSupportedError("Ollama embeddings not yet implemented")
        
        else:
            raise ProviderNotAvailableError(f"Embedding provider {config.provider} is not supported")


class LLMManager:
    """Manages multiple LLM providers with automatic fallback and load balancing."""
    
    def __init__(self) -> None:
        """Initialize the LLM manager."""
        self._providers: Dict[str, AsyncLLMProvider] = {}
        self._default_provider: Optional[str] = None
        self.logger = logger.bind(component="llm_manager")
    
    def add_provider(self, name: str, config: LLMProviderConfig, is_default: bool = False) -> None:
        """Add a provider to the manager."""
        provider = LLMProviderFactory.create_provider(config)
        self._providers[name] = provider
        
        if is_default or self._default_provider is None:
            self._default_provider = name
        
        self.logger.info(f"Added provider {name} ({config.provider.value})")
    
    def get_provider(self, name: Optional[str] = None) -> AsyncLLMProvider:
        """Get a provider by name, or the default provider."""
        if name is None:
            name = self._default_provider
        
        if name is None or name not in self._providers:
            raise ProviderNotAvailableError(f"Provider {name} is not available")
        
        return self._providers[name]
    
    async def generate_with_fallback(
        self, 
        messages: List[BaseMessage],
        provider_names: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """Generate text with automatic fallback to other providers."""
        if provider_names is None:
            provider_names = list(self._providers.keys())
        
        last_exception = None
        
        for provider_name in provider_names:
            try:
                provider = self.get_provider(provider_name)
                result = await provider.agenerate(messages, **kwargs)
                self.logger.info(f"Successfully generated text using {provider_name}")
                return result
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        # If all providers failed, raise the last exception
        if last_exception:
            raise last_exception
        else:
            raise ProviderNotAvailableError("No providers available")
    
    async def embed_with_fallback(
        self,
        texts: List[str],
        provider_names: Optional[List[str]] = None
    ) -> List[List[float]]:
        """Embed texts with automatic fallback to other providers."""
        if provider_names is None:
            # Filter to providers that support embeddings
            provider_names = [
                name for name, provider in self._providers.items()
                if provider.supports_embeddings
            ]
        
        last_exception = None
        
        for provider_name in provider_names:
            try:
                provider = self.get_provider(provider_name)
                if not provider.supports_embeddings:
                    continue
                
                result = await provider.aembed_documents(texts)
                self.logger.info(f"Successfully embedded texts using {provider_name}")
                return result
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Provider {provider_name} failed for embeddings: {e}")
                continue
        
        # If all providers failed, raise the last exception
        if last_exception:
            raise last_exception
        else:
            raise EmbeddingNotSupportedError("No embedding providers available")
    
    def list_providers(self) -> Dict[str, Dict[str, Any]]:
        """List all available providers with their configurations."""
        return {
            name: {
                "provider": provider.config.provider.value,
                "model": provider.config.model,
                "supports_embeddings": provider.supports_embeddings,
            }
            for name, provider in self._providers.items()
        }
    
    def remove_provider(self, name: str) -> bool:
        """Remove a provider from the manager."""
        if name in self._providers:
            del self._providers[name]
            if self._default_provider == name:
                # Set new default if available
                self._default_provider = next(iter(self._providers.keys())) if self._providers else None
            self.logger.info(f"Removed provider {name}")
            return True
        return False


# Global LLM manager instance
llm_manager = LLMManager()


def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance."""
    return llm_manager