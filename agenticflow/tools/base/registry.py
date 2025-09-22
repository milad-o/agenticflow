from __future__ import annotations

from typing import Dict, Any

from .tool import SecureTool
from ...security.context import SecurityContext


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, SecureTool] = {}

    def register(self, tool: SecureTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> SecureTool:
        return self._tools[name]

    async def invoke(self, name: str, params: Dict[str, Any], *, security: SecurityContext, breaker=None) -> Any:
        # Authorize
        await security.authorize("invoke", f"tool:{name}")
        tool = self.get(name)

        async def _call():
            return await tool.execute(params)

        if breaker is not None:
            result = await breaker.call(_call)
        else:
            result = await _call()

        # Audit success already logged by authorize as granted; optional additional log:
        await security.audit_logger.log({
            "principal": security.principal,
            "tool": name,
            "status": "success",
        })
        return result
