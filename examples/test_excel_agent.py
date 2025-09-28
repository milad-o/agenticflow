#!/usr/bin/env python3
"""Test ExcelAgent in isolation."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow, ExcelAgent

async def test_excel_agent():
    """Test ExcelAgent in isolation."""
    print("🧪 Testing ExcelAgent in isolation")
    print("=" * 40)
    
    # Create flow with just excel agent
    flow = Flow("excel_test")
    excel_agent = ExcelAgent("excel_agent")
    flow.add_agent(excel_agent)
    
    print(f"✅ Created ExcelAgent with {len(excel_agent.tools)} tools")
    
    # Test 1: Create Excel file
    print("\n📊 Test 1: Create Excel file")
    result1 = await flow.run("Create an Excel file called 'test_data.xlsx' with a sheet called 'Sales'")
    print(f"Result: {result1['messages'][-1].content}")
    
    # Test 2: Write data to Excel
    print("\n📝 Test 2: Write data to Excel")
    data = '[{"Name": "John", "Age": 30, "City": "New York"}, {"Name": "Jane", "Age": 25, "City": "Boston"}]'
    result2 = await flow.run(f"Write this data to the Excel file: {data}")
    print(f"Result: {result2['messages'][-1].content}")
    
    # Test 3: Read Excel file
    print("\n📖 Test 3: Read Excel file")
    result3 = await flow.run("Read the Excel file 'test_data.xlsx' and show its contents")
    print(f"Result: {result3['messages'][-1].content}")
    
    # Test 4: Analyze Excel data
    print("\n📈 Test 4: Analyze Excel data")
    result4 = await flow.run("Analyze the Excel file 'test_data.xlsx' and provide statistics")
    print(f"Result: {result4['messages'][-1].content}")
    
    print("\n✅ ExcelAgent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_excel_agent())
