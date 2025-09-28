"""Simple test for SSIS Agent."""

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

async def test_ssis_simple():
    """Simple test of SSIS agent."""
    print("🧪 Simple SSIS Agent Test")
    print("=" * 30)
    
    # Create SSIS agent
    ssis_agent = SSISAnalysisAgent("ssis_analyst")
    flow = Flow("ssis_test_flow")
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSIS Agent with {len(ssis_agent.tools)} tools")
    
    # Test 1: Parse the DTSX file
    print("\n📄 Test 1: Parse DTSX file")
    result = await flow.run("Parse the sample_complex_package.dtsx file and show its basic structure")
    print(f"Result: {result['messages'][-1].content}")
    
    print("\n✅ Simple test completed!")

if __name__ == "__main__":
    asyncio.run(test_ssis_simple())
