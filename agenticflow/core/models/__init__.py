"""
Core Models

Easy LLM and embedding setup - just plug and play!
"""

from .models import (
    get_chat_model,
    get_easy_llm, get_embeddings,
    get_ollama_embeddings
)

from enum import Enum


class ModelProvider(Enum):
    """Available model providers."""
    GROQ = "groq"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    AUTO = "auto"


__all__ = [
    # Original functions
    "get_chat_model",
    "get_ollama_embeddings",

    # Easy helper functions - just plug and play!
    "get_easy_llm",
    "get_embeddings",

    # Enum
    "ModelProvider"
]