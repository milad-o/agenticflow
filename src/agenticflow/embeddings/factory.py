"""
Embedding Provider Factory
==========================

Factory functions for easy creation and configuration of embedding providers.
"""

import os
from typing import Any, Dict, Optional, Union

from .base import (
    AsyncEmbeddingProvider,
    EmbeddingProvider,
    EmbeddingConfig,
    EmbeddingTaskType,
    EmbeddingProviderNotAvailableError,
)


def create_embedding_provider(
    provider: Union[str, EmbeddingProvider],
    model: str,
    api_key: Optional[str] = None,
    **kwargs
) -> AsyncEmbeddingProvider:
    """
    Create an embedding provider using factory pattern.
    
    Args:
        provider: Provider name ('openai', 'huggingface', 'cohere', etc.)
        model: Model name/identifier
        api_key: API key for cloud providers
        **kwargs: Additional configuration options
        
    Returns:
        Configured embedding provider
        
    Raises:
        EmbeddingProviderNotAvailableError: If provider is not available
        ValueError: If provider is not supported
    """
    
    # Normalize provider name
    if isinstance(provider, str):
        provider = provider.lower()
        provider_map = {
            'openai': EmbeddingProvider.OPENAI,
            'azure_openai': EmbeddingProvider.AZURE_OPENAI,
            'huggingface': EmbeddingProvider.HUGGINGFACE,
            'cohere': EmbeddingProvider.COHERE,
            'google': EmbeddingProvider.GOOGLE,
            'anthropic': EmbeddingProvider.ANTHROPIC,
            'ollama': EmbeddingProvider.OLLAMA,
            'local': EmbeddingProvider.LOCAL,
        }
        if provider not in provider_map:
            raise ValueError(f"Unsupported provider: {provider}. Supported: {list(provider_map.keys())}")
        provider_enum = provider_map[provider]
    else:
        provider_enum = provider
    
    # Create provider based on type
    if provider_enum == EmbeddingProvider.OPENAI:
        from .openai import create_openai_embedding_provider
        return create_openai_embedding_provider(
            model=model,
            api_key=api_key,
            **kwargs
        )
    
    elif provider_enum == EmbeddingProvider.HUGGINGFACE:
        from .huggingface import create_huggingface_embedding_provider
        return create_huggingface_embedding_provider(
            model=model,
            **kwargs
        )
    
    elif provider_enum == EmbeddingProvider.COHERE:
        from .cohere import create_cohere_embedding_provider
        return create_cohere_embedding_provider(
            model=model,
            api_key=api_key,
            **kwargs
        )
    
    elif provider_enum == EmbeddingProvider.OLLAMA:
        from .ollama import create_ollama_embedding_provider
        return create_ollama_embedding_provider(
            model=model,
            **kwargs
        )
    
    else:
        raise EmbeddingProviderNotAvailableError(
            f"Provider {provider_enum.value} not yet implemented"
        )


def get_default_model(provider: Union[str, EmbeddingProvider]) -> str:
    """
    Get the default model for a provider.
    
    Args:
        provider: Provider name or enum
        
    Returns:
        Default model name
    """
    if isinstance(provider, str):
        provider = provider.lower()
    
    defaults = {
        'openai': 'text-embedding-3-small',
        EmbeddingProvider.OPENAI: 'text-embedding-3-small',
        'huggingface': 'sentence-transformers/all-MiniLM-L6-v2',
        EmbeddingProvider.HUGGINGFACE: 'sentence-transformers/all-MiniLM-L6-v2',
        'cohere': 'embed-english-light-v3.0',
        EmbeddingProvider.COHERE: 'embed-english-light-v3.0',
        'ollama': 'nomic-embed-text',
        EmbeddingProvider.OLLAMA: 'nomic-embed-text',
    }
    
    return defaults.get(provider, 'unknown')


