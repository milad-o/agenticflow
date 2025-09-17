#!/usr/bin/env python3
"""
Validate Tool Calling Fix

This script tests the enhanced tool calling functionality in AgenticFlow
by creating an agent that can properly detect and execute tools based on
LLM responses.
"""

import asyncio
import time
from datetime import datetime
import platform
from pathlib import Path
import sys

# Add the src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# Direct imports to bypass circular dependency issues
from agenticflow.tools.base import tool
from agenticflow.config.settings import AgentConfig, LLMConfig, MemoryConfig, LLMProvider


# Define test tools
@tool("get_time", "Gets the current date and time")
def get_time_tool() -> str:
    """Get current time"""
    print(f"🔧 TOOL EXECUTED: get_time_tool()")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool("system_info", "Gets system information like platform and Python version")
def system_info_tool() -> str:
    """Get system information"""
    print(f"🔧 TOOL EXECUTED: system_info_tool()")
    return f"Platform: {platform.system()} {platform.release()}, Python: {platform.python_version()}"


@tool("precise_math", "Performs precise mathematical calculations")
def precise_math_tool(expression: str) -> str:
    """Calculate mathematical expression"""
    print(f"🔧 TOOL EXECUTED: precise_math_tool({expression})")
    try:
        # Simple safe evaluation for basic math
        allowed_chars = "0123456789+-*/.() "
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return f"Result: {expression} = {result}"
        else:
            return "Error: Invalid characters in expression"
    except Exception as e:
        return f"Error calculating: {str(e)}"


async def test_agent_tool_calling():
    """Test tool calling using actual Agent class"""
    
    print("=" * 70)
    print("🔧 AGENT TOOL CALLING VALIDATION")
    print("=" * 70)
    print()
    
    # Register tools in global registry
    from agenticflow.tools.base_tool import get_tool_registry
    global_registry = get_tool_registry()
    
    tools = [get_time_tool, system_info_tool, precise_math_tool]
    print("📋 Registering test tools globally:")
    for tool_func in tools:
        global_registry.register_tool(tool_func)
        print(f"   ✅ {tool_func.name}: {tool_func.description}")
    
    print(f"\n🎯 Total tools in global registry: {len(global_registry.list_tools())}")
    print()
    
    # Create agent configuration
    agent_config = AgentConfig(
        name="ToolTestAgent",
        instructions="You are a helpful assistant that uses tools to complete tasks. When you need information that requires a tool, use the appropriate tool available to you.",
        tools=["get_time", "system_info", "precise_math"],  # Reference tools by name
        llm=LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="qwen2.5:7b",
            temperature=0.1
        ),
        memory=MemoryConfig(type="buffer", max_messages=10),
        verbose=True
    )
    
    # Import Agent after tools are registered
    try:
        # Fix the circular import by importing Agent directly from the file
        import importlib.util
        agent_module_path = src_dir / "agenticflow" / "core" / "agent.py"
        
        print("🤖 Loading Agent class...")
        # This should work now that we've fixed the tool calling logic
        from agenticflow.core.agent import Agent
        
        print("✅ Agent class loaded successfully")
        
        # Create and start agent
        agent = Agent(agent_config)
        await agent.start()
        
        print(f"🤖 Agent '{agent.name}' started")
        print(f"🔧 Agent has {len(agent._tool_registry.list_tools()) if agent._tool_registry else 0} tools")
        
        if agent._tool_registry:
            print("   Tools available:")
            for tool_name in agent._tool_registry.list_tools():
                print(f"     - {tool_name}")
        
        print()
        
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        print("This likely indicates the circular import issue is not fully resolved.")
        import traceback
        traceback.print_exc()
        return {"success_rate": 0, "error": str(e)}
    
    # Test queries that should trigger tool usage
    test_queries = [
        {
            "query": "What time is it right now?",
            "expected_tool": "get_time",
            "description": "Time query should trigger get_time tool"
        },
        {
            "query": "What system am I running on?",
            "expected_tool": "system_info",
            "description": "System query should trigger system_info tool"
        },
        {
            "query": "Calculate 15 * 8 + 23 for me",
            "expected_tool": "precise_math",
            "description": "Math query should trigger precise_math tool"
        },
    ]
    
    results = []
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"📝 Test {i}: {test_case['description']}")
        print(f"   Query: \"{test_case['query']}\"")
        print()
        
        try:
            # Execute task using the agent
            start_time = time.time()
            result = await agent.execute_task(test_case['query'])
            execution_time = time.time() - start_time
            
            # Check the result
            response = result.get('response', '')
            tool_results = result.get('tool_results', [])
            
            print(f"📝 Agent Response: {response[:200]}...")
            print(f"🔧 Tool Results: {tool_results}")
            print(f"⏱️  Execution time: {execution_time:.2f}s")
            
            # Check if expected tool was executed
            tool_executed = any(
                tr.get('tool') == test_case['expected_tool'] and tr.get('success', False)
                for tr in tool_results
            )
            
            results.append({
                "query": test_case['query'],
                "expected_tool": test_case['expected_tool'],
                "tool_executed": tool_executed,
                "tool_results": tool_results,
                "response": response,
                "execution_time": execution_time,
                "success": tool_executed
            })
            
            if tool_executed:
                print("✅ Expected tool executed successfully!")
            else:
                print("❌ Expected tool was not executed")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append({
                "query": test_case['query'],
                "expected_tool": test_case['expected_tool'],
                "success": False,
                "error": str(e)
            })
        
        print("   " + "-" * 60)
        print()
    
    # Stop agent
    try:
        await agent.stop()
        print("🛑 Agent stopped successfully")
    except Exception as e:
        print(f"⚠️ Error stopping agent: {e}")
    
    # Results summary
    print("=" * 70)
    print("📊 VALIDATION RESULTS")
    print("=" * 70)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    print(f"🎯 Tool Execution Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    print()
    
    for i, result in enumerate(results, 1):
        status = "✅" if result.get('success', False) else "❌"
        print(f"  {status} Test {i}: {result['expected_tool']} - {result.get('query', '')[:40]}...")
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    print()
    
    if successful_tests == 0:
        print("🚨 TOOL CALLING STILL BROKEN!")
        print("   The enhanced tool detection may need further refinement.")
    elif successful_tests < total_tests:
        print("⚠️  PARTIAL SUCCESS")
        print("   Some tools are working, continue investigating failures.")
    else:
        print("🎉 TOOL CALLING FIXED!")
        print("   All tools are being properly detected and executed.")
    
    return {
        "success_rate": successful_tests / total_tests,
        "results": results,
        "total_tests": total_tests,
        "successful_tests": successful_tests
    }


if __name__ == "__main__":
    result = asyncio.run(test_agent_tool_calling())
    
    print()
    print("=" * 70)
    if result["success_rate"] == 0:
        print("🚨 TOOL CALLING FIX UNSUCCESSFUL")
        print("   → Need further investigation and refinement")
    elif result["success_rate"] < 1.0:
        print("⚠️  TOOL CALLING PARTIALLY FIXED")
        print("   → Continue debugging failing cases")
    else:
        print("✅ TOOL CALLING SUCCESSFULLY FIXED!")
        print("   → The enhanced implicit tool detection is working")
    print("=" * 70)