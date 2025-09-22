from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from agenticflow.agents.tool_agent import ToolAgent
from agenticflow.agents.tools.mcp import MCPHttpTool, MCPSSEStreamTool
# Prefer official SDK tools if installed
try:
    from agenticflow.agents.tools.mcp_sdk import MCPClientSDKTool, MCPClientSDKStreamTool  # type: ignore
    _MCP_SDK_AVAILABLE = True
except Exception:
    _MCP_SDK_AVAILABLE = False
from agenticflow.orchestration.core.orchestrator import Orchestrator, WorkflowDefinition
from agenticflow.orchestration.tasks.graph import TaskNode
from agenticflow.observability.debug import DebugInterface
from agenticflow.observability.viz import VisualizationRenderer


@dataclass
class Config:
    outdir: str = "examples/06_mcp_demo/artifacts"
    store_kind: str = "sqlite"
    db_path: str = "examples/06_mcp_demo/events.sqlite3"
    # Remote MCP endpoints
    tavily_url: Optional[str] = None  # e.g., https://mcp.tavily.com/mcp/?tavilyApiKey=...
    meteo_url: Optional[str] = None   # e.g., https://<your-open-meteo-mcp-host>/mcp


class MCPDemo:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.out = Path(cfg.outdir)
        self.out.mkdir(parents=True, exist_ok=True)
        # Orchestrator
        if cfg.store_kind == "sqlite":
            from agenticflow.adapters.store.sqlite import SQLiteEventStore
            es = SQLiteEventStore(cfg.db_path)
        else:
            from agenticflow.adapters.store.memory import InMemoryEventStore
            es = InMemoryEventStore()
        self.orch = Orchestrator(event_store=es, emit_workflow_started=True, emit_workflow_lifecycle=True)
        # Tools: restrict to known domains
        allow_domains = []
        if cfg.tavily_url:
            allow_domains.append(cfg.tavily_url.split("/")[2])
        if cfg.meteo_url:
            allow_domains.append(cfg.meteo_url.split("/")[2])
        if _MCP_SDK_AVAILABLE:
            tools = {
                "mcp_sdk_call": MCPClientSDKTool(),
                "mcp_sdk_stream": MCPClientSDKStreamTool(),
                # Keep fallbacks too if desired
                "mcp_http": MCPHttpTool(allow_domains=allow_domains or None),
                "mcp_sse_stream": MCPSSEStreamTool(allow_domains=allow_domains or None),
            }
        else:
            tools = {
                "mcp_http": MCPHttpTool(allow_domains=allow_domains or None),
                "mcp_sse_stream": MCPSSEStreamTool(allow_domains=allow_domains or None),
            }
        self.orch.register_agent(ToolAgent("mcp", tools=tools))
        # Apply tool schemas
        try:
            from examples.utils.mcp_hardening import apply_default_tool_schemas
            apply_default_tool_schemas(self.orch)
        except Exception:
            pass

    def build_workflow_tavily(self, query: str) -> WorkflowDefinition:
        if not self.cfg.tavily_url:
            raise RuntimeError("Tavily URL not configured")
        if _MCP_SDK_AVAILABLE:
            params = {
                "endpoint": self.cfg.tavily_url,
                "tool": "search",
                "args": {"query": query, "maxResults": 5},
                "timeout": 40.0,
            }
            tasks = [TaskNode(task_id="tavily", agent_id="mcp", task_type="mcp_sdk_call", params=params)]
        else:
            params = {
                "endpoint": self.cfg.tavily_url,
                "method": "search",
                "params": {"query": query, "maxResults": 5},
                "timeout": 40.0,
            }
            tasks = [TaskNode(task_id="tavily", agent_id="mcp", task_type="mcp_http", params=params)]
        return WorkflowDefinition(tasks=tasks)

    def build_workflow_meteo(self, lat: float, lon: float) -> WorkflowDefinition:
        if not self.cfg.meteo_url:
            raise RuntimeError("Open-Meteo MCP URL not configured")
        if _MCP_SDK_AVAILABLE:
            params = {
                "endpoint": self.cfg.meteo_url,
                "tool": "weather_forecast",
                "args": {"latitude": lat, "longitude": lon},
                "timeout": 40.0,
            }
            tasks = [TaskNode(task_id="meteo", agent_id="mcp", task_type="mcp_sdk_call", params=params)]
        else:
            params = {
                "endpoint": self.cfg.meteo_url,
                "method": "weather_forecast",
                "params": {"latitude": lat, "longitude": lon},
                "timeout": 40.0,
            }
            tasks = [TaskNode(task_id="meteo", agent_id="mcp", task_type="mcp_http", params=params)]
        return WorkflowDefinition(tasks=tasks)


