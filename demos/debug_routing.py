#!/usr/bin/env python3
"""Debug routing to see what's happening."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from agenticflow import Flow, Orchestrator, Supervisor, SimpleAgent


async def debug_routing():
    """Debug routing step by step."""
    print("🔍 Debugging Routing Step by Step")
    print("=" * 40)
    
    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not found!")
        return
    
    # Create simple flow with team
    flow = Flow("debug_flow")
    
    # Add orchestrator
    orchestrator = Orchestrator("main", llm_model="gpt-4o-mini", api_key=openai_key)
    flow.add_orchestrator(orchestrator)
    
    # Add team
    team = Supervisor(
        "test_team",
        description="Test team",
        keywords=["test"],
        llm_model="gpt-4o-mini",
        api_key=openai_key
    )
    
    # Add agent to team
    agent = SimpleAgent(
        "test_agent", 
        description="Test agent"
    )
    team.add_agent(agent)
    
    orchestrator.add_team(team)
    
    print("✅ Flow created")
    print(f"   - Orchestrator: {orchestrator.name}")
    print(f"   - Teams: {list(orchestrator.teams.keys())}")
    print(f"   - Team agents: {list(team.agents.keys())}")
    print(f"   - Agent supervisor: {getattr(agent, 'supervisor', None)}")
    if hasattr(agent, 'supervisor') and agent.supervisor:
        print(f"   - Agent supervisor name: {agent.supervisor.name}")
    
    # Check graph structure
    if flow._graph:
        print(f"\n📊 Graph nodes: {list(flow._graph.nodes.keys())}")
        print(f"📊 Graph edges: {list(flow._graph.edges)}")
    
    # Test with a simple message
    print(f"\n🎯 Testing with SimpleAgent (no LLM)...")
    try:
        await flow.start("Hello, test agent!")
        
        # Get messages
        messages = await flow.get_messages()
        print(f"\n📝 Generated {len(messages)} messages:")
        
        for i, msg in enumerate(messages, 1):
            print(f"\n{i}. [{msg.sender}]:")
            print(f"   Content: {msg.content}")
            print(f"   Type: {msg.type}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_routing())

