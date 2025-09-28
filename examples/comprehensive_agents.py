#!/usr/bin/env python3
"""Comprehensive agents example demonstrating all specialized agents."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agenticflow import Flow, Agent, Team
from agenticflow.agents.filesystem_agent import FilesystemAgent
from agenticflow.agents.python_agent import PythonAgent
from agenticflow.agents.excel_agent import ExcelAgent
from agenticflow.agents.data_agent import DataAgent

async def main():
    """Comprehensive agents example."""
    print("🚀 AgenticFlow - Comprehensive Agents Example")
    print("=" * 55)
    
    # Create flow
    flow = Flow("comprehensive_workflow")
    
    # Create specialized agents
    filesystem_agent = FilesystemAgent("filesystem_agent")
    python_agent = PythonAgent("python_agent")
    excel_agent = ExcelAgent("excel_agent")
    data_agent = DataAgent("data_agent")
    
    # Add agents to flow
    flow.add_agent(filesystem_agent)
    flow.add_agent(python_agent)
    flow.add_agent(excel_agent)
    flow.add_agent(data_agent)
    
    print("✅ Created comprehensive workflow with specialized agents:")
    print(f"   📁 Filesystem Agent: {len(filesystem_agent.tools)} tools")
    print(f"   🐍 Python Agent: {len(python_agent.tools)} tools")
    print(f"   📊 Excel Agent: {len(excel_agent.tools)} tools")
    print(f"   📄 Data Agent: {len(data_agent.tools)} tools")
    
    # Run workflow
    print("\n🎯 Running comprehensive workflow...")
    result = await flow.run("Create a Python script that processes Excel data and saves results as JSON")
    
    print("✅ Workflow completed!")
    print(f"📝 Messages: {len(result['messages'])}")
    
    for i, msg in enumerate(result["messages"], 1):
        sender = getattr(msg, 'name', 'user')
        print(f"   {i}. [{sender}]: {msg.content[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
