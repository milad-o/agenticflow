# AgenticFlow Workboard

## Current Sprint: Blueprint Ecosystem ✅ COMPLETE

### Priority Tasks

1. ✅ **Add `as_tool()` to Agent** - Convert agent to tool for use in other agents
2. ✅ **Add `as_retriever()` to VectorStore** - Convert store to retriever  
3. ✅ **Implement `MapReduce` blueprint** - Chunk processing + aggregation
4. ✅ **Implement `MultiHopRAG` blueprint** - Multi-step retrieval
5. ✅ **Implement `FactCheck` blueprint** - Claim verification

---

## Completed Implementation Summary

### Agent.as_tool()

```python
researcher = Agent(name="researcher", model=model, tools=[search])
writer = Agent(name="writer", model=model)

# Supervisor can call researcher as a tool
supervisor = Agent(
    name="supervisor",
    model=model,
    tools=[researcher.as_tool(), writer.as_tool()],
)
```

**Location**: `agenticflow/agent/base.py` - `Agent.as_tool()` method

---

### VectorStore.as_retriever()

```python
store = VectorStore(embeddings=embeddings)
await store.add_documents(chunks)

retriever = store.as_retriever()
retriever = store.as_retriever(k=10, filter={"type": "doc"})
```

**Location**: `agenticflow/vectorstore/store.py` - `VectorStore.as_retriever()` method

---

### MapReduce Blueprint

```python
from agenticflow.blueprints import MapReduce, MapReduceConfig

map_reduce = MapReduce(
    config=MapReduceConfig(
        map_prompt="Extract key points from: {chunk}",
        reduce_prompt="Synthesize these points: {results}",
        chunk_size=2000,
    ),
    model=model,
)
result = await map_reduce.run(huge_document)
```

**Location**: `agenticflow/blueprints/mapreduce.py`

---

### MultiHopRAG Blueprint

```python
from agenticflow.blueprints import MultiHopRAG, MultiHopRAGConfig

multi_hop = MultiHopRAG(
    config=MultiHopRAGConfig(max_hops=3),
    retriever=retriever,
    model=model,
)
result = await multi_hop.run("How does X relate to Y through Z?")
# Access evidence chain: result.metadata["hops"]
```

**Location**: `agenticflow/blueprints/multihop.py`

---

### FactCheck Blueprint

```python
from agenticflow.blueprints import FactCheck, FactCheckConfig, Verdict

fact_check = FactCheck(
    config=FactCheckConfig(confidence_threshold=0.7),
    retriever=retriever,
    model=model,
)
result = await fact_check.run_detailed("The Eiffel Tower is 300m tall")
# FactCheckResult(verdict=Verdict.VERIFIED, confidence=0.92, evidence=[...])
```

**Location**: `agenticflow/blueprints/factcheck.py`

---

## Architecture Notes

### FlowResident Protocol

All agents and blueprints implement the `FlowResident` protocol:

```python
from agenticflow import FlowResident

class FlowResident(Protocol):
    @property
    def name(self) -> str: ...
    async def run(self, input: str) -> str: ...
```

### Blueprint Composability

Blueprints support pre/post processors for pipeline composition:

```python
from agenticflow.blueprints import RAG, CitationFormatter

rag = RAG(
    config=RAGConfig(top_k=5),
    retriever=retriever,
    model=model,
    post_processors=[CitationFormatter()],
)
```

---

## Next Sprint Ideas

- [ ] Summarization blueprint (hierarchical summarization)
- [ ] Chain-of-Thought blueprint (explicit reasoning steps)
- [ ] Debate blueprint (multi-agent deliberation)
- [ ] Code Review blueprint (static analysis + LLM review)

---

## Architecture Reminder

```
Flow (container)
├── Agent (resident) → has as_tool()
├── Blueprint (resident) → has as_tool()
│   ├── RAG ✅
│   ├── MapReduce 🔄
│   ├── MultiHopRAG 🔄
│   └── FactCheck 🔄
└── ...

VectorStore → has as_retriever()
```

---

## Implementation Order

1. [ ] `Agent.as_tool()` - enables hierarchical patterns
2. [ ] `VectorStore.as_retriever()` - convenience method
3. [ ] `MapReduce` blueprint - foundational pattern
4. [ ] `MultiHopRAG` blueprint - extends RAG
5. [ ] `FactCheck` blueprint - specialized verification
