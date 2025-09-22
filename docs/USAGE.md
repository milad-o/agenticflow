# Usage Guide

This guide covers common workflows with AgenticFlow: building workflows, running them, and inspecting results.

Install
```bash
uv sync --dev
```

Build and run a simple pipeline
```python
from agenticflow.agents.utilities import StatsAgent, ReportAgent
from agenticflow.orchestration.core.orchestrator import Orchestrator
from agenticflow.orchestration.topologies import PipelineTopology, PipelineStage

orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
orch.register_agent(StatsAgent("processor"))
orch.register_agent(ReportAgent("writer"))

stages = [
  PipelineStage("stats", "processor", "compute_stats", {"path": "README.md", "outdir": "artifacts"}),
  PipelineStage("report", "writer", "write_report", {"stats": "artifacts/stats.json", "outdir": "artifacts"}),
]
wf = PipelineTopology(stages).build()
wid = await orch.execute_workflow(wf)
print("started:", wid)
```

Visualize
```python
from pathlib import Path
from agenticflow.observability.debug import DebugInterface
from agenticflow.observability.viz import VisualizationRenderer

dbg = DebugInterface(event_store=orch.event_store)
viz = VisualizationRenderer(dbg)
await viz.render_workflow(wid, out_mmd=Path("artifacts/workflow.mmd"))
await viz.render_system(
  workflow_id=wid,
  out_mmd=Path("artifacts/system.mmd"),
  out_dot=Path("artifacts/system.dot"),
  out_svg=Path("artifacts/system.svg"),
  agents=["processor","writer"],
  tools_by_agent={},
  task_types_by_agent={"processor":["compute_stats"],"writer":["write_report"]},
)
```

Validation & Policy (local)
```python
from agenticflow.security.policy import TaskSchemaRegistry, PolicyGuard

reg = TaskSchemaRegistry(schemas={
  "processor:compute_stats": {
    "type":"object",
    "properties": {"path": {"type":"string"}},
    "required": ["path"],
  }
})
orch.set_task_schema_registry(reg)

orch.set_policy_guard(PolicyGuard(
  allow_agent_tasks={"processor":["compute_stats"], "writer":["write_report"]},
  default_allow=False,
))
```

Examples
- Self-contained demos in examples/, each with demo.py and data/ vs artifacts/
- Try Tools pipeline: `uv run python examples/04_tools_pipeline/demo.py`
- Try Local docs: `uv run python examples/05_local_docs/demo.py`

Web UI (minimal)
```bash
uv sync --extra ui
AGENTICFLOW_LOG_LEVEL=WARNING uv run python examples/webui/run_server.py
# Visit http://127.0.0.1:8000
```

Troubleshooting
- Use `AGENTICFLOW_LOG_LEVEL=DEBUG` for verbose logs
- Validation errors include hints (e.g., "hint: add 'foo' to params") when jsonschema is installed
