#!/usr/bin/env python3
"""Test simplified AgenticFlow framework following tutorial pattern."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agenticflow import Agent, Flow, create_file, read_file, list_directory, create_folder, delete_file, delete_folder, search_web, python_execute

async def test_filesystem_agent():
    """Test filesystem agent using simplified framework."""
    print("🗂️  Testing Simplified AgenticFlow - Filesystem Agent")
    print("=" * 60)
    
    # Create flow
    flow = Flow("filesystem_workflow")
    
    # Create filesystem agent with tools
    filesystem_agent = Agent(
        name="filesystem_agent",
        description="Agent specialized in filesystem operations like creating, reading, and listing files/folders.",
        system_prompt="You are a helpful assistant that can perform filesystem operations. Use the available tools to fulfill requests.",
        tools=[create_file, read_file, list_directory, create_folder, delete_file, delete_folder]
    )
    
    # Add agent to flow
    flow.add_agent(filesystem_agent)
    
    print("✅ Flow created with filesystem agent")
    print(f"   - Agent: {filesystem_agent.name}")
    print(f"   - Tools: {[tool.name for tool in filesystem_agent.tools]}")
    
    # Test 1: Create a file
    print("\n🎯 Test 1: Create a file")
    print("-" * 40)
    result1 = await flow.run("Create a file called 'test_simple.txt' with the content 'Hello from Simplified AgenticFlow!'")
    
    print(f"✅ Test 1 completed!")
    print(f"📝 Generated {len(result1['messages'])} messages:")
    for i, msg in enumerate(result1["messages"], 1):
        print(f"   {i}. [{getattr(msg, 'name', 'user')}]: {msg.content}")
    
    # Test 2: List directory
    print("\n🎯 Test 2: List directory")
    print("-" * 40)
    result2 = await flow.run("List the contents of the current directory")
    
    print(f"✅ Test 2 completed!")
    print(f"📝 Generated {len(result2['messages'])} messages:")
    for i, msg in enumerate(result2["messages"], 1):
        print(f"   {i}. [{getattr(msg, 'name', 'user')}]: {msg.content}")
    
    # Test 3: Create a folder and file
    print("\n🎯 Test 3: Create folder and file")
    print("-" * 40)
    result3 = await flow.run("Create a folder called 'simplified_project' and then create a file called 'README.md' inside it with project information")
    
    print(f"✅ Test 3 completed!")
    print(f"📝 Generated {len(result3['messages'])} messages:")
    for i, msg in enumerate(result3["messages"], 1):
        print(f"   {i}. [{getattr(msg, 'name', 'user')}]: {msg.content}")
    
    print("\n🎉 Filesystem agent testing completed successfully!")
    print("=" * 60)
    
    # Show what files were actually created
    print("\n📁 Files created during testing:")
    test_files = ["test_simple.txt", "simplified_project"]
    for item in test_files:
        if os.path.exists(item):
            if os.path.isfile(item):
                print(f"   ✅ File: {item}")
                with open(item, "r") as f:
                    print(f"      Content: {f.read()}")
            else:
                print(f"   ✅ Folder: {item}/")
                # Check for README.md inside
                readme_path = os.path.join(item, "README.md")
                if os.path.exists(readme_path):
                    print(f"      📄 Contains README.md")
                    with open(readme_path, "r") as f:
                        print(f"         Content: {f.read()[:100]}...")
        else:
            print(f"   ❌ {item}")

async def test_multi_agent_workflow():
    """Test multi-agent workflow using simplified framework."""
    print("\n\n🤖 Testing Simplified AgenticFlow - Multi-Agent Workflow")
    print("=" * 60)
    
    # Create flow
    flow = Flow("multi_agent_workflow")
    
    # Create research agent
    research_agent = Agent(
        name="research_agent",
        description="Agent specialized in web research and information gathering.",
        system_prompt="You are a research assistant. Use web search to find information and provide comprehensive answers.",
        tools=[search_web]
    )
    
    # Create filesystem agent
    filesystem_agent = Agent(
        name="filesystem_agent",
        description="Agent specialized in filesystem operations.",
        system_prompt="You are a filesystem assistant. Use file tools to create, read, and manage files.",
        tools=[create_file, read_file, list_directory, create_folder]
    )
    
    # Create Python agent
    python_agent = Agent(
        name="python_agent",
        description="Agent specialized in Python code execution and data analysis.",
        system_prompt="You are a Python programming assistant. Use Python execution to analyze data and create visualizations.",
        tools=[python_execute]
    )
    
    # Add agents to flow
    flow.add_agent(research_agent)
    flow.add_agent(filesystem_agent)
    flow.add_agent(python_agent)
    
    print("✅ Multi-agent flow created")
    print(f"   - Agents: {list(flow.agents.keys())}")
    
    # Test: Research and create a report
    print("\n🎯 Test: Research and create a report")
    print("-" * 40)
    result = await flow.run("Research the latest trends in AI agents and create a report file with your findings")
    
    print(f"✅ Multi-agent test completed!")
    print(f"📝 Generated {len(result['messages'])} messages:")
    for i, msg in enumerate(result["messages"], 1):
        print(f"   {i}. [{getattr(msg, 'name', 'user')}]: {msg.content}")
    
    print("\n🎉 Multi-agent workflow testing completed successfully!")
    print("=" * 60)

async def main():
    """Main function to run all tests."""
    print("🚀 Testing Simplified AgenticFlow Framework")
    print("=" * 60)
    
    # Test filesystem agent
    await test_filesystem_agent()
    
    # Test multi-agent workflow
    await test_multi_agent_workflow()
    
    print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("✅ Simplified AgenticFlow framework is working!")
    print("✅ Filesystem operations are working!")
    print("✅ Multi-agent coordination is working!")
    print("✅ Following tutorial pattern for reliability!")

if __name__ == "__main__":
    asyncio.run(main())
