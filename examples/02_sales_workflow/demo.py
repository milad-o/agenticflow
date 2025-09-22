from __future__ import annotations

"""
Self-contained OOP Sales workflow demo (no CLI).
- Reads CSV data from data/sales.csv
- Agent 1 (SalesAnalyzeAgent) computes total/count and writes analysis.json
- Agent 2 (SalesReportAgent) writes a markdown report from analysis.json
- Renders workflow/system diagrams

Run: uv run python examples/02_sales_workflow/demo.py
"""

import asyncio
import csv
from dataclasses import dataclass
from pathlib import Path

from agenticflow.agents.base.agent import Agent
from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.observability.debug import DebugInterface
from agenticflow.observability.viz import VisualizationRenderer


@dataclass
class Config:
    csv_path: str = str(Path(__file__).parent / "data" / "sales.csv")
    outdir: str = str(Path(__file__).parent / "artifacts")
    store_kind: str = "sqlite"  # "sqlite" or "memory"
    db_path: str = str(Path(__file__).parent / "events.sqlite3")


class SalesAnalyzeAgent(Agent):
    async def perform_task(self, task_type, params):
        if task_type != "analyze_sales":
            return {"ok": False}
        csv_path = Path(params["csv_path"])  # format: item,amount
        total = 0.0
        count = 0
        with csv_path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    total += float(row.get("amount", 0) or 0)
                    count += 1
                except Exception:
                    continue
        outdir = Path(params.get("outdir", csv_path.parent / "artifacts"))
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "analysis.json").write_text("{\n  \"total\": %.2f,\n  \"count\": %d\n}\n" % (total, count))
        return {"ok": True, "total": total, "count": count}


class SalesReportAgent(Agent):
    async def perform_task(self, task_type, params):
        if task_type != "generate_sales_report":
            return {"ok": False}
        outdir = Path(params.get("outdir", "."))
        outdir.mkdir(parents=True, exist_ok=True)
        report = outdir / "report.md"
        # naive summary
        analysis = (outdir / "analysis.json").read_text(errors="ignore") if (outdir / "analysis.json").exists() else "{}"
        report.write_text(f"# Sales Report\n\n````json\n{analysis}\n````\n")
        return {"ok": True, "report": str(report)}


class SalesDemo:
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
        self.orch = Orchestrator(event_store=es, emit_workflow_started=True, emit_workflow_lifecycle=True)
        self.orch.register_agent(SalesAnalyzeAgent("analyst"))
        self.orch.register_agent(SalesReportAgent("reporter"))

    def build_workflow(self) -> WorkflowDefinition:
        params = {"csv_path": self.cfg.csv_path, "outdir": self.cfg.outdir}
        tasks = [
            TaskNode(task_id="analyze_sales", agent_id="analyst", task_type="analyze_sales", params=params),
            TaskNode(task_id="generate_report", agent_id="reporter", task_type="generate_sales_report", params=params, dependencies={"analyze_sales"}),
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
            agents=["analyst", "reporter"],
            tools_by_agent={},
            task_types_by_agent={"analyst": ["analyze_sales"], "reporter": ["generate_sales_report"]},
        )
        return wf_id


async def main():
    cfg = Config()
    demo = SalesDemo(cfg)
    wf_id = await demo.run()
    print("[02_sales_workflow] wf:", wf_id)
    print("Artifacts:", Path(cfg.outdir).resolve())


if __name__ == "__main__":
    asyncio.run(main())
