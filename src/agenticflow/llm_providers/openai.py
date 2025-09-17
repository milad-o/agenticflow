"""
OpenAI provider implementation.

Provides OpenAI integration with support for both LLM and embedding models.
"""

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .base import AsyncLLMProvider


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