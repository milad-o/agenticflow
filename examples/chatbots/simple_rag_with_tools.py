#!/usr/bin/env python3
"""
RAGAgent Tools and Multi-Agent Coordination Example
====================================================

Demonstrates how RAGAgent can use:
1. Traditional tools (calculators, APIs, search engines)
2. Agent tools via .as_tool() for multi-agent coordination
3. Hybrid approach with both knowledge base and dynamic tools

This example shows the recommended patterns for building sophisticated
RAG systems that can both retrieve from static knowledge and coordinate
with other agents for dynamic information.
"""

import asyncio
import os
from pathlib import Path

from agenticflow.chatbots import ChatbotConfig, KnowledgeMode, CitationStyle, CitationConfig
from agenticflow.chatbots import RAGAgent
from agenticflow.config.settings import LLMProviderConfig, LLMProvider, AgentConfig
from agenticflow.core.agent import Agent


def create_llm_config():
    """Standard LLM configuration for examples."""
    return LLMProviderConfig(
        provider=LLMProvider.GROQ,
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY", "sk-dummy")
    )


async def example_traditional_tools():
    """Example 1: RAGAgent with traditional tools (APIs, calculators, etc.)"""
    print("=== Example 1: RAGAgent with Traditional Tools ===")
    
    # Create RAGAgent with traditional tools
    rag_with_tools = RAGAgent(ChatbotConfig(
        name="Research Assistant",
        llm=create_llm_config(),
        knowledge_sources=[],  # Could have documents here
        tools=["web_search", "calculator", "weather", "time"],  # Traditional tools
        instructions="You help users by searching the web, doing calculations, and providing weather info."
    ))
    
    print(f"Created {rag_with_tools.name} with traditional tools")
    print(f"Tools available: {rag_with_tools.config.tools}")
    print("✅ This RAGAgent can use both knowledge base AND external APIs")
    print()


async def example_agent_as_tools():
    """Example 2: Using .as_tool() to convert agents into delegation tools"""
    print("=== Example 2: Multi-Agent Coordination via .as_tool() ===")
    
    # Create specialist agents
    data_scientist = Agent(AgentConfig(
        name="Data Scientist",
        llm=create_llm_config(),
        instructions="You analyze data, run statistical tests, and create visualizations."
    ))
    
    content_writer = Agent(AgentConfig(
        name="Content Writer", 
        llm=create_llm_config(),
        instructions="You write engaging articles, blog posts, and marketing content."
    ))
    
    code_reviewer = Agent(AgentConfig(
        name="Code Reviewer",
        llm=create_llm_config(),
        instructions="You review code for quality, performance, and best practices."
    ))
    
    # Create RAGAgent coordinator
    project_coordinator = RAGAgent(ChatbotConfig(
        name="Project Coordinator",
        llm=create_llm_config(),
        knowledge_sources=[],  # Would have project docs, standards, etc.
        instructions="""You coordinate project tasks across specialist team members.
        
        Your team:
        - Data Scientist: For analysis, statistics, and data visualization
        - Content Writer: For articles, documentation, and marketing content
        - Code Reviewer: For code quality and best practices review
        
        Delegate tasks appropriately and synthesize results."""
    ))
    
    print(f"🏗️ Created team:")
    print(f"  Coordinator: {project_coordinator.name} (RAGAgent)")
    print(f"  Specialists: {data_scientist.name}, {content_writer.name}, {code_reviewer.name}")
    
    # Start agents
    await data_scientist.start()
    await content_writer.start()
    await code_reviewer.start()
    await project_coordinator.start()
    
    # Convert specialists to tools using .as_tool()
    data_tool = data_scientist.as_tool(
        name="data_analysis",
        description="Delegate data analysis and statistical tasks"
    )
    
    writing_tool = content_writer.as_tool(
        name="content_creation",
        description="Delegate writing and content creation tasks"
    )
    
    review_tool = code_reviewer.as_tool(
        name="code_review",
        description="Delegate code review and quality assessment tasks"
    )
    
    # Register tools with coordinator
    project_coordinator.register_async_tool(data_tool)
    project_coordinator.register_async_tool(writing_tool)
    project_coordinator.register_async_tool(review_tool)
    
    available_tools = project_coordinator.get_available_tools()
    print(f"\n🔧 Coordinator tools: {available_tools}")
    print("✅ RAGAgent can now delegate to specialists via tools")
    print("✅ Clean .as_tool() API - no complex inheritance needed")
    
    # Test delegation
    print("\n🧪 Testing delegation:")
    try:
        result = await data_tool.execute({
            "task": "Calculate the average of numbers: 10, 25, 30, 45, 50",
            "context": {"project": "demo"}
        })
        
        print(f"  Data analysis result: success={result.success}")
        if result.success:
            print(f"  Response: {result.result.get('response', 'No response')[:100]}...")
            print(f"  Agent: {result.metadata.get('agent_name', 'Unknown')}")
    except Exception as e:
        print(f"  Demo delegation: {e}")
    
    # Cleanup
    await data_scientist.stop()
    await content_writer.stop()
    await code_reviewer.stop()
    await project_coordinator.stop()
    print("\n✅ Multi-agent coordination demonstrated")
    print()


