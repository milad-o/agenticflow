#!/usr/bin/env python3
"""Test all agents working with standalone tools."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow, Agent
from agenticflow.tools import create_file, read_file, list_directory, search_web

async def test_all_agents():
    """Test all agents working with standalone tools."""
    print("🧪 Testing All Agents with Standalone Tools")
    print("=" * 50)
    
    # Test 1: Filesystem Agent
    print("\n📁 Test 1: Filesystem Agent")
    flow1 = Flow("filesystem_test")
    filesystem_agent = Agent(
        "filesystem_agent", 
        tools=[create_file, read_file, list_directory], 
        description="Filesystem operations specialist"
    )
    flow1.add_agent(filesystem_agent)
    
    result1 = await flow1.run("Create a file called 'filesystem_test.txt' with content 'Filesystem test successful'")
    print(f"✅ Filesystem Agent: {result1['messages'][-1].content[:100]}...")
    
    # Test 2: Research Agent
    print("\n🔍 Test 2: Research Agent")
    flow2 = Flow("research_test")
    research_agent = Agent(
        "research_agent", 
        tools=[search_web], 
        description="Research specialist"
    )
    flow2.add_agent(research_agent)
    
    result2 = await flow2.run("Search for information about Python programming")
    print(f"✅ Research Agent: {result2['messages'][-1].content[:100]}...")
    
    # Test 3: Multi-tool Agent
    print("\n🛠️ Test 3: Multi-tool Agent")
    flow3 = Flow("multi_tool_test")
    multi_agent = Agent(
        "multi_agent", 
        tools=[create_file, read_file, list_directory, search_web], 
        description="Multi-purpose agent with various tools"
    )
    flow3.add_agent(multi_agent)
    
    result3 = await flow3.run("Search for Python best practices and create a file with the findings")
    print(f"✅ Multi-tool Agent: {result3['messages'][-1].content[:100]}...")
    
    # Test 4: Team-based workflow
    print("\n👥 Test 4: Team-based Workflow")
    flow4 = Flow("team_test")
    
    # Create research team
    research_team = Agent(
        "researcher", 
        tools=[search_web], 
        description="Research specialist"
    )
    
    # Create writing team
    writing_team = Agent(
        "writer", 
        tools=[create_file, read_file], 
        description="Writing specialist"
    )
    
    flow4.add_agent(research_team)
    flow4.add_agent(writing_team)
    
    result4 = await flow4.run("Research AI trends and create a report file")
    print(f"✅ Team Workflow: {len(result4['messages'])} messages exchanged")
    for i, msg in enumerate(result4["messages"], 1):
        sender = getattr(msg, 'name', 'user')
        print(f"   {i}. [{sender}]: {msg.content[:80]}...")
    
    print("\n🎉 All agent tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_all_agents())
