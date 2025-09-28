#!/usr/bin/env python3
"""Simple test script to verify LangGraph integration without API keys."""

import asyncio
import os
from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
from agenticflow.tools import WriteFileTool, ReadFileTool

async def test_langgraph_integration_simple():
    """Test the LangGraph integration without requiring API keys."""
    
    print("🚀 Testing LangGraph Integration (Simple) with AgenticFlow...")
    
    # Create flow (your beautiful API!)
    flow = Flow("test_flow")
    
    # Add orchestrator (without initializing LLM for testing)
    orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
    flow.add_orchestrator(orchestrator)
    
    # Create research team
    research_team = Supervisor(
        "research_team", 
        description="Web research specialists",
        keywords=["research", "web", "search"],
        initialize_llm=False
    )
    
    # Add agents to research team
    searcher = ReActAgent(
        "searcher",
        description="Web search specialist",
        keywords=["search", "web", "research"],
        initialize_llm=False
    ).add_tool(WriteFileTool())
    
    research_team.add_agent(searcher)
    orchestrator.add_team(research_team)
    
    # Create writing team
    writing_team = Supervisor(
        "writing_team",
        description="Document creation specialists", 
        keywords=["writing", "document", "content"],
        initialize_llm=False
    )
    
    # Add agents to writing team
    writer = ReActAgent(
        "writer",
        description="Content writer",
        keywords=["writing", "content", "document"],
        initialize_llm=False
    ).add_tool(WriteFileTool())
    
    writing_team.add_agent(writer)
    orchestrator.add_team(writing_team)
    
    print("✅ Flow setup complete!")
    print(f"   - Flow: {flow.name}")
    print(f"   - Orchestrator: {orchestrator.name}")
    print(f"   - Teams: {list(orchestrator.teams.keys())}")
    print(f"   - Research team agents: {list(research_team.agents.keys())}")
    print(f"   - Writing team agents: {list(writing_team.agents.keys())}")
    
    # Test LangGraph integration
    print("\n🔧 Testing LangGraph StateGraph building...")
    
    if hasattr(flow, '_compiled_graph') and flow._compiled_graph:
        print("✅ LangGraph StateGraph compiled successfully!")
        print(f"   - Graph nodes: {list(flow._graph.nodes.keys()) if flow._graph else 'None'}")
        
        # Test that we can access the graph structure
        if flow._graph:
            print(f"   - Total nodes: {len(flow._graph.nodes)}")
            print(f"   - Node types: {[type(node).__name__ for node in flow._graph.nodes.values()]}")
    else:
        print("❌ LangGraph StateGraph not compiled")
        return False
    
    # Test that the API structure is preserved
    print("\n🎯 Testing API structure preservation...")
    
    # Test method chaining
    test_flow = (Flow("test2")
                .add_orchestrator(Orchestrator("test_orchestrator", initialize_llm=False)))
    
    print("✅ Method chaining works!")
    
    # Test agent tool addition
    test_agent = (ReActAgent("test_agent", initialize_llm=False)
                 .add_tool(WriteFileTool())
                 .add_tool(ReadFileTool()))
    
    print(f"✅ Agent tool addition works! Tools: {list(test_agent.tools.keys())}")
    
    # Test supervisor team building
    test_supervisor = (Supervisor("test_team", initialize_llm=False)
                      .add_agent(test_agent))
    
    print(f"✅ Supervisor team building works! Agents: {list(test_supervisor.agents.keys())}")
    
    print("\n🎉 LangGraph integration test completed successfully!")
    print("   - Your beautiful OOP API is preserved")
    print("   - LangGraph StateGraph integration works")
    print("   - All method chaining works as expected")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_langgraph_integration_simple())
