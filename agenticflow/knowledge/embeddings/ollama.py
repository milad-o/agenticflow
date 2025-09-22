from __future__ import annotations

from typing import List, Sequence

import httpx

from .base import EmbeddingClient, Embedding


class OllamaEmbeddingClient(EmbeddingClient):
    """Embedding client for local Ollama server.

    Default base_url: http://localhost:11434
    """

    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url)
        self._checked = False

    async def list_local_models(self) -> list[str]:
        try:
            resp = await self._client.get("/api/tags", timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models") or data.get("data") or []
            names: list[str] = []
            for m in models:
                if isinstance(m, dict):
                    nm = m.get("name") or m.get("model")
                    if isinstance(nm, str):
                        names.append(nm)
            return names
        except Exception:
            return []

    def _normalize(self, name: str) -> str:
        # Strip optional tag suffix ":tag"
        return name.split(":")[0]

    async def is_model_available(self, model: str | None = None) -> bool:
        """Check if the embedding model is available locally via /api/tags."""
        used_model = self._normalize(model or self.model)
        local = [self._normalize(n) for n in await self.list_local_models()]
        return used_model in set(local)

    async def ensure_model_available(self, model: str | None = None) -> None:
        used_model = self._normalize(model or self.model)
        if await self.is_model_available(used_model):
            # Normalize configured model to exact local name if possible
            local = await self.list_local_models()
            for n in local:
                if self._normalize(n) == used_model:
                    self.model = n  # use exact installed name (with tag) for API
                    break
            return
        # Try to auto-select an embedding-like model from local ones
        local = await self.list_local_models()
        candidate = None
        for n in local:
            base = self._normalize(n).lower()
            if "embed" in base or base in {"nomic-embed-text", "all-minilm", "all-minilm-l6-v2"}:
                candidate = n
                break
        if candidate:
            self.model = candidate
            return
        raise RuntimeError(
            f"Ollama model '{used_model}' not found. Pull it with: 'ollama pull {used_model}' and ensure ollama is running."
        )

    async def embed_texts(self, texts: Sequence[str], *, model: str | None = None) -> List[Embedding]:
        used_model = model or self.model
        if not self._checked:
            await self.ensure_model_available(used_model)
            self._checked = True
        results: List[Embedding] = []
        for t in texts:
            resp = await self._client.post("/api/embeddings", json={"model": used_model, "input": t}, timeout=30.0)
            # Some errors return 200 with {"error": "..."}
            data = None
            try:
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                raise RuntimeError(f"Ollama embeddings HTTP error for model '{used_model}': {e}")
            if isinstance(data, dict) and data.get("error"):
                raise RuntimeError(f"Ollama embeddings error: {data.get('error')}")
            vec = None
            if isinstance(data, dict):
                vec = data.get("embedding")
                if vec is None:
                    arr = data.get("data")
                    if isinstance(arr, list) and arr:
                        vec = arr[0].get("embedding")
            if vec is None:
                raise RuntimeError("Invalid Ollama embeddings response: missing 'embedding'")
            results.append(Embedding(vector=list(map(float, vec)), model=used_model, dim=len(vec)))
        return results
