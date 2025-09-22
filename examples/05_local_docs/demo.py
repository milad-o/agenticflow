from __future__ import annotations

"""
OOP runner for Local Docs Summary example with parameters in-script (no CLI).
Uses utility agents to summarize local text files under a root directory and
renders workflow and system diagrams.

Run: uv run python examples/05_local_docs/demo.py
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List

from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.observability.debug import DebugInterface
from agenticflow.observability.viz import VisualizationRenderer
from agenticflow.agents.utilities import ScanAgent, SummarizeAgent


@dataclass
class Config:
    root: str = str(Path(__file__).parent / "data")
    outdir: str = str(Path(__file__).parent / "artifacts")
    store_kind: str = "sqlite"  # "sqlite" or "memory"
    db_path: str = str(Path(__file__).parent / "events.sqlite3")
    ignore: List[str] = ("**/artifacts/**", ".git/**", ".venv/**", "**/__pycache__/**")
    max_files: int = 20
    top_k: int = 20


class LocalDocsSummaryDemo:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.out = Path(cfg.outdir)
        self.out.mkdir(parents=True, exist_ok=True)

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
            max_parallelism=2,
            per_agent_concurrency=1,
        )
        self.orch.register_agent(ScanAgent("scanner"))
        self.orch.register_agent(SummarizeAgent("summarizer"))

    def build_workflow(self) -> WorkflowDefinition:
        tasks = [
            TaskNode(
                task_id="scan",
                agent_id="scanner",
                task_type="scan_files",
                params={"root": self.cfg.root, "ignore": list(self.cfg.ignore), "outdir": self.cfg.outdir, "max_files": self.cfg.max_files},
            ),
            TaskNode(
                task_id="summary",
                agent_id="summarizer",
                task_type="write_summary",
                params={"root": self.cfg.root, "ignore": list(self.cfg.ignore), "outdir": self.cfg.outdir, "top_k": self.cfg.top_k, "max_files": self.cfg.max_files},
                dependencies={"scan"},
            ),
        ]
        return WorkflowDefinition(tasks=tasks)

    async def run(self) -> str:
        wf = self.build_workflow()
        wf_id = await self.orch.execute_workflow(wf)
        dbg = DebugInterface(event_store=self.orch.event_store)
        viz = VisualizationRenderer(dbg)
        await viz.render_workflow(wf_id, out_mmd=self.out / "workflow.mmd")
        await viz.render_system(
            workflow_id=wf_id,
            out_mmd=self.out / "system.mmd",
            out_dot=self.out / "system.dot",
            out_svg=self.out / "system.svg",
            agents=["scanner", "summarizer"],
            tools_by_agent={},
            task_types_by_agent={"scanner": ["scan_files"], "summarizer": ["write_summary"]},
        )
        return wf_id


async def main():
    cfg = Config()
    demo = LocalDocsSummaryDemo(cfg)
    wf_id = await demo.run()
    print("[05_local_docs] wf:", wf_id)
    print("Artifacts:", Path(cfg.outdir).resolve())


if __name__ == "__main__":
    asyncio.run(main())