async def example_hybrid_approach():
    """Example 3: Hybrid RAG with both traditional tools AND agent tools"""
    print("=== Example 3: Hybrid RAG (Knowledge + Tools + Agents) ===")
    
    # Create specialist for complex tasks
    research_specialist = Agent(AgentConfig(
        name="Research Specialist",
        llm=create_llm_config(),
        instructions="You conduct in-depth research and provide comprehensive analysis."
    ))
    
    # Create hybrid RAGAgent with everything
    hybrid_rag = RAGAgent(ChatbotConfig(
        name="Hybrid Intelligence Assistant",
        llm=create_llm_config(),
        knowledge_sources=[],  # Would have curated documents
        tools=["web_search", "calculator", "weather"],  # Traditional tools
        instructions="""You are an intelligent assistant with multiple capabilities:
        
        1. Access to curated knowledge base (documents, policies, etc.)
        2. Traditional tools (web search, calculator, weather, etc.)
        3. Specialist agents for complex research tasks
        
        Use the most appropriate source for each query:
        - Knowledge base: For documented policies, procedures, facts
        - Traditional tools: For real-time data, calculations, current info  
        - Research specialist: For complex analysis requiring deep investigation
        """
    ))
    
    await research_specialist.start()
    await hybrid_rag.start()
    
    # Add research specialist as a tool
    research_tool = research_specialist.as_tool(
        name="deep_research",
        description="Delegate complex research and analysis tasks"
    )
    
    hybrid_rag.register_async_tool(research_tool)
    
    print(f"🎯 Created {hybrid_rag.name}")
    print(f"  Knowledge sources: {len(hybrid_rag.config.knowledge_sources)} documents")
    print(f"  Traditional tools: {hybrid_rag.config.tools}")
    print(f"  Agent tools: {len([t for t in hybrid_rag.get_available_tools() if 'research' in t])} specialist(s)")
    
    print("\n💡 This agent can handle any query by choosing the right source:")
    print("  📚 'What's our vacation policy?' → Knowledge base")
    print("  🌤️ 'What's the weather today?' → Weather tool")
    print("  📊 'Calculate quarterly growth' → Calculator tool")
    print("  🔍 'Research market trends in AI' → Research specialist agent")
    print("  🌐 'Latest news about Python' → Web search tool")
    
    await research_specialist.stop()
    await hybrid_rag.stop()
    print("\n✅ Hybrid RAG approach demonstrated")
    print()


async def main():
    """Run all examples demonstrating RAGAgent capabilities"""
    print("RAGAgent Tools and Multi-Agent Coordination Examples")
    print("=" * 60)
    
    try:
        await example_traditional_tools()
        await example_agent_as_tools()
        await example_hybrid_approach()
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS: All RAGAgent patterns demonstrated!")
        print("=" * 60)
        
        print("\n💡 Key Takeaways:")
        print("✅ RAGAgent inherits all Agent tool capabilities")
        print("✅ .as_tool() enables clean multi-agent coordination")
        print("✅ Hybrid approach: knowledge + tools + agents")
        print("✅ Choose the right tool for each task type")
        print("✅ No complex inheritance - just composition")
        
        print("\n🚀 Recommended Architecture:")
        print("• RAGAgent as intelligent coordinator")
        print("• Traditional tools for APIs, calculations, etc.")
        print("• Agent tools via .as_tool() for complex delegation")
        print("• Knowledge base for curated/static information")
        print("• LLM decides which source to use for each query")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())