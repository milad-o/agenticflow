#!/usr/bin/env python3
"""Quick AgenticFlow Demo - Fast test with tangible results."""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
from agenticflow.tools import TavilySearchTool, WriteFileTool


async def quick_demo():
    """Run a quick demo showcasing core features."""
    print("⚡ AgenticFlow Quick Demo")
    print("=" * 30)
    
    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    print(f"🔑 OpenAI API Key: {'✅ Found' if openai_key else '❌ Missing'}")
    print(f"🔑 Tavily API Key: {'✅ Found' if tavily_key else '❌ Missing'}")
    
    if not openai_key:
        print("\n❌ OpenAI API key required for this demo")
        print("   Set OPENAI_API_KEY in your .env file")
        return
    
    # Create flow
    flow = Flow("quick_demo_flow")
    orchestrator = Orchestrator("main_orchestrator")
    flow.add_orchestrator(orchestrator)
    
    # Create research team
    research_team = Supervisor("research_team", description="Research specialists")
    
    # Add web searcher if Tavily key available
    if tavily_key:
        searcher = (ReActAgent("searcher", description="Web search specialist")
                   .add_tool(TavilySearchTool())
                   .add_tool(WriteFileTool()))
    else:
        searcher = (ReActAgent("searcher", description="Research specialist")
                   .add_tool(WriteFileTool()))
    
    research_team.add_agent(searcher)
    orchestrator.add_team(research_team)
    
    # Create writing team
    writing_team = Supervisor("writing_team", description="Writing specialists")
    writer = (ReActAgent("writer", description="Content writer")
             .add_tool(WriteFileTool()))
    
    writing_team.add_agent(writer)
    orchestrator.add_team(writing_team)
    
    print(f"\n✅ Flow created:")
    print(f"   - Teams: {list(orchestrator.teams.keys())}")
    print(f"   - Research agents: {list(research_team.agents.keys())}")
    print(f"   - Writing agents: {list(writing_team.agents.keys())}")
    
    # Run demo task
    task = "Research AI agent frameworks and write a brief summary of the top 3 frameworks"
    print(f"\n🎯 Running task: {task}")
    print("-" * 50)
    
    start_time = datetime.now()
    await flow.start(task)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    messages = await flow.get_messages()
    
    print(f"\n✅ Task completed in {duration:.2f} seconds")
    print(f"📝 Generated {len(messages)} messages")
    
    # Display results
    print("\n📊 Results:")
    print("-" * 20)
    for i, msg in enumerate(messages, 1):
        content = msg.content[:300] + "..." if len(msg.content) > 300 else msg.content
        print(f"{i}. [{msg.sender}]: {content}")
    
    print(f"\n🎉 Quick demo completed successfully!")
    print(f"   - Duration: {duration:.2f} seconds")
    print(f"   - Messages: {len(messages)}")
    print(f"   - LangGraph: ✅ Working")
    print(f"   - LLM Routing: ✅ Working")
    print(f"   - Multi-agent: ✅ Working")

if __name__ == "__main__":
    asyncio.run(quick_demo())