async def list_tools(endpoint: str, outdir: Path) -> list[str]:
    names: list[str] = []
    tools_out = outdir / "tools.json"
    if not _MCP_SDK_AVAILABLE:
        return names
    import json as _json
    # Try fastmcp
    try:
        import fastmcp  # type: ignore
        client = await fastmcp.Client.connect(endpoint)  # type: ignore
        t = getattr(client, "tools", None)
        if isinstance(t, dict):
            names = list(t.keys())
        elif hasattr(client, "list_tools"):
            lst = await client.list_tools()  # type: ignore
            if isinstance(lst, dict):
                names = list(lst.keys())
            elif isinstance(lst, list):
                names = [getattr(x, "name", None) or str(x) for x in lst]
        try:
            await client.aclose()
        except Exception:
            pass
    except Exception:
        pass
    # Try official mcp if still empty
    if not names:
        try:
            import mcp  # type: ignore
            session = await mcp.ClientSession.from_url(endpoint) if hasattr(mcp, "ClientSession") else await mcp.connect_http(endpoint)  # type: ignore
            t = getattr(session, "tools", None)
            if isinstance(t, dict):
                names = list(t.keys())
            elif hasattr(session, "list_tools"):
                lst = await session.list_tools()  # type: ignore
                if isinstance(lst, dict):
                    names = list(lst.keys())
                elif isinstance(lst, list):
                    names = [getattr(x, "name", None) or str(x) for x in lst]
            try:
                if hasattr(session, "aclose"):
                    await session.aclose()  # type: ignore
            except Exception:
                pass
        except Exception:
            pass
    try:
        tools_out.write_text(_json.dumps({"tools": names}, indent=2))
    except Exception:
        pass
    return names


async def run_demo() -> None:
    # Resolve env for Tavily
    tav_key = os.environ.get("TAVILY_API_KEY")
    tav_url = None
    if tav_key:
        tav_url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={tav_key}"
    meteo_url = os.environ.get("OPEN_METEO_MCP_URL")  # set if you have a hosted open-meteo MCP

    cfg = Config(tavily_url=tav_url, meteo_url=meteo_url)
    demo = MCPDemo(cfg)

    # Choose a workflow to run (web search if Tavily key is present, else skip)
    wf = None
    label = None
    if tav_url:
        # Attempt to discover tools (SDK only) and log to artifacts
        try:
            await list_tools(tav_url, Path(cfg.outdir))
        except Exception:
            pass
        wf = demo.build_workflow_tavily("latest AI research news")
        label = "tavily"
    elif meteo_url:
        try:
            await list_tools(meteo_url, Path(cfg.outdir))
        except Exception:
            pass
        wf = demo.build_workflow_meteo(37.7749, -122.4194)
        label = "meteo"
    else:
        print("No MCP endpoints configured. Set TAVILY_API_KEY and/or OPEN_METEO_MCP_URL.")
        return

    wid = await demo.orch.execute_workflow(wf)
    print("[MCP Demo] Started:", wid, "workflow:", label)

    # Write tool result artifact for convenience
    try:
        task_id = "tavily" if label == "tavily" else "meteo"
        res = demo.orch._task_results[wid][task_id]  # type: ignore[attr-defined]
        payload = res.get("result") if isinstance(res, dict) else res
        if payload is None and isinstance(res, dict):
            payload = res.get("data", res)
        out_json = Path(cfg.outdir) / f"{task_id}_result.json"
        import json as _json
        out_json.write_text(_json.dumps(payload, indent=2, ensure_ascii=False))
        print("[MCP Demo] Result ->", out_json)
    except Exception as _e:
        print("[MCP Demo] No result artifact written:", type(_e).__name__)

    dbg = DebugInterface(event_store=demo.orch.event_store)
    viz = VisualizationRenderer(dbg)
    await viz.render_workflow(wid, out_mmd=Path(cfg.outdir) / "workflow.mmd")
    await viz.render_system(
        workflow_id=wid,
        out_mmd=Path(cfg.outdir) / "system.mmd",
        out_dot=Path(cfg.outdir) / "system.dot",
        out_svg=Path(cfg.outdir) / "system.svg",
        agents=["mcp"],
        tools_by_agent={"mcp": ["mcp_http", "mcp_sse_stream", "mcp_sdk_call", "mcp_sdk_stream"]},
        task_types_by_agent={"mcp": ["mcp_http", "mcp_sse_stream", "mcp_sdk_call", "mcp_sdk_stream"]},
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_demo())
