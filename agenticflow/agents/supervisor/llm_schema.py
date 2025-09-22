from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from agenticflow.orchestration.core.orchestrator import WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.agents.capabilities.matcher import CapabilityMatcher


@dataclass
class PlannedTask:
    id: str
    type: str
    capability: Optional[str]
    params: Dict[str, Any]
    dependencies: Set[str]


def _normalize_task(raw: Dict[str, Any], index: int) -> PlannedTask:
    tid = str(raw.get("id") or f"t{index}")
    ttype = str(raw.get("type") or raw.get("task_type") or raw.get("capability") or raw.get("cap") or "noop")
    cap = raw.get("capability") or raw.get("cap")
    params = raw.get("params") or raw.get("parameters") or {}
    deps_list = raw.get("deps") or raw.get("dependencies") or []
    deps = {str(d) for d in deps_list}
    return PlannedTask(id=tid, type=str(ttype), capability=str(cap) if cap else None, params=dict(params), dependencies=deps)


async def parse_plan(text: str, *, matcher: CapabilityMatcher, default_agent: str = "analyst") -> WorkflowDefinition:
    """Parse and validate an LLM-produced plan.

    Accepts a JSON string with a top-level {"tasks": [...]} structure, where each task may contain:
    - id (optional) -> auto-generated as t{index}
    - type (optional) -> defaults to capability or "noop"
    - capability (optional) -> used to select agent via matcher
    - params (optional) -> dict
    - deps / dependencies (optional) -> list of ids
    """
    data = json.loads(text)
    tasks_raw = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks_raw, list) or not tasks_raw:
        # Empty plan -> noop single task on default agent
        return WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id=default_agent, task_type="noop", params={})])

    planned: List[PlannedTask] = []
    for i, raw in enumerate(tasks_raw, start=1):
        if not isinstance(raw, dict):
            continue
        planned.append(_normalize_task(raw, i))

    # Resolve agent IDs via capability matcher when provided
    wf_tasks: List[TaskNode] = []
    seen_ids: Set[str] = set()
    for pt in planned:
        agent_id = default_agent
        if pt.capability:
            try:
                resolved = await matcher.find_agent_for(pt.capability)
                if resolved:
                    agent_id = resolved
            except Exception:
                pass
        # Deduplicate ids if needed
        tid = pt.id if pt.id not in seen_ids else f"{pt.id}-{len(seen_ids)+1}"
        seen_ids.add(tid)
        wf_tasks.append(
            TaskNode(
                task_id=tid,
                agent_id=agent_id,
                task_type=pt.type or (pt.capability or "noop"),
                params=pt.params,
                dependencies=pt.dependencies,
            )
        )

    return WorkflowDefinition(tasks=wf_tasks)
