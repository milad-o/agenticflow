from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List, Set

try:
    import jsonschema  # type: ignore
    from jsonschema.exceptions import ValidationError as _JSValidationError  # type: ignore
except Exception:
    jsonschema = None  # type: ignore
    _JSValidationError = None  # type: ignore


@dataclass
class TaskSchemaRegistry:
    schemas: Dict[str, dict]  # key: f"{agent_id}:{task_type}"

    @staticmethod
    def _format_error(e: Exception) -> str:
        # jsonschema-rich formatting when available
        if _JSValidationError is not None and isinstance(e, _JSValidationError):
            path = "/".join([str(p) for p in getattr(e, "path", [])])
            msg = getattr(e, "message", str(e))
            if path:
                return f"{msg} at '{path}'"
            return msg
        return str(e)

    def validate(self, agent_id: str, task_type: str, params: dict) -> None:
        key = f"{agent_id}:{task_type}"
        schema = self.schemas.get(key)
        if not schema:
            return
        if jsonschema is not None:
            try:
                jsonschema.validate(instance=params, schema=schema)  # type: ignore
            except Exception as e:  # jsonschema ValidationError
                fe = self._format_error(e)
                # Provide simple hints for missing required
                if "is a required property" in fe:
                    # Extract property name heuristically
                    import re
                    m = re.search(r"'([^']+)' is a required property", fe)
                    if m:
                        missing = m.group(1)
                        fe = fe + f" | hint: add '{missing}' to params"
                raise ValueError(fe)
            return
        # Fallback minimal validation: enforce 'required' keys
        req = schema.get("required") if isinstance(schema, dict) else None
        if isinstance(req, list):
            missing = [k for k in req if k not in params]
            if missing:
                raise ValueError(f"missing required params: {missing}")


@dataclass
class PolicyGuard:
    """Simple allow/deny guard for agent task types.

    Configure per-agent allow/deny lists of task types. If both are provided for an agent,
    deny takes precedence. If neither is provided, default_allow controls behavior.
    """

    allow_agent_tasks: Dict[str, List[str]] | None = None
    deny_agent_tasks: Dict[str, List[str]] | None = None
    default_allow: bool = True

    def _allowed(self, agent_id: str, task_type: str) -> bool:
        deny = set((self.deny_agent_tasks or {}).get(agent_id, []))
        if task_type in deny:
            return False
        allow = (self.allow_agent_tasks or {}).get(agent_id)
        if allow is None:
            return self.default_allow
        return task_type in set(allow)

    def check(self, agent_id: str, task_type: str, params: dict) -> None:
        if not self._allowed(agent_id, task_type):
            raise PermissionError(f"policy_denied {agent_id}:{task_type}")
