#!/usr/bin/env python3
"""
Planner demo: prepare a plan (DAG) first, then run orchestrator to execute tasks.

Usage:
  AGENTICFLOW_LLM_PROVIDER=groq uv run examples/planner_demo.py
"""
import asyncio
from agenticflow import Flow
from agenticflow.core.env import load_env
from agenticflow.agent import Agent
from agenticflow.core.config import AgentConfig
from agenticflow.planner.planner import Planner

async def main():
    # Ensure .env is loaded for LangSmith and provider/env overrides
    load_env()
    flow = Flow()

    # Agents
    file_tools = flow.tool_registry.get_tools_by_names(["read_file", "write_file"])  # file ops
    file_mgr = Agent(AgentConfig(name="file_mgr", model="", temperature=0.0), [])
    file_mgr.add_tools(file_tools)

    shell_tools = flow.tool_registry.get_tools_by_names(["shell", "list_dir", "mkdir"])  # shell + dir list + mkdir
    sys_admin = Agent(AgentConfig(name="sys_admin", model="", temperature=0.0), [])
    sys_admin.add_tools(shell_tools)

    flow.add_agent("file_mgr", file_mgr)
    flow.add_agent("sys_admin", sys_admin)

    # Planner (use Groq or local based on env)
    planner = Planner()
    flow.set_planner(planner)

    flow.start()

    request = (
        "Create a folder 'plan_out', create 'plan.txt' and list the current dir files in it"
        " Ensure dependencies are satisfied in order."
    )
    result = await flow.arun(request)
    print("Final:", result.get("final_response"))

    flow.stop()

if __name__ == "__main__":
    asyncio.run(main())
