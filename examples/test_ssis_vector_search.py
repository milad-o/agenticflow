"""Test SSIS Agent with vector store and semantic search capabilities."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import Flow
from agenticflow.agents.ssis_agent import SSISAnalysisAgent

async def test_ssis_vector_search():
    """Test SSIS agent with vector store and semantic search."""
    print("🧠 Testing SSIS Agent with Vector Store & Semantic Search")
    print("=" * 55)
    
    # Create SSIS agent
    ssis_agent = SSISAnalysisAgent("ssis_analyst")
    flow = Flow("ssis_vector_flow")
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSIS Agent with vector capabilities")
    
    # Test 1: Index the package
    print("\n📚 Test 1: Index package for semantic search")
    result1 = await flow.run("Index sample_complex_package.dtsx for semantic search")
    print(f"Result: {result1['messages'][-1].content}")
    
    # Test 2: Semantic search queries
    queries = [
        "What are the data sources in this package?",
        "How does data flow from source to destination?",
        "What transformations are applied to the data?",
        "What error handling is configured?",
        "What are the performance bottlenecks?",
        "How are connections managed?",
        "What variables are used?",
        "What logging is configured?"
    ]
    
    for i, query in enumerate(queries, 2):
        print(f"\n🔍 Test {i}: Semantic search - '{query}'")
        result = await flow.run(f"Use semantic search to answer: {query}")
        print(f"Result: {result['messages'][-1].content}")
    
    # Test 10: Complex analysis query
    print("\n🎯 Test 10: Complex analysis query")
    complex_query = "Analyze the complete data pipeline from source to destination, including all transformations, error handling, and performance considerations"
    result10 = await flow.run(f"Use semantic search to answer: {complex_query}")
    print(f"Result: {result10['messages'][-1].content}")
    
    print("\n🎉 Vector search tests completed!")

if __name__ == "__main__":
    asyncio.run(test_ssis_vector_search())
