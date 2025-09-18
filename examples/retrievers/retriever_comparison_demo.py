#!/usr/bin/env python3
"""
Retriever Comparison Demo

This demo compares different retriever types (text-based, semantic, and composite)
on the same document set to showcase their strengths and use cases.

Features:
- Side-by-side comparison of retriever types
- Performance metrics and accuracy analysis
- Different query types to test various capabilities
- Visual comparison of results

Usage:
    python examples/retrievers/retriever_comparison_demo.py
"""

import asyncio
import os
import time
from typing import List, Dict, Any
from pathlib import Path

from agenticflow.retrievers import (
    KeywordRetriever, BM25Retriever, FuzzyRetriever, RegexRetriever,
    SemanticRetriever, CosineRetriever, EuclideanRetriever,
    EnsembleRetriever, HybridRetriever, ContextualRetriever,
    create_from_memory
)
from agenticflow.memory import VectorMemory
from agenticflow.memory.vector_memory import VectorMemoryConfig
from agenticflow.config.settings import MemoryConfig
from agenticflow.vectorstores.factory import VectorStoreFactory
from agenticflow.text import split_text, ChunkingStrategy
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

class RetrieverComparisonDemo:
    """Compare different retriever types on the same dataset."""
    
    def __init__(self):
        self.documents = []
        self.chunks = []
        self.text_data = []
        self.memory = None
        self.embeddings = None
        
        # Different categories of retrievers
        self.text_retrievers = {}
        self.semantic_retrievers = {}
        self.composite_retrievers = {}
    
    async def setup_embeddings(self):
        """Setup embedding provider."""
        print("🧮 Setting up embeddings...")
        
        if os.getenv("OPENAI_API_KEY"):
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            print("  Using OpenAI embeddings")
        else:
            try:
                self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
                await self.embeddings.aembed_query("test")
                print("  Using Ollama embeddings")
            except Exception as e:
                raise RuntimeError(f"No embedding provider available: {e}")
    
    async def load_test_documents(self):
        """Load diverse test documents for comparison."""
        print("📖 Loading test documents...")
        
        self.documents = [
            # Technical document
            """
            Machine Learning and Neural Networks
            
            Machine learning is a method of data analysis that automates analytical model building. 
            It is a branch of artificial intelligence based on the idea that systems can learn from data, 
            identify patterns and make decisions with minimal human intervention.
            
            Neural networks are computing systems inspired by biological neural networks. They consist 
            of interconnected nodes (neurons) that can learn to recognize patterns. Deep learning uses 
            neural networks with multiple layers to model and understand complex patterns in data.
            
            Key concepts include:
            - Supervised learning with labeled training data
            - Unsupervised learning for pattern discovery
            - Reinforcement learning through trial and error
            - Backpropagation for training neural networks
            - Gradient descent for optimization
            """,
            
            # Programming document
            """
            Python Programming Best Practices
            
            Python is a versatile programming language that emphasizes code readability and simplicity. 
            Here are essential best practices for Python development:
            
            Code Style:
            - Follow PEP 8 guidelines for consistent formatting
            - Use meaningful variable and function names
            - Keep functions small and focused on single tasks
            - Add docstrings to document your code
            
            Data Structures:
            - Lists for ordered, mutable collections
            - Tuples for ordered, immutable collections  
            - Dictionaries for key-value mappings
            - Sets for unique, unordered collections
            
            Error Handling:
            - Use try-except blocks appropriately
            - Handle specific exceptions rather than broad catches
            - Log errors for debugging purposes
            """,
            
            # Scientific document
            """
            Climate Change and Environmental Impact
            
            Climate change refers to long-term changes in temperature and weather patterns. While climate 
            variations occur naturally, human activities have been the main driver of climate change since 
            the Industrial Revolution.
            
            Primary causes include:
            - Greenhouse gas emissions from burning fossil fuels
            - Deforestation reducing carbon absorption capacity
            - Industrial processes releasing various pollutants
            - Agriculture contributing methane and nitrous oxide
            
            Environmental impacts:
            - Rising global temperatures and extreme weather
            - Melting polar ice caps and glaciers
            - Sea level rise affecting coastal communities  
            - Changes in precipitation patterns
            - Ecosystem disruption and species migration
            
            Mitigation strategies focus on reducing emissions through renewable energy, energy efficiency, 
            and sustainable practices.
            """,
            
            # Business document
            """
            Digital Marketing Strategies for Modern Businesses
            
            Digital marketing encompasses all marketing efforts that use electronic devices and internet 
            connectivity. Businesses leverage digital channels to connect with current and prospective customers.
            
            Core digital marketing channels:
            - Search Engine Optimization (SEO) for organic visibility
            - Pay-per-click (PPC) advertising for immediate results
            - Social media marketing for community engagement
            - Email marketing for direct customer communication
            - Content marketing to provide value and build trust
            
            Analytics and measurement:
            - Website traffic analysis using tools like Google Analytics
            - Conversion rate optimization to improve performance
            - Customer acquisition cost and lifetime value metrics
            - Return on investment (ROI) calculations
            
            Success requires understanding target audiences, creating compelling content, 
            and continuously optimizing based on data-driven insights.
            """
        ]
        
        print(f"📚 Loaded {len(self.documents)} test documents")
    
    async def prepare_data(self):
        """Chunk documents and prepare data for retrievers."""
        print("✂️ Preparing data...")
        
        all_chunks = []
        for i, doc in enumerate(self.documents):
            chunks = await split_text(
                doc.strip(),
                splitter_type=ChunkingStrategy.RECURSIVE,
                chunk_size=200,
                chunk_overlap=50
            )
            
            for chunk in chunks:
                chunk.metadata["doc_id"] = i
                chunk.metadata["doc_type"] = ["Technical", "Programming", "Scientific", "Business"][i]
                all_chunks.append(chunk)
        
        self.chunks = all_chunks
        self.text_data = [chunk.content for chunk in self.chunks]
        
        print(f"📄 Created {len(self.chunks)} chunks")
    
    async def setup_vector_memory(self):
        """Setup vector memory for semantic retrievers."""
        print("🧠 Setting up vector memory...")
        
        vector_store_config = VectorStoreFactory.create_faiss_config(
            persist_path="./comparison_vectors",
            embedding_dimension=1536 if "openai" in str(self.embeddings.__class__).lower() else 768
        )
        
        memory_config = VectorMemoryConfig(vector_store_config=vector_store_config)
        base_config = MemoryConfig()
        
        self.memory = VectorMemory(base_config, memory_config, self.embeddings)
        await self.memory.initialize()
        
        # Index chunks
        from langchain_core.messages import HumanMessage
        
        for chunk in self.chunks:
            message = HumanMessage(content=chunk.content)
            await self.memory.add_message(message, metadata=chunk.metadata)
        
        print("✅ Vector memory ready")
    
    async def setup_retrievers(self):
        """Setup all retriever types for comparison."""
        print("🔍 Setting up retrievers...")
        
        # Text-based retrievers
        self.text_retrievers = {
            "Keyword": KeywordRetriever(self.text_data),
            "BM25": BM25Retriever(self.text_data),
            "Fuzzy": FuzzyRetriever(self.text_data),
            "Regex": RegexRetriever(self.text_data)
        }
        
        # Semantic retrievers
        self.semantic_retrievers = {
            "Semantic": create_from_memory(self.memory),
            "Cosine": CosineRetriever.from_memory(self.memory),
            "Euclidean": EuclideanRetriever.from_memory(self.memory)
        }
        
        # Composite retrievers
        self.composite_retrievers = {
            "Ensemble": EnsembleRetriever([
                BM25Retriever(self.text_data),
                create_from_memory(self.memory)
            ]),
            "Hybrid": HybridRetriever(
                text_retriever=BM25Retriever(self.text_data),
                semantic_retriever=create_from_memory(self.memory)
            ),
            "Contextual": ContextualRetriever(
                base_retriever=create_from_memory(self.memory),
                context_window=2
            )
        }
        
        total_retrievers = len(self.text_retrievers) + len(self.semantic_retrievers) + len(self.composite_retrievers)
        print(f"🛠️ Setup {total_retrievers} retrievers across 3 categories")
    
    async def test_query_types(self):
        """Test different types of queries to showcase retriever strengths."""
        print("\\n🔍 TESTING DIFFERENT QUERY TYPES")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "Exact Term Match",
                "query": "neural networks",
                "description": "Tests exact keyword matching capabilities"
            },
            {
                "name": "Conceptual Query",
                "query": "learning from data patterns",
                "description": "Tests semantic understanding"
            },
            {
                "name": "Fuzzy/Typo Query", 
                "query": "machne lerning algoritms",
                "description": "Tests fuzzy matching and typo tolerance"
            },
            {
                "name": "Complex Question",
                "query": "What are the environmental effects of human industrial activities?",
                "description": "Tests context understanding and complex retrieval"
            },
            {
                "name": "Technical Jargon",
                "query": "backpropagation gradient descent optimization",
                "description": "Tests technical term recognition"
            }
        ]
        
        for test_case in test_cases:
            await self.compare_all_retrievers(
                test_case["query"], 
                test_case["name"],
                test_case["description"]
            )
    
    async def compare_all_retrievers(self, query: str, test_name: str, description: str):
        """Compare all retriever types on a single query."""
        print(f"\\n🎯 TEST: {test_name}")
        print(f"Query: '{query}'")
        print(f"Purpose: {description}")
        print("-" * 80)
        
        all_results = {}
        
        # Test text retrievers
        print("\\n📝 TEXT-BASED RETRIEVERS:")
        for name, retriever in self.text_retrievers.items():
            result = await self.test_single_retriever(name, retriever, query)
            all_results[f"Text-{name}"] = result
        
        # Test semantic retrievers
        print("\\n🧠 SEMANTIC RETRIEVERS:")
        for name, retriever in self.semantic_retrievers.items():
            result = await self.test_single_retriever(name, retriever, query)
            all_results[f"Semantic-{name}"] = result
        
        # Test composite retrievers
        print("\\n🔧 COMPOSITE RETRIEVERS:")
        for name, retriever in self.composite_retrievers.items():
            result = await self.test_single_retriever(name, retriever, query)
            all_results[f"Composite-{name}"] = result
        
        # Summary
        self.print_test_summary(test_name, all_results)
    
    async def test_single_retriever(self, name: str, retriever: Any, query: str, top_k: int = 3):
        """Test a single retriever and return results."""
        try:
            start_time = time.time()
            results = await retriever.retrieve(query, top_k=top_k)
            duration = time.time() - start_time
            
            print(f"  {name:<12} | {duration:.3f}s | {len(results)} results")
            
            # Show top result
            if results:
                top_result = results[0]
                content_preview = top_result.content[:60] + "..." if len(top_result.content) > 60 else top_result.content
                score = getattr(top_result, 'score', 0.0)
                print(f"               | Score: {score:.3f} | {content_preview}")
            
            return {
                "results": results,
                "duration": duration,
                "count": len(results),
                "success": True
            }
            
        except Exception as e:
            print(f"  {name:<12} | ERROR: {str(e)[:50]}")
            return {
                "error": str(e),
                "duration": 0,
                "count": 0,
                "success": False
            }
    
    def print_test_summary(self, test_name: str, all_results: Dict):
        """Print summary of test results."""
        print(f"\\n📊 SUMMARY FOR '{test_name}':")
        print("-" * 50)
        
        successful_results = {k: v for k, v in all_results.items() if v["success"]}
        
        if successful_results:
            # Best performance
            fastest = min(successful_results.items(), key=lambda x: x[1]["duration"])
            most_results = max(successful_results.items(), key=lambda x: x[1]["count"])
            
            print(f"⚡ Fastest: {fastest[0]} ({fastest[1]['duration']:.3f}s)")
            print(f"📈 Most Results: {most_results[0]} ({most_results[1]['count']} results)")
        
        # Count by category
        text_success = sum(1 for k, v in all_results.items() if k.startswith("Text-") and v["success"])
        semantic_success = sum(1 for k, v in all_results.items() if k.startswith("Semantic-") and v["success"])
        composite_success = sum(1 for k, v in all_results.items() if k.startswith("Composite-") and v["success"])
        
        print(f"✅ Success Rates: Text({text_success}/{len(self.text_retrievers)}) | " +
              f"Semantic({semantic_success}/{len(self.semantic_retrievers)}) | " +
              f"Composite({composite_success}/{len(self.composite_retrievers)})")
    
    async def performance_analysis(self):
        """Analyze overall performance across all retrievers."""
        print("\\n📈 OVERALL PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        # Performance test queries
        performance_queries = [
            "machine learning algorithms",
            "python programming",
            "climate change impact",
            "digital marketing strategy"
        ]
        
        performance_data = {}
        
        # Collect performance data
        all_retrievers = {
            **{f"Text-{k}": v for k, v in self.text_retrievers.items()},
            **{f"Semantic-{k}": v for k, v in self.semantic_retrievers.items()},
            **{f"Composite-{k}": v for k, v in self.composite_retrievers.items()}
        }
        
        for query in performance_queries:
            for name, retriever in all_retrievers.items():
                try:
                    start_time = time.time()
                    results = await retriever.retrieve(query, top_k=5)
                    duration = time.time() - start_time
                    
                    if name not in performance_data:
                        performance_data[name] = {"durations": [], "counts": []}
                    
                    performance_data[name]["durations"].append(duration)
                    performance_data[name]["counts"].append(len(results))
                    
                except Exception:
                    continue
        
        # Calculate and display averages
        print("\\n📊 AVERAGE PERFORMANCE METRICS:")
        print(f"{'Retriever':<20} {'Avg Time (s)':<12} {'Avg Results':<12} {'Category':<12}")
        print("-" * 65)
        
        for name, data in sorted(performance_data.items()):
            if data["durations"]:
                avg_time = sum(data["durations"]) / len(data["durations"])
                avg_count = sum(data["counts"]) / len(data["counts"])
                category = name.split("-")[0]
                
                print(f"{name:<20} {avg_time:<12.3f} {avg_count:<12.1f} {category:<12}")
    
    async def recommendations_and_use_cases(self):
        """Provide recommendations for different use cases."""
        print("\\n💡 RETRIEVER RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = [
            {
                "use_case": "Exact keyword search in documentation",
                "best_retriever": "Keyword or BM25",
                "reason": "Fast, accurate for precise term matching"
            },
            {
                "use_case": "Semantic search with query understanding", 
                "best_retriever": "Semantic or Cosine",
                "reason": "Understands meaning beyond exact words"
            },
            {
                "use_case": "Handling typos and approximate matches",
                "best_retriever": "Fuzzy",
                "reason": "Tolerates spelling errors and variations"
            },
            {
                "use_case": "Complex questions requiring context",
                "best_retriever": "Hybrid or Ensemble",
                "reason": "Combines multiple approaches for better coverage"
            },
            {
                "use_case": "Pattern matching in technical documents",
                "best_retriever": "Regex",
                "reason": "Precise pattern matching capabilities"
            },
            {
                "use_case": "General-purpose search with good balance",
                "best_retriever": "Hybrid",
                "reason": "Best of both text and semantic approaches"
            }
        ]
        
        for rec in recommendations:
            print(f"\\n🎯 {rec['use_case']}")
            print(f"   Recommended: {rec['best_retriever']}")
            print(f"   Reason: {rec['reason']}")
    
    async def run_comparison_demo(self):
        """Run the complete retriever comparison demonstration."""
        print("🚀 RETRIEVER COMPARISON DEMO")
        print("=" * 40)
        
        try:
            await self.setup_embeddings()
            await self.load_test_documents()
            await self.prepare_data()
            await self.setup_vector_memory()
            await self.setup_retrievers()
            
            await self.test_query_types()
            await self.performance_analysis()
            await self.recommendations_and_use_cases()
            
            print("\\n✅ COMPARISON DEMO COMPLETE!")
            print("\\n📋 Key Takeaways:")
            print("   • Text retrievers excel at exact matches and speed")
            print("   • Semantic retrievers understand meaning and context")
            print("   • Composite retrievers provide balanced performance")
            print("   • Choose based on your specific use case and requirements")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Run the retriever comparison demo."""
    demo = RetrieverComparisonDemo()
    await demo.run_comparison_demo()

if __name__ == "__main__":
    print("🔍 AgenticFlow Retriever Comparison Demo")
    print("This demo compares different retriever types on the same dataset")
    print()
    print("Requirements:")
    print("- OPENAI_API_KEY or Ollama with 'nomic-embed-text' model")
    print()
    
    asyncio.run(main())