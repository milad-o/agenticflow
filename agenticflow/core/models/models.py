"""Easy LLM and Embedding integration for AgenticFlow.

Just pass any LangChain LLM or embedding model - plug and play!
"""
from __future__ import annotations

import os
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings

# Popular LLM providers
try:
    from langchain_groq import ChatGroq  # type: ignore
except ImportError:
    ChatGroq = None  # type: ignore

try:
    from langchain_openai import ChatOpenAI  # type: ignore
except ImportError:
    ChatOpenAI = None  # type: ignore

try:
    from langchain_anthropic import ChatAnthropic  # type: ignore
except ImportError:
    ChatAnthropic = None  # type: ignore

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

# Popular embedding providers
try:
    from langchain_openai import OpenAIEmbeddings  # type: ignore
except ImportError:
    OpenAIEmbeddings = None  # type: ignore

try:
    from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore
except ImportError:
    HuggingFaceEmbeddings = None  # type: ignore

try:
    from langchain_cohere import CohereEmbeddings  # type: ignore
except ImportError:
    CohereEmbeddings = None  # type: ignore


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


# Easy embedding helper functions - just plug and play!
def get_embeddings(provider: str = "auto", **kwargs) -> Embeddings:
    """
    Get embeddings from any provider - super easy!

    Args:
        provider: 'openai', 'huggingface', 'ollama', 'cohere', or 'auto'
        **kwargs: Provider-specific arguments

    Returns:
        Any LangChain embeddings instance

    Examples:
        # OpenAI (requires OPENAI_API_KEY)
        embeddings = get_embeddings("openai")

        # HuggingFace (free, runs locally)
        embeddings = get_embeddings("huggingface", model_name="all-MiniLM-L6-v2")

        # Ollama (free, local)
        embeddings = get_embeddings("ollama", model="nomic-embed-text")

        # Auto-detect (tries OpenAI -> HuggingFace -> Ollama)
        embeddings = get_embeddings("auto")
    """
    if provider == "auto":
        # Try providers in order of preference
        if os.getenv("OPENAI_API_KEY") and OpenAIEmbeddings:
            return OpenAIEmbeddings(**kwargs)
        elif HuggingFaceEmbeddings:
            return HuggingFaceEmbeddings(
                model_name=kwargs.get("model_name", "all-MiniLM-L6-v2"),
                **{k: v for k, v in kwargs.items() if k != "model_name"}
            )
        elif OllamaEmbeddings:
            return get_ollama_embeddings(kwargs.get("model_name"))
        else:
            raise RuntimeError("No embedding provider available. Install langchain-openai, langchain-huggingface, or langchain-community")

    elif provider == "openai":
        if not OpenAIEmbeddings:
            raise RuntimeError("OpenAI embeddings not available. Install: pip install langchain-openai")
        return OpenAIEmbeddings(**kwargs)

    elif provider == "huggingface":
        if not HuggingFaceEmbeddings:
            raise RuntimeError("HuggingFace embeddings not available. Install: pip install langchain-huggingface")
        return HuggingFaceEmbeddings(
            model_name=kwargs.get("model_name", "all-MiniLM-L6-v2"),
            **{k: v for k, v in kwargs.items() if k != "model_name"}
        )

    elif provider == "ollama":
        return get_ollama_embeddings(kwargs.get("model_name"))

    elif provider == "cohere":
        if not CohereEmbeddings:
            raise RuntimeError("Cohere embeddings not available. Install: pip install langchain-cohere")
        return CohereEmbeddings(**kwargs)

    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


def get_easy_llm(provider: str = "auto", **kwargs) -> BaseChatModel:
    """
    Get any LLM - super easy!

    Args:
        provider: 'groq', 'openai', 'anthropic', 'ollama', or 'auto'
        **kwargs: Provider-specific arguments

    Returns:
        Any LangChain chat model

    Examples:
        # Groq (fast and free with API key)
        llm = get_easy_llm("groq", model="llama-3.2-90b-text-preview")

        # OpenAI (requires API key)
        llm = get_easy_llm("openai", model="gpt-4o-mini")

        # Ollama (free, local)
        llm = get_easy_llm("ollama", model="llama3.2:latest")

        # Auto-detect (tries in order: Groq -> OpenAI -> Ollama)
        llm = get_easy_llm("auto")
    """
    if provider == "auto":
        # Try providers in order of preference
        if os.getenv("GROQ_API_KEY") and ChatGroq:
            return ChatGroq(
                model=kwargs.get("model", "llama-3.3-70b-versatile"),
                temperature=kwargs.get("temperature", 0.1),
                **{k: v for k, v in kwargs.items() if k not in ["model", "temperature"]}
            )
        elif os.getenv("OPENAI_API_KEY") and ChatOpenAI:
            return ChatOpenAI(
                model=kwargs.get("model", "gpt-4o-mini"),
                temperature=kwargs.get("temperature", 0.1),
                **{k: v for k, v in kwargs.items() if k not in ["model", "temperature"]}
            )
        elif ChatOllama:
            return ChatOllama(
                model=kwargs.get("model", "llama3.2:latest"),
                temperature=kwargs.get("temperature", 0.1),
                **{k: v for k, v in kwargs.items() if k not in ["model", "temperature"]}
            )
        else:
            raise RuntimeError("No LLM provider available. Set API keys or install Ollama")

    elif provider == "groq":
        if not ChatGroq:
            raise RuntimeError("Groq not available. Install: pip install langchain-groq")
        return ChatGroq(**kwargs)

    elif provider == "openai":
        if not ChatOpenAI:
            raise RuntimeError("OpenAI not available. Install: pip install langchain-openai")
        return ChatOpenAI(**kwargs)

    elif provider == "anthropic":
        if not ChatAnthropic:
            raise RuntimeError("Anthropic not available. Install: pip install langchain-anthropic")
        return ChatAnthropic(**kwargs)

    elif provider == "ollama":
        if not ChatOllama:
            raise RuntimeError("Ollama not available. Install: pip install langchain-ollama")
        return ChatOllama(**kwargs)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
