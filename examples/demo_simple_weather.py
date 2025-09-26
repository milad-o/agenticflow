#!/usr/bin/env python3
"""
Simple Weather Demo - Enhanced RPAVH Agent with Tavily Search

This simplified demo shows:
1. Enhanced RPAVH agent brain working with real tools
2. Intelligent reflection and decision-making
3. Tool usage for weather research
4. Clean agent architecture

Fixes the serialization issues by using simpler checkpointer setup.
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AgenticFlow components
from agenticflow.agent.base.agent import Agent
from agenticflow.agent.strategies.enhanced_rpavh_agent import EnhancedRPAVHGraphFactory
from agenticflow.observability.flow_logger import get_flow_logger, LogLevel
from agenticflow.core.models import get_chat_model

# Import Tavily search tool
from langchain_community.tools.tavily_search import TavilySearchResults

# Import file tools for report writing
from agenticflow.tools.file.file_tools import WriteTextAtomicTool


async def run_simple_weather_demo():
    """Run a simple weather research demo."""
    
    logger = get_flow_logger()
    
    logger.flow("🌤️ Simple Weather Research Demo", 
               demo_type="weather_research",
               agent_type="enhanced_rpavh",
               level=LogLevel.SUCCESS)
    
    print("🌤️ Simple Weather Research Demo")
    print("=" * 50)
    print("Testing Enhanced RPAVH agent with Tavily search...")
    print()
    
    try:
        # Create LLM
        model = get_chat_model(
            model_name="granite3.2:8b", 
            temperature=0.1
        )
        
        # Create Tavily search tool
        tavily_search = TavilySearchResults(
            max_results=3,
            search_depth="basic",
            include_answer=True
        )
        
        tools = [tavily_search]
        
        # Create enhanced brain
        enhanced_brain = EnhancedRPAVHGraphFactory(
            use_llm_for_planning=True,
            use_llm_for_verification=True,
            max_parallel_tasks=1,
            max_retries=1
        ).create_graph()
        
        # Create agent with NO checkpointer to avoid serialization issues
        agent = Agent(
            model=model,  # Required LLM instance
            name="weather_researcher",  # Required name
            tools=tools,
            custom_graph=enhanced_brain,
            checkpointer=None,  # Disable checkpointing to avoid serialization
            use_llm_reflection=True,
            use_llm_verification=False  # Simplified for this demo
        )
        
        logger.agent("🤖 Created Enhanced RPAVH Weather Agent",
                    agent_name="weather_researcher",
                    tools_count=len(tools),
                    brain_type="enhanced_rpavh",
                    checkpointer_disabled=True,
                    level=LogLevel.SUCCESS)
        
        # Simple weather request
        weather_request = """
        Please research the current weather in Toronto, Canada. 
        
        I need to know:
        - Current temperature
        - Weather conditions (sunny, cloudy, etc.)  
        - Any weather alerts
        
        Use online search to get the most current information available.
        """
        
        print("📡 Asking agent to research Toronto weather...")
        print(f"🔍 Request: {weather_request.strip()}")
        print()
        
        # Execute with enhanced agent
        result = await agent.arun(
            message=weather_request,
            thread_id=f"weather_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Display results
        success = result.get("success", False)
        message = result.get("message", "No response")
        agent_name = result.get("agent_name", "unknown")
        
        logger.agent(f"🎯 Agent Execution: {'✅ Success' if success else '❌ Failed'}",
                    agent_name=agent_name,
                    execution_success=success,
                    level=LogLevel.SUCCESS if success else LogLevel.ERROR)
        
        print("=" * 50)
        print("🎯 RESULTS:")
        print("=" * 50)
        print(f"Agent: {agent_name}")
        print(f"Success: {'✅ Yes' if success else '❌ No'}")
        print()
        print("📝 Response:")
        print(message)
        print("=" * 50)
        
        if success:
            print("\n🎉 Demo completed successfully!")
            print("✨ The Enhanced RPAVH agent successfully:")
            print("  • Reflected on the weather research task")
            print("  • Decided to use the Tavily search tool")
            print("  • Executed online search for current weather")
            print("  • Provided comprehensive weather information")
        else:
            print("\n⚠️ Demo had issues. See details above.")
            if "serialization" in message.lower():
                print("💡 This might be due to tool serialization in checkpointer.")
                print("   The agent brain is working but complex objects can't be serialized.")
        
        return result
        
    except Exception as e:
        logger.flow(f"❌ Demo failed: {str(e)}", 
                   error=str(e),
                   level=LogLevel.ERROR)
        print(f"\n❌ Demo failed: {str(e)}")
        return {"success": False, "error": str(e)}


async def main():
    """Main demo function."""
    
    # Check for API key
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ Please set your TAVILY_API_KEY in the .env file")
        print("You can get a free API key from: https://tavily.com/")
        return
    
    await run_simple_weather_demo()


if __name__ == "__main__":
    asyncio.run(main())