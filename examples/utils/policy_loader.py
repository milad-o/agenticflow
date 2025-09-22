from __future__ import annotations

"""
Dev-only loader for task validation schemas and policy guards from YAML/JSON.
- Returns (TaskSchemaRegistry | None, PolicyGuard | None).
- Intended for examples and local development; keep core framework free of IO.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import json

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # type: ignore

from agenticflow.security.policy import TaskSchemaRegistry, PolicyGuard


@dataclass
class LoadedPolicy:
    schema: Optional[TaskSchemaRegistry]
    guard: Optional[PolicyGuard]


def _read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _load_obj(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    text = _read_text(p)
    if p.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML not installed; cannot load YAML policy file")
        data = yaml.safe_load(text)  # type: ignore
        if not isinstance(data, dict):
            raise ValueError("policy file root must be a mapping")
        return data
    # default: JSON
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("policy file root must be a mapping")
    return data


def load_policy(path: str | Path) -> LoadedPolicy:
    obj = _load_obj(path)
    schemas = obj.get("schemas") or {}
    policy = obj.get("policy") or {}

    reg = None
    guard = None

    if isinstance(schemas, dict):
        # schemas: {"agent:task": {jsonschema}}
        reg = TaskSchemaRegistry(schemas=schemas)

    if isinstance(policy, dict):
        guard = PolicyGuard(
            allow_agent_tasks=dict(policy.get("allow_agent_tasks", {})),
            deny_agent_tasks=dict(policy.get("deny_agent_tasks", {})),
            default_allow=bool(policy.get("default_allow", True)),
        )
    return LoadedPolicy(schema=reg, guard=guard)
