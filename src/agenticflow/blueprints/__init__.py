"""
Blueprints - Pre-configured Agent Workflows.

Blueprints are convenience wrappers that leverage the Agent and Flow system
with sensible defaults, pre-processing, and post-processing.

Example:
    ```python
    from agenticflow.blueprints import RAG

    rag = RAG(retriever=retriever, model=model)
    answer = await rag.run("What are the key findings?")
    ```
"""

from agenticflow.blueprints.base import BaseBlueprint, BlueprintResult
from agenticflow.blueprints.rag import RAG, RAGConfig, RAGResult, CitationStyle

__all__ = [
    # Base
    "BaseBlueprint",
    "BlueprintResult",
    # RAG
    "RAG",
    "RAGConfig",
    "RAGResult",
    "CitationStyle",
]
