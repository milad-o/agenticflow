"""ToolSet: a named bundle of tools.

A ToolSet can be registered or passed to Flow.register_tools so that
all tools within the set are registered in one call.

Duck-typing is supported: any object with an `instantiate()` method that
returns a list of BaseTool will be treated as a ToolSet.
"""
from __future__ import annotations

from typing import Callable, List
from langchain_core.tools import BaseTool


class ToolSet:
    def __init__(self, name: str, factory: Callable[[], List[BaseTool]]):
        self.name = name
        self._factory = factory

    def instantiate(self) -> List[BaseTool]:
        return list(self._factory())