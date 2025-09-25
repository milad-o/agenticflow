"""Ephemeral Chroma indexing and retrieval tools.

- BuildEphemeralChromaTool: stream-chunk a large file and build an in-memory Chroma index.
- QueryEphemeralChromaTool: query the ephemeral index with a question (similarity search).

Indexes are held in-process (per-tool instance) and identified by `index_id`.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import os
import uuid

from langchain_core.tools import BaseTool
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from agenticflow.core.models import get_ollama_embeddings


@dataclass
class _EphemeralStore:
    vectorstore: Chroma


class BuildEphemeralChromaTool(BaseTool):
    name: str = "build_ephemeral_chroma"
    description: str = (
        "Build an ephemeral Chroma index from a large text file by streaming and chunking. "
        "Args: path (str), index_id (optional str), chunk_size (int, default 2000), chunk_overlap (int, default 200). "
        "Returns: {'index_id': str, 'chunks': int}"
    )

    def __init__(self):
        super().__init__()
        self._stores: Dict[str, _EphemeralStore] = {}

    def _run(
        self,
        path: str,
        index_id: Optional[str] = None,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        encoding: str = "utf-8",
        max_bytes: Optional[int] = None,
    ) -> Dict[str, Any]:  # type: ignore[override]
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}

        # Read progressively to avoid huge memory usage
        # We still need text chunks for Chroma; we stream the file and accumulate up to chunk_size
        docs: List[Document] = []
        read_bytes = 0
        with open(path, "r", encoding=encoding, errors="ignore") as f:
            for line in f:
                read_bytes += len(line.encode(encoding, errors="ignore"))
                docs.append(Document(page_content=line))
                if max_bytes and read_bytes >= max_bytes:
                    break

        if not docs:
            return {"error": "No content read from file."}

        # Combine then split with a recursive splitter for semantic chunks
        all_text = "".join([d.page_content for d in docs])
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_text(all_text)
        chunk_docs = [Document(page_content=c, metadata={"source": path}) for c in chunks]

        embeddings = get_ollama_embeddings()
        # Use an in-memory Chroma (ephemeral); client defaults to in-process
        vs = Chroma.from_documents(documents=chunk_docs, embedding=embeddings)

        idx = index_id or str(uuid.uuid4())
        self._stores[idx] = _EphemeralStore(vectorstore=vs)
        return {"index_id": idx, "chunks": len(chunk_docs)}


class QueryEphemeralChromaTool(BaseTool):
    name: str = "query_ephemeral_chroma"
    description: str = (
        "Query an ephemeral Chroma index created earlier. "
        "Args: index_id (str), question (str), k (int, default 4). Returns: answer-like context text."
    )

    def __init__(self, builder: BuildEphemeralChromaTool):
        super().__init__()
        self._builder = builder

    def _run(self, index_id: str, question: str, k: int = 4) -> str:  # type: ignore[override]
        store = self._builder._stores.get(index_id)
        if not store:
            return f"Index '{index_id}' not found. Build index first."
        retriever = store.vectorstore.as_retriever(search_kwargs={"k": k})
        docs = retriever.get_relevant_documents(question)
        if not docs:
            return "No relevant context found."
        # Simple concat context
        contents = []
        for d in docs:
            txt = d.page_content.strip()
            if txt:
                contents.append(txt)
        return "\n---\n".join(contents[:k])