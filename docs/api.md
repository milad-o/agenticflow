# AgenticFlow API Reference

This document summarizes the primary components and their responsibilities.

Flow
- Purpose: System assembly and lifecycle. Loads config, registers agents/tools/resources, wires observability, and exposes run/stream interfaces.
- Key methods:
  - start() / stop()
  - arun(request: str, thread_id?: str) -> dict
  - astream(request: str, thread_id?: str) -> async iterator of chunks
  - add_agent(name: str, agent: Agent)
  - register_tool(name: str, tool_class: type, ...)
  - register_resource(name: str, resource_type: str, factory, ...)
  - set_planner(planner) and set_capability_extractor(extractor)

Agent
- Self-contained LangGraph agent using create_react_agent with bound tools.
- Tool/resource management:
  - set_tools([...]) / add_tools([...]) / register_tool(tool)
  - register_resource(name, resource)
- Execution:
  - arun(message: str, thread_id?: str, verify: bool = True) -> dict
  - astream(message: str, thread_id?: str)
  - run(message) (sync convenience)
- Self-verification: one retry on failure signals and missing FS targets; provides tool usage hints.

Orchestrator
- Meta-graph: analyze → decompose → assign → execute → synthesize.
- Assignment: capability-aware routing using agent tool capabilities and optional LLM-based extraction.
- Provides both compiled graph execution and an "orchestrator-as-agent" interface via DelegateTool.

Planner
- LLM-backed planner that returns a structured DAG (tasks with dependencies), with conservative fallbacks.
- Used by the orchestrator when set on Flow.

ToolRegistry
- Discovers/registers tools with metadata (tags, capabilities) and returns instances by name, tags, or capabilities.
- Defaults include:
  - Filesystem: read_file, write_file, mkdir, list_dir/list_directory, file_stat
  - Search: regex_search_file, regex_search_dir, find_files
  - Directory walking: dir_tree
  - Shell: shell
  - Vector demo: build_ephemeral_chroma, query_ephemeral_chroma

ResourceRegistry
- Register factories for retrievers, vector stores, or other resources and lazily instantiate them.

Models
- Model selection is handled via env/config; Groq and Ollama supported for chat and embeddings.

Examples
- See the scripts under examples/ for runnable demonstrations:
  - dir_walk_search.py – explore directories and search files
  - dir_search_demo.py – regex search across the repo
  - orchestrator_as_agent.py – orchestrator delegates to agents via tool calls
  - planner_demo.py – planning to DAG and executing with Flow
  - capabilities_demo.py – capability extraction aided routing
  - ebay_chroma_demo.py / ebay_intelligent_demo.py – demo vector indexing and retrieval
