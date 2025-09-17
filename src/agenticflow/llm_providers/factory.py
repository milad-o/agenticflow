"""
Factory classes for creating LLM and embedding providers.

Provides factory methods to instantiate providers based on configuration.
"""

from typing import List

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from ..config.settings import EmbeddingConfig, LLMProvider, LLMProviderConfig
from .azure_openai import AzureOpenAIProvider
from .base import AsyncLLMProvider, EmbeddingNotSupportedError, ProviderNotAvailableError
from .groq import GroqProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers = {
        LLMProvider.OPENAI: OpenAIProvider,
        LLMProvider.GROQ: GroqProvider,
        LLMProvider.OLLAMA: OllamaProvider,
        LLMProvider.AZURE_OPENAI: AzureOpenAIProvider,
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
        
        elif config.provider == LLMProvider.AZURE_OPENAI:
            from langchain_openai import AzureOpenAIEmbeddings
            kwargs = {
                "model": config.model,
            }
            
            if config.api_key:
                kwargs["openai_api_key"] = config.api_key.get_secret_value()
            
            if config.dimensions:
                kwargs["dimensions"] = config.dimensions
                
            return AzureOpenAIEmbeddings(**kwargs)
        
        else:
            raise ProviderNotAvailableError(f"Embedding provider {config.provider} is not supported")
