from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class SecureTool(ABC):
    name: str

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Any: ...
