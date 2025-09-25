"""Custom file tools for faster file IO operations.

These are simple wrappers around pathlib that we can benchmark against
LangChain's ReadFileTool/WriteFileTool and our existing search tools.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from langchain_core.tools import BaseTool
import os
import tempfile
from agenticflow.security.validation.path_guard import PathGuard


class ReadTextFastTool(BaseTool):
    name: str = "read_text_fast"
    description: str = (
        "Read a UTF-8 text file using pathlib with errors ignored. Args: path (str), encoding (str='utf-8')."
    )

    def _run(self, path: str, encoding: str = "utf-8") -> str:  # type: ignore[override]
        # apply path guard if present
        try:
            guard = getattr(self, "_path_guard", None)
            if isinstance(guard, PathGuard):
                path = guard.resolve(path, mode="read")
        except Exception as _e:
            return f"Read error: {_e}"
        p = Path(path)
        if not p.exists() or p.is_dir():
            return f"File not found or is a directory: {path}"
        try:
            return p.read_text(encoding=encoding, errors="ignore")
        except Exception as e:
            return f"Read error: {e}"


class ReadBytesFastTool(BaseTool):
    name: str = "read_bytes_fast"
    description: str = (
        "Read a file as bytes using pathlib. Args: path (str). Returns bytes in a repr string (not base64)."
    )

    def _run(self, path: str) -> bytes:  # type: ignore[override]
        # apply path guard if present
        try:
            guard = getattr(self, "_path_guard", None)
            if isinstance(guard, PathGuard):
                path = guard.resolve(path, mode="read")
        except Exception as _e:
            return f"Read error: {_e}".encode()
        p = Path(path)
        if not p.exists() or p.is_dir():
            return f"File not found or is a directory: {path}".encode()
        try:
            return p.read_bytes()
        except Exception as e:
            return f"Read error: {e}".encode()


class WriteTextAtomicTool(BaseTool):
    name: str = "write_text_atomic"
    description: str = (
        "Write text to a file atomically by writing to a temp file then renaming. Args: path (str), content (str), encoding (str='utf-8')."
    )

    def _run(self, path: str, content: str, encoding: str = "utf-8") -> str:  # type: ignore[override]
        # apply path guard if present
        try:
            guard = getattr(self, "_path_guard", None)
            if isinstance(guard, PathGuard):
                path = guard.resolve(path, mode="write")
        except Exception as _e:
            return f"Write error: {_e}"
        target = Path(path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Create temp file in the same directory for atomic rename
            fd, tmp_path = tempfile.mkstemp(prefix=target.name + ".", dir=str(target.parent))
            try:
                with os.fdopen(fd, "w", encoding=encoding) as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, target)
            finally:
                # If replace failed for some reason, ensure temp is cleaned up
                if os.path.exists(tmp_path) and not os.path.samefile(tmp_path, target):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
            return f"Wrote {len(content)} bytes to {target}"
        except Exception as e:
            return f"Write error: {e}"
