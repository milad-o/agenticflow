"""
LLM manager for multi-provider orchestration.

Provides high-level management of multiple LLM providers with automatic 
fallback and load balancing capabilities.
"""

from typing import Any, Dict, List, Optional

import structlog
from langchain_core.messages import BaseMessage

from ..config.settings import LLMProviderConfig
from .base import AsyncLLMProvider, EmbeddingNotSupportedError, ProviderNotAvailableError
from .factory import LLMProviderFactory

logger = structlog.get_logger(__name__)


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