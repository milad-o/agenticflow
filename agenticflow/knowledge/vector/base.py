from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional, Sequence

from ..types import Document, Embedding, ScoredDocument


class VectorIndex(ABC):
    @abstractmethod
    async def upsert(self, documents: Iterable[Document], embeddings: Iterable[Embedding]) -> None: ...

    @abstractmethod
    async def delete(self, ids: Sequence[str]) -> None: ...

    @abstractmethod
    async def query_by_vector(self, vector: Sequence[float], k: int = 5, *, filters: Optional[Dict] = None) -> List[ScoredDocument]: ...


class InMemoryVectorIndex(VectorIndex):
    def __init__(self) -> None:
        self._store: Dict[str, tuple[Document, List[float]]] = {}

    async def upsert(self, documents: Iterable[Document], embeddings: Iterable[Embedding]) -> None:
        for doc, emb in zip(documents, embeddings):
            self._store[doc.id] = (doc, emb.vector)

    async def delete(self, ids: Sequence[str]) -> None:
        for i in ids:
            self._store.pop(i, None)

    async def query_by_vector(self, vector: Sequence[float], k: int = 5, *, filters: Optional[Dict] = None) -> List[ScoredDocument]:
        # Simple cosine similarity for 1D or nD vectors
        import math

        def cos(a: Sequence[float], b: Sequence[float]) -> float:
            dot = sum(x*y for x, y in zip(a, b))
            na = math.sqrt(sum(x*x for x in a))
            nb = math.sqrt(sum(y*y for y in b))
            if na == 0 or nb == 0:
                return 0.0
            return dot / (na * nb)

        scored: List[ScoredDocument] = []
        for doc, vec in self._store.values():
            scored.append(ScoredDocument(doc=doc, score=cos(vec, vector)))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:k]
