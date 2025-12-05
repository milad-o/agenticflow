"""
Blueprints - Pre-configured Agent Workflows.

Blueprints are Flow-compatible agent workflows with:
- Sensible defaults for common patterns
- Pre/post processing pipelines
- Tool conversion via `as_tool()`

Blueprints can be used:
- Standalone: `await rag.run("query")`
- In Flow: `Flow(agents=[rag, writer], topology="pipeline")`
- As Tool: `Agent(tools=[rag.as_tool()])`

Example:
    ```python
    from agenticflow.blueprints import RAG

    rag = RAG(retriever=retriever, model=model)
    answer = await rag.run("What are the key findings?")
    ```

Example in Flow:
    ```python
    flow = Flow(
        agents=[rag, fact_checker, writer],
        topology="pipeline",
    )
    result = await flow.run("Research AI trends")
    ```
"""

from agenticflow.blueprints.base import (
    BaseBlueprint,
    BlueprintResult,
    PreProcessor,
    PostProcessor,
)
from agenticflow.blueprints.context import BlueprintContext
from agenticflow.blueprints.protocol import FlowResident
from agenticflow.blueprints.processors import (
    CitationStyle,
    CitedPassage,
    CitationFormatter,
    BibliographyAppender,
    CITE_MARKER_PATTERN,
)
from agenticflow.blueprints.rag import RAG, RAGConfig, RAGResult

__all__ = [
    # Protocol
    "FlowResident",
    # Base
    "BaseBlueprint",
    "BlueprintResult",
    "BlueprintContext",
    "PreProcessor",
    "PostProcessor",
    # Processors
    "CitationStyle",
    "CitedPassage",
    "CitationFormatter",
    "BibliographyAppender",
    "CITE_MARKER_PATTERN",
    # RAG
    "RAG",
    "RAGConfig",
    "RAGResult",
]

