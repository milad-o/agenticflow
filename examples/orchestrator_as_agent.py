#!/usr/bin/env python3
"""
Demo: orchestrator acting as a special Agent using DelegateTool to route to sub-agents.

Usage:
  AGENTICFLOW_LLM_PROVIDER=groq uv run examples/orchestrator_as_agent.py
"""
import asyncio
from agenticflow import Flow
from agenticflow.agent import Agent
from agenticflow.core.config import AgentConfig

async def main():
    flow = Flow()

    # Two specialized agents
    tools_a = flow.tool_registry.get_tools_by_names(["read_file", "write_file"])  # file ops
    agent_a = Agent(AgentConfig(name="file_mgr", model="", temperature=0.0), [])
    agent_a.add_tools(tools_a)

    tools_b = flow.tool_registry.get_tools_by_names(["shell"])  # shell ops
    agent_b = Agent(AgentConfig(name="sys_admin", model="", temperature=0.0), [])
    agent_b.add_tools(tools_b)

    flow.add_agent("file_mgr", agent_a)
    flow.add_agent("sys_admin", agent_b)

    flow.start()

    # Ask the orchestrator-as-agent to decide which agent to call via delegate tool
    request = (
        "Create 'oa_demo.txt' with 'orchestrator agent demo', then list the current directory."
        " Use the appropriate abilities."
    )
    result = await flow.orchestrator.aagent_run(request)
    print("Final message:", result.get("message"))

    flow.stop()

if __name__ == "__main__":
    asyncio.run(main())
