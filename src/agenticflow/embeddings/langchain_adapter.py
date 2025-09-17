"""
LangChain Embeddings Adapter
===========================
Seamless integration with LangChain embedding models for AgenticFlow vector stores.
"""

from typing import Any, Dict, List, Optional
import asyncio
import structlog

from langchain_core.embeddings import Embeddings as LangChainEmbeddings

from .base import AsyncEmbeddingProvider, EmbeddingProvider, EmbeddingConfig, EmbeddingTaskType

logger = structlog.get_logger(__name__)


class LangChainEmbeddingsAdapter(AsyncEmbeddingProvider):
    """
    Adapter to use any LangChain embeddings model with our unified interface.
    
    Supports all LangChain embedding models including:
    - OpenAI embeddings
    - HuggingFace embeddings  
    - Cohere embeddings
    - SentenceTransformers
    - Azure OpenAI embeddings
    - And many more!
    """
    
    def __init__(
        self,
        langchain_embeddings: LangChainEmbeddings,
        config: Optional[EmbeddingConfig] = None
    ):
        """
        Initialize with a LangChain embeddings model.
        
        Args:
            langchain_embeddings: Any LangChain Embeddings instance
            config: Optional embedding config
        """
        # Create default config if none provided
        if config is None:
            config = EmbeddingConfig(
                provider=EmbeddingProvider.CUSTOM,
                model=getattr(langchain_embeddings, 'model', 'langchain_model')
            )
        
        super().__init__(config)
        self.langchain_embeddings = langchain_embeddings
        
        self.logger.debug(f"Initialized LangChain embeddings adapter: {type(langchain_embeddings).__name__}")
    
    @property
    def supports_batch(self) -> bool:
        """Check if the provider supports batch embedding."""
        return hasattr(self.langchain_embeddings, 'embed_documents') or hasattr(self.langchain_embeddings, 'aembed_documents')
    
    @property
    def max_batch_size(self) -> int:
        """Get maximum batch size for this provider."""
        return self.config.batch_size
    
    @property
    def max_text_length(self) -> int:
        """Get maximum text length for this provider."""
        # Default for most LangChain models, can be overridden
        return 8192 * 4  # chars
    
    async def _embed_texts_impl(
        self, 
        texts: List[str],
        task_type: Optional[EmbeddingTaskType] = None
    ) -> List[List[float]]:
        """Implementation-specific embedding method."""
        if not texts:
            return []
        
        try:
            if len(texts) == 1:
                # Single text - use query embedding
                text = texts[0]
                if hasattr(self.langchain_embeddings, 'aembed_query'):
                    embedding = await self.langchain_embeddings.aembed_query(text)
                else:
                    # Fallback to sync embedding in thread pool
                    loop = asyncio.get_event_loop()
                    embedding = await loop.run_in_executor(
                        None,
                        self.langchain_embeddings.embed_query,
                        text
                    )
                return [embedding]
            else:
                # Multiple texts - use document embedding
                if hasattr(self.langchain_embeddings, 'aembed_documents'):
                    embeddings = await self.langchain_embeddings.aembed_documents(texts)
                else:
                    # Fallback to sync batch embedding in thread pool
                    loop = asyncio.get_event_loop()
                    embeddings = await loop.run_in_executor(
                        None,
                        self.langchain_embeddings.embed_documents,
                        texts
                    )
                return embeddings
        
        except Exception as e:
            self.logger.error(f"Failed to embed texts: {e}")
            raise
    
    
    async def get_dimension(self) -> int:
        """
        Get the embedding dimension.
        
        Returns:
            Embedding vector dimension
        """
        if self._dimension is not None:
            return self._dimension
        
        if self.config.dimensions is not None:
            self._dimension = self.config.dimensions
            return self._dimension
        
        # Determine dimension by embedding a test string
        try:
            test_embeddings = await self._embed_texts_impl(["test"])
            self._dimension = len(test_embeddings[0])
            return self._dimension
        
        except Exception as e:
            self.logger.error(f"Failed to determine embedding dimension: {e}")
            # Default fallback dimension
            self._dimension = 1536  # Common dimension for many models
            return self._dimension
    
    async def is_available(self) -> bool:
        """
        Check if the embedding model is available.
        
        Returns:
            True if model is available
        """
        try:
            # Try to embed a simple test string
            await self._embed_texts_impl(["test"])
            return True
        except Exception as e:
            self.logger.warning(f"LangChain embeddings not available: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.
        
        Returns:
            Dictionary with model information
        """
        info = {
            'provider': EmbeddingProvider.CUSTOM.value,
            'adapter_type': type(self.langchain_embeddings).__name__,
            'dimension': self._dimension,
            'model': self.config.model,
            'supports_batch': self.supports_batch,
            'max_batch_size': self.max_batch_size,
            'max_text_length': self.max_text_length,
            'local_model': False,  # Most LangChain models are API-based
            'cost_per_1k_tokens': 0.0,  # Unknown, varies by provider
        }
        
        # Add additional info from the LangChain model if available
        if hasattr(self.langchain_embeddings, 'model'):
            info['langchain_model'] = self.langchain_embeddings.model
        
        if hasattr(self.langchain_embeddings, 'model_name'):
            info['langchain_model_name'] = self.langchain_embeddings.model_name
        
        return info


# Convenience functions for common LangChain embedding models

def create_openai_adapter(
    api_key: Optional[str] = None,
    model: str = "text-embedding-ada-002",
    **kwargs
) -> LangChainEmbeddingsAdapter:
    """
    Create adapter for OpenAI embeddings.
    
    Args:
        api_key: OpenAI API key (can be None to use environment variable)
        model: OpenAI embedding model name
        **kwargs: Additional arguments for OpenAI embeddings
        
    Returns:
        LangChainEmbeddingsAdapter instance
    """
    try:
        from langchain_openai import OpenAIEmbeddings
        
        openai_embeddings = OpenAIEmbeddings(
            openai_api_key=api_key,
            model=model,
            **kwargs
        )
        
        config = EmbeddingConfig(
            model_name=model,
            provider='openai'
        )
        
        return LangChainEmbeddingsAdapter(openai_embeddings, config)
    
    except ImportError:
        raise ImportError("langchain-openai not installed. Install with: pip install langchain-openai")


def create_huggingface_adapter(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    **kwargs
) -> LangChainEmbeddingsAdapter:
    """
    Create adapter for HuggingFace embeddings.
    
    Args:
        model_name: HuggingFace model name
        **kwargs: Additional arguments for HuggingFace embeddings
        
    Returns:
        LangChainEmbeddingsAdapter instance
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        
        hf_embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            **kwargs
        )
        
        config = EmbeddingConfig(
            model_name=model_name,
            provider='huggingface'
        )
        
        return LangChainEmbeddingsAdapter(hf_embeddings, config)
    
    except ImportError:
        raise ImportError("langchain-huggingface not installed. Install with: pip install langchain-huggingface")


