#!/usr/bin/env python3
"""Test specialized agents with real comprehensive tools."""

import asyncio
import os
import json
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow, Agent
from agenticflow.tools import create_file, read_file, list_directory, search_web
from langchain_core.tools import tool

async def test_specialized_agents_real():
    """Test specialized agents with real comprehensive tools."""
    print("🧪 Testing Specialized Agents with Real Tools")
    print("=" * 50)
    
    # Test 1: Comprehensive Filesystem Agent
    print("\n📁 Test 1: Comprehensive Filesystem Agent")
    flow1 = Flow("filesystem_comprehensive")
    
    # Create comprehensive filesystem tools
    @tool
    def create_file_advanced(content: str, filename: str, directory: str = "examples/artifacts") -> str:
        """Create a file with advanced features."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ Created file '{filepath}' with {len(content)} characters"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @tool
    def read_file_advanced(filename: str, directory: str = "examples/artifacts") -> str:
        """Read file with metadata."""
        try:
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            size = os.path.getsize(filepath)
            return f"📖 File: {filename}\n📏 Size: {size} bytes\n📄 Content:\n{content}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @tool
    def list_directory_advanced(directory: str = "examples/artifacts") -> str:
        """List directory with detailed info."""
        try:
            if not os.path.exists(directory):
                return f"⚠️ Directory '{directory}' not found"
            
            items = []
            for item in sorted(os.listdir(directory)):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"📄 {item} ({size} bytes)")
            
            return f"📂 Directory: {directory}\n" + "\n".join(items)
        except Exception as e:
            return f"❌ Error: {e}"
    
    filesystem_agent = Agent(
        "filesystem_agent", 
        tools=[create_file_advanced, read_file_advanced, list_directory_advanced], 
        description="Advanced filesystem operations specialist"
    )
    flow1.add_agent(filesystem_agent)
    
    result1 = await flow1.run("Create a comprehensive test file called 'comprehensive_test.txt' with detailed content about filesystem operations")
    print(f"✅ Filesystem Agent Result: {result1['messages'][-1].content[:150]}...")
    
    # Test 2: Data Processing Agent
    print("\n📊 Test 2: Data Processing Agent")
    flow2 = Flow("data_processing")
    
    @tool
    def create_json_file(data: str, filename: str, directory: str = "examples/artifacts") -> str:
        """Create a JSON file with structured data."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            
            # Parse the data as JSON to validate
            parsed_data = json.loads(data)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
            return f"✅ Created JSON file '{filepath}' with {len(parsed_data)} items"
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON: {e}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @tool
    def read_json_file(filename: str, directory: str = "examples/artifacts") -> str:
        """Read and analyze JSON file."""
        try:
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            info = f"📄 JSON File: {filename}\n"
            info += f"📏 Size: {os.path.getsize(filepath)} bytes\n"
            info += f"🔢 Type: {type(data).__name__}\n"
            
            if isinstance(data, dict):
                info += f"🔑 Keys: {', '.join(data.keys())}\n"
            elif isinstance(data, list):
                info += f"📊 Items: {len(data)}\n"
            
            info += f"📋 Content:\n{json.dumps(data, indent=2)[:500]}...\n"
            return info
        except Exception as e:
            return f"❌ Error: {e}"
    
    data_agent = Agent(
        "data_agent", 
        tools=[create_json_file, read_json_file, create_file_advanced], 
        description="Data processing specialist"
    )
    flow2.add_agent(data_agent)
    
    test_data = '{"users": [{"name": "Alice", "age": 30, "city": "New York"}, {"name": "Bob", "age": 25, "city": "Boston"}], "total": 2}'
    result2 = await flow2.run(f"Create a JSON file called 'test_data.json' with this data: {test_data}")
    print(f"✅ Data Agent Result: {result2['messages'][-1].content[:150]}...")
    
    # Test 3: Multi-step Workflow
    print("\n🔄 Test 3: Multi-step Workflow")
    flow3 = Flow("multi_step")
    
    multi_agent = Agent(
        "multi_agent", 
        tools=[create_file_advanced, read_file_advanced, list_directory_advanced, create_json_file, read_json_file, search_web], 
        description="Multi-purpose agent for complex workflows"
    )
    flow3.add_agent(multi_agent)
    
    result3 = await flow3.run("Search for information about machine learning, create a JSON file with the findings, and then create a summary text file")
    print(f"✅ Multi-step Result: {result3['messages'][-1].content[:150]}...")
    
    # Verify all files were created
    print("\n📋 Verification: Checking created files")
    try:
        files = os.listdir("examples/artifacts")
        print(f"📁 Total files in artifacts: {len(files)}")
        for file in sorted(files):
            if file.endswith(('.txt', '.json')):
                size = os.path.getsize(os.path.join("examples/artifacts", file))
                print(f"   📄 {file} ({size} bytes)")
    except Exception as e:
        print(f"❌ Error listing files: {e}")
    
    print("\n🎉 Specialized agent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_specialized_agents_real())
