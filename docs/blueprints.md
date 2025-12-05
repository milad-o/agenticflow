# Blueprints

Blueprints are pre-configured agent workflows that solve common patterns. They leverage the Agent system internally while providing a simple, focused API.

## Concept

| Concept | What it is | Example |
|---------|-----------|---------|
| **Agent** | Core LLM executor with tools | `agent.run("query")` |
| **Capability** | Tools for agents | Filesystem, WebSearch |
| **Flow** | Multi-agent orchestration | Pipeline, Mesh, Supervisor |
| **Blueprint** | Pre-configured workflow | RAG, Summarize, Extract |

Blueprints don't bypass agents—they use them internally with sensible defaults.

## RAG Blueprint

Retrieval-Augmented Generation with automatic citation formatting.

### Simple Mode (just model)

```python
from agenticflow.blueprints import RAG
from agenticflow.retriever import DenseRetriever
from agenticflow.vectorstore import VectorStore

# Prepare retriever
store = VectorStore(embeddings=embeddings)
await store.add_documents(chunks)
retriever = DenseRetriever(store)

# Create RAG blueprint
rag = RAG(retriever=retriever, model=model)

# Query - returns formatted answer with citations
result = await rag.run("What are the key findings?")
print(result.output)
```

### Advanced Mode (pre-configured agent)

```python
from agenticflow import Agent
from agenticflow.blueprints import RAG
from agenticflow.interceptors import BudgetGuard

# Create agent with full configuration
agent = Agent(
    name="research-assistant",
    model=model,
    memory=memory,
    intercept=[BudgetGuard(model_calls=10)],
)

# Blueprint adds search tool and handles citations
rag = RAG(retriever=retriever, agent=agent)
result = await rag.run("What are the key findings?")
```

### Multiple Retrievers with Fusion

```python
from agenticflow.retriever import DenseRetriever, BM25Retriever

dense = DenseRetriever(store)
sparse = BM25Retriever(chunks)

rag = RAG(
    retrievers=[dense, sparse],
    weights=[0.6, 0.4],
    fusion="rrf",  # or "linear", "max", "voting"
    model=model,
)
```

### Configuration

```python
from agenticflow.blueprints import RAG, RAGConfig, CitationStyle

config = RAGConfig(
    top_k=5,
    citation_style=CitationStyle.AUTHOR_YEAR,  # or NUMERIC, FOOTNOTE, INLINE
    include_bibliography=True,
    include_score_in_bibliography=False,
)

rag = RAG(retriever=retriever, model=model, config=config)
```

### RAGResult

The `run()` method returns a `RAGResult` with:

```python
result = await rag.run("query")

result.output      # Formatted answer with citations + bibliography
result.raw_output  # Raw agent output with «1», «2» markers
result.passages    # Retrieved passages used
result.query       # Original query
result.metadata    # Additional metadata
```

### Direct Search

Access retrieval without generation:

```python
passages = await rag.search("query", k=5)
for p in passages:
    print(f"«{p.citation_id}» {p.source} (score: {p.score:.2f})")
    print(f"  {p.text[:100]}...")
```

## Citation Design

Blueprints use collision-resistant markers internally:

1. **Agent sees**: `«1» passage text...` (guillemets are rare in content)
2. **Agent references**: `«1»`, `«2»` in its response
3. **Post-processing**: Markers → formatted citations + bibliography

This keeps the LLM context minimal (no metadata bloat) while enabling deterministic citation formatting.

## Future Blueprints

- `Summarize` - Long document summarization
- `Extract` - Structured data extraction
- `Classify` - Text classification
- `MapReduce` - Chunk → process → aggregate
- `Review` - Multi-agent review pipeline (uses Flow)
