from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ...knowledge.types import Document


class Retriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, *, k: int = 5, filters: Optional[dict] = None) -> List[Document]:
        ...


class PassthroughRetriever(Retriever):
    async def retrieve(self, query: str, *, k: int = 5, filters: Optional[dict] = None) -> List[Document]:
        # No real retrieval; returns the query as a document for smoke tests
        return [Document(id="q", text=query, metadata={})]
