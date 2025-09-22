from __future__ import annotations

from typing import Any, Dict

from ..base.tool import SecureTool


class EchoTool(SecureTool):
    def __init__(self) -> None:
        super().__init__("echo")

    async def execute(self, params: Dict[str, Any]) -> Any:
        return {"echo": params.get("text", "")}
