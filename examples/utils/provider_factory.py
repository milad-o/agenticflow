# Dev-only provider factory (kept out of the core framework).
from __future__ import annotations

import os


def create_llm_from_env():
    provider = os.environ.get("AGENTICFLOW_LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        from agenticflow.tools.external.llm_groq import GroqLLMClient
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for groq provider")
        model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
        base_url = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        return GroqLLMClient(api_key=api_key, model=model, base_url=base_url)
    if provider in ("azure", "azure-openai", "azureopenai"):
        from agenticflow.tools.external.llm_azure_openai import AzureOpenAILLMClient
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        if not (endpoint and api_key and deployment):
            raise ValueError("AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT are required for azure provider")
        return AzureOpenAILLMClient(endpoint=endpoint, api_key=api_key, deployment=deployment, api_version=api_version)
    if provider in ("ollama", "ollama-llm"):
        from agenticflow.tools.external.llm_ollama import OllamaLLMClient
        model = os.environ.get("OLLAMA_LLM_MODEL", "qwen2.5:7b")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaLLMClient(model=model, base_url=base_url)
    if provider in ("noop",):
        from agenticflow.tools.external.llm import NoopLLMClient
        return NoopLLMClient()
    raise ValueError(f"Unsupported LLM provider: {provider}")


def create_embedding_from_env():
    provider = os.environ.get("AGENTICFLOW_EMBED_PROVIDER", "ollama").lower()
    if provider == "ollama":
        from agenticflow.knowledge.embeddings.ollama import OllamaEmbeddingClient
        model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaEmbeddingClient(model=model, base_url=base_url)
    if provider in ("hf", "huggingface"):
        from agenticflow.knowledge.embeddings.hf import HFEmbeddingClient
        model_name = os.environ.get("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        return HFEmbeddingClient(model_name=model_name)
    raise ValueError(f"Unsupported embedding provider: {provider}")
