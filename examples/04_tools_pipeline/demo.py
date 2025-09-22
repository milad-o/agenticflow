from __future__ import annotations

"""
OOP runner for the Tools Pipeline example, with parameters set in-script.
Self-contained: builds agents, orchestrator, and workflow, then renders artifacts.

Run: uv run python examples/04_tools_pipeline/demo.py
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from agenticflow.agents.tool_agent import ToolAgent
from agenticflow.agents.tools.builtin import FSReadTool
from agenticflow.agents.utilities import StatsAgent, ReportAgent
from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.observability.debug import DebugInterface
from agenticflow.observability.viz import VisualizationRenderer
from examples.utils.policy_loader import load_policy


@dataclass
class Config:
    file_path: str = str(Path(__file__).parent / "data" / "input.txt")
    outdir: str = str(Path(__file__).parent / "artifacts")
    store_kind: str = "sqlite"  # "sqlite" or "memory"
    db_path: Optional[str] = str(Path(__file__).parent / "events.sqlite3")
    max_bytes: int = 200_000


class ToolsPipelineDemo:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.out = Path(cfg.outdir)
        self.out.mkdir(parents=True, exist_ok=True)

        # Event store and orchestrator
        if cfg.store_kind == "sqlite":
            from agenticflow.adapters.store.sqlite import SQLiteEventStore
            es = SQLiteEventStore(cfg.db_path or str(self.out.parent / "events.sqlite3"))
        else:
            from agenticflow.adapters.store.memory import InMemoryEventStore
            es = InMemoryEventStore()
        self.orch = Orchestrator(
            event_store=es,
            emit_workflow_started=True,
            emit_workflow_lifecycle=True,
            max_parallelism=4,
            per_agent_concurrency=1,
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
        roots = [str(Path.cwd())]
        reader_tools = {"fs_read": FSReadTool(roots=roots, default_max_bytes=cfg.max_bytes)}
        self.orch.register_agent(ToolAgent("reader", tools=reader_tools))
        self.orch.register_agent(StatsAgent("processor"))
        self.orch.register_agent(ReportAgent("writer"))

        # Dev: auto-apply tool schemas from registered ToolAgents
        try:
            from examples.utils.mcp_hardening import apply_default_tool_schemas
            apply_default_tool_schemas(self.orch)
        except Exception:
            pass

    def build_workflow(self) -> WorkflowDefinition:
        file_path = self.cfg.file_path
        outdir = self.cfg.outdir
        tasks = [
            TaskNode(
                task_id="read",
                agent_id="reader",
                task_type="fs_read",
                params={"path": file_path, "max_bytes": self.cfg.max_bytes},
            ),
            TaskNode(
                task_id="stats",
                agent_id="processor",
                task_type="compute_stats",
                params={"path": file_path, "outdir": outdir},
                dependencies={"read"},
            ),
            TaskNode(
                task_id="report",
                agent_id="writer",
                task_type="write_report",
                params={"stats": f"{outdir}/stats.json", "outdir": outdir},
                dependencies={"stats"},
            ),
        ]
        return WorkflowDefinition(tasks=tasks)

    async def run(self) -> str:
        wf = self.build_workflow()
        wf_id = await self.orch.execute_workflow(wf)

        # Write content artifact from task result (demo-only; accesses in-memory results)
        try:
            content = self.orch._task_results[wf_id]["read"].get("content")  # type: ignore[attr-defined]
            if content:
                (self.out / "fetched_content.txt").write_text(str(content))
        except Exception:
            pass

        # Render diagrams
        dbg = DebugInterface(event_store=self.orch.event_store)
        viz = VisualizationRenderer(dbg)
        await viz.render_workflow(wf_id, out_mmd=self.out / "workflow.mmd")
        await viz.render_system(
            workflow_id=wf_id,
            out_mmd=self.out / "system.mmd",
            out_dot=self.out / "system.dot",
            out_svg=self.out / "system.svg",
            agents=["reader", "processor", "writer"],
            tools_by_agent={"reader": ["fs_read"]},
            task_types_by_agent={
                "reader": ["fs_read"],
                "processor": ["compute_stats"],
                "writer": ["write_report"],
            },
        )
        return wf_id


async def main():
    cfg = Config()
    demo = ToolsPipelineDemo(cfg)
    wf_id = await demo.run()
    print("[04_tools_pipeline] wf:", wf_id)
    print("Artifacts:", Path(cfg.outdir).resolve())


if __name__ == "__main__":
    asyncio.run(main())
