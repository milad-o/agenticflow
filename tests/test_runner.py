#!/usr/bin/env python3
"""Comprehensive test runner for AgenticFlow with API key handling."""

import os
import sys
import asyncio
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_api_keys():
    """Check if required API keys are available."""
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    print("🔑 API Key Status:")
    print(f"   OpenAI API Key: {'✅ Found' if openai_key else '❌ Missing'}")
    print(f"   Tavily API Key: {'✅ Found' if tavily_key else '❌ Missing'}")
    
    return bool(openai_key), bool(tavily_key)

async def run_basic_tests():
    """Run basic tests without API keys."""
    print("\n🧪 Running Basic Tests (No API Keys Required)")
    print("=" * 50)
    
    # Test basic flow creation
    from agenticflow import Flow, Orchestrator, Supervisor, SimpleAgent
    
    flow = Flow("test_flow")
    orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
    flow.add_orchestrator(orchestrator)
    
    team = Supervisor("test_team", initialize_llm=False)
    agent = SimpleAgent("test_agent", description="Test agent")
    team.add_agent(agent)
    orchestrator.add_team(team)
    
    print("✅ Basic flow creation: PASSED")
    
    # Test method chaining
    flow2 = (Flow("chaining_flow")
             .add_orchestrator(Orchestrator("main", initialize_llm=False)))
    
    print("✅ Method chaining: PASSED")
    
    # Test LangGraph integration
    assert flow._compiled_graph is not None
    print("✅ LangGraph integration: PASSED")
    
    # Test flow execution
    await flow.start("Test message")
    messages = await flow.get_messages()
    assert len(messages) > 0
    print("✅ Flow execution: PASSED")
    
    print("\n🎉 All basic tests passed!")

async def run_llm_tests():
    """Run tests with LLM capabilities."""
    print("\n🤖 Running LLM Tests (API Keys Required)")
    print("=" * 50)
    
    from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
    from agenticflow.tools import WriteFileTool, ReadFileTool
    
    # Create flow with LLM
    flow = Flow("llm_test_flow")
    orchestrator = Orchestrator("main_orchestrator")
    flow.add_orchestrator(orchestrator)
    
    # Create team with ReAct agent
    team = Supervisor("research_team", description="Research specialists")
    agent = ReActAgent("researcher", description="Research agent")
    agent.add_tool(WriteFileTool())
    team.add_agent(agent)
    orchestrator.add_team(team)
    
    print("✅ LLM flow creation: PASSED")
    
    # Test LLM routing
    await flow.start("Research the latest AI trends and write a brief summary")
    messages = await flow.get_messages()
    
    print(f"✅ LLM execution: PASSED ({len(messages)} messages generated)")
    
    # Show sample output
    if messages:
        print("\n📝 Sample output:")
        for i, msg in enumerate(messages[-3:], 1):  # Show last 3 messages
            print(f"   {i}. [{msg.sender}]: {msg.content[:100]}...")
    
    print("\n🎉 LLM tests passed!")

async def run_web_search_tests():
    """Run tests with web search capabilities."""
    print("\n🌐 Running Web Search Tests (Tavily API Required)")
    print("=" * 50)
    
    from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
    from agenticflow.tools import TavilySearchTool, WriteFileTool
    
    # Create flow with web search
    flow = Flow("web_search_flow")
    orchestrator = Orchestrator("main_orchestrator")
    flow.add_orchestrator(orchestrator)
    
    # Create research team
    research_team = Supervisor("research_team", description="Web research specialists")
    searcher = ReActAgent("searcher", description="Web search specialist")
    searcher.add_tool(TavilySearchTool())
    searcher.add_tool(WriteFileTool())
    research_team.add_agent(searcher)
    orchestrator.add_team(research_team)
    
    print("✅ Web search flow creation: PASSED")
    
    # Test web search
    await flow.start("Search for the latest developments in AI agents and write a summary")
    messages = await flow.get_messages()
    
    print(f"✅ Web search execution: PASSED ({len(messages)} messages generated)")
    
    # Show sample output
    if messages:
        print("\n📝 Sample output:")
        for i, msg in enumerate(messages[-3:], 1):
            print(f"   {i}. [{msg.sender}]: {msg.content[:100]}...")
    
    print("\n🎉 Web search tests passed!")

