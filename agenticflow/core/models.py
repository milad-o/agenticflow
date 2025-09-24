"""Model and embedding factories for AgenticFlow (dev: Groq or Ollama)."""
from __future__ import annotations

import os
from typing import Optional

from langchain_core.language_models import BaseChatModel

# Groq chat model
try:
    from langchain_groq import ChatGroq  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    ChatGroq = None  # type: ignore

# Ollama chat model and embeddings (prefer dedicated package)
try:
    from langchain_ollama import ChatOllama, OllamaEmbeddings  # type: ignore
except Exception:  # pragma: no cover
    # Fallbacks to community package
    try:
        from langchain_community.chat_models import ChatOllama  # type: ignore
    except Exception:
        try:
            from langchain_community.chat_models.ollama import ChatOllama  # older path
        except Exception:
            ChatOllama = None  # type: ignore
    try:
        from langchain_community.embeddings import OllamaEmbeddings  # type: ignore
    except Exception:
        OllamaEmbeddings = None  # type: ignore


def get_llm_provider() -> str:
    """Return the configured LLM provider for development.
    Supported: 'groq', 'ollama'. Defaults to 'ollama'.
    """
    return os.getenv("AGENTICFLOW_LLM_PROVIDER", "ollama").lower()


def _select_ollama_model(preferred: Optional[str], base_url: str) -> str:
    """Pick an available Ollama model, preferring a requested one if present.
    Falls back to the first available model.
    """
    try:
        from ollama import Client  # type: ignore
        client = Client(host=base_url)
        data = client.list()
        available = [m.get("model") or m.get("name") for m in data.get("models", [])]
        available = [m for m in available if m]
        if not available:
            raise RuntimeError(
                "No Ollama models found. Run 'ollama run <model>' or 'ollama pull <model>' first."
            )
        def contains(name: str) -> bool:
            if name in available:
                return True
            # match prefix before colon tag
            return any(m.startswith(name + ":") for m in available)

        if preferred:
            if contains(preferred):
                # return the exact full name if we can find it
                for m in available:
                    if m == preferred or m.startswith(preferred + ":"):
                        return m

        # Try explicit known good defaults by exact tag first
        for candidate in [
            "qwen2.5:7b",
            "granite3.2:8b",
            "qwen2.5",
            "llama3.1",
            "llama3",
            "phi4",
            "mistral",
            "llama2",
        ]:
            if candidate and contains(candidate):
                # return the best-matching available name
                for m in available:
                    if m == candidate or m.startswith(candidate + ":"):
                        return m
        # Otherwise pick the first available
        return available[0]
    except Exception:
        # If listing fails, just return preferred or a safe default; model may still exist
        return preferred or "llama3.1"


def get_chat_model(model_name: Optional[str] = None, temperature: float = 0.0) -> BaseChatModel:
    """Construct a chat model according to the provider and model name.
    - For Groq, requires GROQ_API_KEY to be set.
    - For Ollama, requires a local Ollama server.
    """
    provider = get_llm_provider()
    if provider == "groq":
        model = model_name or os.getenv("AGENTICFLOW_DEFAULT_MODEL") or "llama-3.1-8b-instant"
        if ChatGroq is None:
            raise RuntimeError("langchain-groq is not installed. Please install it to use Groq.")
        # Reduce retries to avoid long stalls on rate limits
        max_retries = int(os.getenv("AGENTICFLOW_LLM_MAX_RETRIES", "0"))
        return ChatGroq(model=model, temperature=temperature, max_retries=max_retries)

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        preferred = model_name or os.getenv("AGENTICFLOW_DEFAULT_MODEL")
        model = _select_ollama_model(preferred, base_url)
        if ChatOllama is None:
            raise RuntimeError("ChatOllama is unavailable. Ensure langchain-ollama is installed.")
        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url,
            num_ctx=int(os.getenv("AGENTICFLOW_NUM_CTX", "2048")),
            num_predict=int(os.getenv("AGENTICFLOW_NUM_PREDICT", "256")),
        )

    raise ValueError(f"Unsupported AGENTICFLOW_LLM_PROVIDER: {provider}")


def get_ollama_embeddings(model_name: Optional[str] = None):
    """Return an Ollama embeddings instance (dev default).
    Defaults to 'nomic-embed-text'.
    """
    if OllamaEmbeddings is None:
        raise RuntimeError("OllamaEmbeddings unavailable. Ensure langchain-community is installed.")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = model_name or os.getenv("AGENTICFLOW_EMBED_MODEL", "nomic-embed-text")
    return OllamaEmbeddings(model=model, base_url=base_url)
