#!/usr/bin/env python3
"""
Chatbot Performance Testing Suite

This script measures the performance of the interactive RAG chatbot, focusing on:
- Retrieval latency (excluding embedding time)
- Response generation time
- Memory usage patterns
- Throughput under load

Usage:
    python examples/chatbots/performance_test.py
"""

import asyncio
import time
import psutil
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Import the chatbot
from interactive_rag_chatbot import InteractiveRAGChatbot

class ChatbotPerformanceTester:
    """Comprehensive performance testing for the RAG chatbot."""
    
    def __init__(self):
        self.chatbot: Optional[InteractiveRAGChatbot] = None
        self.test_queries = [
            # Ocean life queries
            "What are bioluminescent creatures in the ocean?",
            "How deep can marine animals dive?",
            "Tell me about coral reef ecosystems",
            
            # Space exploration queries  
            "What makes black holes mysterious?",
            "How do we search for life on other planets?",
            "Explain the solar system structure",
            
            # Wildlife behavior queries
            "How do animals migrate long distances?",
            "What are some amazing animal adaptations?",
            "How do predators hunt their prey?",
            
            # Physics and chemistry queries
            "What are the fundamental forces of nature?",
            "How do chemical reactions work?",
            "Explain quantum physics basics",
            
            # Biology queries
            "How does photosynthesis work?",
            "What is DNA and why is it important?",
            "How does evolution shape species?"
        ]
        self.results = []
    
    async def setup_chatbot(self) -> None:
        """Initialize the chatbot for testing."""
        print("🚀 Setting up chatbot for performance testing...")
        
        # Record setup time
        setup_start = time.time()
        
        self.chatbot = InteractiveRAGChatbot()
        await self.chatbot.initialize_chatbot()
        
        setup_time = time.time() - setup_start
        print(f"✅ Chatbot setup completed in {setup_time:.2f}s")
        
        return setup_time
    
    async def measure_retrieval_performance(self, query: str) -> Dict[str, Any]:
        """Measure retrieval performance for a single query."""
        if not self.chatbot:
            raise ValueError("Chatbot not initialized")
        
        # Measure retrieval time (excluding LLM response)
        retrieval_start = time.time()
        
        context_items = await self.chatbot.retrieve_context(query, max_context=3)
        
        retrieval_time = time.time() - retrieval_start
        
        return {
            "query": query[:50] + "..." if len(query) > 50 else query,
            "retrieval_time_ms": retrieval_time * 1000,
            "context_items_found": len(context_items),
            "context_total_chars": sum(len(item) for item in context_items),
        }
    
    async def measure_full_response_performance(self, query: str) -> Dict[str, Any]:
        """Measure full response generation performance."""
        if not self.chatbot:
            raise ValueError("Chatbot not initialized")
        
        # Memory before
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Full response timing
        response_start = time.time()
        
        response = await self.chatbot.get_response(query)
        
        response_time = time.time() - response_start
        
        # Memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = memory_after - memory_before
        
        return {
            "query": query[:50] + "..." if len(query) > 50 else query,
            "total_response_time_ms": response_time * 1000,
            "response_length_chars": len(response),
            "memory_usage_mb": memory_after,
            "memory_delta_mb": memory_delta,
        }
    
    async def run_retrieval_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive retrieval performance tests."""
        print("\\n🔍 Running retrieval performance tests...")
        
        retrieval_results = []
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"  Testing query {i}/{len(self.test_queries)}: {query[:30]}...")
            
            # Run multiple times for statistical accuracy
            query_results = []
            for run in range(3):
                result = await self.measure_retrieval_performance(query)
                query_results.append(result)
            
            # Calculate statistics
            retrieval_times = [r["retrieval_time_ms"] for r in query_results]
            avg_result = {
                "query": query,
                "avg_retrieval_time_ms": statistics.mean(retrieval_times),
                "min_retrieval_time_ms": min(retrieval_times),
                "max_retrieval_time_ms": max(retrieval_times),
                "std_retrieval_time_ms": statistics.stdev(retrieval_times) if len(retrieval_times) > 1 else 0,
                "avg_context_items": statistics.mean([r["context_items_found"] for r in query_results]),
                "avg_context_chars": statistics.mean([r["context_total_chars"] for r in query_results]),
            }
            
            retrieval_results.append(avg_result)
        
        # Overall statistics
        all_avg_times = [r["avg_retrieval_time_ms"] for r in retrieval_results]
        all_min_times = [r["min_retrieval_time_ms"] for r in retrieval_results]
        all_max_times = [r["max_retrieval_time_ms"] for r in retrieval_results]
        
        return {
            "individual_results": retrieval_results,
            "overall_stats": {
                "total_queries": len(self.test_queries),
                "avg_retrieval_time_ms": statistics.mean(all_avg_times),
                "min_retrieval_time_ms": min(all_min_times),
                "max_retrieval_time_ms": max(all_max_times),
                "std_retrieval_time_ms": statistics.stdev(all_avg_times),
                "retrieval_throughput_qps": 1000 / statistics.mean(all_avg_times),
            }
        }
    
    async def run_full_response_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive full response performance tests."""
        print("\\n🤖 Running full response performance tests...")
        
        response_results = []
        
        # Test subset of queries for full response (LLM calls are expensive)
        test_subset = self.test_queries[:8]  # First 8 queries
        
        for i, query in enumerate(test_subset, 1):
            print(f"  Testing full response {i}/{len(test_subset)}: {query[:30]}...")
            
            result = await self.measure_full_response_performance(query)
            response_results.append(result)
            
            # Small delay to avoid overwhelming the LLM provider
            await asyncio.sleep(0.5)
        
        # Calculate overall statistics
        response_times = [r["total_response_time_ms"] for r in response_results]
        response_lengths = [r["response_length_chars"] for r in response_results]
        memory_usage = [r["memory_usage_mb"] for r in response_results]
        
        return {
            "individual_results": response_results,
            "overall_stats": {
                "total_queries": len(test_subset),
                "avg_response_time_ms": statistics.mean(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "std_response_time_ms": statistics.stdev(response_times),
                "avg_response_length": statistics.mean(response_lengths),
                "avg_memory_usage_mb": statistics.mean(memory_usage),
                "response_throughput_qpm": 60000 / statistics.mean(response_times),  # queries per minute
            }
        }
    
    async def run_concurrent_load_test(self, concurrent_queries: int = 5) -> Dict[str, Any]:
        """Test performance under concurrent load."""
        print(f"\\n⚡ Running concurrent load test with {concurrent_queries} simultaneous queries...")
        
        if not self.chatbot:
            raise ValueError("Chatbot not initialized")
        
        # Select queries for concurrent testing
        queries = self.test_queries[:concurrent_queries]
        
        start_time = time.time()
        
        # Run queries concurrently (retrieval only to avoid LLM rate limits)
        tasks = [
            self.measure_retrieval_performance(query) 
            for query in queries
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        retrieval_times = [r["retrieval_time_ms"] for r in results]
        
        return {
            "concurrent_queries": concurrent_queries,
            "total_time_ms": total_time * 1000,
            "avg_time_per_query_ms": statistics.mean(retrieval_times),
            "max_time_ms": max(retrieval_times),
            "min_time_ms": min(retrieval_times),
            "throughput_qps": concurrent_queries / total_time,
            "results": results
        }
    
    def generate_performance_report(self, 
                                   setup_time: float,
                                   retrieval_results: Dict[str, Any], 
                                   response_results: Dict[str, Any],
                                   load_test_results: Dict[str, Any]) -> None:
        """Generate a comprehensive performance report."""
        
        print("\\n" + "="*80)
        print("📊 CHATBOT PERFORMANCE REPORT")
        print("="*80)
        
        print(f"\\n🚀 Setup Performance:")
        print(f"  Chatbot initialization time: {setup_time:.2f}s")
        
        print(f"\\n🔍 Retrieval Performance:")
        stats = retrieval_results["overall_stats"]
        print(f"  Average retrieval time: {stats['avg_retrieval_time_ms']:.2f}ms")
        print(f"  Min retrieval time: {stats['min_retrieval_time_ms']:.2f}ms")
        print(f"  Max retrieval time: {stats['max_retrieval_time_ms']:.2f}ms")
        print(f"  Standard deviation: {stats['std_retrieval_time_ms']:.2f}ms")
        print(f"  Retrieval throughput: {stats['retrieval_throughput_qps']:.1f} queries/second")
        
        print(f"\\n🤖 Full Response Performance:")
        stats = response_results["overall_stats"]
        print(f"  Average response time: {stats['avg_response_time_ms']:.2f}ms ({stats['avg_response_time_ms']/1000:.2f}s)")
        print(f"  Min response time: {stats['min_response_time_ms']:.2f}ms")
        print(f"  Max response time: {stats['max_response_time_ms']:.2f}ms")
        print(f"  Standard deviation: {stats['std_response_time_ms']:.2f}ms")
        print(f"  Average response length: {stats['avg_response_length']:.0f} characters")
        print(f"  Average memory usage: {stats['avg_memory_usage_mb']:.1f}MB")
        print(f"  Response throughput: {stats['response_throughput_qpm']:.1f} queries/minute")
        
        print(f"\\n⚡ Concurrent Load Test:")
        print(f"  Concurrent queries: {load_test_results['concurrent_queries']}")
        print(f"  Total time: {load_test_results['total_time_ms']:.2f}ms")
        print(f"  Average time per query: {load_test_results['avg_time_per_query_ms']:.2f}ms")
        print(f"  Concurrent throughput: {load_test_results['throughput_qps']:.1f} queries/second")
        
        print(f"\\n📈 Performance Summary:")
        print(f"  🏃 Retrieval: {retrieval_results['overall_stats']['avg_retrieval_time_ms']:.0f}ms avg (very fast)")
        print(f"  🧠 Full Response: {response_results['overall_stats']['avg_response_time_ms']/1000:.1f}s avg (includes LLM)")
        print(f"  🔥 Peak Throughput: {retrieval_results['overall_stats']['retrieval_throughput_qps']:.1f} retrievals/sec")
        print(f"  💾 Memory Efficient: {response_results['overall_stats']['avg_memory_usage_mb']:.0f}MB avg")
        
        # Performance rating
        avg_retrieval = retrieval_results['overall_stats']['avg_retrieval_time_ms']
        if avg_retrieval < 50:
            rating = "🚀 EXCELLENT"
        elif avg_retrieval < 100:
            rating = "✅ VERY GOOD"  
        elif avg_retrieval < 200:
            rating = "👍 GOOD"
        else:
            rating = "⚠️ NEEDS OPTIMIZATION"
        
        print(f"\\n🎯 Overall Performance Rating: {rating}")
        print(f"   Retrieval latency: {avg_retrieval:.0f}ms")
        
        print("="*80)
    
    async def save_detailed_results(self, 
                                  setup_time: float,
                                  retrieval_results: Dict[str, Any], 
                                  response_results: Dict[str, Any],
                                  load_test_results: Dict[str, Any]) -> None:
        """Save detailed results to JSON file."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chatbot_performance_{timestamp}.json"
        
        detailed_results = {
            "timestamp": timestamp,
            "setup_time_seconds": setup_time,
            "retrieval_performance": retrieval_results,
            "response_performance": response_results,
            "load_test_performance": load_test_results,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "memory_total_mb": psutil.virtual_memory().total / 1024 / 1024,
                "cpu_count": psutil.cpu_count(),
            }
        }
        
        results_path = Path("performance_results") / filename
        results_path.parent.mkdir(exist_ok=True)
        
        with open(results_path, 'w') as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        print(f"\\n💾 Detailed results saved to: {results_path}")
    
    async def run_comprehensive_performance_test(self) -> None:
        """Run the complete performance test suite."""
        print("🧪 Starting Comprehensive Chatbot Performance Test")
        print("=" * 60)
        
        try:
            # Setup
            setup_time = await self.setup_chatbot()
            
            # Retrieval performance test
            retrieval_results = await self.run_retrieval_performance_test()
            
            # Full response performance test  
            response_results = await self.run_full_response_performance_test()
            
            # Concurrent load test
            load_test_results = await self.run_concurrent_load_test(concurrent_queries=5)
            
            # Generate report
            self.generate_performance_report(
                setup_time, retrieval_results, response_results, load_test_results
            )
            
            # Save detailed results
            await self.save_detailed_results(
                setup_time, retrieval_results, response_results, load_test_results
            )
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main function to run performance tests."""
    tester = ChatbotPerformanceTester()
    await tester.run_comprehensive_performance_test()

if __name__ == "__main__":
    print("🔬 Interactive RAG Chatbot Performance Testing")
    print("This test measures retrieval and response performance")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n❌ Performance test interrupted")
    except Exception as e:
        print(f"❌ Performance test failed: {e}")