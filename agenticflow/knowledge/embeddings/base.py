from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Sequence

from ..types import Embedding


class EmbeddingClient(ABC):
    @abstractmethod
    async def embed_texts(self, texts: Sequence[str], *, model: str | None = None) -> List[Embedding]:
        ...


class NoopEmbeddingClient(EmbeddingClient):
    async def embed_texts(self, texts: Sequence[str], *, model: str | None = None) -> List[Embedding]:
        # Deterministic pseudo-embeddings based on length; useful for tests
        return [Embedding(vector=[float(len(t))], model=model or "noop", dim=1) for t in texts]
