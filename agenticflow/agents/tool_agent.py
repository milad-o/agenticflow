from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from .base.agent import Agent
from ..security.context import SecurityContext
from .tools.base import Tool, ToolResult


class ToolAgent(Agent):
    def __init__(self, agent_id: str, tools: Dict[str, Tool], *, security: Optional[SecurityContext] = None) -> None:
        super().__init__(agent_id)
        self.tools = tools
        self.security = security

    async def perform_task(self, task_type: str, params: Dict[str, Any]):
        tool_name = params.get("tool") or task_type
        tool = self.tools.get(tool_name)
        if not tool:
            return {"ok": False, "error": f"tool '{tool_name}' not found"}
        if self.security is not None:
            await self.security.authorize("use:tool", f"{self.agent_id}:{tool_name}")
        # Orchestrator enforces timeouts; we call tool directly
        res: ToolResult = await tool.invoke(**{k: v for k, v in params.items() if k != "tool"})
        return {"ok": res.ok, **res.data}