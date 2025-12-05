# Blueprints - Pre-configured Agent Workflows

## Concept

**Blueprints** are pre-configured agent/flow wrappers with pre/post processing.
They leverage the existing Agent and Flow system, not bypass it.

```
Agent       → Core LLM executor
Capability  → Tools for agents  
Flow        → Multi-agent orchestration
Blueprint   → Pre-configured workflow using Agents/Flows
```

## API Design

```python
from agenticflow.blueprints import RAG, Summarize, Extract

# RAG Blueprint - uses Agent internally
rag = RAG(retriever=retriever, model=model)
answer = await rag.run("What are the findings?")

# Customizable
rag = RAG(
    retriever=retriever,
    model=model,
    citation_style=CitationStyle.NUMERIC,
    include_bibliography=True,
)
```

## Tasks

- [x] Create `blueprints/` module structure
- [x] Implement `BaseBlueprint` abstract class
- [x] Implement `RAG` blueprint
  - [x] Uses Agent internally with search tool
  - [x] Unique citation markers «1», «2» (collision-resistant)
  - [x] Deterministic post-processing for citations
  - [x] Bibliography formatting
- [x] Support `model` (simple) or `agent` (advanced) modes
- [x] Update exports in `__init__.py`
- [x] Update example `10_rag.py`
- [x] Run tests (1221 passed)
- [x] Remove old RAG capability
- [x] Test example with real LLM
- [x] Create docs/blueprints.md

## Blueprint Architecture

```python
class BaseBlueprint(ABC):
    """Base class for all blueprints."""
    
    @abstractmethod
    async def run(self, input: str, **kwargs) -> BlueprintResult: ...
    
    @property
    @abstractmethod
    def name(self) -> str: ...

class RAG(BaseBlueprint):
    """Retrieval-Augmented Generation blueprint."""
    
    def __init__(self, retriever, model, ...):
        # Creates internal agent with search tool
        self._agent = Agent(...)
    
    async def run(self, query: str) -> RAGResult:
        # 1. Agent searches and generates with «1» markers
        raw = await self._agent.run(query)
        # 2. Deterministic post-processing
        return self._format_citations(raw)
```

## Future Blueprints

- `Summarize` - Long document summarization
- `Extract` - Structured data extraction  
- `Classify` - Text classification
- `MapReduce` - Chunk → process → aggregate
- `Review` - Multi-agent review pipeline (uses Flow)
