#!/usr/bin/env python3
"""
Standalone Tool Calling Test

This script tests tool calling functionality by directly importing LLM providers
and bypassing the complex Agent system to isolate the tool calling issue.
"""

import asyncio
import time
from datetime import datetime
import sys
import platform
from pathlib import Path

# Add the src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# Direct imports to avoid circular dependencies
from agenticflow.llm_providers import get_llm_manager
from langchain_core.messages import HumanMessage, SystemMessage


def get_time_tool() -> str:
    """Get current time - MANUAL TOOL"""
    print(f"🔧 TOOL EXECUTED: get_time_tool()")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def system_info_tool() -> str:
    """Get system information - MANUAL TOOL"""
    print(f"🔧 TOOL EXECUTED: system_info_tool()")
    return f"Platform: {platform.system()} {platform.release()}, Python: {sys.version}"


def math_tool(expression: str) -> str:
    """Calculate mathematical expression - MANUAL TOOL"""
    print(f"🔧 TOOL EXECUTED: math_tool({expression})")
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


# Manual tool registry
AVAILABLE_TOOLS = {
    "get_time": {
        "func": get_time_tool,
        "description": "Gets the current date and time",
        "params": []
    },
    "system_info": {
        "func": system_info_tool,
        "description": "Gets system information like platform and Python version",
        "params": []
    },
    "math": {
        "func": math_tool,
        "description": "Performs mathematical calculations",
        "params": ["expression"]
    }
}


