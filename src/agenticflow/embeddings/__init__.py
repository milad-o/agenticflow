"""Embeddings integration for AgenticFlow."""

# Core components
from .base import (
    EmbeddingProvider, 
    EmbeddingConfig, 
    EmbeddingTaskType,
    AsyncEmbeddingProvider,
    EmbeddingMetrics,
    AgenticFlowEmbeddingError,
    EmbeddingProviderNotAvailableError,
    EmbeddingModelNotFoundError,
    EmbeddingDimensionMismatchError,
    EmbeddingRateLimitError
)

# Direct provider implementations
try:
    from .openai import OpenAIEmbeddingProvider, create_openai_embedding_provider
except ImportError:
    OpenAIEmbeddingProvider = None
    create_openai_embedding_provider = None

try:
    from .huggingface import HuggingFaceEmbeddingProvider, create_huggingface_embedding_provider
except ImportError:
    HuggingFaceEmbeddingProvider = None
    create_huggingface_embedding_provider = None

try:
    from .cohere import CohereEmbeddingProvider, create_cohere_embedding_provider
except ImportError:
    CohereEmbeddingProvider = None
    create_cohere_embedding_provider = None

try:
    from .ollama import OllamaEmbeddingProvider, create_ollama_embedding_provider
except ImportError:
    OllamaEmbeddingProvider = None
    create_ollama_embedding_provider = None

# Factory functions
from .factory import (
    create_embedding_provider,
    get_default_model,
    auto_select_provider,
    create_auto_provider,
    list_available_providers,
)

# LangChain integration (if available)
try:
    from .langchain_adapter import (
        LangChainEmbeddingsAdapter,
        create_langchain_embeddings_adapter,
        create_openai_adapter,
        create_huggingface_adapter,
        create_cohere_adapter,
        create_azure_openai_adapter,
        create_sentence_transformers_adapter
    )
except ImportError:
    LangChainEmbeddingsAdapter = None
    create_langchain_embeddings_adapter = None
    create_openai_adapter = None
    create_huggingface_adapter = None
    create_cohere_adapter = None
    create_azure_openai_adapter = None
    create_sentence_transformers_adapter = None

__all__ = [
    # Core components
    'EmbeddingProvider',
    'EmbeddingConfig',
    'EmbeddingTaskType',
    'AsyncEmbeddingProvider',
    'EmbeddingMetrics',
    'AgenticFlowEmbeddingError',
    'EmbeddingProviderNotAvailableError',
    'EmbeddingModelNotFoundError',
    'EmbeddingDimensionMismatchError',
    'EmbeddingRateLimitError',
    
    # Direct providers
    'OpenAIEmbeddingProvider',
    'create_openai_embedding_provider',
    'HuggingFaceEmbeddingProvider',
    'create_huggingface_embedding_provider',
    'CohereEmbeddingProvider',
    'create_cohere_embedding_provider',
    'OllamaEmbeddingProvider',
    'create_ollama_embedding_provider',
    
    # Factory functions
    'create_embedding_provider',
    'get_default_model',
    'auto_select_provider',
    'create_auto_provider',
    'list_available_providers',
    
    # LangChain integration
    'LangChainEmbeddingsAdapter',
    'create_langchain_embeddings_adapter',
    'create_openai_adapter',
    'create_huggingface_adapter',
    'create_cohere_adapter',
    'create_azure_openai_adapter',
    'create_sentence_transformers_adapter'
]
