#!/usr/bin/env python3
"""
Intelligent large-file QA demo over ebay.xml:
- Agent decides whether to index (ephemeral Chroma) or regex/scan based on file size and question.
- Uses local Ollama embeddings for fast, local retrieval.
- Loads .env for LangSmith and provider overrides.
"""
import asyncio
from pathlib import Path
from agenticflow import Flow
from agenticflow.core.env import load_env
from agenticflow.agent import Agent
from agenticflow.core.config import AgentConfig

async def main():
    load_env()

    flow = Flow()

    agent = Agent(AgentConfig(name="smart_retriever", model="", temperature=0.0), [])
    agent.discover_tools_by_names(flow.tool_registry, [
        "file_stat", "regex_search_file", "build_ephemeral_chroma", "query_ephemeral_chroma", "read_file"
    ])

    flow.add_agent("smart_retriever", agent)
    flow.start()

    file_path = str(Path("ebay.xml").resolve())
    if not Path(file_path).exists():
        print(f"⚠️ File not found: {file_path}. Place ebay.xml in repo root to test.")
        flow.stop()
        return

    question = "What categories and brands are most common? Summarize briefly."

    # Single instruction: let the agent choose the strategy using available tools
    prompt = (
        f"You can choose how to retrieve context from '{file_path}'. "
        "First, check file size (file_stat). If large, build an ephemeral chroma index and query it; "
        "otherwise, try regex_search_file for relevant snippets. Use read_file only for small snippets. "
        f"Answer the question: {question}"
    )

    res = await flow.arun(prompt)
    print("Answer:\n", res.get("final_response"))

    flow.stop()

if __name__ == "__main__":
    asyncio.run(main())