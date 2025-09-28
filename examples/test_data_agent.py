#!/usr/bin/env python3
"""Test DataAgent in isolation."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow, DataAgent

async def test_data_agent():
    """Test DataAgent in isolation."""
    print("🧪 Testing DataAgent in isolation")
    print("=" * 40)
    
    # Create flow with just data agent
    flow = Flow("data_test")
    data_agent = DataAgent("data_agent")
    flow.add_agent(data_agent)
    
    print(f"✅ Created DataAgent with {len(data_agent.tools)} tools")
    
    # Test 1: Create JSON file
    print("\n📄 Test 1: Create JSON file")
    json_data = '{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}], "total": 2}'
    result1 = await flow.run(f"Create a JSON file called 'users.json' with this data: {json_data}")
    print(f"Result: {result1['messages'][-1].content}")
    
    # Test 2: Read JSON file
    print("\n📖 Test 2: Read JSON file")
    result2 = await flow.run("Read the JSON file 'users.json' and show its contents")
    print(f"Result: {result2['messages'][-1].content}")
    
    # Test 3: Convert JSON to CSV
    print("\n🔄 Test 3: Convert JSON to CSV")
    result3 = await flow.run("Convert the JSON file 'users.json' to CSV format and save as 'users.csv'")
    print(f"Result: {result3['messages'][-1].content}")
    
    # Test 4: Validate data
    print("\n✅ Test 4: Validate data")
    result4 = await flow.run("Validate the JSON file 'users.json' for any issues")
    print(f"Result: {result4['messages'][-1].content}")
    
    print("\n✅ DataAgent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_data_agent())
