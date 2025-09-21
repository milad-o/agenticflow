from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class WorkflowId:
    value: str

    @staticmethod
    def new() -> "WorkflowId":
        return WorkflowId(str(uuid4()))
