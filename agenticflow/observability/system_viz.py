from __future__ import annotations

from typing import Dict, List


def mermaid_system(agents: List[str], tools_by_agent: Dict[str, List[str]] | None = None, task_types_by_agent: Dict[str, List[str]] | None = None) -> str:
    tools_by_agent = tools_by_agent or {}
    task_types_by_agent = task_types_by_agent or {}
    lines: List[str] = ["flowchart LR"]
    # Agents as rounded rectangles
    for a in agents:
        lines.append(f'  {a}(["Agent: {a}"])')
        lines.append(f"  class {a} agent;")
    # Tools as parallelograms linked from agents
    lines.append("  classDef agent fill:#eef7ff,stroke:#05c;")
    lines.append("  classDef tool fill:#f9f0d0,stroke:#b98;")
    lines.append("  classDef task fill:#e8ffe8,stroke:#0a0;")
    for a, tools in tools_by_agent.items():
        for t in tools:
            tnode = f"tool_{a}_{t}".replace("-","_")
            lines.append(f'  {tnode}[/"Tool: {t}"/]')
            lines.append(f"  class {tnode} tool;")
            lines.append(f"  {a} --> {tnode}")
    # Task types as capsules
    for a, ttypes in task_types_by_agent.items():
        for tt in ttypes:
            n = f"task_{a}_{tt}".replace("-","_")
            lines.append(f'  {n}(["Task: {tt}"])')
            lines.append(f"  class {n} task;")
            lines.append(f"  {a} --> {n}")
    return "\n".join(lines)


def dot_system(agents: List[str], tools_by_agent: Dict[str, List[str]] | None = None, task_types_by_agent: Dict[str, List[str]] | None = None) -> str:
    tools_by_agent = tools_by_agent or {}
    task_types_by_agent = task_types_by_agent or {}
    lines: List[str] = ["digraph G {", "  rankdir=LR;", "  node [shape=box, style=rounded];"]
    # Agents
    for a in agents:
        lines.append(f'  "{a}" [label="Agent: {a}", shape=box, style="rounded,filled", fillcolor="#eef7ff"];')
    # Tools
    for a, tools in tools_by_agent.items():
        for t in tools:
            tn = f"tool::{a}::{t}"
            lines.append(f'  "{tn}" [label="Tool: {t}", shape=parallelogram, style=filled, fillcolor="#f9f0d0"];')
            lines.append(f'  "{a}" -> "{tn}";')
    # Task types
    for a, ttypes in task_types_by_agent.items():
        for tt in ttypes:
            tn = f"task::{a}::{tt}"
            lines.append(f'  "{tn}" [label="Task: {tt}", shape=oval, style=filled, fillcolor="#e8ffe8"];')
            lines.append(f'  "{a}" -> "{tn}";')
    lines.append("}")
    return "\n".join(lines)