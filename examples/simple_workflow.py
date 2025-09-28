#!/usr/bin/env python3
"""Simple workflow example."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agenticflow import Flow, Agent, create_file, search_web

async def main():
    """Simple workflow example."""
    print("🚀 AgenticFlow - Simple Workflow")
    print("=" * 35)
    
    # Create flow
    flow = Flow("simple_workflow")
    
    # Create agents
    researcher = Agent("researcher", tools=[search_web], description="Research specialist")
    writer = Agent("writer", tools=[create_file], description="Writing specialist")
    
    # Add agents to flow
    flow.add_agent(researcher)
    flow.add_agent(writer)
    
    print("✅ Created flow with 2 agents")
    print(f"   Agents: {list(flow.agents.keys())}")
    
    # Run workflow
    print("\n🎯 Running workflow...")
    result = await flow.run("Research AI trends and create a simple report")
    
    print("✅ Workflow completed!")
    print(f"📝 Messages: {len(result['messages'])}")
    
    for i, msg in enumerate(result["messages"], 1):
        sender = getattr(msg, 'name', 'user')
        print(f"   {i}. [{sender}]: {msg.content[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())