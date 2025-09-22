# Framework utilities and ready-to-use building blocks

This framework ships opinionated, ready-to-use utilities that you can compose without writing boilerplate, while remaining fully extensible.

Key pieces

- ToolAgent and tools
  - ToolAgent lets agents invoke tools by name (e.g., fs_read, http_fetch). You can register your own Tool implementations.
  - Built-in tools:
    - FSReadTool(roots=[...], default_max_bytes=...): whitelisted file reads, size-capped
    - HttpFetchTool(allow_patterns=["^https?://"], max_bytes=...): safe HTTP GET
  - Example (in code):
    ```python
    from agenticflow.agents.tool_agent import ToolAgent
    from agenticflow.agents.tools.builtin import FSReadTool
    agent = ToolAgent("reader", tools={"fs_read": FSReadTool(roots=["."])})
    ```

- Utility Agents (agenticflow.agents.utilities)
  - ChatAgent / ChatToolAgent: minimal local chat stubs (great for demos)
  - StatsAgent: compute basic file stats (lines, words, sha256) and write stats.json
  - ReportAgent: render a small Markdown report from stats.json
  - ScanAgent: find text files under a root with glob ignores, write files.txt
  - SummarizeAgent: naïve top-term frequency summary over local files with citations
  - These agents enable realistic local examples without custom boilerplate code.

- Orchestration topologies (agenticflow.orchestration.topologies)
  - pipeline(stages): linear chain of TaskNodes (function helper)
  - fanout_reduce(fanout_tasks, reduce_task): fork/join pattern (function helper)
  - PipelineTopology: OOP builder for linear pipelines
  - FanoutReduceTopology: OOP builder for fanout/reduce DAGs
  - GroupChatSupervisor (agenticflow.agents.supervisor.group_chat): static multi-round chat topology

- Policies and validation (agenticflow.security.policy)
  - TaskSchemaRegistry: enforce per agent:task_type JSON-like schemas before task assignment (jsonschema if installed, fallback to required-only). Errors include hints.
  - PolicyGuard: simple allow/deny lists per agent for task types (deny > allow; default_allow configurable)
  - Dev-only loader: examples/utils/policy_loader.load_policy(path) -> (schema, guard)

- Workflow visualization (agenticflow.observability.viz)
  - VisualizationRenderer renders:
    - workflow.mmd (Mermaid) with status coloring (completed/failed/in_progress)
    - system.mmd (Mermaid) and system.dot (Graphviz DOT) and optionally system.svg
  - System diagrams via agenticflow.observability.system_viz

- Debugging and observability
  - DebugInterface: list workflows, timeline, summary
  - Durable stores (SQLite) for resuming across processes

Patterns (OOP in code)

- Build and run a pipeline (function helper)
  ```python
  from pathlib import Path
  from agenticflow.agents.tool_agent import ToolAgent
  from agenticflow.agents.tools.builtin import FSReadTool
  from agenticflow.agents.utilities import StatsAgent, ReportAgent
  from agenticflow.orchestration.core.orchestrator import Orchestrator
  from agenticflow.orchestration.topologies import pipeline, PipelineStage

  roots = [str(Path(".").resolve())]
  orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
  orch.register_agent(ToolAgent("reader", tools={"fs_read": FSReadTool(roots=roots)}))
  orch.register_agent(StatsAgent("processor"))
  orch.register_agent(ReportAgent("writer"))

  stages = [
    PipelineStage("read", "reader", "fs_read", {"path": "README.md"}),
    PipelineStage("stats", "processor", "compute_stats", {"path": "README.md", "outdir": "artifacts"}),
    PipelineStage("report", "writer", "write_report", {"stats": "artifacts/stats.json", "outdir": "artifacts"}),
  ]
  wf = pipeline(stages)
  wf_id = await orch.execute_workflow(wf)
  ```

- Build and run a pipeline (OOP helper)
  ```python
  from agenticflow.orchestration.topologies import PipelineTopology, PipelineStage

  stages = [
    PipelineStage("read", "reader", "fs_read", {"path": "README.md"}),
    PipelineStage("stats", "processor", "compute_stats", {"path": "README.md", "outdir": "artifacts"}),
    PipelineStage("report", "writer", "write_report", {"stats": "artifacts/stats.json", "outdir": "artifacts"}),
  ]
  wf = PipelineTopology(stages).build()
  wf_id = await orch.execute_workflow(wf)
  ```

- Visualize
  ```python
  from agenticflow.observability.debug import DebugInterface
  from agenticflow.observability.viz import VisualizationRenderer

  dbg = DebugInterface(event_store=orch.event_store)
  viz = VisualizationRenderer(dbg)
  await viz.render_workflow(wf_id, out_mmd=Path("artifacts/workflow.mmd"))
  await viz.render_system(
    workflow_id=wf_id,
    out_mmd=Path("artifacts/system.mmd"),
    out_dot=Path("artifacts/system.dot"),
    out_svg=Path("artifacts/system.svg"),
    agents=["reader","processor","writer"],
    tools_by_agent={"reader": ["fs_read"]},
    task_types_by_agent={"reader": ["fs_read"], "processor": ["compute_stats"], "writer": ["write_report"]},
  )
  ```

Extend topologies

- Composition
  - Build pipelines with PipelineTopology and then append stages with `.add()` or `.extend()` before calling `.build()`.

- Custom fanout/reduce
  - Create TaskNode fanout tasks and a reduce TaskNode. Use FanoutReduceTopology(fanout=[...], reduce=reduce_node).build(). The helper will ensure the reduce node depends on all fanout ids.

- Mixed patterns
  - You can create multiple topologies and then merge their TaskNodes into a single WorkflowDefinition if needed (ensure unique task_ids and proper dependencies).

Testing workflows (best practices)

- Use orchestrator with in-memory store for speed:
  ```python
  from agenticflow.orchestration.core.orchestrator import Orchestrator
  orch = Orchestrator()
  ```
- Register simple OK/Noop agents to isolate orchestration behavior.
- Assert on event sequences using DebugInterface or directly replaying from the event_store.
- Prefer uv to run tests: `PYTHONPATH=. uv run pytest -q --ignore=tests/integration`.

Notes
- All examples are designed to run locally (no remote agents required). SQLite backs persistence for cross-process resume.
- You can mix Utilities agents and your own Agents/Tools.
- For human-in-the-loop (HITL), use ApprovalGateAgent to emit review_requested and await review_approved/denied.
