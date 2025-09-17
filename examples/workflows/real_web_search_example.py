#!/usr/bin/env python3
"""
Production Web Search Example
============================
Demonstrates using a real external MCP server for web search capabilities
integrated with AgenticFlow agents.
"""

import asyncio
import json
from pathlib import Path
from agenticflow import Agent
from agenticflow.config.settings import AgentConfig, LLMProvider, LLMProviderConfig
from agenticflow.mcp.config import MCPServerConfig, MCPConfig

async def main():
    """Demonstrate real web search with MCP integration."""
    print("🌐 AgenticFlow + Real Web Search MCP Server")
    print("=" * 55)
    print("This example shows AgenticFlow using a real external")
    print("MCP server to search the web via Google results.\n")
    
    # Check if web search server exists (beside this example)
    current_dir = Path(__file__).parent  # Same directory as this example
    web_search_path = current_dir / "web-search" / "build" / "index.js"
    
    if not web_search_path.exists():
        print("❌ Web search MCP server not found!")
        print(f"Expected at: {web_search_path}")
        print("\nTo set up:")
        print("1. cd examples/workflows/web-search")
        print("2. npm install")
        print("3. npm run build")
        return
    
    print(f"✅ Found web search server: {web_search_path}\n")
    
    # Configure MCP integration
    mcp_config = MCPConfig(
        servers=[
            MCPServerConfig(
                name="web-search",
                command=["node", str(web_search_path)],
                timeout=30.0,
                max_retries=2,
                expected_tools=["search"],
                description="Google web search via MCP"
            )
        ],
        auto_register_tools=True,
        tool_namespace=True
    )
    
    # Create agent with web search capability
    agent = Agent(AgentConfig(
        name="web_search_assistant",
        llm=LLMProviderConfig(
            provider=LLMProvider.OLLAMA,
            model="granite3.2:8b"
        ),
        mcp_config=mcp_config
    ))
    
    try:
        print("🚀 Starting agent with web search capability...")
        await agent.start()
        print("✅ Agent started with web search enabled!\n")
        
        # Example 1: Technical search
        print("1️⃣ Searching for 'Python async programming best practices'...")
        result1 = await agent.execute_task(
            "Search for 'Python async programming best practices' and summarize the key points from the top result"
        )
        if result1.get('success'):
            print("📋 Result:")
            print(f"   {result1['response']}\n")
        else:
            print(f"   ❌ Search failed: {result1.get('error', 'Unknown')}\n")
        
        # Example 2: News/Current events
        print("2️⃣ Searching for 'latest AI developments 2025'...")
        result2 = await agent.execute_task(
            "Search for 'latest AI developments 2025' and tell me about the most interesting finding"
        )
        if result2.get('success'):
            print("📋 Result:")
            print(f"   {result2['response']}\n")
        else:
            print(f"   ❌ Search failed: {result2.get('error', 'Unknown')}\n")
        
        # Example 3: Direct API usage
        print("3️⃣ Direct MCP tool usage...")
        if hasattr(agent, '_tool_registry'):
            # Try direct tool execution
            search_result = await agent._tool_registry.execute_tool(
                "search", 
                {"query": "Model Context Protocol GitHub", "limit": 2}
            )
            
            if search_result.success:
                print("✅ Direct search successful!")
                try:
                    results = json.loads(search_result.result)
                    print("📊 Search results:")
                    for i, result in enumerate(results, 1):
                        print(f"   {i}. {result.get('title', 'No title')}")
                        print(f"      {result.get('url', 'No URL')}")
                except json.JSONDecodeError:
                    print(f"📄 Raw result: {search_result.result}")
            else:
                print(f"❌ Direct search failed: {search_result.error}")
        
        print("\n🎉 Web search integration demonstration complete!")
        print("🔍 Your AgenticFlow agent can now search the web!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        print("\n🛑 Stopping agent...")
        await agent.stop()
        print("✅ Agent stopped")

if __name__ == "__main__":
    asyncio.run(main())