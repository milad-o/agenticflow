"""Tool registry for AgenticFlow."""

from typing import Any, Dict, List, Set, Optional, Callable
from langchain_core.tools import BaseTool
from langchain_community.tools import ShellTool
from langchain_community.tools.file_management import ReadFileTool, WriteFileTool
from pathlib import Path
from agenticflow.tools.ephemeral_chroma import BuildEphemeralChromaTool, QueryEphemeralChromaTool
from agenticflow.tools.search_tools import FileStatTool, RegexSearchTool, RegexSearchDirTool, DirTreeTool, FindFilesTool
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
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register default LangChain tools."""
        # File tools
        self.register_tool(
            "read_file",
            ReadFileTool,
            description="Read contents of a file",
            tags={"filesystem", "read"},
            capabilities={"file_access"}
        )
        
        self.register_tool(
            "write_file", 
            WriteFileTool,
            description="Write content to a file",
            tags={"filesystem", "write"},
            capabilities={"file_access"}
        )
        
        # Shell tool
        self.register_tool(
            "shell",
            ShellTool,
            description="Execute shell commands",
            tags={"system", "execution"},
            capabilities={"system_access"}
        )
        
        # Simple Python directory listing tools (aliases)
        class ListDirTool(BaseTool):
            name: str = "list_dir"
            description: str = "List files in a directory (non-recursive)"
            def _run(self, dir_path: str = ".") -> str:  # type: ignore[override]
                p = Path(dir_path)
                if not p.exists() or not p.is_dir():
                    return f"Directory not found: {dir_path}"
                return "\n".join(sorted([f.name for f in p.iterdir()]))
        class ListDirectoryTool(BaseTool):
            name: str = "list_directory"
            description: str = "List files in a directory (non-recursive)"
            def _run(self, path: str = ".") -> str:  # type: ignore[override]
                p = Path(path)
                if not p.exists() or not p.is_dir():
                    return f"Directory not found: {path}"
                return "\n".join(sorted([f.name for f in p.iterdir()]))
        self.register_tool(
            "list_dir",
            ListDirTool,
            description="List files in a directory (alias)",
            tags={"filesystem", "read"},
            capabilities={"file_access"}
        )
        self.register_tool(
            "list_directory",
            ListDirectoryTool,
            description="List files in a directory",
            tags={"filesystem", "read"},
            capabilities={"file_access"}
        )

        # Mkdir tool (safe, non-destructive if exists)
        class MkdirTool(BaseTool):
            name: str = "mkdir"
            description: str = "Create a directory (like mkdir -p)"
            def _run(self, dir_path: str) -> str:  # type: ignore[override]
                p = Path(dir_path)
                try:
                    p.mkdir(parents=True, exist_ok=True)
                    return f"Created directory: {p}"
                except Exception as e:
                    return f"Mkdir error: {e}"
        self.register_tool(
            "mkdir",
            MkdirTool,
            description="Create a directory (mkdir -p)",
            tags={"filesystem", "write"},
            capabilities={"file_access"}
        )

        # File stat & regex search
        self.register_tool(
            "file_stat",
            FileStatTool,
            description="Return file metadata (exists, size_bytes, is_dir)",
            tags={"filesystem", "stat"},
            capabilities={"file_access"}
        )
        self.register_tool(
            "regex_search_file",
            RegexSearchTool,
            description="Search a file with a regex. Supports flags, context, max matches.",
            tags={"filesystem", "search"},
            capabilities={"file_access"}
        )
        self.register_tool(
            "regex_search_dir",
            RegexSearchDirTool,
            description="Recursively search a directory for a regex pattern with glob, ext filters, and context.",
            tags={"filesystem", "search"},
            capabilities={"file_access", "dir_walk"}
        )
        self.register_tool(
            "dir_tree",
            DirTreeTool,
            description="List directory tree with depth, ext filters, and limits.",
            tags={"filesystem", "walk"},
            capabilities={"dir_walk"}
        )
        self.register_tool(
            "find_files",
            FindFilesTool,
            description="Find files by glob/regex/size filters.",
            tags={"filesystem", "search"},
            capabilities={"search", "dir_walk"}
        )

        # Ephemeral Chroma tools
        builder = BuildEphemeralChromaTool()
        self._tools["build_ephemeral_chroma"] = ToolMetadata(
            name="build_ephemeral_chroma",
            description=builder.description,
            tags={"index", "retrieval", "vector"},
            capabilities={"retrieval"},
            tool_class=BuildEphemeralChromaTool,
            factory=lambda: builder,
            config={}
        )
        query_tool = QueryEphemeralChromaTool(builder)
        self._tools["query_ephemeral_chroma"] = ToolMetadata(
            name="query_ephemeral_chroma",
            description=query_tool.description,
            tags={"index", "retrieval", "vector"},
            capabilities={"retrieval"},
            tool_class=QueryEphemeralChromaTool,
            factory=lambda: query_tool,
            config={}
        )
    
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
        self._tools[name] = ToolMetadata(
            name=name,
            description=description or tool_class.__doc__ or "",
            tags=tags or set(),
            capabilities=capabilities or set(),
            tool_class=tool_class,
            factory=factory,
            config=config or {}
        )
    
    def get_tool(self, name: str) -> BaseTool:
        """Get a tool instance by name."""
        if name in self._instances:
            return self._instances[name]
            
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not registered")
            
        metadata = self._tools[name]
        
        # Use factory if available, otherwise instantiate directly
        if metadata.factory:
            tool = metadata.factory(**metadata.config)
        else:
            tool = metadata.tool_class(**metadata.config)
            
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
    
    def get_tools_by_names(self, names: List[str]) -> List[BaseTool]:
        """Get tool instances by their names."""
        return [self.get_tool(name) for name in names if name in self._tools]