def create_cohere_adapter(
    api_key: Optional[str] = None,
    model: str = "embed-english-v2.0",
    **kwargs
) -> LangChainEmbeddingsAdapter:
    """
    Create adapter for Cohere embeddings.
    
    Args:
        api_key: Cohere API key (can be None to use environment variable)
        model: Cohere embedding model name
        **kwargs: Additional arguments for Cohere embeddings
        
    Returns:
        LangChainEmbeddingsAdapter instance
    """
    try:
        from langchain_cohere import CohereEmbeddings
        
        cohere_embeddings = CohereEmbeddings(
            cohere_api_key=api_key,
            model=model,
            **kwargs
        )
        
        config = EmbeddingConfig(
            model_name=model,
            provider='cohere'
        )
        
        return LangChainEmbeddingsAdapter(cohere_embeddings, config)
    
    except ImportError:
        raise ImportError("langchain-cohere not installed. Install with: pip install langchain-cohere")


def create_azure_openai_adapter(
    azure_endpoint: str,
    api_key: Optional[str] = None,
    api_version: str = "2024-02-01",
    model: str = "text-embedding-ada-002",
    **kwargs
) -> LangChainEmbeddingsAdapter:
    """
    Create adapter for Azure OpenAI embeddings.
    
    Args:
        azure_endpoint: Azure OpenAI endpoint URL
        api_key: Azure OpenAI API key (can be None to use environment variable)
        api_version: Azure API version
        model: Azure OpenAI embedding model deployment name
        **kwargs: Additional arguments for Azure OpenAI embeddings
        
    Returns:
        LangChainEmbeddingsAdapter instance
    """
    try:
        from langchain_openai import AzureOpenAIEmbeddings
        
        azure_embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
            azure_deployment=model,
            **kwargs
        )
        
        config = EmbeddingConfig(
            model_name=f"azure-{model}",
            provider='azure_openai'
        )
        
        return LangChainEmbeddingsAdapter(azure_embeddings, config)
    
    except ImportError:
        raise ImportError("langchain-openai not installed. Install with: pip install langchain-openai")


def create_sentence_transformers_adapter(
    model_name: str = "all-MiniLM-L6-v2",
    cache_folder: Optional[str] = None,
    **kwargs
) -> LangChainEmbeddingsAdapter:
    """
    Create adapter for SentenceTransformers embeddings.
    
    Args:
        model_name: SentenceTransformers model name
        cache_folder: Cache folder for model downloads
        **kwargs: Additional arguments for SentenceTransformers
        
    Returns:
        LangChainEmbeddingsAdapter instance
    """
    try:
        from langchain_community.embeddings import SentenceTransformerEmbeddings
        
        st_embeddings = SentenceTransformerEmbeddings(
            model_name=model_name,
            cache_folder=cache_folder,
            **kwargs
        )
        
        config = EmbeddingConfig(
            model_name=model_name,
            provider='sentence_transformers'
        )
        
        return LangChainEmbeddingsAdapter(st_embeddings, config)
    
    except ImportError:
        raise ImportError("langchain-community and sentence-transformers required. Install with: pip install langchain-community sentence-transformers")


# Generic adapter creation function

def create_langchain_embeddings_adapter(
    langchain_embeddings: LangChainEmbeddings,
    model_name: Optional[str] = None,
    provider: str = 'langchain'
) -> LangChainEmbeddingsAdapter:
    """
    Create a generic LangChain embeddings adapter.
    
    Args:
        langchain_embeddings: Any LangChain Embeddings instance
        model_name: Optional model name override
        provider: Provider name for identification
        
    Returns:
        LangChainEmbeddingsAdapter instance
    """
    if model_name is None:
        model_name = getattr(langchain_embeddings, 'model', 'unknown_model')
    
    config = EmbeddingConfig(
        model_name=model_name,
        provider=provider
    )
    
    return LangChainEmbeddingsAdapter(langchain_embeddings, config)