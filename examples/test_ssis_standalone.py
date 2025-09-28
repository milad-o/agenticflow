"""Test SSIS Agent with standalone tools."""

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

async def test_ssis_standalone():
    """Test SSIS agent with standalone tools."""
    print("🧪 SSIS Agent with Standalone Tools Test")
    print("=" * 45)
    
    # Create agent with standalone SSIS tools
    ssis_agent = Agent(
        name="ssis_analyst",
        description="SSIS DTSX file analysis specialist",
        tools=[
            parse_dtsx_file, extract_data_flows, extract_connections,
            extract_tasks, extract_variables, create_package_summary,
            search_package_content
        ]
    )
    
    flow = Flow("ssis_standalone_flow")
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSIS Agent with {len(ssis_agent.tools)} tools")
    print(f"   Tool names: {[tool.name for tool in ssis_agent.tools]}")
    
    # Test 1: Parse the DTSX file
    print("\n📄 Test 1: Parse DTSX file")
    result1 = await flow.run("Parse the sample_complex_package.dtsx file and show its basic structure")
    print(f"Result: {result1['messages'][-1].content}")
    
    # Test 2: Extract data flows
    print("\n🔄 Test 2: Extract data flows")
    result2 = await flow.run("Extract all data flow information from sample_complex_package.dtsx")
    print(f"Result: {result2['messages'][-1].content}")
    
    # Test 3: Extract connections
    print("\n🔗 Test 3: Extract connections")
    result3 = await flow.run("Find all connection managers in sample_complex_package.dtsx")
    print(f"Result: {result3['messages'][-1].content}")
    
    # Test 4: Extract tasks
    print("\n⚙️ Test 4: Extract tasks")
    result4 = await flow.run("List all tasks in sample_complex_package.dtsx")
    print(f"Result: {result4['messages'][-1].content}")
    
    # Test 5: Extract variables
    print("\n📊 Test 5: Extract variables")
    result5 = await flow.run("Show all variables defined in sample_complex_package.dtsx")
    print(f"Result: {result5['messages'][-1].content}")
    
    # Test 6: Create package summary
    print("\n📋 Test 6: Create package summary")
    result6 = await flow.run("Create a comprehensive summary of sample_complex_package.dtsx")
    print(f"Result: {result6['messages'][-1].content}")
    
    # Test 7: Search package content
    print("\n🔎 Test 7: Search package content")
    result7 = await flow.run("Search for 'Customer' in sample_complex_package.dtsx")
    print(f"Result: {result7['messages'][-1].content}")
    
    print("\n✅ Standalone tools test completed!")

if __name__ == "__main__":
    asyncio.run(test_ssis_standalone())
