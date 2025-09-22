from __future__ import annotations

from typing import List, Sequence

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception as e:  # pragma: no cover - import-time hint only
    SentenceTransformer = None  # type: ignore

from .base import EmbeddingClient, Embedding


class HFEmbeddingClient(EmbeddingClient):
    """Hugging Face sentence-transformers embedding client.

    Requires sentence-transformers extra. Loads model lazily on first use.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            if SentenceTransformer is None:
                raise ImportError("sentence-transformers is not installed. Install with [embed-hf] extra.")
            self._model = SentenceTransformer(self.model_name)

    async def embed_texts(self, texts: Sequence[str], *, model: str | None = None) -> List[Embedding]:
        self._ensure_model()
        # sentence_transformers is sync; run in thread with asyncio.to_thread if needed.
        from asyncio import to_thread

        vectors = await to_thread(self._model.encode, list(texts), convert_to_numpy=True, normalize_embeddings=False)  # type: ignore
        dim = int(vectors.shape[1])
        out: List[Embedding] = []
        for i, t in enumerate(texts):
            vec = vectors[i].tolist()
            out.append(Embedding(vector=[float(x) for x in vec], model=model or self.model_name, dim=dim))
        return out
