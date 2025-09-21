from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class Embedding:
    vector: List[float]
    model: str
    dim: int
    metadata: Dict[str, Any] | None = None


@dataclass(frozen=True)
class ScoredDocument:
    doc: Document
    score: float
    metadata: Optional[Dict[str, Any]] = None
