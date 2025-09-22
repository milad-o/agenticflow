from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Dict
import hashlib
import re
from collections import Counter

from .base.agent import Agent
from .tool_agent import ToolAgent


class ChatAgent(Agent):
    async def perform_task(self, task_type, params):
        if task_type != "chat":
            return {"ok": False}
        return {
            "ok": True,
            "message": f"[{self.agent_id} r{params.get('round',0)}] {params.get('topic','')}"
        }


class ChatToolAgent(ToolAgent):
    async def perform_task(self, task_type, params):
        if task_type == "chat":
            return {
                "ok": True,
                "message": f"[{self.agent_id} r{params.get('round',0)}] {params.get('topic','')}"
            }
        return await super().perform_task(task_type, params)


class StatsAgent(Agent):
    async def perform_task(self, task_type, params):
        if task_type != "compute_stats":
            return {"ok": False}
        p = Path(params["path"]).read_text(errors="ignore")
        words = p.split()
        lines = p.splitlines()
        sha = hashlib.sha256(p.encode()).hexdigest()
        outdir = Path(params.get("outdir", "."))
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "stats.json").write_text(
            "{\n  \"path\": \"%s\",\n  \"lines\": %d,\n  \"words\": %d,\n  \"sha256\": \"%s\"\n}\n" % (params["path"], len(lines), len(words), sha)
        )
        return {"ok": True, "stats": str(outdir / "stats.json")}


class ReportAgent(Agent):
    async def perform_task(self, task_type, params):
        if task_type != "write_report":
            return {"ok": False}
        stats_p = Path(params.get("stats", ""))
        outdir = Path(params.get("outdir", stats_p.parent))
        outdir.mkdir(parents=True, exist_ok=True)
        if stats_p.exists():
            data = stats_p.read_text(errors="ignore")
            report = outdir / "report.md"
            report.write_text("# File Report\n\n````json\n%s\n````\n" % data)
            return {"ok": True, "report": str(report)}
        return {"ok": False, "error": "stats_missing"}


class ScanAgent(Agent):
    async def perform_task(self, task_type, params):
        if task_type != "scan_files":
            return {"ok": False}
        root = Path(params["root"]).resolve()
        ignore = params.get("ignore", [])
        files = []
        import fnmatch
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(fnmatch.fnmatch(str(p), pat) for pat in ignore):
                continue
            files.append(str(p))
            if len(files) >= int(params.get("max_files", 20)):
                break
        outdir = Path(params.get("outdir", root / "artifacts"))
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "files.txt").write_text("\n".join(files))
        return {"ok": True, "files": files}


class SummarizeAgent(Agent):
    async def perform_task(self, task_type, params):
        if task_type != "write_summary":
            return {"ok": False}
        root = Path(params["root"]).resolve()
        outdir = Path(params.get("outdir", root / "artifacts"))
        ignore = params.get("ignore", [])
        max_files = int(params.get("max_files", 20))
        # Build a naive word frequency report across files
        word_re = re.compile(r"[A-Za-z]{3,}")
        cnt = Counter()
        files = []
        import fnmatch
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(fnmatch.fnmatch(str(p), pat) for pat in ignore):
                continue
            try:
                for w in word_re.findall(p.read_text(errors="ignore")):
                    cnt[w.lower()] += 1
                files.append(str(p))
            except Exception:
                continue
            if len(files) >= max_files:
                break
        top = cnt.most_common(int(params.get("top_k", 20)))
        lines = ["# Local Docs Summary", "", f"Scanned {len(files)} files under {root}", "", "Top terms:"]
        for w, c in top:
            lines.append(f"- {w}: {c}")
        lines.append("")
        lines.append("Citations:")
        for s in files:
            lines.append(f"- {s}")
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "summary.md").write_text("\n".join(lines))
        return {"ok": True, "summary": str(outdir / "summary.md")}