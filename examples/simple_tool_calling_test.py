#!/usr/bin/env python3
"""
Simple Tool Calling Test for AgenticFlow

This script tests the LLM tool calling integration to reproduce the issue
where tools are mentioned by the LLM but not actually executed.

This is a simplified version that avoids complex memory imports.
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

# Use direct imports to avoid circular dependency issues
from agenticflow.tools.base import tool, ToolRegistry
from agenticflow.config.settings import AgentConfig, LLMConfig
from agenticflow.llm_providers import get_llm_manager
from langchain_core.messages import HumanMessage, SystemMessage


# Register specialized test tools
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


class SimpleTestAgent:
    """Simplified test agent to isolate tool calling functionality"""
    
    def __init__(self, tools=None):
        self.tools = {}
        self.llm_provider = None
        if tools:
            for tool in tools:
                self.tools[tool.name] = tool
        
    async def initialize(self):
        """Initialize LLM provider"""
        try:
            # Try to get LLM manager
            llm_manager = get_llm_manager()
            self.llm_provider = llm_manager.get_provider()
            print(f"✅ LLM provider initialized: {type(self.llm_provider).__name__}")
        except Exception as e:
            print(f"❌ Failed to initialize LLM provider: {e}")
            raise
            
    async def execute_task(self, task: str) -> str:
        """Execute a task using the LLM"""
        if not self.llm_provider:
            raise Exception("LLM provider not initialized")
            
        # Create system message with tool information
        system_content = f"""You are a helpful assistant with access to the following tools:
{self._get_tool_descriptions()}

When you need to use a tool, format your request as JSON like this:
{{"tool": "tool_name", "parameters": {{"param1": "value1"}}}}

Use tools when appropriate to answer user questions."""
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=task)
        ]
        
        try:
            # Get LLM response
            print(f"🤖 Sending task to LLM: {task}")
            response = await self.llm_provider.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            print(f"📝 LLM Response: {response_text[:200]}...")
            
            # Check if response contains tool calls and execute them
            tool_results = await self._process_tool_calls(response_text)
            
            if tool_results:
                print(f"✅ Tool calls executed: {len(tool_results)}")
                # Add tool results to response
                response_text += f"\n\nTool Results: {tool_results}"
            else:
                print("❌ No tool calls detected/executed")
            
            return response_text
            
        except Exception as e:
            print(f"❌ Error executing task: {e}")
            raise
    
    def _get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions"""
        if not self.tools:
            return "No tools available."
        
        descriptions = []
        for tool_name, tool in self.tools.items():
            descriptions.append(f"- {tool_name}: {tool.description}")
        
        return "\n".join(descriptions)
    
    async def _process_tool_calls(self, response_text: str) -> dict:
        """Look for and execute tool calls in the response"""
        import json
        import re
        
        tool_results = {}
        
        # Look for JSON tool calls in the response
        json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
        matches = re.findall(json_pattern, response_text)
        
        for match in matches:
            try:
                tool_call = json.loads(match)
                if "tool" in tool_call:
                    tool_name = tool_call["tool"]
                    parameters = tool_call.get("parameters", {})
                    
                    if tool_name in self.tools:
                        print(f"🔧 Executing tool: {tool_name} with params: {parameters}")
                        tool = self.tools[tool_name]
                        
                        # Execute tool
                        if parameters:
                            result = tool.func(**parameters)
                        else:
                            result = tool.func()
                        
                        tool_results[tool_name] = result
                        print(f"✅ Tool {tool_name} executed successfully")
                    else:
                        print(f"❌ Tool {tool_name} not found in registry")
                        
            except json.JSONDecodeError:
                # Try alternative patterns
                pass
        
        # Also look for function call style patterns
        func_pattern = r'(\w+)\(([^)]*)\)'
        func_matches = re.findall(func_pattern, response_text.lower())
        
        for func_name, params in func_matches:
            if func_name in [t.lower() for t in self.tools.keys()]:
                # Find the actual tool name
                actual_tool_name = None
                for tool_name in self.tools.keys():
                    if tool_name.lower() == func_name:
                        actual_tool_name = tool_name
                        break
                
                if actual_tool_name:
                    print(f"🔧 Found function-style call: {func_name}")
                    tool = self.tools[actual_tool_name]
                    try:
                        result = tool.func()
                        tool_results[actual_tool_name] = result
                        print(f"✅ Tool {actual_tool_name} executed via function pattern")
                    except Exception as e:
                        print(f"❌ Error executing {actual_tool_name}: {e}")
        
        return tool_results


async def test_simple_tool_calling():
    """Test tool calling with simplified agent"""
    
    print("=" * 70)
    print("🔧 SIMPLE TOOL CALLING TEST")
    print("=" * 70)
    print()
    
    # Create test tools
    tools = [get_time_tool, system_info_tool, precise_math_tool]
    
    print("📋 Test tools:")
    for tool in tools:
        print(f"   ✅ {tool.name}: {tool.description}")
    
    print()
    
    # Create simple test agent
    agent = SimpleTestAgent(tools=tools)
    
    try:
        await agent.initialize()
        print(f"🤖 Agent initialized with {len(agent.tools)} tools")
        print()
        
        # Test scenarios
        test_queries = [
            "What time is it right now?",
            "Calculate 15 * 8 + 23",
            "What system am I running on?",
        ]
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"📝 Test {i}: {query}")
            print("   " + "-" * 40)
            
            try:
                start_time = time.time()
                response = await agent.execute_task(query)
                execution_time = time.time() - start_time
                
                print(f"   ⏱️  Execution time: {execution_time:.2f}s")
                
                results.append({
                    "query": query,
                    "success": True,
                    "response": response,
                    "execution_time": execution_time
                })
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "execution_time": 0
                })
            
            print()
        
        # Summary
        print("=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        successful_tests = sum(1 for r in results if r['success'])
        print(f"🎯 Success Rate: {successful_tests}/{len(results)} ({successful_tests/len(results)*100:.1f}%)")
        print()
        
        for i, result in enumerate(results, 1):
            status = "✅" if result['success'] else "❌"
            print(f"  {status} Test {i}: {result['query'][:50]}...")
            if not result['success']:
                print(f"      Error: {result['error']}")
        
        print()
        
        if successful_tests == 0:
            print("🚨 CRITICAL: No tests passed - likely LLM provider issue")
        elif successful_tests < len(results):
            print("⚠️  PARTIAL: Some tests failed - investigate specific failures")
        else:
            print("✅ SUCCESS: All tests passed!")
        
        return {
            "success_rate": successful_tests / len(results),
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return {
            "success_rate": 0,
            "error": str(e)
        }


if __name__ == "__main__":
    result = asyncio.run(test_simple_tool_calling())
    
    print()
    print("=" * 70)  
    if result["success_rate"] == 0:
        print("🚨 TOOL CALLING BROKEN - NEEDS INVESTIGATION")
    elif result["success_rate"] < 1.0:
        print("⚠️  TOOL CALLING PARTIALLY WORKING")
    else:
        print("✅ TOOL CALLING WORKING CORRECTLY")
    print("=" * 70)