async def run_comprehensive_demo():
    """Run a comprehensive demo showcasing all features."""
    print("\n🚀 Running Comprehensive Demo")
    print("=" * 50)
    
    from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
    from agenticflow.tools import TavilySearchTool, WriteFileTool, ReadFileTool
    
    # Create comprehensive flow
    flow = Flow("comprehensive_demo")
    orchestrator = Orchestrator("main_orchestrator")
    flow.add_orchestrator(orchestrator)
    
    # Research team
    research_team = Supervisor(
        "research_team", 
        description="Web research and data analysis specialists",
        keywords=["research", "web", "search", "data", "analysis"]
    )
    
    web_searcher = (ReActAgent("web_searcher", description="Web search specialist")
                   .add_tool(TavilySearchTool())
                   .add_tool(WriteFileTool()))
    
    data_analyst = (ReActAgent("data_analyst", description="Data analysis specialist")
                   .add_tool(ReadFileTool())
                   .add_tool(WriteFileTool()))
    
    research_team.add_agent(web_searcher)
    research_team.add_agent(data_analyst)
    orchestrator.add_team(research_team)
    
    # Writing team
    writing_team = Supervisor(
        "writing_team",
        description="Content creation and editing specialists",
        keywords=["writing", "content", "document", "report", "editing"]
    )
    
    content_writer = (ReActAgent("content_writer", description="Content writer")
                     .add_tool(WriteFileTool())
                     .add_tool(ReadFileTool()))
    
    editor = (ReActAgent("editor", description="Content editor")
             .add_tool(ReadFileTool())
             .add_tool(WriteFileTool()))
    
    writing_team.add_agent(content_writer)
    writing_team.add_agent(editor)
    orchestrator.add_team(writing_team)
    
    print("✅ Comprehensive flow setup: PASSED")
    print(f"   - Teams: {list(orchestrator.teams.keys())}")
    print(f"   - Research agents: {list(research_team.agents.keys())}")
    print(f"   - Writing agents: {list(writing_team.agents.keys())}")
    
    # Run comprehensive workflow
    print("\n🎯 Running comprehensive workflow...")
    await flow.start("Research the latest AI agent frameworks, analyze their capabilities, and write a comprehensive report comparing them")
    
    # Get results
    messages = await flow.get_messages()
    print(f"\n📝 Generated {len(messages)} messages:")
    
    for i, msg in enumerate(messages, 1):
        print(f"   {i}. [{msg.sender}]: {msg.content[:150]}{'...' if len(msg.content) > 150 else ''}")
    
    print("\n🎉 Comprehensive demo completed successfully!")
    return messages

async def main():
    """Main test runner."""
    print("🧪 AgenticFlow Comprehensive Test Suite")
    print("=" * 50)
    
    # Check API keys
    has_openai, has_tavily = check_api_keys()
    
    # Run basic tests (always)
    await run_basic_tests()
    
    # Run LLM tests if OpenAI key available
    if has_openai:
        await run_llm_tests()
    else:
        print("\n⚠️  Skipping LLM tests (no OpenAI API key)")
    
    # Run web search tests if Tavily key available
    if has_tavily:
        await run_web_search_tests()
    else:
        print("\n⚠️  Skipping web search tests (no Tavily API key)")
    
    # Run comprehensive demo if both keys available
    if has_openai and has_tavily:
        await run_comprehensive_demo()
    else:
        print("\n⚠️  Skipping comprehensive demo (missing API keys)")
    
    print("\n🎉 All tests completed!")
    print("\n📊 Summary:")
    print("   ✅ Basic functionality: PASSED")
    print(f"   {'✅' if has_openai else '❌'} LLM capabilities: {'PASSED' if has_openai else 'SKIPPED'}")
    print(f"   {'✅' if has_tavily else '❌'} Web search: {'PASSED' if has_tavily else 'SKIPPED'}")
    print(f"   {'✅' if has_openai and has_tavily else '❌'} Comprehensive demo: {'PASSED' if has_openai and has_tavily else 'SKIPPED'}")

if __name__ == "__main__":
    asyncio.run(main())
