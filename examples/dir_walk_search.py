#!/usr/bin/env python3
"""
Demo: directory tree walking and file search tools.

Usage:
  AGENTICFLOW_LLM_PROVIDER=groq uv run examples/dir_walk_search.py
  # or with Ollama provider set via env if configured
"""
import asyncio
from agenticflow import Flow
from agenticflow.core.env import load_env
from agenticflow.agent import Agent
from agenticflow.core.config import AgentConfig


async def main():
    # Load .env if present (LangSmith, provider, model overrides)
    load_env()
    flow = Flow()

    # Create a code_searcher agent with directory + search tools
    tools = flow.tool_registry.get_tools_by_names([
        "dir_tree",          # directory walk
        "find_files",        # file discovery
        "regex_search_dir",  # recursive regex search with context
    ])
    code_searcher = Agent(AgentConfig(name="code_searcher", model="", temperature=0.0), [])
    code_searcher.add_tools(tools)

    flow.add_agent("code_searcher", code_searcher)

    flow.start()

    # Ask it to explore this repo directory and search for patterns
    request = (
        "First, list a directory tree of the current project up to depth 2, excluding common virtualenv folders. "
        "Then, find all Python files under agenticflow/tools and report how many there are. "
        "Finally, search the repository for occurrences of 'BaseTool' and summarize which files contain it."
    )

    result = await flow.arun(request)
    print("Final:", result.get("final_response"))

    flow.stop()


if __name__ == "__main__":
    asyncio.run(main())
