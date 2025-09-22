from __future__ import annotations

from typing import Any, Dict, Sequence

import httpx

from .llm import LLMClient, LLMResult


class GroqLLMClient(LLMClient):
    """LLM client for Groq (OpenAI-compatible API).

    Expects GROQ_API_KEY to be provided by the caller, not read here.
    """

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.groq.com/openai/v1") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    async def generate(self, prompt: str, *, model: str | None = None, **params: Any) -> LLMResult:
        payload = {
            "model": model or self.model,
            "messages": [{"role": "user", "content": prompt}],
            **({k: v for k, v in params.items() if v is not None})
        }
        resp = await self._client.post("/chat/completions", json=payload, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResult(text=text, model=payload["model"], tokens_prompt=usage.get("prompt_tokens", 0), tokens_completion=usage.get("completion_tokens", 0), metadata={"id": data.get("id")})

    async def chat(self, messages: Sequence[Dict[str, str]], *, model: str | None = None, **params: Any) -> LLMResult:
        payload = {
            "model": model or self.model,
            "messages": list(messages),
            **({k: v for k, v in params.items() if v is not None})
        }
        resp = await self._client.post("/chat/completions", json=payload, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResult(text=text, model=payload["model"], tokens_prompt=usage.get("prompt_tokens", 0), tokens_completion=usage.get("completion_tokens", 0), metadata={"id": data.get("id")})
