#!/usr/bin/env python3
"""Debug agent execution to see what's actually happening."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
from agenticflow.tools import TavilySearchTool, WriteFileTool


async def debug_agent_execution():
    """Debug what's happening with agent execution."""
    print("🔍 Debugging Agent Execution")
    print("=" * 50)
    
    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not found!")
        return
    
    # Create simple flow
    flow = Flow("debug_flow")
    
    # Add orchestrator
    orchestrator = Orchestrator("main", llm_model="gpt-4o-mini", api_key=openai_key)
    flow.add_orchestrator(orchestrator)
    
    # Add single agent directly to orchestrator
    agent = ReActAgent("researcher", description="Research agent", llm_model="gpt-4o-mini", api_key=openai_key)
    if tavily_key:
        agent.add_tool(TavilySearchTool(api_key=tavily_key))
    agent.add_tool(WriteFileTool())
    orchestrator.add_agent(agent)
    
    print("✅ Flow created with single agent")
    print(f"   - Agent: {agent.name}")
    print(f"   - Tools: {list(agent.tools.keys())}")
    
    # Test simple message
    print("\n🎯 Testing simple message...")
    await flow.start("Hello, can you search for information about AI agents?")
    
    # Get messages
    messages = await flow.get_messages()
    print(f"\n📝 Generated {len(messages)} messages:")
    
    for i, msg in enumerate(messages, 1):
        print(f"\n{i}. [{msg.sender}]:")
        print(f"   Content: {msg.content[:200]}...")
        print(f"   Type: {msg.type}")
    
    # Check if agent actually used tools
    print(f"\n🔧 Agent tools: {list(agent.tools.keys())}")
    print(f"🔧 Agent LLM: {agent.llm is not None}")
    
    return messages


if __name__ == "__main__":
    asyncio.run(debug_agent_execution())
