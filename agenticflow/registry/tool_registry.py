"""Tool registry for AgenticFlow."""

from typing import Any, Dict, List, Set, Optional, Callable
from langchain_core.tools import BaseTool
from langchain_community.tools import ShellTool
from langchain_community.tools.file_management import ReadFileTool, WriteFileTool
from pathlib import Path
from agenticflow.tools.ephemeral_chroma import BuildEphemeralChromaTool, QueryEphemeralChromaTool
from agenticflow.core.path_guard import PathGuard
from agenticflow.tools.search_tools import FileStatTool, RegexSearchTool, RegexSearchDirTool, DirTreeTool, FindFilesTool
from agenticflow.tools.file_tools import ReadTextFastTool, ReadBytesFastTool, WriteTextAtomicTool
from pydantic import BaseModel


class ToolMetadata(BaseModel):
    """Metadata for registered tools."""
    name: str
    description: str
    tags: Set[str] = set()
    capabilities: Set[str] = set()
    tool_class: type
    factory: Optional[Callable[..., BaseTool]] = None
    config: Dict[str, Any] = {}


class ToolRegistry:
    """Registry for discovering and managing tools."""
    
    def __init__(self) -> None:
        self._tools: Dict[str, ToolMetadata] = {}
        self._instances: Dict[str, BaseTool] = {}
        self._listeners: Dict[str, Callable[[str, ToolMetadata], None]] = {}
        self._path_guard: PathGuard | None = None
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """No-op: defaults are now provided by ToolRepo and installed explicitly by Flow."""
        return
    
    def register_tool(
        self,
        name: str,
        tool_class: type,
        description: str = "",
        tags: Optional[Set[str]] = None,
        capabilities: Optional[Set[str]] = None,
        factory: Optional[Callable[..., BaseTool]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a tool class."""
        meta = ToolMetadata(
            name=name,
            description=description or tool_class.__doc__ or "",
            tags=tags or set(),
            capabilities=capabilities or set(),
            tool_class=tool_class,
            factory=factory,
            config=config or {}
        )
        self._tools[name] = meta
        # notify listeners
        for cb in list(self._listeners.values()):
            try:
                cb("register_tool", meta)
            except Exception:
                pass
    
    def get_tool(self, name: str) -> BaseTool:
        """Get a tool instance by name."""
        if name in self._instances:
            tool = self._instances[name]
            # ensure guard is present if set after instantiation
            if self._path_guard is not None and not hasattr(tool, "_path_guard"):
                try:
                    setattr(tool, "_path_guard", self._path_guard)
                except Exception:
                    pass
            return tool
            
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not registered")
            
        metadata = self._tools[name]
        
        # Use factory if available, otherwise instantiate directly
        if metadata.factory:
            tool = metadata.factory(**metadata.config)
        else:
            tool = metadata.tool_class(**metadata.config)
        # inject guard if configured
        if self._path_guard is not None:
            try:
                setattr(tool, "_path_guard", self._path_guard)
            except Exception:
                pass
            
        self._instances[name] = tool
        return tool
    
    def get_tools_by_tags(self, tags: Set[str]) -> List[BaseTool]:
        """Get tools that match any of the given tags."""
        matching_tools = []
        for tool_name, metadata in self._tools.items():
            if metadata.tags & tags:  # Set intersection
                matching_tools.append(self.get_tool(tool_name))
        return matching_tools
    
    def get_tools_by_capabilities(self, capabilities: Set[str]) -> List[BaseTool]:
        """Get tools that have any of the given capabilities."""
        matching_tools = []
        for tool_name, metadata in self._tools.items():
            if metadata.capabilities & capabilities:
                matching_tools.append(self.get_tool(tool_name))
        return matching_tools
    
    def list_tools(self) -> Dict[str, ToolMetadata]:
        """List all registered tools with their metadata."""
        return self._tools.copy()

    def add_listener(self, callback: Callable[[str, ToolMetadata], None]) -> str:
        """Subscribe to tool registry events. Returns a listener id to remove later."""
        import uuid as _uuid
        lid = str(_uuid.uuid4())
        self._listeners[lid] = callback
        return lid

    def remove_listener(self, listener_id: str) -> None:
        self._listeners.pop(listener_id, None)
    
    def get_tools_by_names(self, names: List[str]) -> List[BaseTool]:
        """Get tool instances by their names."""
        return [self.get_tool(name) for name in names if name in self._tools]

    def register_tool_instance(
        self,
        tool: BaseTool,
        description: str = "",
        tags: Optional[Set[str]] = None,
        capabilities: Optional[Set[str]] = None,
    ) -> None:
        """Register a concrete tool instance (preferred when already constructed)."""
        name = getattr(tool, "name", None) or tool.__class__.__name__
        meta = ToolMetadata(
            name=name,
            description=description or getattr(tool, "description", "") or tool.__doc__ or "",
            tags=tags or set(),
            capabilities=capabilities or set(),
            tool_class=type(tool),
            factory=lambda: tool,
            config={},
        )
        # inject guard if configured
        if self._path_guard is not None:
            try:
                setattr(tool, "_path_guard", self._path_guard)
            except Exception:
                pass
        self._tools[name] = meta
        self._instances[name] = tool
        # notify listeners
        for cb in list(self._listeners.values()):
            try:
                cb("register_tool", meta)
            except Exception:
                pass

    def get_all_tools(self) -> List[BaseTool]:
        """Return all registered tool instances (constructing if needed)."""
        tools: List[BaseTool] = []
        for name in list(self._tools.keys()):
            tools.append(self.get_tool(name))
        return tools

    def set_path_guard(self, guard: PathGuard) -> None:
        """Attach a PathGuard to all current and future tool instances."""
        self._path_guard = guard
        # update existing instances
        for tool in list(self._instances.values()):
            try:
                setattr(tool, "_path_guard", guard)
            except Exception:
                pass
