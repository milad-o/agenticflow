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

    def set_run_id(self, run_id: str):
        self.run_id = run_id

    # Generic event
    def log(self, event: str, **kwargs: Any) -> None:
        _logger().info(event, run_id=self.run_id, **kwargs)

    # Convenience wrappers
    def flow(self, msg: str, **kwargs: Any) -> None:
        self.log("flow", msg=msg, **kwargs)

    def planner(self, msg: str, **kwargs: Any) -> None:
        self.log("planner", msg=msg, **kwargs)

    def router(self, msg: str, **kwargs: Any) -> None:
        self.log("router", msg=msg, **kwargs)

    def orchestrator(self, msg: str, **kwargs: Any) -> None:
        self.log("orchestrator", msg=msg, **kwargs)

    def task(self, msg: str, **kwargs: Any) -> None:
        self.log("task", msg=msg, **kwargs)

    def agent(self, msg: str, **kwargs: Any) -> None:
        self.log("agent", msg=msg, **kwargs)