"""
LLM providers integration for AgenticFlow.

This module provides wrapper classes for OpenAI, Groq, and Ollama with async support,
configurable switching, and embedding support for memory/retrieval.

The module is organized as follows:
- base: Abstract base classes and exceptions
- openai: OpenAI provider implementation
- groq: Groq provider implementation  
- ollama: Ollama provider implementation
- factory: Provider factory classes
- manager: Multi-provider management with fallback

All public classes are exported at the top level to maintain backward compatibility.
"""

# Import all public classes to maintain backward compatibility
from .base import (
    AgenticFlowLLMError,
    AsyncLLMProvider,
    EmbeddingNotSupportedError,
    ProviderNotAvailableError,
)
from .factory import EmbeddingProviderFactory, LLMProviderFactory
from .groq import GroqProvider
from .manager import LLMManager, get_llm_manager, llm_manager
from .ollama import OllamaProvider
from .openai import OpenAIProvider

# Export all public classes
__all__ = [
    # Exceptions
    "AgenticFlowLLMError",
    "ProviderNotAvailableError", 
    "EmbeddingNotSupportedError",
    
    # Base classes
    "AsyncLLMProvider",
    
    # Provider implementations
    "OpenAIProvider",
    "GroqProvider",
    "OllamaProvider",
    
    # Factory classes
    "LLMProviderFactory",
    "EmbeddingProviderFactory",
    
    # Manager classes
    "LLMManager",
    "llm_manager",
    "get_llm_manager",
]