def process_tool_calls(response_text: str) -> dict:
    """Manually process tool calls in LLM response"""
    import json
    import re
    
    print(f"🔍 Looking for tool calls in response...")
    tool_results = {}
    
    # Method 1: Look for JSON-style tool calls
    json_patterns = [
        r'\{[^{}]*"tool"[^{}]*\}',
        r'\{[^{}]*"function"[^{}]*\}',
        r'\{[^{}]*"name"[^{}]*\}'
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        for match in matches:
            try:
                tool_call = json.loads(match)
                tool_name = tool_call.get("tool") or tool_call.get("function") or tool_call.get("name")
                if tool_name and tool_name in AVAILABLE_TOOLS:
                    print(f"🔧 Found JSON tool call: {tool_name}")
                    params = tool_call.get("parameters", {}) or tool_call.get("arguments", {})
                    result = execute_tool(tool_name, params)
                    tool_results[tool_name] = result
            except json.JSONDecodeError:
                continue
    
    # Method 2: Look for function-style calls
    func_patterns = [
        r'(\w+)\(([^)]*)\)',
        r'call (\w+)',
        r'use (\w+)'
    ]
    
    for pattern in func_patterns:
        matches = re.findall(pattern, response_text.lower())
        for match in matches:
            if isinstance(match, tuple):
                func_name, params = match[0], match[1] if len(match) > 1 else ""
            else:
                func_name, params = match, ""
                
            if func_name in AVAILABLE_TOOLS:
                print(f"🔧 Found function-style call: {func_name}")
                result = execute_tool(func_name, {"expression": params} if params else {})
                tool_results[func_name] = result
    
    # Method 3: Look for explicit mentions of tools
    for tool_name in AVAILABLE_TOOLS.keys():
        if tool_name.lower() in response_text.lower():
            print(f"🔧 Tool {tool_name} mentioned, executing...")
            result = execute_tool(tool_name, {})
            tool_results[tool_name] = result
            break  # Only execute one tool per mention pattern
    
    return tool_results


def execute_tool(tool_name: str, params: dict) -> str:
    """Execute a tool manually"""
    if tool_name not in AVAILABLE_TOOLS:
        return f"Tool {tool_name} not found"
    
    tool_info = AVAILABLE_TOOLS[tool_name]
    try:
        if params and "expression" in params:
            return tool_info["func"](params["expression"])
        else:
            return tool_info["func"]()
    except Exception as e:
        print(f"❌ Error executing {tool_name}: {e}")
        return f"Error: {str(e)}"


async def test_standalone_tool_calling():
    """Test tool calling without Agent class"""
    
    print("=" * 70)
    print("🔧 STANDALONE TOOL CALLING TEST")
    print("=" * 70)
    print()
    
    # Initialize LLM provider directly
    try:
        print("🤖 Initializing LLM provider...")
        llm_manager = get_llm_manager()
        llm_provider = llm_manager.get_provider()
        print(f"✅ LLM provider: {type(llm_provider).__name__}")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        return {"success_rate": 0, "error": str(e)}
    
    print()
    
    # Show available tools
    print("📋 Available tools:")
    for tool_name, tool_info in AVAILABLE_TOOLS.items():
        print(f"   - {tool_name}: {tool_info['description']}")
    print()
    
    # Test queries that should trigger tools
    test_queries = [
        {
            "query": "What time is it right now?",
            "expected_tools": ["get_time"],
            "description": "Time query should trigger get_time tool"
        },
        {
            "query": "What system am I running on?",
            "expected_tools": ["system_info"],
            "description": "System query should trigger system_info tool"
        },
        {
            "query": "Calculate 15 * 8 + 23 for me",
            "expected_tools": ["math"],
            "description": "Math query should trigger math tool"
        },
    ]
    
    results = []
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"📝 Test {i}: {test_case['description']}")
        print(f"   Query: \"{test_case['query']}\"")
        print()
        
        try:
            # Create messages with tool instructions
            tools_desc = "\n".join([f"- {name}: {info['description']}" for name, info in AVAILABLE_TOOLS.items()])
            
            system_message = f"""You are a helpful assistant. You have access to these tools:
{tools_desc}

When you need information that requires a tool, mention the tool name or describe what you're doing.
For calculations, you can use the math tool.
For time information, use get_time.
For system information, use system_info.

Please be direct and mention when you would use tools to get the information."""
            
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=test_case['query'])
            ]
            
            # Get LLM response
            print(f"🤖 Sending to LLM...")
            start_time = time.time()
            response = await llm_provider.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            execution_time = time.time() - start_time
            
            print(f"📝 LLM Response: {response_text[:300]}...")
            print(f"⏱️  LLM Response time: {execution_time:.2f}s")
            print()
            
            # Process tool calls
            tool_results = process_tool_calls(response_text)
            
            print(f"🔧 Tool results: {tool_results}")
            
            # Check if expected tools were executed
            expected_executed = any(tool in tool_results for tool in test_case['expected_tools'])
            
            results.append({
                "query": test_case['query'],
                "expected_tools": test_case['expected_tools'],
                "tools_executed": list(tool_results.keys()),
                "expected_executed": expected_executed,
                "llm_response": response_text,
                "tool_results": tool_results,
                "execution_time": execution_time,
                "success": expected_executed
            })
            
            print(f"✅ Expected tool executed: {expected_executed}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append({
                "query": test_case['query'],
                "expected_tools": test_case['expected_tools'],
                "success": False,
                "error": str(e)
            })
        
        print("   " + "-" * 60)
        print()
    
    # Results summary
    print("=" * 70)
    print("📊 TEST RESULTS")
    print("=" * 70)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    print(f"🎯 Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    print()
    
    for i, result in enumerate(results, 1):
        status = "✅" if result.get('success', False) else "❌"
        print(f"  {status} Test {i}: {result['query'][:50]}...")
        if 'tools_executed' in result:
            print(f"      Tools executed: {result['tools_executed']}")
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    print()
    
    # Analysis
    if successful_tests == 0:
        print("🚨 NO TOOLS EXECUTED!")
        print("   This confirms the tool calling integration issue.")
        print("   The LLM likely generates responses but doesn't trigger tool execution.")
        print()
        print("🔍 Diagnosis:")
        print("   • LLM provider responds correctly")
        print("   • Tool parsing/execution logic may be incomplete")
        print("   • Agent's execute_task method needs tool execution integration")
    elif successful_tests < total_tests:
        print("⚠️  PARTIAL SUCCESS")
        print("   Some tools executed, some didn't.")
    else:
        print("✅ ALL TOOLS EXECUTED SUCCESSFULLY!")
        print("   The basic tool calling mechanism works.")
    
    return {
        "success_rate": successful_tests / total_tests,
        "results": results,
        "total_tests": total_tests,
        "successful_tests": successful_tests
    }


if __name__ == "__main__":
    result = asyncio.run(test_standalone_tool_calling())
    
    print()
    print("=" * 70)
    if result["success_rate"] == 0:
        print("🚨 CRITICAL: Tool calling system broken")
        print("   → Need to implement tool execution in Agent.execute_task()")
    elif result["success_rate"] < 1.0:
        print("⚠️  PARTIAL: Tool calling partially working")
    else:
        print("✅ SUCCESS: Tool calling system functional")
    print("=" * 70)