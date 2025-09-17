#!/usr/bin/env python3
"""
Quick Tool Test - Bypasses memory system completely

This script tests only the tool calling mechanism without any memory system.
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

# Import only what we need for tool testing
from agenticflow.tools.base import tool
from agenticflow.tools.base_tool import ToolRegistry
from agenticflow.llm_providers import get_llm_manager
from langchain_core.messages import HumanMessage, SystemMessage


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


def detect_tool_calls(response_text: str, available_tools: list) -> list:
    """Simplified version of the enhanced implicit tool detection"""
    import re
    
    tool_calls = []
    response_lower = response_text.lower()
    
    # Generic tool detection - look for explicit tool mentions
    for tool_name in available_tools:
        tool_mention_patterns = [
            rf'(?:will\\s+use\\s+(?:the\\s+)?`?{re.escape(tool_name)}`?(?:\\s+tool)?)',
            rf'(?:using\\s+(?:the\\s+)?`?{re.escape(tool_name)}`?(?:\\s+tool)?)', 
            rf'(?:use\\s+(?:the\\s+)?`?{re.escape(tool_name)}`?(?:\\s+tool)?)',
        ]
        
        for pattern in tool_mention_patterns:
            if re.search(pattern, response_lower):
                tool_calls.append((tool_name, {}))
                break
    
    # Time-related requests
    if any('time' in tool for tool in available_tools):
        time_patterns = [
            r'what\\s+time\\s+is\\s+it',
            r'current\\s+time',
            r'time\\s+right\\s+now',
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, response_lower):
                for tool_name in available_tools:
                    if 'time' in tool_name:
                        tool_calls.append((tool_name, {}))
                        break
                break
    
    # System information requests
    if any('system' in tool for tool in available_tools):
        system_patterns = [
            r'what\\s+system\\s+am\\s+i\\s+(?:running\\s+)?on',
            r'system\\s+information',
        ]
        
        for pattern in system_patterns:
            if re.search(pattern, response_lower):
                for tool_name in available_tools:
                    if 'system' in tool_name:
                        tool_calls.append((tool_name, {}))
                        break
                break
    
    # Math/calculation requests
    if any('math' in tool for tool in available_tools):
        math_patterns = [
            r'calculate\\s+([0-9+\\-*/\\s().]+)',
            r'([0-9]+(?:\\.[0-9]+)?\\s*[+\\-*/]\\s*[0-9]+(?:\\.[0-9]+)?(?:\\s*[+\\-*/]\\s*[0-9]+(?:\\.[0-9]+)?)*)',
        ]
        
        for pattern in math_patterns:
            matches = re.findall(pattern, response_lower)
            for match in matches:
                if match.strip():
                    expression = match.strip()
                    for tool_name in available_tools:
                        if 'math' in tool_name:
                            tool_calls.append((tool_name, {'expression': expression}))
                            break
                    break
    
    # Remove duplicates
    seen = set()
    unique_calls = []
    for tool_name, params in tool_calls:
        key = (tool_name, str(params))
        if key not in seen:
            seen.add(key)
            unique_calls.append((tool_name, params))
    
    return unique_calls


async def test_enhanced_tool_detection():
    """Test the enhanced tool detection logic"""
    
    print("=" * 70)
    print("🔧 QUICK TOOL CALLING TEST")
    print("=" * 70)
    print()
    
    # Create tool registry
    registry = ToolRegistry()
    tools = [get_time_tool, system_info_tool, precise_math_tool]
    
    print("📋 Registering tools:")
    for tool_func in tools:
        registry.register_tool(tool_func)
        print(f"   ✅ {tool_func.name}: {tool_func.description}")
    
    print()
    
    # Initialize LLM
    try:
        print("🤖 Initializing LLM...")
        llm_manager = get_llm_manager()
        llm_provider = llm_manager.get_provider()
        print(f"✅ LLM provider ready: {type(llm_provider).__name__}")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        return {"success_rate": 0, "error": str(e)}
    
    print()
    
    # Test cases
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
        }
    ]
    
    results = []
    available_tools = registry.list_tools()
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"📝 Test {i}: {test_case['description']}")
        print(f"   Query: \"{test_case['query']}\"")
        print()
        
        try:
            # Create system message with tool info
            tools_desc = "\\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
            system_message = f"""You are a helpful assistant with access to these tools:
{tools_desc}

When you need information that requires a tool, mention the tool name or describe what you're doing.
For time information, use get_time.
For system information, use system_info.  
For calculations, use precise_math."""
            
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=test_case['query'])
            ]
            
            # Get LLM response
            print("🤖 Getting LLM response...")
            start_time = time.time()
            response = await llm_provider.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            response_time = time.time() - start_time
            
            print(f"📝 LLM Response: {response_text[:200]}...")
            print(f"⏱️  LLM Response time: {response_time:.2f}s")
            print()
            
            # Apply enhanced tool detection
            print("🔍 Applying enhanced tool detection...")
            tool_calls = detect_tool_calls(response_text, available_tools)
            
            print(f"🔧 Detected tool calls: {tool_calls}")
            
            # Execute detected tools
            tool_results = []
            for tool_name, params in tool_calls:
                try:
                    result = await registry.execute_tool(tool_name, params)
                    tool_results.append({
                        "tool": tool_name,
                        "success": result.success,
                        "result": result.result if result.success else None,
                        "error": result.error if not result.success else None
                    })
                except Exception as e:
                    tool_results.append({
                        "tool": tool_name,
                        "success": False,
                        "error": str(e)
                    })
            
            # Check success
            expected_executed = any(
                tr.get('tool') == test_case['expected_tool'] and tr.get('success', False)
                for tr in tool_results
            )
            
            results.append({
                "query": test_case['query'],
                "expected_tool": test_case['expected_tool'],
                "tool_calls": tool_calls,
                "tool_results": tool_results,
                "expected_executed": expected_executed,
                "llm_response": response_text,
                "success": expected_executed
            })
            
            if expected_executed:
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
    
    # Summary
    print("=" * 70)
    print("📊 ENHANCED TOOL DETECTION RESULTS")
    print("=" * 70)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    print(f"🎯 Tool Detection Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    print()
    
    for i, result in enumerate(results, 1):
        status = "✅" if result.get('success', False) else "❌"
        print(f"  {status} Test {i}: {result['expected_tool']}")
        if 'tool_calls' in result:
            print(f"      Detected: {[tc[0] for tc in result['tool_calls']]}")
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    print()
    
    if successful_tests == total_tests:
        print("🎉 ENHANCED TOOL DETECTION WORKING!")
        print("   The improved implicit tool detection successfully identifies and executes tools.")
    elif successful_tests > 0:
        print("⚠️  PARTIAL SUCCESS")
        print("   Some tool detection patterns are working.")
    else:
        print("🚨 TOOL DETECTION NEEDS MORE WORK")
        print("   The enhanced patterns may need refinement.")
    
    return {
        "success_rate": successful_tests / total_tests,
        "results": results
    }


if __name__ == "__main__":
    result = asyncio.run(test_enhanced_tool_detection())
    
    print()
    print("=" * 70)
    if result["success_rate"] == 1.0:
        print("✅ TOOL CALLING ENHANCEMENT SUCCESSFUL!")
        print("   → The enhanced implicit tool detection is working")
        print("   → Ready to integrate into full Agent system")
    elif result["success_rate"] > 0:
        print("⚠️  PARTIAL SUCCESS - CONTINUE REFINEMENT")
    else:
        print("🚨 ENHANCEMENT NEEDS MORE WORK")
    print("=" * 70)