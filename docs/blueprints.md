# Blueprints

Blueprints are pre-configured agent workflows that solve common patterns. They leverage the Agent system internally while providing a simple, focused API.

## Concept

| Concept | What it is | Example |
|---------|-----------|---------|
| **Agent** | Core LLM executor with tools | `agent.run("query")` |
| **Capability** | Tools for agents | Filesystem, WebSearch |
| **Flow** | Multi-agent orchestration | Pipeline, Mesh, Supervisor |
| **Blueprint** | Pre-configured workflow | RAG, MapReduce, FactCheck |

Blueprints don't bypass agents—they use them internally with sensible defaults.

## FlowResident Protocol

All blueprints (and agents) implement the `FlowResident` protocol, enabling them to participate in Flows:

```python
from agenticflow import FlowResident

class FlowResident(Protocol):
    @property
    def name(self) -> str: ...
    async def run(self, input: str, **kwargs) -> str: ...
```

This means you can use blueprints directly in Flow topologies alongside agents.

## RAG Blueprint

Retrieval-Augmented Generation with automatic citation formatting.

### Basic Usage

```python
from agenticflow.blueprints import RAG, RAGConfig
from agenticflow.retriever import DenseRetriever
from agenticflow.vectorstore import VectorStore

# Prepare retriever
store = VectorStore(embeddings=embeddings)
await store.add_documents(chunks)
retriever = store.as_retriever()  # Convenience method

# Create RAG blueprint
rag = RAG(retriever=retriever, model=model)

# Query - returns formatted answer with citations
result = await rag.run("What are the key findings?")
print(result)
```

### With Configuration

```python
from agenticflow.blueprints import RAG, RAGConfig, CitationFormatter

config = RAGConfig(
    top_k=5,
    include_scores=True,
)

rag = RAG(
    retriever=retriever,
    model=model,
    config=config,
    post_processors=[CitationFormatter()],  # Add citation formatting
)

# For detailed results
result = await rag.run_detailed("What are the key findings?")
print(result.output)      # Formatted answer
print(result.passages)    # Retrieved passages
print(result.metadata)    # Execution metadata
```

### As a Tool

Use RAG as a tool in other agents:

```python
supervisor = Agent(
    name="supervisor",
    model=model,
    tools=[rag.as_tool()],  # RAG becomes a search tool
)
```

## MapReduce Blueprint

Process large documents in chunks, aggregate results.

```python
from agenticflow.blueprints import MapReduce, MapReduceConfig

config = MapReduceConfig(
    map_prompt="Extract key points from this section:\n\n{chunk}",
    reduce_prompt="Synthesize these points into a coherent summary:\n\n{results}",
    chunk_size=2000,
    chunk_overlap=200,
)

map_reduce = MapReduce(config=config, model=model)
result = await map_reduce.run(huge_document)
```

### Detailed Results

```python
result = await map_reduce.run_detailed(huge_document)
print(result.output)              # Final synthesized output
print(result.metadata["chunks"])  # Number of chunks processed
print(result.metadata["map_results"])  # Individual chunk results
```

## MultiHopRAG Blueprint

Complex queries requiring multiple retrieval steps.

```python
from agenticflow.blueprints import MultiHopRAG, MultiHopRAGConfig

config = MultiHopRAGConfig(
    max_hops=3,
    min_confidence=0.7,
)

multi_hop = MultiHopRAG(
    config=config,
    retriever=retriever,
    model=model,
)

result = await multi_hop.run("How does X relate to Y through Z?")
```

### Evidence Chain

```python
result = await multi_hop.run_detailed("Complex multi-step query")
for hop in result.metadata["hops"]:
    print(f"Hop {hop.hop_number}: {hop.query}")
    print(f"  Found: {len(hop.passages)} passages")
    print(f"  Confidence: {hop.confidence:.2f}")
```

## FactCheck Blueprint

Verify claims against sources with confidence scoring.

```python
from agenticflow.blueprints import FactCheck, FactCheckConfig, Verdict

config = FactCheckConfig(
    confidence_threshold=0.7,
    max_evidence=5,
)

fact_check = FactCheck(
    config=config,
    retriever=retriever,
    model=model,
)

result = await fact_check.run_detailed("The Eiffel Tower is 300 meters tall")
print(f"Verdict: {result.verdict}")       # Verdict.VERIFIED
print(f"Confidence: {result.confidence}") # 0.92
for evidence in result.evidence:
    print(f"  - {evidence.text} (supports: {evidence.supports})")
```

### Verdict Types

```python
from agenticflow.blueprints import Verdict

Verdict.VERIFIED      # Claim is supported by evidence
Verdict.REFUTED       # Claim is contradicted by evidence
Verdict.UNCERTAIN     # Insufficient evidence
Verdict.UNVERIFIABLE  # Cannot be fact-checked
```

## Composable Processors

Blueprints support pre and post processors for customization:

```python
from agenticflow.blueprints import (
    RAG,
    CitationFormatter,
    BibliographyAppender,
    CitationStyle,
)

rag = RAG(
    retriever=retriever,
    model=model,
    post_processors=[
        CitationFormatter(style=CitationStyle.AUTHOR_YEAR),
        BibliographyAppender(),
    ],
)
```

### Custom Processors

```python
from agenticflow.blueprints import BlueprintContext

async def add_disclaimer(ctx: BlueprintContext) -> BlueprintContext:
    """Add a disclaimer to the output."""
    return BlueprintContext(
        input=ctx.input,
        output=ctx.output + "\n\n*This is AI-generated content.*",
        metadata=ctx.metadata,
        run_id=ctx.run_id,
    )

rag = RAG(
    retriever=retriever,
    model=model,
    post_processors=[add_disclaimer],
)
```

## Citation Design

Blueprints use collision-resistant markers internally:

1. **Agent sees**: `«1» passage text...` (guillemets are rare in content)
2. **Agent references**: `«1»`, `«2»` in its response
3. **Post-processing**: Markers → formatted citations + bibliography

This keeps the LLM context minimal (no metadata bloat) while enabling deterministic citation formatting.
