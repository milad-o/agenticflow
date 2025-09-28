#!/usr/bin/env python3
"""Test the original specialized agent classes with their comprehensive tools."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow
from agenticflow.agents.filesystem_agent import FilesystemAgent
from agenticflow.agents.python_agent import PythonAgent
from agenticflow.agents.excel_agent import ExcelAgent
from agenticflow.agents.data_agent import DataAgent

async def test_original_specialized_agents():
    """Test the original specialized agent classes."""
    print("🧪 Testing Original Specialized Agent Classes")
    print("=" * 50)
    
    # Test 1: FilesystemAgent
    print("\n📁 Test 1: FilesystemAgent")
    try:
        flow1 = Flow("filesystem_original")
        filesystem_agent = FilesystemAgent("filesystem_agent")
        flow1.add_agent(filesystem_agent)
        
        print(f"✅ Created FilesystemAgent with {len(filesystem_agent.tools)} tools")
        print(f"   Tool names: {[tool.name for tool in filesystem_agent.tools]}")
        
        result1 = await flow1.run("Create a file called 'original_filesystem_test.txt' with content 'Testing original FilesystemAgent'")
        print(f"✅ FilesystemAgent Result: {result1['messages'][-1].content[:100]}...")
        
    except Exception as e:
        print(f"❌ FilesystemAgent failed: {e}")
    
    # Test 2: PythonAgent
    print("\n🐍 Test 2: PythonAgent")
    try:
        flow2 = Flow("python_original")
        python_agent = PythonAgent("python_agent")
        flow2.add_agent(python_agent)
        
        print(f"✅ Created PythonAgent with {len(python_agent.tools)} tools")
        print(f"   Tool names: {[tool.name for tool in python_agent.tools]}")
        
        result2 = await flow2.run("Execute Python code: print('Hello from PythonAgent')")
        print(f"✅ PythonAgent Result: {result2['messages'][-1].content[:100]}...")
        
    except Exception as e:
        print(f"❌ PythonAgent failed: {e}")
    
    # Test 3: ExcelAgent
    print("\n📊 Test 3: ExcelAgent")
    try:
        flow3 = Flow("excel_original")
        excel_agent = ExcelAgent("excel_agent")
        flow3.add_agent(excel_agent)
        
        print(f"✅ Created ExcelAgent with {len(excel_agent.tools)} tools")
        print(f"   Tool names: {[tool.name for tool in excel_agent.tools]}")
        
        result3 = await flow3.run("Create an Excel file called 'original_excel_test.xlsx' with sample data")
        print(f"✅ ExcelAgent Result: {result3['messages'][-1].content[:100]}...")
        
    except Exception as e:
        print(f"❌ ExcelAgent failed: {e}")
    
    # Test 4: DataAgent
    print("\n📄 Test 4: DataAgent")
    try:
        flow4 = Flow("data_original")
        data_agent = DataAgent("data_agent")
        flow4.add_agent(data_agent)
        
        print(f"✅ Created DataAgent with {len(data_agent.tools)} tools")
        print(f"   Tool names: {[tool.name for tool in data_agent.tools]}")
        
        result4 = await flow4.run("Create a JSON file called 'original_data_test.json' with sample data")
        print(f"✅ DataAgent Result: {result4['messages'][-1].content[:100]}...")
        
    except Exception as e:
        print(f"❌ DataAgent failed: {e}")
    
    # Check what files were actually created
    print("\n📋 Verification: Checking created files")
    try:
        files = os.listdir("examples/artifacts")
        print(f"📁 Total files in artifacts: {len(files)}")
        for file in sorted(files):
            if file.endswith(('.txt', '.json', '.xlsx')):
                size = os.path.getsize(os.path.join("examples/artifacts", file))
                print(f"   📄 {file} ({size} bytes)")
    except Exception as e:
        print(f"❌ Error listing files: {e}")
    
    print("\n🎉 Original specialized agent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_original_specialized_agents())
