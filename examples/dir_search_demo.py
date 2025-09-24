#!/usr/bin/env python3
"""
Directory-wide regex search demo:
- Agent uses regex_search_dir (and regex_search_file if needed) to scan the repo for patterns.
- Loads .env to enable LangSmith (optional) and local LLM provider overrides.
"""
import asyncio
from agenticflow import Flow
from agenticflow.core.env import load_env
from agenticflow.agent import Agent
from agenticflow.core.config import AgentConfig

async def main():
    load_env()

    flow = Flow()

    agent = Agent(AgentConfig(name="grep_agent", model="", temperature=0.0), [])
    agent.discover_tools_by_names(flow.tool_registry, [
        "regex_search_dir", "regex_search_file", "file_stat", "read_file"
    ])

    flow.add_agent("grep_agent", agent)
    flow.start()

    # Ask the agent to search for a pattern in this repo and summarize contexts
    pattern = r"(Agent|Flow|Orchestrator|Planner)"
    prompt = (
        "Search the current project directory recursively for the given regex pattern. "
        "Use regex_search_dir with options: file_glob='*', include_exts=['.py', '.md', '.yaml', '.yml', '.toml'], "
        "exclude_dirs=['.git', '.venv', 'node_modules'], max_files=200, max_matches=50, context_lines=1. "
        f"Pattern: {pattern}. After finding matches, summarize where these terms appear and what components do."
    )

    res = await flow.arun(prompt)
    print("Summary:\n", res.get("final_response"))

    flow.stop()

if __name__ == "__main__":
    asyncio.run(main())