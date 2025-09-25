"""PathGuard: enforce a workspace root and read/write policy for filesystem tools.

Usage:
- Instantiate PathGuard(workspace_root: str | Path, allow_read_outside: bool = False)
- Inject into tools via ToolRegistry so each tool can consult self._path_guard if present.

Semantics:
- write operations (creating/modifying files/dirs) MUST be within workspace_root.
- read operations are allowed within workspace_root; outside reads are permitted only if allow_read_outside=True.
- resolve() returns a normalized absolute path or raises ValueError with a clear policy error.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional


Mode = Literal["read", "write"]


class PathGuard:
    def __init__(self, workspace_root: str | Path, allow_read_outside: bool = False) -> None:
        root = Path(workspace_root).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"PathGuard workspace_root must be an existing directory: {workspace_root}")
        self.workspace_root: Path = root
        self.allow_read_outside: bool = bool(allow_read_outside)

    def _is_within(self, p: Path) -> bool:
        try:
            _ = p.resolve().relative_to(self.workspace_root)
            return True
        except Exception:
            return False

    def resolve(self, candidate: str | Path, mode: Mode) -> str:
        """Resolve a candidate path under policy.
        - Returns absolute string path if allowed.
        - Raises ValueError if policy would be violated.
        """
        candidate_path = Path(candidate)
        
        # If the path is relative, resolve it relative to workspace root
        # If the path is absolute, use it as-is
        if candidate_path.is_absolute():
            p = candidate_path.resolve()
        else:
            # Relative path - resolve relative to workspace root
            p = (self.workspace_root / candidate_path).resolve()
        
        within = self._is_within(p)
        if mode == "write":
            if not within:
                raise ValueError(
                    f"Write outside workspace is forbidden. Candidate: {p}, workspace: {self.workspace_root}"
                )
            return str(p)
        # read
        if within or self.allow_read_outside:
            return str(p)
        raise ValueError(
            f"Read outside workspace is not allowed by policy. Candidate: {p}, workspace: {self.workspace_root}"
        )
