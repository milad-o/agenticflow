from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Generator, Iterable, List, Tuple

TEXT_EXTS = {".md", ".txt", ".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".csv"}


def list_files(root: str | Path, *, include_exts: Iterable[str] | None = None, ignore_globs: Iterable[str] | None = None) -> List[Path]:
    r = Path(root)
    include = set(e.lower() for e in (include_exts or TEXT_EXTS))
    ignores = [g for g in (ignore_globs or [])]
    out: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(r):
        d = Path(dirpath)
        # apply ignore globs to directories
        if _ignored(d, ignores, r):
            continue
        for fn in filenames:
            p = d / fn
            if _ignored(p, ignores, r):
                continue
            if include and p.suffix.lower() not in include:
                continue
            out.append(p)
    return out


def _ignored(p: Path, patterns: List[str], root: Path) -> bool:
    if not patterns:
        return False
    rel = str(p.relative_to(root)) if p.is_absolute() else str(p)
    rel = rel.replace("\\", "/")
    from pathlib import PurePosixPath
    rel_path = PurePosixPath(rel)
    rel_parts = rel.split("/")
    for pat in patterns:
        # Try Path.match and fnmatch first
        if rel_path.match(pat) or rel_path.match(pat.lstrip("./")):
            return True
        import fnmatch as _fnm
        if _fnm.fnmatch(rel, pat) or _fnm.fnmatch(rel, pat.lstrip("./")):
            return True
        # Heuristic: if pattern targets a directory like **/name/**, ignore if present in path parts
        toks = [t for t in pat.split("/") if t and all(ch not in t for ch in "*?[]")]
        if any(t in rel_parts for t in toks):
            return True
    return False


def read_text_safe(p: str | Path, *, max_bytes: int = 2000) -> str:
    path = Path(p)
    data = path.read_bytes()[:max_bytes]
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def chunk_text(text: str, *, chunk_size: int = 2000, overlap: int = 0) -> List[str]:
    if chunk_size <= 0:
        return [text]
    if overlap < 0:
        overlap = 0
    out: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        out.append(text[i : i + chunk_size])
        i += max(1, chunk_size - overlap)
    return out