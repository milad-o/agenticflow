"""Test SSIS Analysis Agent with complex DTSX file."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow
from agenticflow.agents.ssis_agent import SSISAnalysisAgent

async def test_ssis_agent():
    """Test SSIS agent with comprehensive analysis capabilities."""
    print("🧪 Testing SSIS Analysis Agent")
    print("=" * 40)
    
    # Create SSIS agent
    ssis_agent = SSISAnalysisAgent("ssis_analyst")
    flow = Flow("ssis_analysis_flow")
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
    
    # Test 6: Analyze package structure
    print("\n🏗️ Test 6: Analyze package structure")
    result6 = await flow.run("Analyze the overall structure of sample_complex_package.dtsx")
    print(f"Result: {result6['messages'][-1].content}")
    
    # Test 7: Find data sources and destinations
    print("\n📥📤 Test 7: Find data sources and destinations")
    result7 = await flow.run("Identify all data sources and destinations in sample_complex_package.dtsx")
    print(f"Result: {result7['messages'][-1].content}")
    
    # Test 8: Trace data lineage
    print("\n🔍 Test 8: Trace data lineage")
    result8 = await flow.run("Trace the data lineage through sample_complex_package.dtsx")
    print(f"Result: {result8['messages'][-1].content}")
    
    # Test 9: Validate package
    print("\n✅ Test 9: Validate package")
    result9 = await flow.run("Validate sample_complex_package.dtsx for common issues")
    print(f"Result: {result9['messages'][-1].content}")
    
    # Test 10: Create package summary
    print("\n📋 Test 10: Create package summary")
    result10 = await flow.run("Create a comprehensive summary of sample_complex_package.dtsx")
    print(f"Result: {result10['messages'][-1].content}")
    
    # Test 11: Search package content
    print("\n🔎 Test 11: Search package content")
    result11 = await flow.run("Search for 'Customer' in sample_complex_package.dtsx")
    print(f"Result: {result11['messages'][-1].content}")
    
    # Test 12: Index package for semantic search
    print("\n🧠 Test 12: Index package for semantic search")
    result12 = await flow.run("Index sample_complex_package.dtsx for semantic search capabilities")
    print(f"Result: {result12['messages'][-1].content}")
    
    # Test 13: Semantic search query
    print("\n🔍 Test 13: Semantic search query")
    result13 = await flow.run("Use semantic search to find information about data transformations in sample_complex_package.dtsx")
    print(f"Result: {result13['messages'][-1].content}")
    
    # Test 14: Export analysis
    print("\n💾 Test 14: Export analysis")
    result14 = await flow.run("Export a comprehensive analysis of sample_complex_package.dtsx to ssis_analysis.json")
    print(f"Result: {result14['messages'][-1].content}")
    
    # Test 15: Extract error handling
    print("\n⚠️ Test 15: Extract error handling")
    result15 = await flow.run("Extract error handling configuration from sample_complex_package.dtsx")
    print(f"Result: {result15['messages'][-1].content}")
    
    # Test 16: Analyze performance implications
    print("\n⚡ Test 16: Analyze performance implications")
    result16 = await flow.run("Analyze performance implications of sample_complex_package.dtsx")
    print(f"Result: {result16['messages'][-1].content}")
    
    print("\n🎉 SSIS Agent tests completed!")
    
    # Check if analysis file was created
    analysis_file = "examples/artifacts/ssis_analysis.json"
    if os.path.exists(analysis_file):
        file_size = os.path.getsize(analysis_file)
        print(f"📄 Analysis file created: {analysis_file} ({file_size} bytes)")

if __name__ == "__main__":
    asyncio.run(test_ssis_agent())
