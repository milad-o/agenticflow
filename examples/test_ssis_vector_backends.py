"""Test SSIS Agent with different vector backends (ChromaDB, SQLite, None)."""

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

async def test_vector_backend(backend_name: str, vector_backend: str, persistent: bool = False):
    """Test a specific vector backend."""
    print(f"\n🧪 Testing {backend_name} Backend")
    print("=" * 40)
    
    # Create agent with specific vector backend
    ssis_agent = Agent(
        name=f"ssis_{backend_name.lower()}",
        description=f"SSIS analyst with {backend_name} backend",
        tools=[
            parse_dtsx_file, extract_data_flows, extract_connections,
            extract_tasks, extract_variables, create_package_summary,
            search_package_content
        ]
    )
    
    # Add vector backend configuration
    ssis_agent._vector_backend = vector_backend
    ssis_agent._persistent = persistent
    ssis_agent._db_path = f"examples/artifacts/ssis_{backend_name.lower()}.db" if persistent else ":memory:"
    
    flow = Flow(f"ssis_{backend_name.lower()}_flow")
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSIS Agent with {backend_name} backend")
    print(f"   Vector backend: {vector_backend}")
    print(f"   Persistent: {persistent}")
    print(f"   DB path: {ssis_agent._db_path}")
    
    # Test 1: Parse the DTSX file
    print(f"\n📄 Test 1: Parse DTSX file with {backend_name}")
    result1 = await flow.run("Parse the sample_complex_package.dtsx file and show its basic structure")
    print(f"Result: {result1['messages'][-1].content[:200]}...")
    
    # Test 2: Index for search (if backend supports it)
    if vector_backend != "none":
        print(f"\n📚 Test 2: Index package with {backend_name}")
        result2 = await flow.run("Index sample_complex_package.dtsx for search")
        print(f"Result: {result2['messages'][-1].content}")
        
        # Test 3: Semantic search
        print(f"\n🔍 Test 3: Semantic search with {backend_name}")
        result3 = await flow.run("Search for 'Customer' using semantic search in sample_complex_package.dtsx")
        print(f"Result: {result3['messages'][-1].content[:300]}...")
    else:
        print(f"\n⏭️ Skipping vector search tests for {backend_name} (no backend)")
    
    print(f"\n✅ {backend_name} backend test completed!")

async def test_all_vector_backends():
    """Test all vector backends."""
    print("🚀 Testing SSIS Agent with Multiple Vector Backends")
    print("=" * 55)
    
    # Test configurations
    backends = [
        ("ChromaDB", "chroma", False),  # Ephemeral ChromaDB
        ("ChromaDB-Persistent", "chroma", True),  # Persistent ChromaDB
        ("SQLite", "sqlite", False),  # Ephemeral SQLite
        ("SQLite-Persistent", "sqlite", True),  # Persistent SQLite
        ("None", "none", False),  # No vector backend
    ]
    
    for backend_name, vector_backend, persistent in backends:
        try:
            await test_vector_backend(backend_name, vector_backend, persistent)
        except Exception as e:
            print(f"❌ Error testing {backend_name}: {e}")
    
    print("\n🎉 All vector backend tests completed!")
    
    # Check created files
    print("\n📁 Checking created files:")
    artifacts_dir = "examples/artifacts"
    if os.path.exists(artifacts_dir):
        files = os.listdir(artifacts_dir)
        db_files = [f for f in files if f.endswith('.db')]
        if db_files:
            print(f"   Database files: {db_files}")
            for db_file in db_files:
                file_path = os.path.join(artifacts_dir, db_file)
                size = os.path.getsize(file_path)
                print(f"   📄 {db_file}: {size} bytes")
        else:
            print("   No database files created")

if __name__ == "__main__":
    asyncio.run(test_all_vector_backends())
