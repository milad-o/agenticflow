"""Observability reporter for structured events.

Provides a tiny façade over structlog to standardize fields across Flow/Orchestrator/Agent.
"""
from __future__ import annotations

import structlog
from typing import Any, Dict, Optional


def _logger():
    return structlog.get_logger()


class Reporter:
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id
        self._transcript: list[str] = []
        # Control which categories emit to console logger (others only go to transcript)
        self._emit_console = {
            "flow": True,
            "planner": False,
            "router": False,
            "orchestrator": False,
            "task": False,
            "agent": False,
        }

    def set_run_id(self, run_id: str):
        self.run_id = run_id

    def set_console_verbosity(self, minimal: bool = True, overrides: Optional[Dict[str, bool]] = None):
        """Control which reporter categories emit to console.
        minimal=True -> only 'flow' emits; others suppressed (still recorded in transcript).
        'overrides' can selectively enable categories, e.g., {"planner": True}.
        """
        if minimal:
            self._emit_console = {k: (k == "flow") for k in self._emit_console}
        if overrides:
            self._emit_console.update(overrides)

    # Internal helpers
    def _fmt_human(self, role: str, msg: str, data: Dict[str, Any]) -> str:
        try:
            import time as _time
            ts = _time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            ts = ""
        parts = [f"[{ts}] {role}: {msg}" if ts else f"{role}: {msg}"]
        # Preferentially include common fields in a readable order
        order = [
            "task_id", "agent", "assigned_agent", "depends_on", "dependencies",
            "chosen", "tool", "action", "phase", "status", "attempt",
            "edges", "nodes", "roots", "leaves", "preview", "error",
        ]
        seen = set()
        for k in order:
            if k in data and data[k] is not None:
                parts.append(f"{k}={data[k]}")
                seen.add(k)
        # Include a few remaining short keys (avoid dumping huge blobs)
        for k, v in data.items():
            if k in seen:
                continue
            try:
                s = str(v)
            except Exception:
                s = "<unrepr>"
            if len(s) <= 120 and k not in ("raw", "content", "params", "task_results", "tasks"):
                parts.append(f"{k}={s}")
        return " | ".join(parts)

    def _record(self, role: str, msg: str, **kwargs: Any) -> None:
        try:
            line = self._fmt_human(role, msg, kwargs or {})
            self._transcript.append(line)
        except Exception:
            # Best-effort only
            pass

    def dump_transcript_to_logger(self) -> None:
        if not self._transcript:
            return
        _logger().info("transcript.start", run_id=self.run_id, lines=len(self._transcript))
        for line in self._transcript:
            _logger().debug("transcript.line", run_id=self.run_id, line=line)
        _logger().info("transcript.end", run_id=self.run_id)

    def dump_transcript_to_file(self, file_path: Optional[str] = None) -> Optional[str]:
        """Write the human-readable transcript to a file and return its path."""
        if not self._transcript:
            return None
        try:
            import os
            from pathlib import Path
            if not file_path:
                log_dir = Path.cwd() / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                fname = f"flow_transcript-{self.run_id or 'default'}.log"
                file_path = str(log_dir / fname)
            with open(file_path, "w", encoding="utf-8") as f:
                for line in self._transcript:
                    f.write(line + "\n")
            return file_path
        except Exception:
            return None

    # Generic event
    def log(self, event: str, **kwargs: Any) -> None:
        _logger().info(event, run_id=self.run_id, **kwargs)

    # Convenience wrappers (each also records human-readable transcript line)
    def flow(self, msg: str, **kwargs: Any) -> None:
        self._record("Flow", msg, **kwargs)
        if self._emit_console.get("flow", False):
            self.log("flow", msg=msg, **kwargs)

    def planner(self, msg: str, **kwargs: Any) -> None:
        self._record("Planner", msg, **kwargs)
        if self._emit_console.get("planner", False):
            self.log("planner", msg=msg, **kwargs)

    def router(self, msg: str, **kwargs: Any) -> None:
        self._record("Router", msg, **kwargs)
        if self._emit_console.get("router", False):
            self.log("router", msg=msg, **kwargs)

    def orchestrator(self, msg: str, **kwargs: Any) -> None:
        self._record("Orchestrator", msg, **kwargs)
        if self._emit_console.get("orchestrator", False):
            self.log("orchestrator", msg=msg, **kwargs)

    def task(self, msg: str, **kwargs: Any) -> None:
        self._record("Task", msg, **kwargs)
        if self._emit_console.get("task", False):
            self.log("task", msg=msg, **kwargs)

    def agent(self, msg: str, **kwargs: Any) -> None:
        self._record("Agent", msg, **kwargs)
        if self._emit_console.get("agent", False):
            self.log("agent", msg=msg, **kwargs)
