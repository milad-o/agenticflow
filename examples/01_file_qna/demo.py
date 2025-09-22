from __future__ import annotations

"""
Self-contained OOP runner for File QnA example (no CLI).
- Scans a directory and answers a question using an LLM client from env
  (or a provider-free noop client if AGENTICFLOW_LLM_PROVIDER=noop).
- Writes answer/citations and renders workflow/system diagrams.

Run examples:
- Provider-free: AGENTICFLOW_LLM_PROVIDER=noop uv run python examples/01_file_qna/demo.py
- With Groq (example):
  export AGENTICFLOW_LLM_PROVIDER=groq
  export GROQ_API_KEY={{GROQ_API_KEY}}
  uv run python examples/01_file_qna/demo.py
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from agenticflow.agents.base.agent import Agent
from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.observability.debug import DebugInterface
from agenticflow.observability.viz import VisualizationRenderer

from agenticflow.ai.file_qa import answer_question_over_dir
from examples.utils.provider_factory import create_llm_from_env


@dataclass
class Config:
    path: str = str(Path(__file__).parent / "data")
    question: str = "What topics are covered across these files?"
    outdir: str = str(Path(__file__).parent / "artifacts")
    ignore_globs: List[str] = None  # default applied in code
    store_kind: str = "sqlite"  # "sqlite" or "memory"
    db_path: Optional[str] = str(Path(__file__).parent / "events.sqlite3")
    max_files: int = 12
    max_bytes_per_file: int = 2000


class QnAAgent(Agent):
    async def perform_task(self, task_type, params):
        if task_type != "file_qna":
            return {"ok": False}
        path = str(params.get("path"))
        question = str(params.get("question"))
        outdir = Path(str(params.get("outdir")))
        ignore = list(params.get("ignore_globs") or ["**/artifacts/**"])  # type: ignore
        max_files = int(params.get("max_files", 12))
        max_bytes_per_file = int(params.get("max_bytes_per_file", 2000))
        outdir.mkdir(parents=True, exist_ok=True)

        llm = create_llm_from_env()
        answer, citations = await answer_question_over_dir(
            path,
            question,
            llm=llm,
            ignore_globs=ignore,
            max_files=max_files,
            max_bytes_per_file=max_bytes_per_file,
        )
        (outdir / "qa_answer.md").write_text(answer or "")
        (outdir / "qa_citations.txt").write_text("\n".join(citations))
        return {"ok": True, "answer_path": str(outdir / "qa_answer.md"), "citations": citations}


class FileQnADemo:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.out = Path(cfg.outdir)
        self.out.mkdir(parents=True, exist_ok=True)

        if cfg.store_kind == "sqlite":
            from agenticflow.adapters.store.sqlite import SQLiteEventStore
            es = SQLiteEventStore(cfg.db_path or str(Path(self.out).parent / "events.sqlite3"))
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
        self.orch.register_agent(QnAAgent("qna"))

    def build_workflow(self) -> WorkflowDefinition:
        p = {
            "path": self.cfg.path,
            "question": self.cfg.question,
            "outdir": self.cfg.outdir,
            "ignore_globs": self.cfg.ignore_globs or ["**/artifacts/**"],
            "max_files": self.cfg.max_files,
            "max_bytes_per_file": self.cfg.max_bytes_per_file,
        }
        tasks = [TaskNode(task_id="qna", agent_id="qna", task_type="file_qna", params=p)]
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
            agents=["qna"],
            tools_by_agent={},
            task_types_by_agent={"qna": ["file_qna"]},
        )
        return wf_id


async def main_async():
    cfg = Config()
    demo = FileQnADemo(cfg)
    wf_id = await demo.run()
    print("[01_file_qna] wf:", wf_id)
    print("Artifacts:", Path(cfg.outdir).resolve())


if __name__ == "__main__":
    asyncio.run(main_async())
