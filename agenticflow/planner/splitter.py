"""Heuristic atomic-task splitter (schema-preserving, generic).

Takes a list of tasks (each a dict with id, description, priority, dependencies, status)
and returns a possibly expanded list with descriptions split into atomic actions.

No hardcoded actions; purely textual heuristics based on numbering/bullets/semicolons.
"""
from __future__ import annotations

from typing import List, Dict
import re


def _extract_items(text: str) -> List[str]:
    s = text.strip()
    items: List[str] = []

    # Look for numbered list items like (1) ..., 2) ..., 1. ..., etc.
    numbered = re.findall(r"(?:^|\n|\s)(?:\(?\d+\)?[\.)]|\d+\s+-)\s+([^\n;]+)", s)
    if numbered:
        items = [it.strip().rstrip('.') for it in numbered if it.strip()]
        return items

    # Bullet-like items (- foo, • foo)
    bullets = re.findall(r"(?:^|\n|\s)(?:[-•]\s+)([^\n;]+)", s)
    if bullets:
        items = [it.strip().rstrip('.') for it in bullets if it.strip()]
        return items

    # Semicolon-separated clauses if there are multiple
    if ";" in s:
        parts = [p.strip() for p in s.split(";") if p.strip()]
        if len(parts) > 1:
            items = [p.rstrip('.') for p in parts]
            return items

    # ' and ' split (very conservative): only if long and contains ' and '
    if " and " in s and len(s) > 60:
        parts = [p.strip() for p in re.split(r"\band\b", s) if p.strip()]
        if len(parts) > 1:
            items = [p.rstrip('.') for p in parts]
            return items

    return [s]


def split_atomic(tasks: List[Dict]) -> List[Dict]:
    """Return a new list of tasks with any composite descriptions split atomically.

    - Preserves original dependencies; when a numbered ordering is detected,
      sub-items are chained in sequence; otherwise, sub-items share the same deps
      (enabling parallel execution by the orchestrator).
    - Task IDs are made unique by suffixing _1, _2, ...
    """
    new_tasks: List[Dict] = []
    for t in tasks:
        desc = str(t.get("description", ""))
        items = _extract_items(desc)
        if len(items) <= 1:
            new_tasks.append(t)
            continue

        base_id = t.get("id", "task")
        deps = list(t.get("dependencies", []) or [])
        priority = t.get("priority", 1)
        status = t.get("status", "pending")

        # If items came from an ordered list, chain deps; otherwise keep same deps
        ordered_match = re.search(r"\(?(\d+)\)?[\.)]", desc) or re.search(r"\b1\b\s*(?:[\.)-])", desc)
        prev_id = None
        for idx, item in enumerate(items, start=1):
            sub_id = f"{base_id}_{idx}"
            sub_deps = list(deps)
            if ordered_match and prev_id:
                sub_deps = [prev_id]
            new_tasks.append({
                "id": sub_id,
                "description": item,
                "required_capabilities": t.get("required_capabilities", ["general"]),
                "priority": priority,
                "dependencies": sub_deps,
                "status": status,
            })
            prev_id = sub_id
    return new_tasks