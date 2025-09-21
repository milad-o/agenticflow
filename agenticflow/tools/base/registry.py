from __future__ import annotations

from typing import Dict

from .tool import SecureTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, SecureTool] = {}

    def register(self, tool: SecureTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> SecureTool:
        return self._tools[name]
