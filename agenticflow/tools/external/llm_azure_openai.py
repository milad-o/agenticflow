from __future__ import annotations

from typing import Any, Dict, Sequence

import httpx

from .llm import LLMClient, LLMResult


class AzureOpenAILLMClient(LLMClient):
    """LLM client for Azure OpenAI Chat Completions API.

    endpoint: e.g., https://YOUR_RESOURCE.openai.azure.com
    deployment: the model deployment name in Azure OpenAI
    api_version: e.g., 2024-02-15-preview
    """

    def __init__(self, endpoint: str, api_key: str, deployment: str, api_version: str = "2024-02-15-preview") -> None:
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment = deployment
        self.api_version = api_version
        self._client = httpx.AsyncClient(headers={
            "api-key": self.api_key,
            "Content-Type": "application/json",
        })

    def _url(self) -> str:
        return f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"

    async def generate(self, prompt: str, *, model: str | None = None, **params: Any) -> LLMResult:
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            **({k: v for k, v in params.items() if v is not None})
        }
        resp = await self._client.post(self._url(), json=payload, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResult(text=text, model=self.deployment, tokens_prompt=usage.get("prompt_tokens", 0), tokens_completion=usage.get("completion_tokens", 0), metadata={"id": data.get("id")})

    async def chat(self, messages: Sequence[Dict[str, str]], *, model: str | None = None, **params: Any) -> LLMResult:
        payload = {
            "messages": list(messages),
            **({k: v for k, v in params.items() if v is not None})
        }
        resp = await self._client.post(self._url(), json=payload, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResult(text=text, model=self.deployment, tokens_prompt=usage.get("prompt_tokens", 0), tokens_completion=usage.get("completion_tokens", 0), metadata={"id": data.get("id")})
