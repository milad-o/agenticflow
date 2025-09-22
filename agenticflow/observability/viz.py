from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional
import shutil
import subprocess

from .debug import DebugInterface
from .graph import mermaid_with_status
from ..orchestration.core.orchestrator import WorkflowDefinition
from ..orchestration.tasks.graph import TaskNode
from .system_viz import mermaid_system, dot_system


async def reconstruct_workflow_definition(dbg: DebugInterface, workflow_id: str) -> WorkflowDefinition:
    events = await dbg.event_store.replay(workflow_id)
    start_ev = next((e for e in events if e.event_type == "workflow_started"), None)
    if not start_ev:
        return WorkflowDefinition(tasks=[])
    tasks = start_ev.payload.get("tasks", [])
    nodes: List[TaskNode] = []
    for td in tasks:
        nodes.append(
            TaskNode(
                task_id=str(td["task_id"]),
                agent_id=str(td["agent_id"]),
                task_type=str(td["task_type"]),
                params=dict(td.get("params", {})),
                dependencies=set(map(str, td.get("dependencies", []))),
                retries=int(td.get("retries", 0)),
                timeout_seconds=int(td.get("timeout_seconds", 30)),
            )
        )
    return WorkflowDefinition(tasks=nodes)


def try_write_svg_from_dot(dot_text: str, out_svg: Path) -> bool:
    if not shutil.which("dot"):
        return False
    p = subprocess.Popen(["dot", "-Tsvg", "-o", str(out_svg)], stdin=subprocess.PIPE, text=True)
    p.communicate(dot_text)
    return p.returncode == 0


async def render_workflow_mermaid(dbg: DebugInterface, workflow_id: str, out_mmd: Path) -> None:
    wf_def = await reconstruct_workflow_definition(dbg, workflow_id)
    summary = await dbg.get_workflow_summary(workflow_id)
    out_mmd.write_text(mermaid_with_status(wf_def, summary))


def derive_agents_and_types(wf_def: WorkflowDefinition) -> tuple[List[str], Dict[str, List[str]]]:
    agents = sorted({t.agent_id for t in wf_def.tasks})
    types: Dict[str, List[str]] = {a: [] for a in agents}
    for t in wf_def.tasks:
        if t.task_type not in types[t.agent_id]:
            types[t.agent_id].append(t.task_type)
    return agents, types


class VisualizationRenderer:
    """OOP renderer for workflow and system diagrams.

    Configure once with a DebugInterface. Provide optional tool and task maps.
    """

    def __init__(self, debug: DebugInterface) -> None:
        self.debug = debug

    async def render_workflow(self, workflow_id: str, *, out_mmd: Path) -> Path:
        await render_workflow_mermaid(self.debug, workflow_id, out_mmd)
        return out_mmd

    async def render_system(
        self,
        *,
        workflow_id: str,
        out_mmd: Path,
        out_dot: Path | None = None,
        out_svg: Path | None = None,
        agents: List[str] | None = None,
        tools_by_agent: Dict[str, List[str]] | None = None,
        task_types_by_agent: Dict[str, List[str]] | None = None,
    ) -> Dict[str, Path]:
        wf_def = await reconstruct_workflow_definition(self.debug, workflow_id)
        if agents is None:
            agents, derived_types = derive_agents_and_types(wf_def)
        else:
            derived_types = {}
        if task_types_by_agent is None:
            task_types_by_agent = derived_types
        tools_by_agent = tools_by_agent or {}
        mmd = mermaid_system(agents, tools_by_agent=tools_by_agent, task_types_by_agent=task_types_by_agent)
        out_mmd.write_text(mmd)
        written = {"mermaid": out_mmd}
        if out_dot is not None:
            dot = dot_system(agents, tools_by_agent=tools_by_agent, task_types_by_agent=task_types_by_agent)
            out_dot.write_text(dot)
            written["dot"] = out_dot
            if out_svg is not None:
                if try_write_svg_from_dot(dot, out_svg):
                    written["svg"] = out_svg
        return written
