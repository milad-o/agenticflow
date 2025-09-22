from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


@dataclass
class ToolResult:
    ok: bool
    data: Dict[str, Any]


class Tool(Protocol):
    name: str
    schema: Optional[Dict[str, Any]]

    async def invoke(self, **kwargs) -> ToolResult: ...