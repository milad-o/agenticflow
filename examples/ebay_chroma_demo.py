#!/usr/bin/env python3
"""
Demo: build an ephemeral Chroma index over a large file (e.g., ebay.xml) and answer a question.
Uses local Ollama embeddings (qwen2.5:7b works well) and LangSmith via .env if configured.
"""
import os
import asyncio
from pathlib import Path
from agenticflow import Flow
from agenticflow.core.env import load_env
from agenticflow.agent import Agent
from agenticflow.core.config import AgentConfig

async def main():
    load_env()  # enable LangSmith + provider overrides from .env

    flow = Flow()

    # Create a retrieval-capable agent with the ephemeral chroma tools and file tools
    retr_agent = Agent(AgentConfig(name="retriever", model="", temperature=0.0), [])
    retr_agent.discover_tools_by_names(flow.tool_registry, [
        "build_ephemeral_chroma", "query_ephemeral_chroma", "read_file"
    ])

    flow.add_agent("retriever", retr_agent)
    flow.start()

    # Pick a file; default ebay.xml in project root if present
    file_path = str(Path("ebay.xml").resolve())
    if not Path(file_path).exists():
        print(f"⚠️ File not found: {file_path}. Place a large file named 'ebay.xml' in the repo root to test.")
        flow.stop()
        return

    # Build index
    build_req = f"Build an ephemeral chroma index from '{file_path}' with chunk_size=2000 and overlap=200 then return the index id"
    build_res = await flow.arun(build_req)
    print("Build result:", build_res.get("final_response"))

    # Ask a question
    question = "What are the most common categories mentioned? Provide a short summary."
    ask_req = f"Using the index you built, query it with: {question}. If you need an id, ask me what the index_id is."
    ask_res = await flow.arun(ask_req)
    print("Answer:", ask_res.get("final_response"))

    flow.stop()

if __name__ == "__main__":
    asyncio.run(main())