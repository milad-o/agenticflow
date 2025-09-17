"""
Ollama provider implementation.

Provides Ollama integration for local LLM inference. Embedding support
is available through some models but not yet implemented.
"""

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_ollama import ChatOllama

from .base import AsyncLLMProvider, EmbeddingNotSupportedError


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