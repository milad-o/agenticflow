#!/usr/bin/env python3
"""Team workflow example."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agenticflow import Flow, Agent, Team, create_file, search_web

async def main():
    """Team workflow example."""
    print("🏢 AgenticFlow - Team Workflow")
    print("=" * 35)
    
    # Create flow
    flow = Flow("team_workflow")
    
    # Create research team
    research_team = Team("research_team")
    researcher = Agent("researcher", tools=[search_web], description="Research specialist")
    research_team.add_agent(researcher)
    flow.add_team(research_team)
    
    # Create writing team
    writing_team = Team("writing_team")
    writer = Agent("writer", tools=[create_file], description="Writing specialist")
    writing_team.add_agent(writer)
    flow.add_team(writing_team)
    
    print("✅ Created team structure:")
    print(f"   Flow: {flow.name}")
    print(f"   Teams: {list(flow.teams.keys())}")
    print(f"   Research Team: {list(research_team.agents.keys())}")
    print(f"   Writing Team: {list(writing_team.agents.keys())}")
    
    # Run workflow
    print("\n🎯 Running team workflow...")
    result = await flow.run("Research AI trends and create a simple report")
    
    print("✅ Workflow completed!")
    print(f"📝 Messages: {len(result['messages'])}")
    
    for i, msg in enumerate(result["messages"], 1):
        sender = getattr(msg, 'name', 'user')
        print(f"   {i}. [{sender}]: {msg.content[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
