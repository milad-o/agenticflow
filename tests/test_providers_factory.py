import os
import pytest

from examples.utils.provider_factory import create_llm_from_env, create_embedding_from_env
from agenticflow.tools.external.llm_groq import GroqLLMClient
from agenticflow.knowledge.embeddings.ollama import OllamaEmbeddingClient


def test_factory_creates_groq_and_ollama(monkeypatch):
    monkeypatch.setenv("AGENTICFLOW_LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")

    llm = create_llm_from_env()
    assert isinstance(llm, GroqLLMClient)

    monkeypatch.setenv("AGENTICFLOW_EMBED_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")

    emb = create_embedding_from_env()
    assert isinstance(emb, OllamaEmbeddingClient)
