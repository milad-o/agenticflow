# Extended API Reference

This reference focuses on the most commonly used public classes and functions.

Core
- Orchestrator
  - execute_workflow(defn: WorkflowDefinition, workflow_id: Optional[str] = None) -> str
  - resume_workflow(workflow_id: str) -> str
  - cancel_workflow(workflow_id: str, reason: str = "user_cancelled") -> None
  - set_task_schema_registry(registry)
  - set_policy_guard(guard)
  - get_last_workflow_id() -> Optional[str]
- WorkflowDefinition
  - tasks: list[TaskNode]
  - Optional workflow-level retry/timeout knobs
- TaskNode
  - task_id, agent_id, task_type, params, dependencies, retries, timeout_seconds

Topologies
- PipelineStage(task_id, agent_id, task_type, params)
- pipeline(stages) -> WorkflowDefinition
- fanout_reduce(fanout_tasks, reduce_task) -> WorkflowDefinition
- PipelineTopology(stages).add(...).build()
- FanoutReduceTopology(fanout=[...], reduce=...).build()

Agents
- Base Agent.perform_task(task_type, params) -> dict
- ToolAgent(agent_id, tools: dict[name->Tool], security: Optional[SecurityContext])
  - Calls Tool.invoke(**params)

Tools (selected)
- HttpFetchTool(url, timeout=10.0) — hardened: https-only, content caps, type allowlist
- FSReadTool(path, max_bytes) — hardened: root allowlist + extension allowlist
- MCPHttpTool(endpoint, method, params, headers) — minimal MCP-style HTTP caller
- MCPSSEStreamTool(endpoint, channel, params) — SSE streaming + mid-task progress
- MCPClientSDKTool(endpoint, tool, args) — prefers fastmcp/mcp SDKs when installed
- MCPClientSDKStreamTool(endpoint, channel, args) — streaming via SDK with progress

Security & Policy
- SecurityContext.authorize(operation, resource)
- TaskSchemaRegistry({"agent:task": jsonschema}) — enforced pre-assignment; jsonschema or required-only fallback with hints
- PolicyGuard(allow_agent_tasks, deny_agent_tasks, default_allow) — enforced pre-assignment (deny > allow)

Observability
- DebugInterface(event_store)
  - list_workflow_summaries(limit, status) -> list[WorkflowSummary]
  - get_workflow_summary(workflow_id) -> WorkflowSummary
  - event_store.replay(workflow_id) -> list[AgenticEvent]
- VisualizationRenderer(debug)
  - render_workflow(workflow_id, out_mmd)
  - render_system(workflow_id, out_mmd, out_dot, out_svg, agents, tools_by_agent, task_types_by_agent)
- progress.emit_progress(kind, data) — mid-task events; Orchestrator publishes task_progress

Adapters
- InMemoryEventStore, SQLiteEventStore
- InMemoryEventBus

UI (optional)
- build_app(orchestrator) -> FastAPI app
  - /api/summaries
  - /api/workflows/{wid}/mermaid
  - /api/workflows/{wid}/system
  - /api/workflows/{wid}/events
  - /api/workflows/{wid}/events/stream (SSE)

Examples folder
- Self-contained demos under examples/XX_name with demo.py and data/ vs artifacts/
- Web UI runner under examples/webui/run_server.py
