from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from .base import Tool, ToolResult


class HttpFetchTool:
    name = "http_fetch"
    schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "timeout": {"type": "number"}
        },
        "required": ["url"],
        "additionalProperties": False,
    }

    def __init__(
        self,
        *,
        allow_patterns: Optional[list[str]] = None,
        max_bytes: int = 2_000_000,
        enforce_https: bool = True,
        allowed_content_types: Optional[list[str]] = None,
    ) -> None:
        self.allow_patterns = allow_patterns or [r"^https?://"]
        self.max_bytes = max_bytes
        self.enforce_https = enforce_https
        # Exact types or prefixes; we'll allow any starting with "text/" automatically if not specified
        self.allowed_content_types = allowed_content_types or ["application/json", "text/plain", "text/html"]
        self._client = httpx.AsyncClient(follow_redirects=True)

    def _allowed(self, url: str) -> bool:
        if self.enforce_https and not url.lower().startswith("https://"):
            return False
        return any(re.match(pat, url) for pat in self.allow_patterns)

    async def invoke(self, **kwargs) -> ToolResult:
        url = str(kwargs.get("url"))
        timeout = float(kwargs.get("timeout", 10.0))
        if not self._allowed(url):
            return ToolResult(ok=False, data={"error": "url_not_allowed"})
        r = await self._client.get(url, timeout=timeout)
        r.raise_for_status()
        # Respect Content-Length header to guard huge payloads
        try:
            clen = int(r.headers.get("Content-Length", "0"))
            if clen and clen > self.max_bytes:
                return ToolResult(ok=False, data={"error": "content_too_large", "content_length": clen})
        except Exception:
            pass
        # Check content type
        ctype = r.headers.get("Content-Type", "").lower()
        allowed = False
        if ctype:
            for t in self.allowed_content_types:
                if ctype.startswith(t):
                    allowed = True
                    break
            if not allowed and ctype.startswith("text/"):
                allowed = True
        else:
            # If missing content type, be conservative
            allowed = False
        if not allowed:
            return ToolResult(ok=False, data={"error": "content_type_not_allowed", "content_type": ctype})
        content = r.content[: self.max_bytes]
        return ToolResult(ok=True, data={"status": r.status_code, "content": content.decode(errors="ignore"), "content_type": ctype})


class FSReadTool:
    name = "fs_read"
    schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}, "max_bytes": {"type": "number"}},
        "required": ["path"],
        "additionalProperties": False,
    }

    def __init__(self, *, roots: list[str], default_max_bytes: int = 200_000, allow_exts: Optional[list[str]] = None) -> None:
        self.roots = [str(Path(r).resolve()) for r in roots]
        self.default_max_bytes = default_max_bytes
        self.allow_exts = [e.lower() for e in (allow_exts or [".md", ".txt", ".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".csv"])]

    def _is_allowed(self, p: Path) -> bool:
        try:
            rp = str(p.resolve())
            return any(rp.startswith(root + "/") or rp == root for root in self.roots)
        except Exception:
            return False

    async def invoke(self, **kwargs) -> ToolResult:
        p = Path(str(kwargs.get("path")))
        max_bytes = int(kwargs.get("max_bytes", self.default_max_bytes))
        if not self._is_allowed(p):
            return ToolResult(ok=False, data={"error": "path_not_allowed"})
        if p.suffix.lower() not in self.allow_exts:
            return ToolResult(ok=False, data={"error": "ext_not_allowed", "ext": p.suffix.lower()})
        try:
            data = p.read_bytes()[:max_bytes]
            try:
                text = data.decode()
            except Exception:
                text = data.decode(errors="ignore")
            return ToolResult(ok=True, data={"path": str(p), "content": text})
        except Exception as e:
            return ToolResult(ok=False, data={"error": str(e)})
