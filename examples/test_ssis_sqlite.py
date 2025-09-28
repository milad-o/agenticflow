"""Test SSIS Agent with SQLite backend."""

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

async def test_ssis_sqlite():
    """Test SSIS agent with SQLite backend."""
    print("🧪 SSIS Agent with SQLite Backend Test")
    print("=" * 40)
    
    # Create agent with SQLite backend
    ssis_agent = Agent(
        name="ssis_sqlite_analyst",
        description="SSIS analyst with SQLite backend",
        tools=[
            parse_dtsx_file, extract_data_flows, extract_connections,
            extract_tasks, extract_variables, create_package_summary,
            search_package_content
        ]
    )
    
    # Configure SQLite backend
    ssis_agent._vector_backend = "sqlite"
    ssis_agent._persistent = True
    ssis_agent._db_path = "examples/artifacts/ssis_sqlite_test.db"
    
    # Initialize SQLite database
    import sqlite3
    conn = sqlite3.connect(ssis_agent._db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ssis_elements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT,
            element_tag TEXT,
            element_text TEXT,
            attributes TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    
    flow = Flow("ssis_sqlite_flow")
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSIS Agent with SQLite backend")
    print(f"   Database: {ssis_agent._db_path}")
    
    # Test 1: Parse the DTSX file
    print("\n📄 Test 1: Parse DTSX file")
    result1 = await flow.run("Parse the sample_complex_package.dtsx file and show its basic structure")
    print(f"Result: {result1['messages'][-1].content[:200]}...")
    
    # Test 2: Index package
    print("\n📚 Test 2: Index package in SQLite")
    result2 = await flow.run("Index sample_complex_package.dtsx for search")
    print(f"Result: {result2['messages'][-1].content}")
    
    # Test 3: Search for specific content
    print("\n🔍 Test 3: Search for 'Customer'")
    result3 = await flow.run("Search for 'Customer' in sample_complex_package.dtsx")
    print(f"Result: {result3['messages'][-1].content[:300]}...")
    
    # Test 4: Search for connections
    print("\n🔗 Test 4: Search for 'Connection'")
    result4 = await flow.run("Search for 'Connection' in sample_complex_package.dtsx")
    print(f"Result: {result4['messages'][-1].content[:300]}...")
    
    # Test 5: Search for SQL statements
    print("\n💾 Test 5: Search for 'SELECT'")
    result5 = await flow.run("Search for 'SELECT' in sample_complex_package.dtsx")
    print(f"Result: {result5['messages'][-1].content[:300]}...")
    
    print("\n✅ SQLite backend test completed!")
    
    # Check database size
    if os.path.exists(ssis_agent._db_path):
        size = os.path.getsize(ssis_agent._db_path)
        print(f"📄 Database size: {size} bytes")

if __name__ == "__main__":
    asyncio.run(test_ssis_sqlite())
