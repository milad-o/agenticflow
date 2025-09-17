"""
Azure OpenAI provider implementation.

Provides Azure OpenAI Service integration with enterprise features,
compliance, and dedicated capacity support.
"""

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from .base import AsyncLLMProvider


class AzureOpenAIProvider(AsyncLLMProvider):
    """Azure OpenAI provider implementation."""
    
    @property
    def supports_embeddings(self) -> bool:
        """Azure OpenAI supports embeddings."""
        return True
    
    def _create_llm(self) -> BaseLanguageModel:
        """Create Azure OpenAI LLM instance."""
        kwargs = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
        }
        
        if self.config.api_key:
            kwargs["openai_api_key"] = self.config.api_key.get_secret_value()
        
        if self.config.base_url:
            kwargs["azure_endpoint"] = self.config.base_url
        
        if self.config.max_tokens:
            kwargs["max_tokens"] = self.config.max_tokens
            
        # Azure-specific configuration
        if hasattr(self.config, 'api_version') and self.config.api_version:
            kwargs["openai_api_version"] = self.config.api_version
        else:
            kwargs["openai_api_version"] = "2024-02-01"  # Default API version
            
        if hasattr(self.config, 'deployment_name') and self.config.deployment_name:
            kwargs["deployment_name"] = self.config.deployment_name
        else:
            kwargs["deployment_name"] = self.config.model  # Use model as deployment name by default
        
        return AzureChatOpenAI(**kwargs)
    
    def _create_embeddings(self) -> Embeddings:
        """Create Azure OpenAI embeddings instance."""
        kwargs = {}
        
        if self.config.api_key:
            kwargs["openai_api_key"] = self.config.api_key.get_secret_value()
        
        if self.config.base_url:
            kwargs["azure_endpoint"] = self.config.base_url
            
        # Azure-specific configuration for embeddings
        if hasattr(self.config, 'api_version') and self.config.api_version:
            kwargs["openai_api_version"] = self.config.api_version
        else:
            kwargs["openai_api_version"] = "2024-02-01"  # Default API version
            
        # Use a default embedding model and deployment name if not specified
        model = "text-embedding-3-small"
        if hasattr(self.config, 'embedding_deployment_name') and self.config.embedding_deployment_name:
            kwargs["deployment"] = self.config.embedding_deployment_name
        else:
            kwargs["deployment"] = model  # Use model as deployment name by default
        
        return AzureOpenAIEmbeddings(model=model, **kwargs)