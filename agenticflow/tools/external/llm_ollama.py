from __future__ import annotations

from typing import Any, Dict, Sequence

import httpx

from .llm import LLMClient, LLMResult


class OllamaLLMClient(LLMClient):
    """Dev-only LLM client for local Ollama server.

    Uses /api/generate for simple prompt completion and /api/chat for chat-style.
    """

    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url)

    async def generate(self, prompt: str, *, model: str | None = None, **params: Any) -> LLMResult:
        used_model = model or self.model
        payload = {"model": used_model, "prompt": prompt, "stream": False}
        # Pass through params such as temperature, top_p if provided
        payload.update({k: v for k, v in params.items() if v is not None})
        resp = await self._client.post("/api/generate", json=payload, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("response") or data.get("message", {}).get("content") or ""
        return LLMResult(text=text, model=used_model)

    async def chat(self, messages: Sequence[Dict[str, str]], *, model: str | None = None, **params: Any) -> LLMResult:
        used_model = model or self.model
        payload = {"model": used_model, "messages": list(messages), "stream": False}
        payload.update({k: v for k, v in params.items() if v is not None})
        resp = await self._client.post("/api/chat", json=payload, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()
        # Ollama chat may return "message": {"content": ...}
        text = ""
        if isinstance(data, dict):
            msg = data.get("message")
            if isinstance(msg, dict):
                text = msg.get("content", "")
            else:
                # Fallback to a 'response' field if present
                text = data.get("response", "")
        return LLMResult(text=text, model=used_model)
