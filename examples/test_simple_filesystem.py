#!/usr/bin/env python3
"""Test simple filesystem agent with standalone tools."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow, Agent
from agenticflow.tools import create_file, read_file, list_directory

async def test_simple_filesystem():
    """Test simple filesystem agent with standalone tools."""
    print("🧪 Testing Simple Filesystem Agent")
    print("=" * 35)
    
    # Create flow with filesystem tools
    flow = Flow("simple_filesystem_test")
    filesystem_agent = Agent(
        "filesystem_agent", 
        tools=[create_file, read_file, list_directory], 
        description="Filesystem operations specialist"
    )
    flow.add_agent(filesystem_agent)
    
    print(f"✅ Created FilesystemAgent with {len(filesystem_agent.tools)} tools")
    
    # Test 1: Create a file
    print("\n📝 Test 1: Create a file")
    result1 = await flow.run("Create a file called 'test.txt' with content 'Hello World'")
    print(f"Result: {result1['messages'][-1].content}")
    
    # Test 2: List directory
    print("\n📂 Test 2: List directory contents")
    result2 = await flow.run("List the contents of the examples/artifacts directory")
    print(f"Result: {result2['messages'][-1].content}")
    
    # Test 3: Read the file
    print("\n📖 Test 3: Read the created file")
    result3 = await flow.run("Read the file 'test.txt' from examples/artifacts")
    print(f"Result: {result3['messages'][-1].content}")
    
    print("\n✅ Simple FilesystemAgent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_simple_filesystem())
