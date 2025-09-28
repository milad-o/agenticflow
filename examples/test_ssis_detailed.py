"""Detailed test for SSIS Agent with specific tool calls."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Set API key if not already set
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ OPENAI_API_KEY not set. Please set it in your .env file or environment.")
    exit(1)

from agenticflow import Flow
from agenticflow.agents.ssis_agent import SSISAnalysisAgent

async def test_ssis_detailed():
    """Detailed test of SSIS agent with specific tool usage."""
    print("🧪 Detailed SSIS Agent Test")
    print("=" * 35)
    
    # Create SSIS agent
    ssis_agent = SSISAnalysisAgent("ssis_analyst")
    flow = Flow("ssis_detailed_flow")
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSIS Agent with {len(ssis_agent.tools)} tools")
    print(f"   Available tools: {[tool.name for tool in ssis_agent.tools]}")
    
    # Test 1: Parse the DTSX file
    print("\n📄 Test 1: Parse DTSX file")
    result1 = await flow.run("Use the parse_dtsx_file tool to parse sample_complex_package.dtsx")
    print(f"Result: {result1['messages'][-1].content}")
    
    # Test 2: Extract data flows
    print("\n🔄 Test 2: Extract data flows")
    result2 = await flow.run("Use the extract_data_flows tool to analyze sample_complex_package.dtsx")
    print(f"Result: {result2['messages'][-1].content}")
    
    # Test 3: Extract connections
    print("\n🔗 Test 3: Extract connections")
    result3 = await flow.run("Use the extract_connections tool to find all connections in sample_complex_package.dtsx")
    print(f"Result: {result3['messages'][-1].content}")
    
    # Test 4: Create package summary
    print("\n📋 Test 4: Create package summary")
    result4 = await flow.run("Use the create_package_summary tool to summarize sample_complex_package.dtsx")
    print(f"Result: {result4['messages'][-1].content}")
    
    print("\n✅ Detailed test completed!")

if __name__ == "__main__":
    asyncio.run(test_ssis_detailed())
