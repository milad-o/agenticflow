from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import httpx

from .base import Tool, ToolResult


class MCPHttpTool:
    name = "mcp_http"
    schema = {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string"},
            "method": {"type": "string"},  # MCP method name or route
            "params": {"type": "object"},
            "headers": {"type": "object"},
            "timeout": {"type": "number"},
        },
        "required": ["endpoint", "method"],
        "additionalProperties": False,
    }

    def __init__(
        self,
        *,
        allow_domains: Optional[list[str]] = None,
        max_bytes: int = 2_000_000,
        enforce_https: bool = True,
    ) -> None:
        self.allow_domains = set(allow_domains or [])
        self.max_bytes = max_bytes
        self.enforce_https = enforce_https
        self._client = httpx.AsyncClient(follow_redirects=True)

    def _allowed(self, url: str) -> bool:
        if self.enforce_https and not url.lower().startswith("https://"):
            return False
        if not self.allow_domains:
            return True
        try:
            host = re.sub(r"^https?://", "", url).split("/")[0].lower()
        except Exception:
            return False
        return host in self.allow_domains

    async def invoke(self, **kwargs) -> ToolResult:
        endpoint = str(kwargs.get("endpoint"))
        method = str(kwargs.get("method"))
        params = kwargs.get("params") or {}
        headers = kwargs.get("headers") or {}
        # Ensure MCP-friendly defaults
        headers.setdefault("Accept", "application/json")
        headers.setdefault("Content-Type", "application/json")
        timeout = float(kwargs.get("timeout", 20.0))
        if not self._allowed(endpoint):
            return ToolResult(ok=False, data={"error": "endpoint_not_allowed"})
        # Minimal MCP-friendly payload: {"method": ..., "params": {...}}
        payload = {"method": method, "params": params}
        try:
            r = await self._client.post(endpoint, json=payload, headers=headers, timeout=timeout)
        except Exception as e:
            return ToolResult(ok=False, data={"error": "request_failed", "detail": str(e.__class__.__name__)})
        if r.status_code >= 400:
            # Sanitize: do not include URL or response body
            return ToolResult(ok=False, data={"error": "http_error", "status": r.status_code})
        content = r.content[: self.max_bytes]
        try:
            data = r.json()
        except Exception:
            data = json.loads(content.decode(errors="ignore") or "{}")
        return ToolResult(ok=True, data={"status": r.status_code, "data": data})


class MCPSSEStreamTool:
    name = "mcp_sse_stream"
    schema = {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string"},
            "channel": {"type": "string"},
            "params": {"type": "object"},
            "out_path": {"type": "string"},
            "timeout": {"type": "number"},
            "max_events": {"type": "number"},
        },
        "required": ["endpoint", "channel"],
        "additionalProperties": False,
    }

    def __init__(
        self,
        *,
        allow_domains: Optional[list[str]] = None,
        enforce_https: bool = True,
    ) -> None:
        self.allow_domains = set(allow_domains or [])
        self.enforce_https = enforce_https
        self._client = httpx.AsyncClient(timeout=None)

    def _allowed(self, url: str) -> bool:
        if self.enforce_https and not url.lower().startswith("https://"):
            return False
        if not self.allow_domains:
            return True
        try:
            host = re.sub(r"^https?://", "", url).split("/")[0].lower()
        except Exception:
            return False
        return host in self.allow_domains

    async def invoke(self, **kwargs) -> ToolResult:
        endpoint = str(kwargs.get("endpoint"))
        channel = str(kwargs.get("channel"))
        params = kwargs.get("params") or {}
        out_path = kwargs.get("out_path") or "artifacts/stream.jsonl"
        timeout = float(kwargs.get("timeout", 60.0))
        max_events = int(kwargs.get("max_events", 100))
        if not self._allowed(endpoint):
            return ToolResult(ok=False, data={"error": "endpoint_not_allowed"})
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        # Simple SSE over GET with query params (?channel=...)
        try:
            with httpx.Client(timeout=timeout) as c:
                with c.stream("GET", endpoint, params={"channel": channel, **params}, headers={"Accept": "text/event-stream"}) as resp:
                    resp.raise_for_status()
                    count = 0
                    buf = []
                    for line in resp.iter_lines():
                        if line is None:
                            continue
                        s = line.decode(errors="ignore") if isinstance(line, (bytes, bytearray)) else str(line)
                        if s.startswith(":"):
                            continue  # comment
                        if s.startswith("data:"):
                            data = s[len("data:"):].strip()
                            buf.append(data)
                            out.write_text("\n".join(buf))
                            count += 1
                            # Emit mid-task progress if available
                            try:
                                from ...observability.progress import emit_progress  # type: ignore
                                import json as _json
                                payload = None
                                try:
                                    payload = _json.loads(data)
                                except Exception:
                                    payload = {"text": data}
                                import asyncio as _asyncio
                                _asyncio.run(emit_progress("sse_chunk", {"channel": channel, "event": payload}))
                            except Exception:
                                pass
                            if count >= max_events:
                                break
        except Exception as e:
            return ToolResult(ok=False, data={"error": str(e)})
        return ToolResult(ok=True, data={"out_path": str(out)})
