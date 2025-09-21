from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class LLMResult:
    text: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, *, model: str | None = None, **params: Any) -> LLMResult: ...

    @abstractmethod
    async def chat(self, messages: Sequence[Dict[str, str]], *, model: str | None = None, **params: Any) -> LLMResult: ...


class NoopLLMClient(LLMClient):
    async def generate(self, prompt: str, *, model: str | None = None, **params: Any) -> LLMResult:
        return LLMResult(text=f"echo: {prompt}", model=model or "noop")

    async def chat(self, messages: Sequence[Dict[str, str]], *, model: str | None = None, **params: Any) -> LLMResult:
        content = messages[-1]["content"] if messages else ""
        return LLMResult(text=f"echo: {content}", model=model or "noop")
