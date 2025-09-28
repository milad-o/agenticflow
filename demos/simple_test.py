#!/usr/bin/env python3
"""Simple test without Command pattern to debug routing."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from agenticflow import Flow, Orchestrator, Supervisor, SimpleAgent


async def simple_test():
    """Test simple routing without Command pattern."""
    print("🔍 Simple Routing Test")
    print("=" * 30)
    
    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not found!")
        return
    
    # Create simple flow
    flow = Flow("simple_test")
    
    # Add orchestrator without LLM (to avoid Command pattern)
    orchestrator = Orchestrator("main", initialize_llm=False)
    flow.add_orchestrator(orchestrator)
    
    # Add simple agent
    agent = SimpleAgent("test_agent", description="Test agent")
    orchestrator.add_agent(agent)
    
    print("✅ Flow created")
    print(f"   - Agent: {agent.name}")
    print(f"   - Orchestrator agents: {list(orchestrator.agents.keys())}")
    print(f"   - Graph nodes: {list(flow._graph.nodes.keys()) if flow._graph else 'None'}")
    
    # Check if agent was added to orchestrator
    if agent.name in orchestrator.agents:
        print(f"   - Agent {agent.name} is in orchestrator.agents")
    else:
        print(f"   - Agent {agent.name} is NOT in orchestrator.agents")
    
    # Test message
    print("\n🎯 Testing message...")
    await flow.start("Hello, test agent!")
    
    # Get messages
    messages = await flow.get_messages()
    print(f"\n📝 Generated {len(messages)} messages:")
    
    for i, msg in enumerate(messages, 1):
        print(f"\n{i}. [{msg.sender}]:")
        print(f"   Content: {msg.content}")
        print(f"   Type: {msg.type}")


if __name__ == "__main__":
    asyncio.run(simple_test())
