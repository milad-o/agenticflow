from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import List, Sequence, Tuple


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sqrt(sum(x * x for x in a)) or 1e-12
    nb = sqrt(sum(y * y for y in b)) or 1e-12
    return dot / (na * nb)


@dataclass
class VectorDoc:
    text: str
    meta: dict
    vec: List[float]


class SimpleVectorIndex:
    def __init__(self) -> None:
        self.docs: List[VectorDoc] = []

    def add(self, text: str, vec: List[float], meta: dict | None = None) -> None:
        self.docs.append(VectorDoc(text=text, meta=meta or {}, vec=vec))

    def search(self, query_vec: List[float], k: int = 5) -> List[Tuple[VectorDoc, float]]:
        scored = [ (doc, cosine(doc.vec, query_vec)) for doc in self.docs ]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:k]