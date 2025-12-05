# Blueprints Roadmap

## Overview

Blueprints are pre-configured agent workflows with **meaningful pre/post processing**.

**Key principle**: A blueprint must provide value through pre-processing (before agent) and/or post-processing (after agent) - not just prompt engineering or tool configuration.

**If it's just prompt + tools → use Agent directly or create a Capability**

---

## What Makes a True Blueprint?

| Aspect | Blueprint | Not Blueprint |
|--------|-----------|---------------|
| Pre-processing | Chunking, retrieval, query decomposition | None |
| Post-processing | Citation formatting, aggregation, synthesis | Just return agent output |
| Agent role | Executes the core task | Is the entire solution |

---

## True Blueprints

### 1. `RAG` ✅ Done

**What it does**: Retrieval-Augmented Generation with citations

**Pre-processing**:
- Retrieve passages from vectorstore
- Format with collision-resistant markers (`«1»`, `«2»`)

**Post-processing**:
- Replace markers with formatted citations
- Generate bibliography

```python
rag = RAG(retriever=retriever, model=model)
result = await rag.run("What are the key findings?")
```

---

### 2. `MapReduce` ✅ Build

**What it does**: Process large documents in chunks, aggregate results

**Pre-processing**:
- Split document into chunks
- Prepare chunk context

**Post-processing**:
- Aggregate chunk results
- Synthesize final output

```python
map_reduce = MapReduce(
    model=model,
    map_prompt="Extract key points: {chunk}",
    reduce_prompt="Synthesize: {results}",
)
result = await map_reduce.run(huge_document)
```

**Note**: This generalizes what Summarizer capability does. Summarizer should use MapReduce internally.

---

### 3. `MultiHopRAG` ✅ Build

**What it does**: Complex queries requiring multiple retrieval steps

**Pre-processing**:
- Query decomposition into sub-queries
- Sequential/parallel retrieval hops

**Post-processing**:
- Evidence chain assembly
- Multi-source citation with hop tracking

```python
multi_hop = MultiHopRAG(
    retriever=retriever,
    model=model,
    max_hops=3,
)
result = await multi_hop.run("How does X relate to Y through Z?")
```

---

### 4. `FactCheck` ✅ Build

**What it does**: Verify claims against sources

**Pre-processing**:
- Claim parsing and structuring
- Evidence retrieval from sources

**Post-processing**:
- Verdict synthesis (verified/refuted/uncertain)
- Confidence scoring
- Evidence citation

```python
fact_check = FactCheck(retriever=retriever, model=model)
result = await fact_check.run("The Eiffel Tower is 300m tall")
# FactCheckResult(verdict="verified", confidence=0.92, evidence=[...])
```

---

## Not Blueprints (Use Agent/Capability/Flow Instead)

### ❌ `Extract` - Use Agent with structured output

No meaningful pre/post processing. Just use:

```python
result = await agent.run(
    "Extract invoice data from this text: ...",
    response_schema=Invoice,
)
```

---

### ❌ `Classify` - Use Agent with structured output

No meaningful pre/post processing. Just use:

```python
class ClassifyResult(BaseModel):
    category: Literal["urgent", "normal", "spam"]
    confidence: float

result = await agent.run(text, response_schema=ClassifyResult)
```

---

### ❌ `Route` - Use Flow with Supervisor topology

This is just classification + dispatch. Use:

```python
flow = Flow(
    agents=[router, technical_agent, billing_agent],
    topology="supervisor",
    supervisor="router",
)
```

---

### ❌ `Review` / `Debate` - Use Flow

These are just multi-agent patterns:

```python
# Review = Pipeline
flow = Flow(agents=[writer, reviewer, editor], topology="pipeline")

# Debate = Mesh
flow = Flow(agents=[optimist, skeptic, pragmatist], topology="mesh")
```

---

### ❌ `Refine` - Use Agent loop or self-critique prompt

The agent loop already iterates. For explicit refinement:

```python
# Option 1: Prompt engineering
agent.run("Write X, then critique and improve it")

# Option 2: Multiple calls
draft = await agent.run("Write X")
refined = await agent.run(f"Improve this: {draft}")
```

---

### ❌ `HyDE` - Move to retriever/ module

This is a retrieval strategy, not a blueprint:

```python
# Should be in retriever/
hyde_retriever = HyDERetriever(base_retriever, model)
results = await hyde_retriever.retrieve("query")
```

---

## Summary

| Name | Type | Reason |
|------|------|--------|
| `RAG` | ✅ Blueprint | Pre: retrieval + markers. Post: citations |
| `MapReduce` | ✅ Blueprint | Pre: chunking. Post: aggregation |
| `MultiHopRAG` | ✅ Blueprint | Pre: decomposition. Post: evidence chain |
| `FactCheck` | ✅ Blueprint | Pre: claim parsing. Post: verdict synthesis |
| `Extract` | ❌ Agent | Just structured output |
| `Classify` | ❌ Agent | Just structured output |
| `Route` | ❌ Flow | Supervisor topology |
| `Review` | ❌ Flow | Pipeline topology |
| `Debate` | ❌ Flow | Mesh topology |
| `Refine` | ❌ Agent | Loop or prompt engineering |
| `HyDE` | ❌ Retriever | Retrieval strategy |

---

## Implementation Priority

1. **`MapReduce`** - Generic pattern, high value
2. **`MultiHopRAG`** - Extends RAG for complex queries  
3. **`FactCheck`** - Specialized verification pattern
