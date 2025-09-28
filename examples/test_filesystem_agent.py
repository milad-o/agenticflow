#!/usr/bin/env python3
"""Test FilesystemAgent in isolation."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow, FilesystemAgent

async def test_filesystem_agent():
    """Test FilesystemAgent in isolation."""
    print("🧪 Testing FilesystemAgent in isolation")
    print("=" * 45)
    
    # Create flow with just filesystem agent
    flow = Flow("filesystem_test")
    filesystem_agent = FilesystemAgent("filesystem_agent")
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
    
    # Test 4: Search for files
    print("\n🔍 Test 4: Search for files")
    result4 = await flow.run("Search for all .txt files in examples/artifacts")
    print(f"Result: {result4['messages'][-1].content}")
    
    print("\n✅ FilesystemAgent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_filesystem_agent())
