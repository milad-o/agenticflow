# AgenticFlow Workboard

## Current Focus: Blueprint Architecture ✅ COMPLETE

### Design Decisions (Dec 5, 2025)

**Flow is the ultimate container.** Blueprints are Flow residents alongside Agents.

```
Flow (container)
├── Agent (resident)
├── Blueprint (resident) ← same interface
└── Agent/Blueprint...
```

### Blueprint Contract

```python
class Blueprint:
    name: str                           # Flow uses for routing
    
    async def run(self, input: str) -> str:  # Flow-compatible
        ...
    
    async def run_detailed(self, input: str) -> BlueprintResult:  # Full metadata
        ...
    
    def as_tool(self) -> Tool:          # Use in other agents
        ...
```

### Usage Patterns

```python
# 1. Standalone
rag = RAG(retriever, model=model)
result = await rag.run("query")  # Returns str

# 2. As Flow resident (list, no | operator)
flow = Flow(
    agents=[rag, fact_checker, writer],
    topology="pipeline",
)

# 3. As tool in another agent
supervisor = Agent(tools=[rag.as_tool()])

# 4. Full metadata
result = await rag.run_detailed("query")  # Returns RAGResult
print(result.passages, result.metadata)
```

### What Blueprint Handles

| Concern | Blueprint Responsibility |
|---------|-------------------------|
| Pre-processing | Query rewriting, context injection |
| Tool setup | Auto-creates specialized tools |
| Post-processing | Citation formatting, validation |
| Encapsulation | Hides complexity, simple `run()` |

---

## Implementation Status ✅

- [x] `FlowResident` Protocol (shared by Agent, Blueprint)
- [x] `BlueprintContext` (immutable, thread-safe)
- [x] `BaseBlueprint` with `as_tool()`, Flow-compatible `run()`
- [x] Composable processors (`CitationFormatter`, `BibliographyAppender`)
- [x] `RAG` blueprint refactored
- [x] Tests passing (1254 passed)

---

## Architecture

```
blueprints/
├── __init__.py       # Exports
├── base.py           # BaseBlueprint, BlueprintResult
├── context.py        # BlueprintContext (immutable)
├── protocol.py       # FlowResident protocol
├── processors.py     # CitationFormatter, BibliographyAppender
└── rag.py            # RAG blueprint
```

---

## Rejected Ideas

- ❌ `|` operator for chaining (LangChain-style) - just use Flow with list
- ❌ Blueprint as separate concept from Flow - it's a resident

---

## Next Steps

- [ ] Test RAG in actual Flow topology
- [ ] Implement MapReduce blueprint
- [ ] Implement MultiHopRAG blueprint
- [ ] Update docs/blueprints.md
