#!/usr/bin/env python3
"""Test PythonAgent in isolation."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow, PythonAgent

async def test_python_agent():
    """Test PythonAgent in isolation."""
    print("🧪 Testing PythonAgent in isolation")
    print("=" * 40)
    
    # Create flow with just python agent
    flow = Flow("python_test")
    python_agent = PythonAgent("python_agent")
    flow.add_agent(python_agent)
    
    print(f"✅ Created PythonAgent with {len(python_agent.tools)} tools")
    
    # Test 1: Execute simple Python code
    print("\n🐍 Test 1: Execute simple Python code")
    result1 = await flow.run("Execute Python code: print('Hello from Python!')")
    print(f"Result: {result1['messages'][-1].content}")
    
    # Test 2: Validate Python code
    print("\n✅ Test 2: Validate Python code")
    result2 = await flow.run("Validate this Python code: def hello(): return 'world'")
    print(f"Result: {result2['messages'][-1].content}")
    
    # Test 3: Analyze Python code
    print("\n📊 Test 3: Analyze Python code")
    code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

print(calculate_fibonacci(10))
"""
    result3 = await flow.run(f"Analyze this Python code: {code}")
    print(f"Result: {result3['messages'][-1].content}")
    
    # Test 4: Create a Python script
    print("\n📝 Test 4: Create a Python script")
    result4 = await flow.run("Create a Python script called 'math_utils.py' with a function to calculate factorial")
    print(f"Result: {result4['messages'][-1].content}")
    
    print("\n✅ PythonAgent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_python_agent())
