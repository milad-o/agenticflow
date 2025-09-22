# Example 06: Online MCP Demo (Weather + Web Search)

This example demonstrates calling online MCP servers with hardened tools and mid-task progress events.

What it shows
- MCPHttpTool: HTTPS-only POST with minimal MCP-compatible payload {method, params}
- MCPSSEStreamTool: SSE streaming with mid-task progress (task_progress events) and JSONL artifact output
- Policy and validation: domain allowlists, schema enforcement, and size/type caps

Requirements
- Web search (Tavily): set TAVILY_API_KEY in your environment (e.g., .env).
  - Remote MCP URL is constructed automatically: https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}
- Weather (Open‑Meteo): if you have a hosted remote MCP URL, set OPEN_METEO_MCP_URL.
  - e.g., export OPEN_METEO_MCP_URL=https://your-open-meteo-mcp.example.com/mcp
- Optional: Official MCP SDK (preferred)
  ```bash
  uv sync --extra mcp  # installs mcp + fastmcp
  ```

Run
- With Tavily (web search):
```bash
# Ensure your key is in the environment
# export TAVILY_API_KEY=${TAVILY_API_KEY}
uv run python examples/06_mcp_demo/demo.py
```
- With Open‑Meteo (weather):
```bash
# export OPEN_METEO_MCP_URL=https://your-open-meteo-mcp.example.com/mcp
uv run python examples/06_mcp_demo/demo.py
```

Artifacts
- artifacts/workflow.mmd — workflow diagram
- artifacts/system.{mmd,dot,svg} — system diagrams
- If using MCPSSEStreamTool (not shown in the default demo), streamed chunks are written to artifacts/stream.jsonl

Notes
- This repo integrates mid-task events via task_progress, so tools can emit streaming progress (see observability/progress.py).
- MCP remote servers may evolve their wire protocol. MCPHttpTool/MCPSSEStreamTool implement a minimal pattern sufficient for demos; for production, prefer a full MCP client library.
- Policy profiles can be applied (examples/policy_profiles/local_default.yaml) to deny-by-default and explicitly allow only the domains/tools you need.
