"""Test SSIS Agent with ChromaDB backend."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Set API key if not already set
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ OPENAI_API_KEY not set. Please set it in your .env file or environment.")
    exit(1)

from agenticflow import Flow, Agent
from agenticflow.tools.ssis_tools import (
    parse_dtsx_file, extract_data_flows, extract_connections,
    extract_tasks, extract_variables, create_package_summary,
    search_package_content
)

async def test_ssis_chroma():
    """Test SSIS agent with ChromaDB backend."""
    print("🧪 SSIS Agent with ChromaDB Backend Test")
    print("=" * 42)
    
    # Create agent with ChromaDB backend
    ssis_agent = Agent(
        name="ssis_chroma_analyst",
        description="SSIS analyst with ChromaDB backend",
        tools=[
            parse_dtsx_file, extract_data_flows, extract_connections,
            extract_tasks, extract_variables, create_package_summary,
            search_package_content
        ]
    )
    
    # Configure ChromaDB backend
    ssis_agent._vector_backend = "chroma"
    ssis_agent._persistent = False  # Ephemeral for testing
    
    flow = Flow("ssis_chroma_flow")
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSIS Agent with ChromaDB backend")
    print(f"   Vector backend: {ssis_agent._vector_backend}")
    print(f"   Persistent: {ssis_agent._persistent}")
    
    # Test 1: Parse the DTSX file
    print("\n📄 Test 1: Parse DTSX file")
    result1 = await flow.run("Parse the sample_complex_package.dtsx file and show its basic structure")
    print(f"Result: {result1['messages'][-1].content[:200]}...")
    
    # Test 2: Index package
    print("\n📚 Test 2: Index package in ChromaDB")
    result2 = await flow.run("Index sample_complex_package.dtsx for semantic search")
    print(f"Result: {result2['messages'][-1].content}")
    
    # Test 3: Semantic search for data flows
    print("\n🔍 Test 3: Semantic search for 'data flow'")
    result3 = await flow.run("Search for 'data flow' using semantic search in sample_complex_package.dtsx")
    print(f"Result: {result3['messages'][-1].content[:300]}...")
    
    # Test 4: Semantic search for connections
    print("\n🔗 Test 4: Semantic search for 'connection'")
    result4 = await flow.run("Search for 'connection' using semantic search in sample_complex_package.dtsx")
    print(f"Result: {result4['messages'][-1].content[:300]}...")
    
    # Test 5: Semantic search for SQL
    print("\n💾 Test 5: Semantic search for 'SQL'")
    result5 = await flow.run("Search for 'SQL' using semantic search in sample_complex_package.dtsx")
    print(f"Result: {result5['messages'][-1].content[:300]}...")
    
    print("\n✅ ChromaDB backend test completed!")

if __name__ == "__main__":
    asyncio.run(test_ssis_chroma())
