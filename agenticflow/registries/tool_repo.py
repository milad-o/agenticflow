"""ToolRepo: curated pool/catalog of tool factories and metadata.

This repo is environment-agnostic and only exposes metadata and factories.
Flow installs tool instances from this repo into its ToolRegistry.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel
from langchain_core.tools import BaseTool

# Import tool classes for factories
from langchain_community.tools.file_management import ReadFileTool, WriteFileTool
from langchain_community.tools import ShellTool
from agenticflow.tools.file.file_tools import ReadTextFastTool, ReadBytesFastTool, WriteTextAtomicTool
from agenticflow.tools.search.search_tools import (
    FileStatTool,
    RegexSearchTool,
    RegexSearchDirTool,
    DirTreeTool,
    FindFilesTool,
)
try:
    from agenticflow.tools.large_file_streaming import StreamingFileReaderTool
except Exception:
    StreamingFileReaderTool = None  # type: ignore


class RepoToolMeta(BaseModel):
    name: str
    description: str = ""
    tags: Set[str] = set()
    capabilities: Set[str] = set()
    factory: Callable[[], BaseTool]


class ToolRepo:
    def __init__(self) -> None:
        self._tools: Dict[str, RepoToolMeta] = {}
        self._sets: Dict[str, List[str]] = {}
        self._register_defaults()

    def _register(self, meta: RepoToolMeta) -> None:
        self._tools[meta.name] = meta

    def _register_defaults(self) -> None:
        # Filesystem basics
        self._register(
            RepoToolMeta(
                name="read_file",
                description="Read contents of a file",
                tags={"filesystem", "read"},
                capabilities={"file_access"},
                factory=lambda: ReadFileTool(),
            )
        )
        self._register(
            RepoToolMeta(
                name="write_file",
                description="Write content to a file",
                tags={"filesystem", "write"},
                capabilities={"file_access"},
                factory=lambda: WriteFileTool(),
            )
        )
        self._register(
            RepoToolMeta(
                name="mkdir",
                description="Create a directory (mkdir -p)",
                tags={"filesystem", "write"},
                capabilities={"file_access"},
                factory=lambda: _MkdirTool(),
            )
        )
        self._register(
            RepoToolMeta(
                name="list_dir",
                description="List files in a directory (non-recursive)",
                tags={"filesystem", "read"},
                capabilities={"file_access"},
                factory=lambda: _ListDirTool(),
            )
        )
        self._register(
            RepoToolMeta(
                name="list_directory",
                description="List files in a directory (non-recursive)",
                tags={"filesystem", "read"},
                capabilities={"file_access"},
                factory=lambda: _ListDirectoryTool(),
            )
        )

        # Fast file tools
        self._register(
            RepoToolMeta(
                name="read_text_fast",
                description="Read text file via pathlib (fast)",
                tags={"filesystem", "read", "fast"},
                capabilities={"file_access"},
                factory=lambda: ReadTextFastTool(),
            )
        )
        self._register(
            RepoToolMeta(
                name="read_bytes_fast",
                description="Read bytes via pathlib (fast)",
                tags={"filesystem", "read", "fast"},
                capabilities={"file_access"},
                factory=lambda: ReadBytesFastTool(),
            )
        )
        self._register(
            RepoToolMeta(
                name="write_text_atomic",
                description="Write text atomically via temp+rename",
                tags={"filesystem", "write", "fast"},
                capabilities={"file_access"},
                factory=lambda: WriteTextAtomicTool(),
            )
        )

        # Search/dir tools
        self._register(
            RepoToolMeta(
                name="file_stat",
                description="Return file metadata (exists, size_bytes, is_dir)",
                tags={"filesystem", "stat"},
                capabilities={"file_access"},
                factory=lambda: FileStatTool(),
            )
        )
        if StreamingFileReaderTool is not None:
            self._register(
                RepoToolMeta(
                    name="streaming_file_reader",
                    description="Stream-read large files in chunks with progress",
                    tags={"filesystem", "read", "stream"},
                    capabilities={"file_access"},
                    factory=lambda: StreamingFileReaderTool(),
                )
            )
        self._register(
            RepoToolMeta(
                name="regex_search_file",
                description="Search a file with a regex. Supports flags, context, max matches.",
                tags={"filesystem", "search"},
                capabilities={"file_access"},
                factory=lambda: RegexSearchTool(),
            )
        )
        self._register(
            RepoToolMeta(
                name="regex_search_dir",
                description="Recursively search a directory for a regex pattern with glob, ext filters, and context.",
                tags={"filesystem", "search"},
                capabilities={"file_access", "dir_walk"},
                factory=lambda: RegexSearchDirTool(),
            )
        )
        self._register(
            RepoToolMeta(
                name="dir_tree",
                description="List directory tree with depth, ext filters, and limits.",
                tags={"filesystem", "walk"},
                capabilities={"dir_walk"},
                factory=lambda: DirTreeTool(),
            )
        )
        self._register(
            RepoToolMeta(
                name="find_files",
                description="Find files by glob/regex/size filters.",
                tags={"filesystem", "search"},
                capabilities={"search", "dir_walk"},
                factory=lambda: FindFilesTool(),
            )
        )

        # Shell
        self._register(
            RepoToolMeta(
                name="shell",
                description="Execute shell commands",
                tags={"system", "execution"},
                capabilities={"system_access"},
                factory=lambda: ShellTool(),
            )
        )

        # CSV (optional)
        try:
            from agenticflow.tools.data.csv_tools import MergeCsvTool, ValidateCsvJoinTool, PandasChunkAggregateTool  # noqa: F401

            self._register(
                RepoToolMeta(
                    name="merge_csv",
                    description="Merge two CSV files by join keys.",
                    tags={"csv", "merge", "filesystem"},
                    capabilities={"file_read", "file_write"},
                    factory=lambda: MergeCsvTool(),
                )
            )
            self._register(
                RepoToolMeta(
                    name="validate_csv_join",
                    description="Validate a CSV join (row/key counts).",
                    tags={"csv", "validate"},
                    capabilities={"file_read"},
                    factory=lambda: ValidateCsvJoinTool(),
                )
            )
            self._register(
                RepoToolMeta(
                    name="pandas_chunk_aggregate",
                    description="Compute grouped aggregations over a large CSV using pandas (chunked).",
                    tags={"csv", "aggregate", "analysis", "pandas"},
                    capabilities={"compute", "file_read"},
                    factory=lambda: PandasChunkAggregateTool(),
                )
            )
        except Exception:
            pass

        # toolsets addition for csv analysis
        if "csv_chunk_aggregate" in self._tools or "pandas_chunk_aggregate" in self._tools:
            names = []
            if "pandas_chunk_aggregate" in self._tools:
                names.append("pandas_chunk_aggregate")
            if "csv_chunk_aggregate" in self._tools:
                names.append("csv_chunk_aggregate")
            self._sets["csv_analysis"] = names

        # Vector search using LangChain's built-in Chroma support
        # Note: Using langchain_community.vectorstores.Chroma directly instead of custom implementation

        # Define default toolsets (groups) after all tools are registered
        self._sets["filesystem"] = [
            "mkdir",
            "read_text_fast",
            "read_bytes_fast", 
            "write_text_atomic",
            "file_stat",
            "find_files",
            "dir_tree",
            "regex_search_dir",
            "regex_search_file",
            "list_dir",
            "list_directory",
        ]
        self._sets["shell"] = ["shell"]
        # Add CSV set if tools are available
        if "merge_csv" in self._tools:
            self._sets["csv"] = ["merge_csv", "validate_csv_join"]
        # Vector set - using LangChain's built-in vector stores
        # Note: Vector operations handled directly via langchain_community.vectorstores

    def list(self) -> Dict[str, RepoToolMeta]:
        return self._tools.copy()

    def by_names(self, names: List[str]) -> List[RepoToolMeta]:
        return [self._tools[n] for n in names if n in self._tools]

    def by_tags(self, tags: Set[str]) -> List[RepoToolMeta]:
        out: List[RepoToolMeta] = []
        for m in self._tools.values():
            if m.tags & tags:
                out.append(m)
        return out

    def instantiate(self, names: Optional[List[str]] = None, tags: Optional[Set[str]] = None) -> List[BaseTool]:
        metas: List[RepoToolMeta]
        if names:
            metas = self.by_names(names)
        elif tags:
            metas = self.by_tags(tags)
        else:
            metas = []
        tools: List[BaseTool] = []
        for m in metas:
            try:
                tools.append(m.factory())
            except Exception:
                pass
        return tools

    def instantiate_set(self, set_name: str) -> List[BaseTool]:
        """Instantiate all tools in a named toolset."""
        names = self._sets.get(set_name, [])
        tools: List[BaseTool] = []
        for name in names:
            if name in self._tools:
                try:
                    tools.append(self._tools[name].factory())
                except Exception:
                    pass
        return tools

    def list_sets(self) -> Dict[str, List[str]]:
        """Return all available toolsets and their tool names."""
        return {k: list(v) for k, v in self._sets.items()}


# Lightweight in-module tool definitions (kept private)
from langchain_core.tools import BaseTool as _Base
from pathlib import Path as _Path


class _ListDirTool(_Base):
    name: str = "list_dir"
    description: str = "List files in a directory (non-recursive)"

    def _run(self, dir_path: str = ".") -> str:  # type: ignore[override]
        p = _Path(dir_path)
        if not p.exists() or not p.is_dir():
            return f"Directory not found: {dir_path}"
        return "\n".join(sorted([f.name for f in p.iterdir()]))


class _ListDirectoryTool(_Base):
    name: str = "list_directory"
    description: str = "List files in a directory (non-recursive)"

    def _run(self, path: str = ".") -> str:  # type: ignore[override]
        p = _Path(path)
        if not p.exists() or not p.is_dir():
            return f"Directory not found: {path}"
        return "\n".join(sorted([f.name for f in p.iterdir()]))


class _MkdirTool(_Base):
    name: str = "mkdir"
    description: str = "Create a directory (like mkdir -p)"

    def _run(self, dir_path: str) -> str:  # type: ignore[override]
        try:
            guard = getattr(self, "_path_guard", None)
            target = dir_path
            if guard:
                target = guard.resolve(dir_path, mode="write")
            p = _Path(target)
            p.mkdir(parents=True, exist_ok=True)
            return f"Created directory: {p}"
        except Exception as e:
            return f"Mkdir error: {e}"