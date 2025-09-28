#!/usr/bin/env python3
"""Advanced Research and Writing Workflow example.

This example demonstrates a complex workflow with multiple teams,
LLM-powered routing, and real tools. Requires API keys to run.
"""

import asyncio
import os
from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
from agenticflow.tools import WriteFileTool, ReadFileTool, TavilySearchTool


async def research_and_writing_workflow():
    """Run a complex research and writing workflow."""
    print("🔬 AgenticFlow Research & Writing Workflow")
    print("=" * 50)
    
    # Check for API keys
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
    
    print("✅ API keys found! Starting advanced workflow...")
    
    # Create flow
    flow = Flow("research_writing_flow")
    
    # Add orchestrator with LLM
    orchestrator = Orchestrator("main_orchestrator")
    flow.add_orchestrator(orchestrator)
    
    # Research team
    research_team = Supervisor(
        "research_team", 
        description="Web research specialists",
        keywords=["research", "web", "search", "information", "data"]
    )
    
    # Research agents
    web_searcher = (ReActAgent("web_searcher", description="Web search specialist")
                   .add_tool(TavilySearchTool()))
    
    data_analyst = (ReActAgent("data_analyst", description="Data analysis specialist")
                   .add_tool(ReadFileTool())
                   .add_tool(WriteFileTool()))
    
    research_team.add_agent(web_searcher)
    research_team.add_agent(data_analyst)
    orchestrator.add_team(research_team)
    
    # Writing team
    writing_team = Supervisor(
        "writing_team",
        description="Document creation specialists", 
        keywords=["writing", "document", "content", "report", "article"]
    )
    
    # Writing agents
    content_writer = (ReActAgent("content_writer", description="Content writer")
                     .add_tool(WriteFileTool())
                     .add_tool(ReadFileTool()))
    
    editor = (ReActAgent("editor", description="Content editor")
             .add_tool(ReadFileTool())
             .add_tool(WriteFileTool()))
    
    writing_team.add_agent(content_writer)
    writing_team.add_agent(editor)
    orchestrator.add_team(writing_team)
    
    # Analysis team
    analysis_team = Supervisor(
        "analysis_team",
        description="Data analysis and insights specialists",
        keywords=["analysis", "insights", "statistics", "trends"]
    )
    
    # Analysis agents
    data_scientist = (ReActAgent("data_scientist", description="Data scientist")
                     .add_tool(ReadFileTool())
                     .add_tool(WriteFileTool()))
    
    analyst = (ReActAgent("analyst", description="Business analyst")
              .add_tool(ReadFileTool())
              .add_tool(WriteFileTool()))
    
    analysis_team.add_agent(data_scientist)
    analysis_team.add_agent(analyst)
    orchestrator.add_team(analysis_team)
    
    print("✅ Advanced flow setup complete!")
    print(f"   - Flow: {flow.name}")
    print(f"   - Orchestrator: {orchestrator.name}")
    print(f"   - Teams: {list(orchestrator.teams.keys())}")
    print(f"   - Research team agents: {list(research_team.agents.keys())}")
    print(f"   - Writing team agents: {list(writing_team.agents.keys())}")
    print(f"   - Analysis team agents: {list(analysis_team.agents.keys())}")
    
    # Test LangGraph integration
    print("\n🔧 LangGraph StateGraph Status:")
    if hasattr(flow, '_compiled_graph') and flow._compiled_graph:
        print("✅ LangGraph StateGraph compiled successfully!")
        print(f"   - Graph nodes: {list(flow._graph.nodes.keys()) if flow._graph else 'None'}")
    else:
        print("❌ LangGraph StateGraph not compiled")
        return False
    
    # Run the complex workflow
    print("\n🎯 Running the advanced workflow...")
    try:
        await flow.start("Research the latest developments in AI agents, analyze the data, and write a comprehensive report about the findings")
        print("✅ Advanced workflow execution completed successfully!")
        
        # Get messages
        messages = await flow.get_messages()
        print(f"\n📝 Generated {len(messages)} messages:")
        for i, msg in enumerate(messages[-10:], 1):  # Show last 10 messages
            print(f"   {i}. [{msg.sender}]: {msg.content[:100]}...")
            
    except Exception as e:
        print(f"❌ Workflow execution failed: {str(e)}")
        return False
    
    print("\n🎉 Advanced workflow completed successfully!")
    print("   - LangGraph integration works perfectly")
    print("   - LLM-powered routing at every level")
    print("   - Complex multi-team coordination")
    print("   - Real tool integration")
    
    return True


if __name__ == "__main__":
    asyncio.run(research_and_writing_workflow())
