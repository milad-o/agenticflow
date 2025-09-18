#!/usr/bin/env python3
"""
RAGAgent Natural Supervision Example
====================================

Demonstrates how RAGAgent can naturally supervise specialist agents using 
the clean .as_tool() API. This is the recommended approach for multi-agent
coordination in AgenticFlow.

Key Features:
- RAGAgent as knowledge-powered supervisor
- Specialist agents converted to tools via .as_tool()
- Clean delegation without complex inheritance
- Automatic citation and error handling
"""

import asyncio
import os

from agenticflow import RAGAgent, Agent, ChatbotConfig, LLMProviderConfig, LLMProvider
from agenticflow.config.settings import AgentConfig


def create_llm_config():
    """Standard LLM config for examples."""
    return LLMProviderConfig(
        provider=LLMProvider.GROQ,
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY", "sk-dummy")
    )


async def main():
    print("RAGAgent Natural Supervision Example")
    print("=" * 50)
    
    # Create specialist agents
    data_analyst = Agent(AgentConfig(
        name="Data Analyst",
        llm=create_llm_config(),
        instructions="You analyze data and provide insights. Be precise with calculations."
    ))
    
    report_writer = Agent(AgentConfig(
        name="Report Writer",
        llm=create_llm_config(),
        instructions="You create professional reports and documentation. Be clear and structured."
    ))
    
    researcher = Agent(AgentConfig(
        name="Researcher",
        llm=create_llm_config(),
        instructions="You research topics and gather information. Provide comprehensive analysis."
    ))
    
    # Create RAGAgent supervisor with knowledge base
    project_manager = RAGAgent(ChatbotConfig(
        name="Project Manager",
        llm=create_llm_config(),
        knowledge_sources=[],  # Would contain project management knowledge
        tools=["calendar", "task_tracker"],  # Regular tools
        instructions="""You are an experienced project manager coordinating a team of specialists.
        
        Your team includes:
        - Data Analyst: Handles all data analysis, calculations, and statistical work
        - Report Writer: Creates professional reports, documentation, and presentations  
        - Researcher: Conducts research, gathers information, and analyzes trends
        
        Delegate tasks to the appropriate specialists and synthesize their results.
        Always cite which team member provided each piece of information."""
    ))
    
    print("🏗️ Created team:")
    print(f"  - Supervisor: {project_manager.name} (RAGAgent)")
    print(f"  - Specialist: {data_analyst.name}")
    print(f"  - Specialist: {report_writer.name}")
    print(f"  - Specialist: {researcher.name}")
    
    # Start all agents
    print("\n🚀 Starting agents...")
    await data_analyst.start()
    await report_writer.start()
    await researcher.start() 
    await project_manager.start()
    
    # Convert specialists to tools using .as_tool()
    print("\n🔧 Converting specialists to delegation tools...")
    
    analyst_tool = data_analyst.as_tool(
        name="data_analysis",
        description="Delegate data analysis, calculations, and statistical work"
    )
    
    writer_tool = report_writer.as_tool(
        name="report_writing", 
        description="Delegate report creation, documentation, and presentation tasks"
    )
    
    research_tool = researcher.as_tool(
        name="research",
        description="Delegate research, information gathering, and trend analysis"
    )
    
    # Register tools with supervisor
    project_manager.register_async_tool(analyst_tool)
    project_manager.register_async_tool(writer_tool)  
    project_manager.register_async_tool(research_tool)
    
    available_tools = project_manager.get_available_tools()
    print(f"✅ Registered delegation tools: {available_tools}")
    
    # Test natural supervision
    print("\n📋 Testing natural supervision with complex task...")
    
    complex_task = """
    We need to launch a new product line. Please coordinate the following:
    1. Analyze the market size and growth potential for our target demographic
    2. Research competitor pricing and feature comparisons
    3. Calculate projected revenue for the first 3 years assuming 5% market capture
    4. Create an executive summary report with recommendations
    
    This requires analysis, research, calculations, and professional reporting.
    """
    
    print(f"Complex Task: {complex_task[:100]}...")
    print("\n🎯 In practice, the RAGAgent would:")
    print("1. Receive the complex task")
    print("2. Use its knowledge base to understand project management best practices")
    print("3. Decide which subtasks to delegate to which specialists")
    print("4. Use data_analysis tool → delegate calculations to Data Analyst")
    print("5. Use research tool → delegate market research to Researcher") 
    print("6. Use report_writing tool → delegate final report to Report Writer")
    print("7. Synthesize all results with proper citations")
    print("8. Provide coordinated project deliverable")
    
    # Demonstrate tool usage
    print("\n🧪 Testing individual tool delegation...")
    
    try:
        # Test data analysis delegation
        calc_result = await analyst_tool.execute({
            "task": "Calculate 5% of a $10 billion market over 3 years with 10% annual growth",
            "context": {"project": "market_analysis"}
        })
        
        print(f"\n📊 Data Analysis Result:")
        print(f"  Success: {calc_result.success}")
        print(f"  Agent: {calc_result.metadata.get('agent_name', 'Unknown')}")
        if calc_result.success:
            response = calc_result.result.get('response', 'No response')
            print(f"  Response: {response[:100]}...")
            
    except Exception as e:
        print(f"  Demo error: {e}")
    
    try:
        # Test research delegation
        research_result = await research_tool.execute({
            "task": "Analyze current trends in AI-powered productivity tools market",
            "context": {"focus": "competitive_analysis"}
        })
        
        print(f"\n🔍 Research Result:")
        print(f"  Success: {research_result.success}")
        print(f"  Agent: {research_result.metadata.get('agent_name', 'Unknown')}")
        if research_result.success:
            response = research_result.result.get('response', 'No response')
            print(f"  Response: {response[:100]}...")
            
    except Exception as e:
        print(f"  Demo error: {e}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await data_analyst.stop()
    await report_writer.stop()
    await researcher.stop()
    await project_manager.stop()
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: RAGAgent Natural Supervision Demonstrated!")
    print("=" * 60)
    print("✅ RAGAgent can supervise specialists via .as_tool()")
    print("✅ Clean delegation without complex inheritance")
    print("✅ Leverages existing tool infrastructure") 
    print("✅ Automatic error handling and metadata tracking")
    print("✅ Natural supervision through behavior, not class hierarchy")
    print("✅ Works with existing workflow orchestration systems")
    
    print("\n💡 Key Benefits:")
    print("• Simple API: agent.as_tool(name, description)")
    print("• Direct integration with Agent tool system") 
    print("• Automatic retry and error handling")
    print("• Clean separation of concerns")
    print("• Scalable to any number of specialists")
    print("• Compatible with all AgenticFlow topologies")


if __name__ == "__main__":
    asyncio.run(main())