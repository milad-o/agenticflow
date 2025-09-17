#!/usr/bin/env python3
"""
Direct LLM Tool Test

This script tests LLM tool calling by directly using LLM providers
without importing any AgenticFlow components.
"""

import asyncio
import os
import time
from datetime import datetime
import platform

# Test if we can use local LLM (Ollama)
USE_OLLAMA = True

def get_time_tool() -> str:
    """Get current time"""
    print(f"🔧 TOOL EXECUTED: get_time_tool()")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def system_info_tool() -> str:
    """Get system information"""
    print(f"🔧 TOOL EXECUTED: system_info_tool()")
    return f"Platform: {platform.system()} {platform.release()}, Python: {platform.python_version()}"

def math_tool(expression: str) -> str:
    """Calculate mathematical expression"""
    print(f"🔧 TOOL EXECUTED: math_tool({expression})")
    try:
        # Simple safe evaluation
        allowed_chars = "0123456789+-*/.() "
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return f"Result: {expression} = {result}"
        else:
            return "Error: Invalid characters in expression"
    except Exception as e:
        return f"Error calculating: {str(e)}"

TOOLS = {
    "get_time": get_time_tool,
    "system_info": system_info_tool,  
    "math": math_tool
}

def execute_tool_if_found(response_text: str) -> dict:
    """Look for tool mentions in response and execute them"""
    results = {}
    
    # Simple keyword-based detection
    response_lower = response_text.lower()
    
    if "time" in response_lower and "current" in response_lower:
        print("🔧 Detected time request, executing get_time")
        results["get_time"] = get_time_tool()
    
    if "system" in response_lower and ("information" in response_lower or "platform" in response_lower):
        print("🔧 Detected system info request, executing system_info")
        results["system_info"] = system_info_tool()
    
    if "calculate" in response_lower or "math" in response_lower:
        # Try to extract mathematical expression
        import re
        math_patterns = [
            r'(\d+\s*[+\-*/]\s*\d+(?:\s*[+\-*/]\s*\d+)*)',
            r'calculate[:\s]+([0-9+\-*/.() ]+)',
            r'(\d+\s*\*\s*\d+\s*\+\s*\d+)'
        ]
        
        for pattern in math_patterns:
            matches = re.findall(pattern, response_text)
            if matches:
                expression = matches[0].strip()
                print(f"🔧 Detected math expression: {expression}")
                results["math"] = math_tool(expression)
                break
    
    return results

async def test_direct_llm():
    """Test LLM directly without AgenticFlow"""
    
    print("=" * 70)
    print("🤖 DIRECT LLM TOOL CALLING TEST")
    print("=" * 70)
    print()
    
    # Initialize LLM provider directly
    if USE_OLLAMA:
        try:
            from langchain_community.llms import Ollama
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            
            print("🔗 Connecting to Ollama...")
            llm = Ollama(model="qwen2.5:7b", base_url="http://localhost:11434")
            print("✅ Ollama connection established")
        except ImportError:
            print("❌ Ollama not available, install with: pip install langchain-community")
            return {"success_rate": 0, "error": "Ollama not available"}
        except Exception as e:
            print(f"❌ Failed to connect to Ollama: {e}")
            print("   Make sure Ollama is running: ollama serve")
            return {"success_rate": 0, "error": str(e)}
    else:
        print("❌ No LLM provider configured")
        return {"success_rate": 0, "error": "No LLM provider"}
    
    print()
    
    # Test queries
    test_queries = [
        {
            "query": "What is the current time right now?",
            "expected_tool": "get_time",
            "description": "Time query should mention or trigger time tool"
        },
        {
            "query": "What system information can you tell me about this machine?",
            "expected_tool": "system_info", 
            "description": "System query should trigger system info tool"
        },
        {
            "query": "Can you calculate 15 * 8 + 23 for me?",
            "expected_tool": "math",
            "description": "Math query should trigger calculation tool"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"📝 Test {i}: {test_case['description']}")
        print(f"   Query: \"{test_case['query']}\"")
        print()
        
        try:
            # Create prompt with tool awareness
            system_prompt = """You are a helpful assistant with access to tools:
- get_time: Gets the current date and time
- system_info: Gets system information like platform and Python version  
- math: Performs mathematical calculations

When answering questions, mention if you would use these tools and what information they would provide."""
            
            full_prompt = f"{system_prompt}\n\nUser: {test_case['query']}\nAssistant:"
            
            # Get LLM response
            print("🤖 Sending to LLM...")
            start_time = time.time()
            response = llm.invoke(full_prompt)
            execution_time = time.time() - start_time
            
            print(f"📝 LLM Response: {response[:300]}...")
            print(f"⏱️  Response time: {execution_time:.2f}s")
            print()
            
            # Check for tool execution
            tool_results = execute_tool_if_found(response)
            
            expected_executed = test_case['expected_tool'] in tool_results
            
            results.append({
                "query": test_case['query'],
                "expected_tool": test_case['expected_tool'],
                "tools_executed": list(tool_results.keys()),
                "expected_executed": expected_executed,
                "llm_response": response,
                "tool_results": tool_results,
                "execution_time": execution_time,
                "success": expected_executed
            })
            
            if tool_results:
                print(f"✅ Tools executed: {list(tool_results.keys())}")
                for tool_name, result in tool_results.items():
                    print(f"   {tool_name}: {result}")
            else:
                print("❌ No tools executed")
            
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
    
    # Results summary
    print("=" * 70)
    print("📊 RESULTS SUMMARY")
    print("=" * 70)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    print(f"🎯 Tool Execution Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    print()
    
    for i, result in enumerate(results, 1):
        status = "✅" if result.get('success', False) else "❌"
        print(f"  {status} Test {i}: Expected {result['expected_tool']}")
        if 'tools_executed' in result:
            executed = result['tools_executed']
            print(f"      Executed: {executed if executed else 'None'}")
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    print()
    
    if successful_tests == 0:
        print("🚨 NO AUTOMATIC TOOL EXECUTION!")
        print("   LLM responses don't automatically trigger tools.")
        print("   This is expected - the AgenticFlow Agent should handle tool execution.")
        print()
        print("💡 Key Insight:")
        print("   The LLM generates text responses but doesn't execute tools.")
        print("   AgenticFlow's Agent.execute_task() needs to:")
        print("   1. Parse LLM responses for tool calls")
        print("   2. Execute matching tools")  
        print("   3. Add tool results to the response")
    elif successful_tests < total_tests:
        print("⚠️  PARTIAL TOOL EXECUTION")
    else:
        print("✅ FULL TOOL EXECUTION")
    
    return {
        "success_rate": successful_tests / total_tests,
        "results": results
    }

if __name__ == "__main__":
    result = asyncio.run(test_direct_llm())
    
    print()
    print("=" * 70)
    if result["success_rate"] == 0:
        print("📋 FINDINGS: LLM tool calling integration missing")
        print("   → This confirms the issue described in the conversation")
        print("   → Agent.execute_task() needs tool execution logic")
    else:
        print("🎉 FINDINGS: Basic tool execution working")
    print("=" * 70)