#!/usr/bin/env python3
"""Test a tool directly."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow.agents.filesystem_agent import FilesystemAgent

async def test_tool_directly():
    """Test a tool directly."""
    print("🧪 Testing FilesystemAgent tool directly")
    print("=" * 40)
    
    # Create filesystem agent
    agent = FilesystemAgent("test_agent")
    
    print(f"✅ Agent created with {len(agent.tools)} tools")
    print(f"   Tool names: {[tool.name for tool in agent.tools]}")
    
    # Test a tool directly
    print("\n🔧 Testing _create_file tool directly...")
    try:
        result = agent._create_file.invoke({"content": "Hello World", "filename": "test_direct.txt"})
        print(f"✅ Tool executed: {result}")
    except Exception as e:
        print(f"❌ Tool failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_directly())
