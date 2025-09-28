#!/usr/bin/env python3
"""Example showing how to use AgenticFlow with API keys for full functionality."""

import asyncio
import os
from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
from agenticflow.tools import WriteFileTool, ReadFileTool, TavilySearchTool

async def example_with_api_keys():
    """Example showing full AgenticFlow functionality with API keys."""
    
    print("🚀 AgenticFlow Example with API Keys")
    print("=" * 50)
    
    # Check if API keys are available
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if not openai_key:
        print("⚠️  OPENAI_API_KEY not found in environment variables")
        print("   Set it with: export OPENAI_API_KEY='your_key_here'")
        print("   Or create a .env file with: OPENAI_API_KEY=your_key_here")
        return
    
    if not tavily_key:
        print("⚠️  TAVILY_API_KEY not found in environment variables")
        print("   Set it with: export TAVILY_API_KEY='your_key_here'")
        print("   Or create a .env file with: TAVILY_API_KEY=your_key_here")
        return
    
    print("✅ API keys found! Starting full example...")
    
    # Create flow (your beautiful API!)
    flow = Flow("research_and_writing_flow")
    
    # Add orchestrator (with LLM enabled)
    orchestrator = Orchestrator("main_orchestrator")
    flow.add_orchestrator(orchestrator)
    
    # Create research team
    research_team = Supervisor(
        "research_team", 
        description="Web research specialists",
        keywords=["research", "web", "search", "information"]
    )
    
    # Add research agents
    searcher = ReActAgent(
        "searcher",
        description="Web search specialist who finds relevant information",
        keywords=["search", "web", "research", "information"]
    ).add_tool(TavilySearchTool())
    
    research_team.add_agent(searcher)
    orchestrator.add_team(research_team)
    
    # Create writing team
    writing_team = Supervisor(
        "writing_team",
        description="Document creation specialists", 
        keywords=["writing", "document", "content", "report"]
    )
    
    # Add writing agents
    writer = ReActAgent(
        "writer",
        description="Content writer who creates well-structured documents",
        keywords=["writing", "content", "document", "report"]
    ).add_tool(WriteFileTool())
    
    outliner = ReActAgent(
        "outliner",
        description="Document outliner who creates structured outlines",
        keywords=["outline", "structure", "organization", "planning"]
    ).add_tool(WriteFileTool())
    
    writing_team.add_agent(writer)
    writing_team.add_agent(outliner)
    orchestrator.add_team(writing_team)
    
    print("✅ Flow setup complete!")
    print(f"   - Flow: {flow.name}")
    print(f"   - Orchestrator: {orchestrator.name}")
    print(f"   - Teams: {list(orchestrator.teams.keys())}")
    print(f"   - Research team agents: {list(research_team.agents.keys())}")
    print(f"   - Writing team agents: {list(writing_team.agents.keys())}")
    
    # Test LangGraph integration
    print("\n🔧 LangGraph StateGraph Status:")
    if hasattr(flow, '_compiled_graph') and flow._compiled_graph:
        print("✅ LangGraph StateGraph compiled successfully!")
        print(f"   - Graph nodes: {list(flow._graph.nodes.keys()) if flow._graph else 'None'}")
    else:
        print("❌ LangGraph StateGraph not compiled")
        return False
    
    # Run the flow
    print("\n🎯 Running the flow...")
    try:
        await flow.start("Research the latest developments in AI agents and write a comprehensive report about them")
        print("✅ Flow execution completed successfully!")
        
        # Get messages
        messages = await flow.get_messages()
        print(f"\n📝 Generated {len(messages)} messages:")
        for i, msg in enumerate(messages[-5:], 1):  # Show last 5 messages
            print(f"   {i}. [{msg.sender}]: {msg.content[:100]}...")
            
    except Exception as e:
        print(f"❌ Flow execution failed: {str(e)}")
        return False
    
    print("\n🎉 Example completed successfully!")
    print("   - LangGraph integration works perfectly")
    print("   - Your beautiful OOP API is preserved")
    print("   - Full LLM-powered routing and execution")
    
    return True

if __name__ == "__main__":
    asyncio.run(example_with_api_keys())
