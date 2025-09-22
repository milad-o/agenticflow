from __future__ import annotations

from typing import Iterable, Optional

from ..orchestration.core.orchestrator import WorkflowDefinition
from .debug import WorkflowSummary


def mermaid_from_definition(defn: WorkflowDefinition) -> str:
    lines = ["flowchart TD"]
    # Nodes
    for t in defn.tasks:
        label = f"{t.task_id}\\n({t.agent_id}:{t.task_type})"
        lines.append(f'  {t.task_id}["{label}"]')
    # Edges
    for t in defn.tasks:
        for dep in t.dependencies:
            lines.append(f"  {dep} --> {t.task_id}")
    return "\n".join(lines)


def mermaid_with_status(defn: WorkflowDefinition, summary: Optional[WorkflowSummary]) -> str:
    m = mermaid_from_definition(defn)
    if not summary:
        return m
    # basic classes: completed, failed, in_progress
    class_defs = [
        "classDef completed fill:#dfffd8,stroke:#0a0;",
        "classDef failed fill:#ffd8d8,stroke:#a00;",
        "classDef in_progress fill:#d8e8ff,stroke:#05c;",
    ]
    # We don't have per-task status in summary; approximate by overall status
    cls = summary.status or "in_progress"
    class_assign = f"class {' '.join([t.task_id for t in defn.tasks])} {cls};"
    return m + "\n" + "\n".join(class_defs + [class_assign])