"""
Groq provider implementation.

Provides Groq integration for fast inference. Note that Groq currently 
does not support embedding models.
"""

from langchain_core.language_models import BaseLanguageModel
from langchain_groq import ChatGroq

from .base import AsyncLLMProvider


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