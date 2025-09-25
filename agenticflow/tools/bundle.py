"""Pre-instantiated tool bundles for convenient registration.

Import and register these with Flow.register_tools(DEFAULT_FILESYSTEM_TOOLS), or
attach them to Agents directly via agent.register_tools(DEFAULT_FILESYSTEM_TOOLS).
"""
from __future__ import annotations

from agenticflow.tools.file_tools import ReadTextFastTool, ReadBytesFastTool, WriteTextAtomicTool
from agenticflow.tools.search_tools import (
    FileStatTool,
    RegexSearchTool,
    RegexSearchDirTool,
    DirTreeTool,
    FindFilesTool,
)

# Pre-instantiate tool objects (LangChain BaseTool instances)
DEFAULT_FILESYSTEM_TOOLS = [
    WriteTextAtomicTool(),
    ReadTextFastTool(),
    ReadBytesFastTool(),
    FileStatTool(),
    RegexSearchTool(),
    RegexSearchDirTool(),
    DirTreeTool(),
    FindFilesTool(),
]
