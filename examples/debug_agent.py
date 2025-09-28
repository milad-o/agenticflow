#!/usr/bin/env python3
"""Debug agent creation and execution."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow, Agent
from agenticflow.tools import create_file

async def debug_agent():
    """Debug agent creation and execution."""
    print("🐛 Debug Agent Creation and Execution")
    print("=" * 40)
    
    # Test 1: Create simple agent with basic tool
    print("\n1. Creating simple agent with create_file tool...")
    flow = Flow("debug_test")
    agent = Agent("test_agent", tools=[create_file], description="Test agent")
    flow.add_agent(agent)
    
    print(f"✅ Agent created with {len(agent.tools)} tools")
    print(f"   Tools: {[tool.name for tool in agent.tools]}")
    print(f"   ReAct agent: {agent._react_agent is not None}")
    
    # Test 2: Try to run the agent
    print("\n2. Testing agent execution...")
    try:
        result = await flow.run("Create a file called 'debug.txt' with content 'Hello Debug'")
        print(f"✅ Agent executed successfully")
        print(f"   Messages: {len(result['messages'])}")
        for i, msg in enumerate(result["messages"], 1):
            sender = getattr(msg, 'name', 'user')
            print(f"   {i}. [{sender}]: {msg.content[:100]}...")
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_agent())
