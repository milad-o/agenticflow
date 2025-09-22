from __future__ import annotations

"""
Quickstart: a minimal end-to-end run using AgenticFlow.
- Builds a tiny two-step pipeline (compute_stats -> write_report)
- Runs it locally with the Orchestrator
- Renders workflow and system diagrams into artifacts/quickstart

Run:
  uv run python quickstart.py
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path

from agenticflow.agents.utilities import StatsAgent, ReportAgent
from agenticflow.orchestration.core.orchestrator import Orchestrator
from agenticflow.orchestration.topologies import PipelineStage, PipelineTopology
from agenticflow.observability.debug import DebugInterface
from agenticflow.observability.viz import VisualizationRenderer
from examples.utils.policy_loader import load_policy


@dataclass
class Config:
    file_path: str = "README.md"
    outdir: str = "artifacts/quickstart"
    store_kind: str = "sqlite"  # or "memory"
    db_path: str = "artifacts/quickstart/events.sqlite3"


class QuickstartDemo:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.out = Path(cfg.outdir)
        self.out.mkdir(parents=True, exist_ok=True)
        # Event store
        if cfg.store_kind == "sqlite":
            from agenticflow.adapters.store.sqlite import SQLiteEventStore
            es = SQLiteEventStore(cfg.db_path)
        else:
            from agenticflow.adapters.store.memory import InMemoryEventStore
            es = InMemoryEventStore()
        self.orch = Orchestrator(
            event_store=es,
            emit_workflow_started=True,
            emit_workflow_lifecycle=True,
        )
        # Optional policy profile (dev-only)
        pol_path = Path("examples/policy_profiles/local_default.yaml")
        if pol_path.exists():
            loaded = load_policy(pol_path)
            if loaded.schema:
                self.orch.set_task_schema_registry(loaded.schema)
            if loaded.guard:
                self.orch.set_policy_guard(loaded.guard)
        # Agents
        self.orch.register_agent(StatsAgent("processor"))
        self.orch.register_agent(ReportAgent("writer"))

        # Dev: auto-apply tool schemas from registered ToolAgents (none here, safe no-op)
        try:
            from examples.utils.mcp_hardening import apply_default_tool_schemas
            apply_default_tool_schemas(self.orch)
        except Exception:
            pass

    def build(self):
        stages = [
            PipelineStage(
                task_id="stats",
                agent_id="processor",
                task_type="compute_stats",
                params={"path": self.cfg.file_path, "outdir": self.cfg.outdir},
            ),
            PipelineStage(
                task_id="report",
                agent_id="writer",
                task_type="write_report",
                params={"stats": f"{self.cfg.outdir}/stats.json", "outdir": self.cfg.outdir},
            ),
        ]
        return PipelineTopology(stages).build()

    async def run(self) -> str:
        wf = self.build()
        wf_id = await self.orch.execute_workflow(wf)
        # Render diagrams
        dbg = DebugInterface(event_store=self.orch.event_store)
        viz = VisualizationRenderer(dbg)
        await viz.render_workflow(wf_id, out_mmd=self.out / "workflow.mmd")
        await viz.render_system(
            workflow_id=wf_id,
            out_mmd=self.out / "system.mmd",
            out_dot=self.out / "system.dot",
            out_svg=self.out / "system.svg",
            agents=["processor", "writer"],
            tools_by_agent={},
            task_types_by_agent={"processor": ["compute_stats"], "writer": ["write_report"]},
        )
        return wf_id


async def main():
    cfg = Config()
    demo = QuickstartDemo(cfg)
    wf_id = await demo.run()
    print("[Quickstart] wf:", wf_id)
    print("Artifacts:", Path(cfg.outdir).resolve())


if __name__ == "__main__":
    asyncio.run(main())