def auto_select_provider(
    preferred_providers: Optional[list] = None,
    requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Automatically select the best available embedding provider.
    
    Args:
        preferred_providers: List of preferred providers in order
        requirements: Requirements dict (e.g., {'local_only': True, 'min_dimension': 512})
        
    Returns:
        Dict with 'provider', 'model', and 'config' keys
        
    Raises:
        EmbeddingProviderNotAvailableError: If no suitable provider is found
    """
    
    if preferred_providers is None:
        # Default preference order
        preferred_providers = ['huggingface', 'ollama', 'openai', 'cohere']
    
    if requirements is None:
        requirements = {}
    
    local_only = requirements.get('local_only', False)
    min_dimension = requirements.get('min_dimension', 0)
    max_cost = requirements.get('max_cost_per_1k', float('inf'))
    
    # Check each provider in preference order
    for provider_name in preferred_providers:
        try:
            provider_name = provider_name.lower()
            
            # Skip API providers if local_only is required
            if local_only and provider_name in ['openai', 'cohere', 'google', 'anthropic']:
                continue
            
            # Check if HuggingFace libraries are available
            if provider_name == 'huggingface':
                try:
                    import sentence_transformers
                except ImportError:
                    try:
                        import transformers
                    except ImportError:
                        continue
            
            # Check if API key is available for cloud providers
            if provider_name == 'openai' and not os.getenv('OPENAI_API_KEY'):
                continue
            if provider_name == 'cohere' and not (os.getenv('COHERE_API_KEY') or os.getenv('CO_API_KEY')):
                continue
            
            # Check if Ollama is available
            if provider_name == 'ollama':
                try:
                    import httpx
                    with httpx.Client(timeout=2.0) as client:
                        response = client.get("http://localhost:11434/api/tags")
                        if response.status_code != 200:
                            continue
                except Exception:
                    continue
            
            # Get default model and check requirements
            model = get_default_model(provider_name)
            
            # For now, return the first viable option
            # In a more sophisticated version, we'd check model specs against requirements
            return {
                'provider': provider_name,
                'model': model,
                'config': {}
            }
            
        except Exception:
            continue
    
    raise EmbeddingProviderNotAvailableError(
        "No suitable embedding provider found. "
        "Install sentence-transformers for local embeddings or set API keys for cloud providers."
    )


def create_auto_provider(
    preferred_providers: Optional[list] = None,
    requirements: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AsyncEmbeddingProvider:
    """
    Automatically create the best available embedding provider.
    
    Args:
        preferred_providers: List of preferred providers in order
        requirements: Requirements dict
        **kwargs: Additional configuration options
        
    Returns:
        Configured embedding provider
    """
    
    selection = auto_select_provider(preferred_providers, requirements)
    
    return create_embedding_provider(
        provider=selection['provider'],
        model=selection['model'],
        **{**selection['config'], **kwargs}
    )


def list_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    List all available embedding providers and their status.
    
    Returns:
        Dict mapping provider names to availability info
    """
    
    providers = {}
    
    # OpenAI
    providers['openai'] = {
        'available': bool(os.getenv('OPENAI_API_KEY')),
        'reason': 'API key required' if not os.getenv('OPENAI_API_KEY') else 'Available',
        'local': False,
        'default_model': get_default_model('openai'),
    }
    
    # HuggingFace
    try:
        import sentence_transformers
        hf_available = True
        hf_reason = 'Available'
    except ImportError:
        try:
            import transformers
            hf_available = True
            hf_reason = 'Available (transformers only)'
        except ImportError:
            hf_available = False
            hf_reason = 'Install sentence-transformers or transformers'
    
    providers['huggingface'] = {
        'available': hf_available,
        'reason': hf_reason,
        'local': True,
        'default_model': get_default_model('huggingface'),
    }
    
    # Cohere
    cohere_key = os.getenv('COHERE_API_KEY') or os.getenv('CO_API_KEY')
    providers['cohere'] = {
        'available': bool(cohere_key),
        'reason': 'API key required' if not cohere_key else 'Available',
        'local': False,
        'default_model': get_default_model('cohere'),
    }
    
    # Ollama - simplified check without async
    try:
        import httpx
        # Try a simple synchronous check
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get("http://localhost:11434/api/tags")
                ollama_available = response.status_code == 200
                ollama_reason = 'Available' if ollama_available else 'Ollama server not running'
        except Exception:
            ollama_available = False
            ollama_reason = 'Ollama server not running'
    except ImportError:
        ollama_available = False
        ollama_reason = 'httpx not available'
    
    providers['ollama'] = {
        'available': ollama_available,
        'reason': ollama_reason,
        'local': True,
        'default_model': get_default_model('ollama'),
    }
    
    return providers
