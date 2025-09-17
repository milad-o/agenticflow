#!/usr/bin/env python3
"""
Test script to verify AgenticFlow installation works correctly.
Run this after installing AgenticFlow to check if all imports work.
"""

import sys
from typing import List, Tuple

def test_imports() -> List[Tuple[str, bool, str]]:
    """Test all critical imports and return results."""
    results = []
    
    # Core imports
    core_imports = [
        ("agenticflow", "from agenticflow import Agent"),
        ("agenticflow.config", "from agenticflow.config.settings import AgentConfig, LLMProviderConfig, MemoryConfig, LLMProvider"),
        ("agenticflow.core.agent", "from agenticflow.core.agent import Agent"),
        ("agenticflow.tools", "from agenticflow.tools import tool"),
        ("agenticflow.memory", "from agenticflow.memory import BufferMemory"),
        ("agenticflow.orchestration", "from agenticflow.orchestration.task_orchestrator import TaskOrchestrator"),
        ("agenticflow.workflows", "from agenticflow.workflows.multi_agent import MultiAgentSystem"),
    ]
    
    # Optional imports (may fail gracefully)
    optional_imports = [
        ("agenticflow.vectorstores", "from agenticflow.vectorstores import VectorStoreFactory"),
        ("agenticflow.embeddings", "from agenticflow.embeddings import create_embedding_provider"),
        ("agenticflow.mcp", "from agenticflow.mcp.config import MCPConfig"),
    ]
    
    print("🧪 Testing AgenticFlow Installation")
    print("=" * 50)
    
    # Test core imports (must succeed)
    print("\n📦 Core Imports (Required):")
    all_core_passed = True
    
    for name, import_str in core_imports:
        try:
            exec(import_str)
            print(f"  ✅ {name}")
            results.append((name, True, "OK"))
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            results.append((name, False, str(e)))
            all_core_passed = False
    
    # Test optional imports (may fail)
    print("\n🔧 Optional Imports (May require extra dependencies):")
    
    for name, import_str in optional_imports:
        try:
            exec(import_str)
            print(f"  ✅ {name}")
            results.append((name, True, "OK"))
        except Exception as e:
            print(f"  ⚠️  {name}: {e}")
            results.append((name, False, str(e)))
    
    return results, all_core_passed

def test_basic_agent_creation():
    """Test basic agent creation."""
    print("\n🤖 Testing Basic Agent Creation:")
    
    try:
        from agenticflow import Agent
        from agenticflow.config.settings import AgentConfig, LLMProviderConfig, LLMProvider
        
        # Create a basic config (without API keys for testing)
        config = AgentConfig(
            name="test_agent",
            instructions="You are a test assistant.",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            )
        )
        
        # Create agent (don't start it to avoid needing API keys)
        agent = Agent(config)
        print(f"  ✅ Agent created successfully: {agent.config.name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Agent creation failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 AgenticFlow Installation Test")
    print("=" * 60)
    print("This script verifies that AgenticFlow is properly installed.")
    print(f"Python version: {sys.version}")
    print("")
    
    # Test imports
    results, core_passed = test_imports()
    
    # Test agent creation if core imports passed
    if core_passed:
        agent_test_passed = test_basic_agent_creation()
    else:
        agent_test_passed = False
        print("\n🤖 Skipping agent creation test due to import failures")
    
    # Summary
    print("\n📊 Test Summary:")
    print("-" * 30)
    
    if core_passed and agent_test_passed:
        print("🎉 SUCCESS: AgenticFlow is properly installed!")
        print("✅ All core components are working")
        print("📚 Check out USAGE.md or examples/ to get started")
        return 0
    else:
        print("❌ ISSUES DETECTED:")
        
        failed = [r for r in results if not r[1]]
        if failed:
            print(f"   • {len(failed)} import(s) failed")
            for name, _, error in failed:
                if any(core_name in name for core_name, _ in [
                    ("agenticflow", ""), ("agenticflow.config", ""), 
                    ("agenticflow.core", ""), ("agenticflow.tools", "")
                ]):
                    print(f"     - {name}: {error}")
        
        if not agent_test_passed:
            print("   • Agent creation test failed")
        
        print("\n🔧 Possible solutions:")
        print("   1. Make sure you installed with: pip install agenticflow[all]")
        print("   2. Or try: uv add agenticflow[all]")
        print("   3. Check that all dependencies are installed")
        print("   4. Report issues at: https://github.com/milad-o/agenticflow/issues")
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)