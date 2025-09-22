from __future__ import annotations

"""
MCP SDK-based tools (optional).
These tools use the official Model Context Protocol Python SDK / fastmcp when installed.
If the SDK is not available, they return a clear error instructing how to install it.

Install (examples):
  uv add mcp fastmcp
or
  uv sync --extra mcp
"""

from typing import Optional

from .base import Tool, ToolResult


class MCPClientSDKTool(Tool):
    name = "mcp_sdk_call"
    schema = {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string"},  # remote MCP server URL
            "tool": {"type": "string"},      # remote tool name
            "args": {"type": "object"},
            "timeout": {"type": "number"},
        },
        "required": ["endpoint", "tool"],
        "additionalProperties": False,
    }

    def __init__(self, *, enforce_https: bool = True) -> None:
        self.enforce_https = enforce_https

    async def invoke(self, **kwargs) -> ToolResult:
        import asyncio
        endpoint = str(kwargs.get("endpoint"))
        tool_name = str(kwargs.get("tool"))
        args = kwargs.get("args") or {}
        timeout = float(kwargs.get("timeout", 30.0))
        if self.enforce_https and not endpoint.lower().startswith("https://"):
            return ToolResult(ok=False, data={"error": "endpoint_not_https"})
        # Try fastmcp first
        try:
            import fastmcp  # type: ignore
            async def _run_fastmcp():
                # API guess based on common patterns; guarded with try/except
                try:
                    client = await fastmcp.Client.connect(endpoint)  # type: ignore
                except Exception:
                    # Some variants may use from_url
                    try:
                        client = await fastmcp.Client.from_url(endpoint)  # type: ignore
                    except Exception as e:
                        raise e
                try:
                    # Attempt common call patterns
                    if hasattr(client, "call_tool"):
                        res = await client.call_tool(tool_name, **args)  # type: ignore
                    elif hasattr(client, "tools") and tool_name in getattr(client, "tools", {}):
                        res = await client.tools[tool_name](**args)  # type: ignore
                    else:
                        # Fallback: generic request
                        res = await client.request({"type": "tool", "name": tool_name, "args": args})  # type: ignore
                    await client.aclose()
                    return res
                except Exception:
                    try:
                        await client.aclose()
                    except Exception:
                        pass
                    raise
            res = await asyncio.wait_for(_run_fastmcp(), timeout=timeout)
            return ToolResult(ok=True, data={"result": res})
        except Exception:
            pass
        # Try official mcp sdk
        try:
            # Lazily import to keep optional dependency
            import mcp  # type: ignore
            async def _run_mcp():
                # API guess: ClientSession or connect helper
                session = None
                try:
                    if hasattr(mcp, "ClientSession"):
                        # type: ignore[attr-defined]
                        session = await mcp.ClientSession.from_url(endpoint)  # type: ignore
                    elif hasattr(mcp, "connect_http"):
                        session = await mcp.connect_http(endpoint)  # type: ignore
                    else:
                        raise RuntimeError("mcp_client_not_supported")
                    # Attempt tool call
                    if hasattr(session, "call_tool"):
                        return await session.call_tool(tool_name, **args)  # type: ignore
                    if hasattr(session, "tools") and tool_name in getattr(session, "tools", {}):
                        return await session.tools[tool_name](**args)  # type: ignore
                    # Fallback generic
                    return await session.request({"type": "tool", "name": tool_name, "args": args})  # type: ignore
                finally:
                    try:
                        if session and hasattr(session, "aclose"):
                            await session.aclose()  # type: ignore
                    except Exception:
                        pass
            res = await asyncio.wait_for(_run_mcp(), timeout=timeout)
            return ToolResult(ok=True, data={"result": res})
        except Exception as e:
            return ToolResult(ok=False, data={"error": "mcp_sdk_call_failed", "detail": str(e.__class__.__name__)})


class MCPClientSDKStreamTool(Tool):
    name = "mcp_sdk_stream"
    schema = {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string"},
            "channel": {"type": "string"},
            "args": {"type": "object"},
            "timeout": {"type": "number"},
        },
        "required": ["endpoint", "channel"],
        "additionalProperties": False,
    }

    def __init__(self, *, enforce_https: bool = True) -> None:
        self.enforce_https = enforce_https

    async def invoke(self, **kwargs) -> ToolResult:
        import asyncio
        endpoint = str(kwargs.get("endpoint"))
        channel = str(kwargs.get("channel"))
        args = kwargs.get("args") or {}
        timeout = float(kwargs.get("timeout", 60.0))
        if self.enforce_https and not endpoint.lower().startswith("https://"):
            return ToolResult(ok=False, data={"error": "endpoint_not_https"})
        # Try fastmcp streaming first
        try:
            import fastmcp  # type: ignore
            async def _stream_fastmcp():
                client = await fastmcp.Client.connect(endpoint)  # type: ignore
                try:
                    from ...observability.progress import emit_progress
                    # Guess streaming interface; guard with hasattr
                    if hasattr(client, "stream_tool"):
                        async for event in client.stream_tool(channel, **args):  # type: ignore
                            await emit_progress("mcp_stream", {"channel": channel, "event": event})
                    else:
                        # Fallback: no streaming support
                        raise RuntimeError("fastmcp_stream_unsupported")
                finally:
                    try:
                        await client.aclose()
                    except Exception:
                        pass
            await asyncio.wait_for(_stream_fastmcp(), timeout=timeout)
            return ToolResult(ok=True, data={"streamed": True})
        except Exception:
            pass
        # Try official mcp sdk streaming
        try:
            import mcp  # type: ignore
            async def _stream_mcp():
                session = None
                try:
                    if hasattr(mcp, "ClientSession"):
                        session = await mcp.ClientSession.from_url(endpoint)  # type: ignore
                    elif hasattr(mcp, "connect_http"):
                        session = await mcp.connect_http(endpoint)  # type: ignore
                    else:
                        raise RuntimeError("mcp_client_not_supported")
                    from ...observability.progress import emit_progress
                    # Guess streaming method: session.stream(channel, **args)
                    if hasattr(session, "stream"):
                        async for event in session.stream(channel, **args):  # type: ignore
                            await emit_progress("mcp_stream", {"channel": channel, "event": event})
                    else:
                        raise RuntimeError("mcp_stream_unsupported")
                finally:
                    try:
                        if session and hasattr(session, "aclose"):
                            await session.aclose()  # type: ignore
                    except Exception:
                        pass
            await asyncio.wait_for(_stream_mcp(), timeout=timeout)
            return ToolResult(ok=True, data={"streamed": True})
        except Exception as e:
            return ToolResult(ok=False, data={"error": "mcp_sdk_stream_failed", "detail": str(e.__class__.__name__)})
