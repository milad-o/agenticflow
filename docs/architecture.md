# AgenticFlow Architecture

Core principles
- Build all execution as LangGraph graphs; do not implement a custom graph engine.
- Use LangChain for tools, models, memory, retrievers/vector stores, and tool invocation.
- Add thin glue layers for registries, configuration, events/reports, and human-in-the-loop gates.
- Async-native with asyncio; prefer LangGraph’s async run/stream APIs and checkpointing.

Key components
- Flow (container)
  - Purpose: System assembly and lifecycle. Loads config, registers agents/tools/resources, wires observability, and exposes run/stream interfaces.
  - Backed by: LangGraph compiled graphs (orchestrator meta-graph + subgraphs).
  - Event/reporting: Wraps LangGraph’s streaming events; optional reporters forward to console, callbacks, or UIs.

- Orchestrator (meta-graph)
  - Purpose: Analyze user request, decompose into tasks, build a task DAG, assign to agents, coordinate parallel/serial execution, retries/backoff.
  - Backed by: LangGraph StateGraph that invokes agent subgraphs via subgraph nodes/functions.
  - Uses: LangGraph routing nodes for capability-based assignment; LangGraph checkpointing for persistence and recovery.

- Agent (graph template)
  - Purpose: Self-contained LangGraph graph; MVP built on langgraph.prebuilt.create_react_agent for speed. Extensible to add plan → act → verify → reflect loops as needed.
  - Tools: LangChain tools bound to the LLM (bind_tools) or invoked explicitly in nodes.
  - Memory: Combination of LangGraph state + LangChain memory/retrievers for persistent/ephemeral memory.
  - Self-verification: Verification node(s) with retry/repair edges; optional evaluator LLM (post-MVP).
  - Communication: Emits events; callable by Orchestrator or directly by users.

- Tool registry (thin layer)
  - Purpose: Discover/register LangChain tools and toolsets; tag, scope, and expose to agents/flow.
  - Sources: langchain-community tools, custom tools, MCP-wrapped tools.
  - Selection: Tag-based and capability-based filtering at orchestration time.

- Resource registry (thin layer)
  - Purpose: Stable data/connectors (retrievers, vector stores, DSNs).
  - Implementation: LangChain retrievers/vectorstores; configuration-driven factories.

- Memory
  - Persistent: LangGraph checkpointing (e.g., SQLite) for graph state; LangChain vector stores (Chroma, Pinecone, etc.) for knowledge.
  - Ephemeral: In-graph state and LangChain in-memory buffers.
  - Embeddings: LangChain embeddings; expose Retriever tool for agents.

- Human-in-the-loop
  - Gate nodes that pause until an approval signal is written to state/checkpoint, or a callback provides approval.
  - Optional LangChain Human tool to surface decisions; pluggable reviewer policies.

- Observability
  - Logging: Structured logs with run_id, node_id, agent_id, task_id.
  - Tracing: LangSmith or OpenTelemetry (optional); wrap LLM/tool calls with spans/metadata.
  - Metrics: Simple counters/timers; emitted via reporter.
  - Visualization: Use LangGraph’s graph visualization; export to Mermaid for docs.

- Communication patterns
  - Request/response: Orchestrator → agent subgraphs (await results).
  - Broadcast: Orchestrator routes same task to multiple agents (parallel).
  - Negotiation/auction: Optional strategy in orchestrator (score tools/agents and pick).
  - Implemented with LangGraph routing + conditional edges.

- MCP integration
  - Wrap MCP clients as LangChain tools; register via Tool registry so agents see them as regular tools.

- Filesystem toolset
  - Use/adapt LangChain file tools; add safe large-file mechanisms (chunking, pagination, partial edits) as utilities exposed as tools.

- Config
  - pyproject.toml + env-var support for providers; declarative config (YAML/TOML) for agents/tools/resources bindings.
