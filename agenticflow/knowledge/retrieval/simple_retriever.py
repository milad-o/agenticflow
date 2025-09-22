from __future__ import annotations

from typing import List, Tuple

from agenticflow.knowledge.vector.simple_index import SimpleVectorIndex, VectorDoc


class SimpleRetriever:
    def __init__(self, index: SimpleVectorIndex):
        self.index = index

    def query(self, query_vec: List[float], k: int = 5) -> List[Tuple[VectorDoc, float]]:
        return self.index.search(query_vec, k=k)