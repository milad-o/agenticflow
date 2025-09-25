"""File search and metadata tools (regex search, file stat)."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool
import fnmatch
from pathlib import Path
from agenticflow.security.validation.path_guard import PathGuard


class FileStatTool(BaseTool):
    name: str = "file_stat"
    description: str = (
        "Return basic metadata about a file. Args: path (str). "
        "Returns JSON: {'path': str, 'exists': bool, 'size_bytes': int, 'is_dir': bool}"
    )

    def _run(self, path: str) -> Dict[str, Any]:  # type: ignore[override]
        # apply path guard for read
        try:
            guard = getattr(self, "_path_guard", None)
            if isinstance(guard, PathGuard):
                path = guard.resolve(path, mode="read")
        except Exception as e:
            return {"path": path, "error": str(e)}
        try:
            st = os.stat(path)
            return {
                "path": path,
                "exists": True,
                "size_bytes": int(st.st_size),
                "is_dir": os.path.isdir(path),
            }
        except FileNotFoundError:
            return {"path": path, "exists": False, "size_bytes": 0, "is_dir": False}
        except Exception as e:
            return {"path": path, "error": str(e)}


class RegexSearchTool(BaseTool):
    name: str = "regex_search_file"
    description: str = (
        "Search a file with a regular expression. Args: path (str), pattern (str), "
        "flags (optional str, e.g., 'i' for IGNORECASE, 'm' for MULTILINE), max_matches (int, default 50), "
        "context_lines (int, default 0). Returns JSON with matches and line numbers."
    )

    def _compile(self, pattern: str, flags: Optional[str]) -> re.Pattern:
        flag_val = 0
        if flags:
            f = flags.lower()
            if 'i' in f:
                flag_val |= re.IGNORECASE
            if 'm' in f:
                flag_val |= re.MULTILINE
            if 's' in f:
                flag_val |= re.DOTALL
        return re.compile(pattern, flag_val)

    def _run(
        self,
        path: str,
        pattern: str,
        flags: Optional[str] = None,
        max_matches: int = 50,
        context_lines: int = 0,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:  # type: ignore[override]
        # apply path guard for read
        try:
            guard = getattr(self, "_path_guard", None)
            if isinstance(guard, PathGuard):
                path = guard.resolve(path, mode="read")
        except Exception as e:
            return {"error": str(e)}
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}
        if os.path.isdir(path):
            return {"error": f"Path is a directory: {path}"}

        rx = self._compile(pattern, flags)
        matches: List[Dict[str, Any]] = []
        window: List[str] = []
        line_no = 0
        try:
            with open(path, "r", encoding=encoding, errors="ignore") as f:
                for line in f:
                    line_no += 1
                    window.append(line.rstrip("\n"))
                    if len(window) > (context_lines * 2 + 1):
                        window.pop(0)
                    m = rx.search(line)
                    if m:
                        # capture context
                        if context_lines > 0:
                            # refetch from file? Keep a small sliding buffer
                            # construct context around current line
                            context_start = max(0, len(window) - 1 - context_lines)
                            ctx = window[context_start:]
                        else:
                            ctx = [line.rstrip("\n")]
                        matches.append({
                            "line": line_no,
                            "text": line.rstrip("\n"),
                            "context": ctx,
                        })
                        if len(matches) >= max_matches:
                            break
        except Exception as e:
            return {"error": str(e)}

        return {
            "path": path,
            "pattern": pattern,
            "flags": flags or "",
            "matches": matches,
            "total": len(matches),
        }


class RegexSearchDirTool(BaseTool):
    name: str = "regex_search_dir"
    description: str = (
        "Recursively search a directory for a regex pattern. Args: root_path (str), pattern (str), "
        "flags (optional 'i','m','s'), file_glob (optional, default '*'), include_exts (optional list), "
        "exclude_dirs (optional list), max_files (int default 100), max_matches (int default 500), context_lines (int default 0). "
        "Returns JSON: {'root': str, 'pattern': str, 'total': int, 'results': [{path, line, text, context}]}"
    )

    def _compile(self, pattern: str, flags: Optional[str]) -> re.Pattern:
        flag_val = 0
        if flags:
            f = flags.lower()
            if 'i' in f:
                flag_val |= re.IGNORECASE
            if 'm' in f:
                flag_val |= re.MULTILINE
            if 's' in f:
                flag_val |= re.DOTALL
        return re.compile(pattern, flag_val)

    def _run(
        self,
        root_path: str,
        pattern: str,
        flags: Optional[str] = None,
        file_glob: str = "*",
        include_exts: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
        max_files: int = 100,
        max_matches: int = 500,
        context_lines: int = 0,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:  # type: ignore[override]
        # apply path guard for read directory
        try:
            guard = getattr(self, "_path_guard", None)
            if isinstance(guard, PathGuard):
                root_path = guard.resolve(root_path, mode="read")
        except Exception as e:
            return {"error": str(e)}
        if not os.path.exists(root_path):
            return {"error": f"Path not found: {root_path}"}
        if not os.path.isdir(root_path):
            return {"error": f"Not a directory: {root_path}"}

        rx = self._compile(pattern, flags)
        exclude_dirs = set(exclude_dirs or [])
        include_exts = [e.lower() for e in (include_exts or [])]
        results: List[Dict[str, Any]] = []
        files_scanned = 0

        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                # prune excluded dirs
                dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
                for fname in filenames:
                    if not fnmatch.fnmatch(fname, file_glob):
                        continue
                    if include_exts:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext not in include_exts:
                            continue
                    fpath = os.path.join(dirpath, fname)
                    files_scanned += 1
                    if files_scanned > max_files:
                        break
                    # search this file
                    line_no = 0
                    window: List[str] = []
                    with open(fpath, "r", encoding=encoding, errors="ignore") as f:
                        for line in f:
                            line_no += 1
                            window.append(line.rstrip("\n"))
                            if len(window) > (context_lines * 2 + 1):
                                window.pop(0)
                            if rx.search(line):
                                if context_lines > 0:
                                    context_start = max(0, len(window) - 1 - context_lines)
                                    ctx = window[context_start:]
                                else:
                                    ctx = [line.rstrip("\n")]
                                results.append({
                                    "path": fpath,
                                    "line": line_no,
                                    "text": line.rstrip("\n"),
                                    "context": ctx,
                                })
                                if len(results) >= max_matches:
                                    break
                    if len(results) >= max_matches or files_scanned >= max_files:
                        break
                if len(results) >= max_matches or files_scanned >= max_files:
                    break
        except Exception as e:
            return {"error": str(e)}

        return {
            "root": root_path,
            "pattern": pattern,
            "flags": flags or "",
            "total": len(results),
            "results": results,
            "files_scanned": files_scanned,
        }


class DirTreeTool(BaseTool):
    name: str = "dir_tree"
    description: str = (
        "Walk a directory tree with depth and filters. Args: root_path (str), max_depth (int, default 2), "
        "include_exts (optional list), exclude_dirs (optional list), follow_symlinks (bool default False), max_entries (int default 500). "
        "Returns JSON: {'root': str, 'total': int, 'entries': [{path, is_dir, size_bytes, depth}]}"
    )

    def _run(
        self,
        root_path: str,
        max_depth: int = 2,
        include_exts: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
        follow_symlinks: bool = False,
        max_entries: int = 500,
    ) -> Dict[str, Any]:  # type: ignore[override]
        # apply path guard for read directory
        try:
            guard = getattr(self, "_path_guard", None)
            if isinstance(guard, PathGuard):
                root_path = guard.resolve(root_path, mode="read")
        except Exception as e:
            return {"error": str(e)}
        p = Path(root_path)
        if not p.exists() or not p.is_dir():
            return {"error": f"Not a directory: {root_path}"}
        include_exts = [e.lower() for e in (include_exts or [])]
        exclude_dirs = set(exclude_dirs or [])
        entries: List[Dict[str, Any]] = []

        root_parts = len(p.parts)
        try:
            for dirpath, dirnames, filenames in os.walk(str(p), followlinks=follow_symlinks):
                # compute depth
                depth = len(Path(dirpath).parts) - root_parts
                # prune dirs by exclude or depth
                dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
                if depth >= max_depth:
                    # do not descend further
                    dirnames[:] = []
                # add directory entry itself (once)
                if len(entries) < max_entries:
                    entries.append({
                        "path": dirpath,
                        "is_dir": True,
                        "size_bytes": 0,
                        "depth": depth,
                    })
                # files
                for fname in filenames:
                    if include_exts:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext not in include_exts:
                            continue
                    fpath = os.path.join(dirpath, fname)
                    size = 0
                    try:
                        size = os.path.getsize(fpath)
                    except Exception:
                        pass
                    entries.append({
                        "path": fpath,
                        "is_dir": False,
                        "size_bytes": int(size),
                        "depth": depth,
                    })
                    if len(entries) >= max_entries:
                        break
                if len(entries) >= max_entries:
                    break
        except Exception as e:
            return {"error": str(e)}

        return {"root": str(p), "total": len(entries), "entries": entries}


class FindFilesTool(BaseTool):
    name: str = "find_files"
    description: str = (
        "Find files by glob/regex and filters. Args: root_path (str), file_glob (str='*'), name_regex (optional str), "
        "include_exts (optional list), exclude_dirs (optional list), size_min (int, optional), size_max (int, optional), max_files (int=500). "
        "Returns JSON: {'root': str, 'total': int, 'files': [{path, size_bytes}]}"
    )

    def _run(
        self,
        root_path: str,
        file_glob: str = "*",
        name_regex: Optional[str] = None,
        include_exts: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
        size_min: Optional[int] = None,
        size_max: Optional[int] = None,
        max_files: int = 500,
    ) -> Dict[str, Any]:  # type: ignore[override]
        # apply path guard for read directory
        try:
            guard = getattr(self, "_path_guard", None)
            if isinstance(guard, PathGuard):
                root_path = guard.resolve(root_path, mode="read")
        except Exception as e:
            return {"error": str(e)}
        p = Path(root_path)
        if not p.exists() or not p.is_dir():
            return {"error": f"Not a directory: {root_path}"}
        include_exts = [e.lower() for e in (include_exts or [])]
        exclude_dirs = set(exclude_dirs or [])
        files: List[Dict[str, Any]] = []
        rx = re.compile(name_regex) if name_regex else None

        try:
            for dirpath, dirnames, filenames in os.walk(str(p)):
                dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
                for fname in filenames:
                    if not fnmatch.fnmatch(fname, file_glob):
                        continue
                    if include_exts:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext not in include_exts:
                            continue
                    if rx and not rx.search(fname):
                        continue
                    fpath = os.path.join(dirpath, fname)
                    try:
                        size = os.path.getsize(fpath)
                    except Exception:
                        size = 0
                    if size_min is not None and size < size_min:
                        continue
                    if size_max is not None and size > size_max:
                        continue
                    files.append({"path": fpath, "size_bytes": int(size)})
                    if len(files) >= max_files:
                        break
                if len(files) >= max_files:
                    break
        except Exception as e:
            return {"error": str(e)}

        return {"root": str(p), "total": len(files), "files": files}
