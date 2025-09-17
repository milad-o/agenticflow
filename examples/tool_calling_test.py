#!/usr/bin/env python3
"""
Tool Calling Test for AgenticFlow

This script tests the LLM tool calling integration to reproduce the issue
where tools are mentioned by the LLM but not actually executed.

Based on the conversation history, the problem is:
- Tools are properly registered in the agent
- LLM mentions using tools and formats requests appropriately
- But no actual tool calls are executed (tool_results remains empty)
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
import sys
import os
import platform

# Add the src directory to path so we can import agenticflow
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from agenticflow import Agent, ToolRegistry
from agenticflow.tools.base import tool


# Register specialized test tools similar to those mentioned in conversation history
@tool("read_file", "Reads the contents of a file and returns it as text")
def read_file_tool(file_path: str) -> str:
    """Read file contents"""
    print(f"🔧 TOOL EXECUTED: read_file_tool({file_path})")
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return f"File content ({len(content)} chars): {content[:200]}..."
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool("get_time", "Gets the current date and time")
def get_time_tool() -> str:
    """Get current time"""
    print(f"🔧 TOOL EXECUTED: get_time_tool()")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool("system_info", "Gets system information like platform and Python version")
def system_info_tool() -> str:
    """Get system information"""
    print(f"🔧 TOOL EXECUTED: system_info_tool()")
    return f"Platform: {platform.system()} {platform.release()}, Python: {sys.version}"


@tool("list_directory", "Lists files and directories in a given path")
def list_directory_tool(path: str = ".") -> str:
    """List directory contents"""
    print(f"🔧 TOOL EXECUTED: list_directory_tool({path})")
    try:
        items = list(Path(path).iterdir())
        return f"Directory {path} contains {len(items)} items: {[item.name for item in items[:10]]}"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@tool("precise_math", "Performs precise mathematical calculations")
def precise_math_tool(expression: str) -> str:
    """Calculate mathematical expression"""
    print(f"🔧 TOOL EXECUTED: precise_math_tool({expression})")
    try:
        # Simple safe evaluation for basic math
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


@tool("network_info", "Gets network and connectivity information")  
def network_info_tool() -> str:
    """Get network information"""
    print(f"🔧 TOOL EXECUTED: network_info_tool()")
    import socket
    hostname = socket.gethostname()
    return f"Hostname: {hostname}, Local IP: {socket.gethostbyname(hostname)}"


async def test_tool_calling():
    """Test tool calling functionality with various scenarios"""
    
    print("=" * 70)
    print("🔧 AGENTICFLOW TOOL CALLING TEST")
    print("=" * 70)
    print()
    
    # Register all test tools
    registry = ToolRegistry()
    tools = [
        read_file_tool,
        get_time_tool, 
        system_info_tool,
        list_directory_tool,
        precise_math_tool,
        network_info_tool
    ]
    
    print("📋 Registering test tools:")
    for tool_func in tools:
        registry.register_tool(tool_func)
        print(f"   ✅ {tool_func.name}: {tool_func.description}")
    
    print(f"\n🎯 Total tools registered: {len(registry.tools)}")
    print()
    
    # Create agent with tools
    print("🤖 Creating agent with tool registry...")
    agent = Agent(
        name="ToolTestAgent",
        persona="You are a helpful assistant that uses tools to complete tasks. When asked to do something, use the appropriate tools available to you.",
        tools=list(registry.tools.values()),
        verbose=True
    )
    
    print(f"🔧 Agent tools loaded: {len(agent.tools)}")
    for tool_name in agent.tools.keys():
        print(f"   - {tool_name}")
    print()
    
    # Test scenarios that should trigger tool usage
    test_queries = [
        {
            "query": "What time is it right now?",
            "expected_tool": "get_time",
            "description": "Time inquiry should use get_time tool"
        },
        {
            "query": "What files are in the current directory?", 
            "expected_tool": "list_directory",
            "description": "Directory listing should use list_directory tool"
        },
        {
            "query": "Calculate 15 * 8 + 23",
            "expected_tool": "precise_math", 
            "description": "Math calculation should use precise_math tool"
        },
        {
            "query": "What system am I running on?",
            "expected_tool": "system_info",
            "description": "System query should use system_info tool"
        },
        {
            "query": "What's my network hostname?",
            "expected_tool": "network_info",
            "description": "Network query should use network_info tool"
        }
    ]
    
    # Track results
    total_tests = len(test_queries)
    tools_executed = 0
    results = []
    
    print("🧪 Running tool calling tests...")
    print()
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"📝 Test {i}/{total_tests}: {test_case['description']}")
        print(f"   Query: \"{test_case['query']}\"")
        print(f"   Expected tool: {test_case['expected_tool']}")
        print()
        
        # Track if tool was executed
        print("   🔍 Looking for tool execution...")
        tool_executed = False
        
        try:
            # Execute the task
            start_time = time.time()
            response = await agent.execute_task(test_case['query'])
            execution_time = time.time() - start_time
            
            # Check if response indicates tool usage
            print(f"   📝 Response: {response[:200]}...")
            print(f"   ⏱️  Execution time: {execution_time:.2f}s")
            
            # In the current broken state, we expect the tool to NOT be executed
            # The fix should make tools actually execute
            
            results.append({
                "test": test_case['description'],
                "query": test_case['query'],
                "expected_tool": test_case['expected_tool'],
                "tool_executed": tool_executed,
                "response": response,
                "execution_time": execution_time
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                "test": test_case['description'], 
                "query": test_case['query'],
                "expected_tool": test_case['expected_tool'],
                "tool_executed": False,
                "error": str(e),
                "execution_time": 0
            })
        
        print("   " + "-" * 60)
        print()
    
    # Summary
    print("=" * 70)
    print("📊 TOOL CALLING TEST RESULTS")
    print("=" * 70)
    
    successful_tool_calls = sum(1 for r in results if r.get('tool_executed', False))
    
    print(f"🎯 Tool Execution Rate: {successful_tool_calls}/{total_tests} ({successful_tool_calls/total_tests*100:.1f}%)")
    print()
    
    print("📋 Individual Test Results:")
    for i, result in enumerate(results, 1):
        status = "✅" if result.get('tool_executed', False) else "❌"
        print(f"  {status} Test {i}: {result['expected_tool']} - {result['test']}")
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    print()
    
    # Analysis
    if successful_tool_calls == 0:
        print("🚨 ISSUE CONFIRMED: No tools were executed!")
        print("   This confirms the tool calling integration problem.")
        print("   The LLM likely mentions tools but doesn't execute them.")
        print()
        print("🔧 Next steps:")
        print("   1. Examine agent.execute_task() method")
        print("   2. Check tool call parsing in LLM responses")  
        print("   3. Verify tool execution dispatch logic")
        print("   4. Test with different LLM providers")
    elif successful_tool_calls < total_tests:
        print("⚠️  PARTIAL ISSUE: Some tools executed, some didn't")
        print("   The tool calling system works partially.")
    else:
        print("✅ SUCCESS: All tools executed correctly!")
        print("   The tool calling integration is working properly.")
    
    return {
        "total_tests": total_tests,
        "successful_tool_calls": successful_tool_calls,
        "success_rate": successful_tool_calls / total_tests,
        "results": results
    }


if __name__ == "__main__":
    result = asyncio.run(test_tool_calling())
    
    print()
    print("=" * 70)  
    if result["success_rate"] == 0:
        print("🚨 TOOL CALLING BROKEN - NEEDS FIXING")
    elif result["success_rate"] < 1.0:
        print("⚠️  TOOL CALLING PARTIALLY WORKING")
    else:
        print("✅ TOOL CALLING WORKING CORRECTLY")
    print("=" * 70)