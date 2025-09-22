from __future__ import annotations

"""
Dev-only MCP hardening helpers:
- apply_default_tool_schemas(orch): inspect registered ToolAgents and build a TaskSchemaRegistry
  from their tool.schema definitions. Merge with existing registry if present.
"""

from typing import Dict

from agenticflow.agents.tool_agent import ToolAgent
from agenticflow.security.policy import TaskSchemaRegistry


def apply_default_tool_schemas(orchestrator) -> None:
    schemas: Dict[str, dict] = {}
    # Pull existing
    existing = getattr(orchestrator, "_task_schema_registry", None)
    if existing and hasattr(existing, "schemas"):
        try:
            schemas.update(dict(existing.schemas))
        except Exception:
            pass
    # Introspect agents
    for aid, agent in getattr(orchestrator, "_agents", {}).items():  # type: ignore[attr-defined]
        if isinstance(agent, ToolAgent):
            tools = getattr(agent, "tools", {})
            for name, tool in tools.items():
                sch = getattr(tool, "schema", None)
                if isinstance(sch, dict):
                    schemas[f"{aid}:{name}"] = sch
    orchestrator.set_task_schema_registry(TaskSchemaRegistry(schemas=schemas))
