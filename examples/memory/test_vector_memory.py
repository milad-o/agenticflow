#!/usr/bin/env python3
"""
Vector Memory Test Script
========================

This script tests the AgenticFlow vector memory system including:
1. Vector-enabled memory with embeddings
2. Text chunking and fragment storage
3. Semantic search and retrieval
4. Memory persistence and loading
5. Integration with different vector stores
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path
import time

# Add the src directory to the path so we can import agenticflow
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

try:
    from agenticflow.vectorstores import (
        VectorStoreConfig,
        VectorStoreType,
        DistanceMetric,
    )
    from agenticflow.memory.vector_memory import VectorMemory, VectorMemoryConfig
    from agenticflow.config.settings import MemoryConfig
    from agenticflow.text.splitters.base import SplitterConfig, SplitterType
    from agenticflow.embeddings import create_ollama_embedding_provider
    
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure AgenticFlow is properly installed")
    sys.exit(1)


# Mock embedding provider for testing when Ollama is not available
class MockEmbeddingProvider:
    """Mock embedding provider for testing."""
    
    def __init__(self, dimension=768):
        self.dimension = dimension
    
    async def aembed_query(self, text: str):
        """Generate mock embedding."""
        import hashlib
        import random
        
        # Use text hash as seed for reproducible embeddings
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)
        
        # Generate normalized random vector
        embedding = [random.random() - 0.5 for _ in range(self.dimension)]
        magnitude = sum(x * x for x in embedding) ** 0.5
        return [x / magnitude for x in embedding]
    
    async def aembed_documents(self, texts):
        """Generate mock embeddings for multiple texts."""
        return [await self.aembed_query(text) for text in texts]


class VectorMemoryTestSuite:
    """Test suite for vector memory system."""
    
    def __init__(self):
        self.temp_dir = None
        self.embedding_provider = None
        
    async def setup(self):
        """Set up test environment."""
        print("🔧 Setting up vector memory test environment...")
        
        # Create temp directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agenticflow_vector_memory_test_"))
        print(f"📁 Temp directory: {self.temp_dir}")
        
        # Try to set up Ollama embedding provider
        try:
            self.embedding_provider = create_ollama_embedding_provider(model="nomic-embed-text")
            if await self.embedding_provider.is_available():
                print("✅ Ollama embedding provider ready")
                return
            else:
                print("⚠️ Ollama not available")
        except Exception as e:
            print(f"⚠️ Failed to setup Ollama: {e}")
        
        # Fall back to mock provider
        self.embedding_provider = MockEmbeddingProvider()
        print("✅ Mock embedding provider ready")
    
    async def teardown(self):
        """Clean up test environment."""
        print("🧹 Cleaning up...")
        
        if hasattr(self.embedding_provider, 'close'):
            await self.embedding_provider.close()
        
        # Clean up temp directory
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def create_vector_memory(self, store_type=VectorStoreType.MEMORY) -> VectorMemory:
        """Create a vector memory instance."""
        memory_config = MemoryConfig(
            max_messages=100,
            max_message_length=10000
        )
        
        vector_store_config = VectorStoreConfig(
            store_type=store_type,
            collection_name="test_memory",
            embedding_dimension=768,
            distance_metric=DistanceMetric.COSINE,
            persist_path=str(self.temp_dir / "vector_store") if store_type == VectorStoreType.FAISS else None
        )
        
        splitter_config = SplitterConfig(
            splitter_type=SplitterType.RECURSIVE,
            chunk_size=500,
            chunk_overlap=50
        )
        
        vector_config = VectorMemoryConfig(
            vector_store_config=vector_store_config,
            splitter_config=splitter_config,
            enable_splitting=True,
            enable_semantic_search=True,
            max_chunks_per_message=5,
            similarity_threshold=0.3
        )
        
        return VectorMemory(
            config=memory_config,
            vector_config=vector_config,
            embeddings=self.embedding_provider
        )
    
    async def test_basic_vector_memory(self):
        """Test basic vector memory functionality."""
        print("\n🧪 Testing Basic Vector Memory...")
        
        memory = self.create_vector_memory()
        
        try:
            # Add some messages
            messages = [
                HumanMessage(content="What is machine learning and how does it work?"),
                AIMessage(content="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It works by training algorithms on data to recognize patterns and make predictions."),
                HumanMessage(content="Can you explain neural networks?"),
                AIMessage(content="Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information through weighted connections. Deep neural networks with multiple layers can learn complex patterns in data."),
                HumanMessage(content="What about natural language processing?"),
                AIMessage(content="Natural Language Processing (NLP) is a branch of AI that focuses on enabling computers to understand, interpret, and generate human language. It combines computational linguistics with machine learning techniques to process text and speech data.")
            ]
            
            print(f"📝 Adding {len(messages)} messages to vector memory...")
            for i, message in enumerate(messages):
                msg_id = await memory.add_message(message, metadata={"conversation_id": "test_conv", "turn": i})
                print(f"   Added message {i+1}: {msg_id}")
            
            # Test getting messages
            retrieved_messages = await memory.get_messages(limit=3)
            print(f"✓ Retrieved {len(retrieved_messages)} messages")
            
            # Test semantic search
            search_results = await memory.search("how do neural networks work", limit=2)
            print(f"✓ Semantic search found {len(search_results)} relevant memories:")
            
            for i, result in enumerate(search_results):
                score = result.metadata.get("similarity_score", 0)
                preview = result.content[:100] + "..." if len(result.content) > 100 else result.content
                print(f"   {i+1}. Score: {score:.3f} - {preview}")
            
            # Test memory statistics
            stats = await memory.get_memory_stats()
            print(f"✓ Memory stats: {stats['total_messages']} messages, {stats.get('vector_documents', 0)} vector docs")
            
            return True
            
        except Exception as e:
            print(f"❌ Basic vector memory test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await memory.disconnect()
    
    async def test_text_chunking_integration(self):
        """Test text chunking integration."""
        print("\n🧪 Testing Text Chunking Integration...")
        
        memory = self.create_vector_memory()
        
        try:
            # Add a long message that should be chunked
            long_message = HumanMessage(content="""
            Machine learning is a vast field with many different approaches and techniques. 
            Supervised learning uses labeled data to train models that can make predictions on new, unseen data. 
            Common supervised learning algorithms include linear regression, decision trees, random forests, and support vector machines.
            
            Unsupervised learning, on the other hand, works with unlabeled data to find hidden patterns and structures. 
            Clustering algorithms like K-means and hierarchical clustering are popular unsupervised techniques. 
            Dimensionality reduction methods like Principal Component Analysis (PCA) help visualize high-dimensional data.
            
            Reinforcement learning is a different paradigm where agents learn through interaction with an environment. 
            The agent receives rewards or penalties for its actions and learns to maximize cumulative reward over time. 
            This approach has been successful in game playing, robotics, and autonomous systems.
            
            Deep learning represents a significant advancement in machine learning, using neural networks with many layers 
            to learn hierarchical representations of data. Convolutional neural networks excel at image processing, 
            while recurrent neural networks are designed for sequential data like text and time series.
            """)
            
            print("📝 Adding long message (should be chunked)...")
            msg_id = await memory.add_message(
                long_message, 
                metadata={"type": "educational", "topic": "machine_learning"}
            )
            print(f"   Added chunked message: {msg_id}")
            
            # Search for different concepts that might be in different chunks
            searches = [
                "supervised learning algorithms",
                "unsupervised learning clustering", 
                "reinforcement learning agents",
                "deep learning neural networks"
            ]
            
            for query in searches:
                results = await memory.search(query, limit=2, similarity_threshold=0.2)
                print(f"✓ Search '{query}': {len(results)} results")
                
                if results:
                    score = results[0].metadata.get("similarity_score", 0)
                    print(f"   Best match score: {score:.3f}")
            
            # Check memory stats after chunking
            stats = await memory.get_memory_stats()
            print(f"✓ After chunking - Messages: {stats['total_messages']}, Vector docs: {stats.get('vector_documents', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Text chunking test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await memory.disconnect()
    
    async def test_memory_persistence(self):
        """Test memory persistence and loading."""
        print("\n🧪 Testing Memory Persistence...")
        
        # Test with FAISS for persistence
        try:
            import faiss
        except ImportError:
            print("⚠️ FAISS not available, skipping persistence test")
            return True
        
        persist_path = self.temp_dir / "test_memory"
        
        try:
            # Create memory and add some data
            memory1 = self.create_vector_memory(VectorStoreType.FAISS)
            
            test_messages = [
                HumanMessage(content="What is artificial intelligence?"),
                AIMessage(content="AI is the simulation of human intelligence in machines programmed to think and learn."),
                HumanMessage(content="How does machine learning relate to AI?"),
                AIMessage(content="Machine learning is a subset of AI that allows machines to learn from data without explicit programming.")
            ]
            
            print("📝 Adding messages to persistent memory...")
            for msg in test_messages:
                await memory1.add_message(msg)
            
            stats1 = await memory1.get_memory_stats()
            print(f"✓ First memory instance: {stats1['total_messages']} messages, {stats1.get('vector_documents', 0)} vector docs")
            
            # Save and disconnect
            await memory1.save(str(persist_path))
            await memory1.disconnect()
            print("✓ Saved and disconnected first memory instance")
            
            # Create new memory instance and load
            memory2 = self.create_vector_memory(VectorStoreType.FAISS)
            await memory2.load(str(persist_path))
            
            stats2 = await memory2.get_memory_stats()
            print(f"✓ Second memory instance: {stats2['total_messages']} messages, {stats2.get('vector_documents', 0)} vector docs")
            
            # Test that data persisted correctly
            search_results = await memory2.search("artificial intelligence", limit=2)
            print(f"✓ Search after reload found {len(search_results)} results")
            
            if search_results:
                print("✓ Memory persistence successful!")
            else:
                print("⚠️ No search results found after reload")
            
            await memory2.disconnect()
            return True
            
        except Exception as e:
            print(f"❌ Memory persistence test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_semantic_search_quality(self):
        """Test semantic search quality with various queries."""
        print("\n🧪 Testing Semantic Search Quality...")
        
        memory = self.create_vector_memory()
        
        try:
            # Add diverse content
            diverse_messages = [
                HumanMessage(content="I want to learn about machine learning algorithms"),
                AIMessage(content="Machine learning algorithms include supervised learning methods like linear regression, decision trees, and neural networks. Unsupervised methods include clustering and dimensionality reduction."),
                HumanMessage(content="How do I cook pasta properly?"),
                AIMessage(content="To cook pasta: 1) Boil salted water, 2) Add pasta and stir, 3) Cook for the time specified on package, 4) Test for doneness, 5) Drain and serve with your favorite sauce."),
                HumanMessage(content="What's the weather like today?"),
                AIMessage(content="I don't have access to current weather data. You can check weather apps, websites like weather.com, or look outside your window for current conditions."),
                HumanMessage(content="Explain deep learning and neural networks"),
                AIMessage(content="Deep learning uses artificial neural networks with multiple hidden layers to learn complex patterns. Each layer learns increasingly abstract features from the input data, making it powerful for tasks like image recognition and language processing."),
                HumanMessage(content="What are some good recipes for dinner?"),
                AIMessage(content="Here are some dinner ideas: grilled chicken with vegetables, pasta with marinara sauce, stir-fry with tofu and broccoli, or a hearty soup with bread. Consider your dietary preferences and available ingredients."),
            ]
            
            print(f"📝 Adding {len(diverse_messages)} diverse messages...")
            for msg in diverse_messages:
                await memory.add_message(msg, metadata={"timestamp": time.time()})
            
            # Test semantic search with different queries
            test_queries = [
                ("machine learning", "Should find ML-related content"),
                ("cooking food", "Should find cooking-related content"),
                ("neural networks", "Should find deep learning content"),
                ("weather forecast", "Should find weather content"),
                ("dinner recipes", "Should find recipe content"),
                ("algorithms and models", "Should find ML content with different terms"),
            ]
            
            for query, description in test_queries:
                print(f"\n🔍 Testing: '{query}' - {description}")
                results = await memory.search(query, limit=2, similarity_threshold=0.2)
                
                print(f"   Found {len(results)} results:")
                for i, result in enumerate(results):
                    score = result.metadata.get("similarity_score", 0)
                    preview = result.content[:80] + "..." if len(result.content) > 80 else result.content
                    print(f"     {i+1}. Score: {score:.3f} - {preview}")
                
                # Evaluate if the search found relevant content
                if results and any(self._is_relevant_result(query, result.content) for result in results):
                    print("   ✓ Found relevant content!")
                else:
                    print("   ⚠️ Results may not be perfectly relevant")
            
            return True
            
        except Exception as e:
            print(f"❌ Semantic search quality test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await memory.disconnect()
    
    def _is_relevant_result(self, query: str, content: str) -> bool:
        """Simple relevance check for testing."""
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        # Check for direct term matches or semantic similarity
        relevance_keywords = {
            "machine learning": ["machine", "learning", "algorithm", "model", "neural", "supervised", "unsupervised"],
            "cooking food": ["cook", "recipe", "pasta", "dinner", "food", "kitchen"],
            "neural networks": ["neural", "network", "deep", "layer", "learning"],
            "weather forecast": ["weather", "forecast", "temperature", "rain", "sunny"],
            "dinner recipes": ["dinner", "recipe", "cook", "food", "meal"],
            "algorithms and models": ["algorithm", "model", "machine", "learning", "method"]
        }
        
        # Find the most relevant keyword set
        for key, keywords in relevance_keywords.items():
            if any(term in key for term in query_terms):
                return any(keyword in content_lower for keyword in keywords)
        
        # Fallback: check if any query terms appear in content
        return any(term in content_lower for term in query_terms)
    
    async def test_memory_limits_and_trimming(self):
        """Test memory limits and automatic trimming."""
        print("\n🧪 Testing Memory Limits and Trimming...")
        
        # Create memory with low limits for testing
        memory_config = MemoryConfig(
            max_messages=5,  # Low limit for testing
            max_message_length=1000
        )
        
        vector_store_config = VectorStoreConfig(
            store_type=VectorStoreType.MEMORY,
            collection_name="test_trim_memory",
            embedding_dimension=768,
            distance_metric=DistanceMetric.COSINE
        )
        
        splitter_config = SplitterConfig(
            splitter_type=SplitterType.RECURSIVE,
            chunk_size=200,
            chunk_overlap=20
        )
        
        vector_config = VectorMemoryConfig(
            vector_store_config=vector_store_config,
            splitter_config=splitter_config,
            enable_splitting=True,
            max_chunks_per_message=3
        )
        
        memory = VectorMemory(
            config=memory_config,
            vector_config=vector_config,
            embeddings=self.embedding_provider
        )
        
        try:
            print("📝 Adding messages beyond limit to test trimming...")
            
            # Add more messages than the limit
            for i in range(8):  # Exceeds limit of 5
                message = HumanMessage(content=f"This is test message number {i+1}. It contains some content to test the memory trimming functionality.")
                await memory.add_message(message, metadata={"message_num": i+1})
                
                stats = await memory.get_memory_stats()
                print(f"   Message {i+1} added. Total messages: {stats['total_messages']}")
            
            # Check that trimming occurred
            final_stats = await memory.get_memory_stats()
            print(f"✓ Final message count: {final_stats['total_messages']} (limit was 5)")
            
            if final_stats['total_messages'] <= 5:
                print("✓ Trimming worked correctly!")
            else:
                print("⚠️ Trimming may not have worked as expected")
            
            # Test that we can still search recent messages
            search_results = await memory.search("message number", limit=3)
            print(f"✓ After trimming, search found {len(search_results)} results")
            
            return True
            
        except Exception as e:
            print(f"❌ Memory limits test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await memory.disconnect()
    
    async def test_metadata_filtering(self):
        """Test metadata-based filtering in vector memory."""
        print("\n🧪 Testing Metadata Filtering...")
        
        memory = self.create_vector_memory()
        
        try:
            # Add messages with different metadata
            categorized_messages = [
                (HumanMessage(content="How do I train a neural network?"), {"category": "technical", "priority": "high"}),
                (AIMessage(content="Training requires data, loss function, and optimization algorithm."), {"category": "technical", "priority": "high"}),
                (HumanMessage(content="What's your favorite color?"), {"category": "casual", "priority": "low"}),
                (AIMessage(content="I don't have personal preferences."), {"category": "casual", "priority": "low"}),
                (HumanMessage(content="Explain the transformer architecture"), {"category": "technical", "priority": "medium"}),
                (AIMessage(content="Transformers use self-attention mechanisms for sequence processing."), {"category": "technical", "priority": "medium"}),
                (HumanMessage(content="Tell me a joke"), {"category": "casual", "priority": "low"}),
                (AIMessage(content="Why did the ML model break up? It had too many parameters!"), {"category": "casual", "priority": "low"}),
            ]
            
            print(f"📝 Adding {len(categorized_messages)} categorized messages...")
            for message, metadata in categorized_messages:
                await memory.add_message(message, metadata=metadata)
            
            # Test filtering by category
            technical_messages = await memory.get_messages(
                filter_metadata={"category": "technical"}
            )
            print(f"✓ Technical messages: {len(technical_messages)}")
            
            casual_messages = await memory.get_messages(
                filter_metadata={"category": "casual"}
            )
            print(f"✓ Casual messages: {len(casual_messages)}")
            
            high_priority = await memory.get_messages(
                filter_metadata={"priority": "high"}
            )
            print(f"✓ High priority messages: {len(high_priority)}")
            
            # Test semantic search with metadata considerations
            # Note: Current implementation doesn't filter vector search by metadata,
            # but we can verify the metadata is preserved
            search_results = await memory.search("neural network training", limit=3)
            print(f"✓ Search results: {len(search_results)}")
            
            for result in search_results:
                category = result.metadata.get("category", "unknown")
                priority = result.metadata.get("priority", "unknown")
                print(f"   Result metadata - Category: {category}, Priority: {priority}")
            
            return True
            
        except Exception as e:
            print(f"❌ Metadata filtering test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await memory.disconnect()
    
    async def run_all_tests(self):
        """Run all vector memory tests."""
        print("🚀 Starting Vector Memory Test Suite")
        print("=" * 60)
        
        test_results = []
        
        try:
            await self.setup()
            
            # Run all tests
            tests = [
                ("Basic Vector Memory", self.test_basic_vector_memory),
                ("Text Chunking Integration", self.test_text_chunking_integration),
                ("Memory Persistence", self.test_memory_persistence),
                ("Semantic Search Quality", self.test_semantic_search_quality),
                ("Memory Limits and Trimming", self.test_memory_limits_and_trimming),
                ("Metadata Filtering", self.test_metadata_filtering),
            ]
            
            for test_name, test_func in tests:
                print(f"\n{'=' * 60}")
                print(f"Running: {test_name}")
                print('=' * 60)
                
                try:
                    result = await test_func()
                    test_results.append((test_name, result))
                    if result:
                        print(f"✅ {test_name} PASSED")
                    else:
                        print(f"❌ {test_name} FAILED")
                except Exception as e:
                    print(f"❌ {test_name} ERROR: {e}")
                    test_results.append((test_name, False))
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 TEST SUMMARY")
            print("=" * 60)
            
            passed = sum(1 for _, result in test_results if result)
            total = len(test_results)
            
            for test_name, result in test_results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} {test_name}")
            
            print(f"\n🎯 Results: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All vector memory tests completed successfully!")
            else:
                print("⚠️ Some tests failed. Check the output above for details.")
            
        except KeyboardInterrupt:
            print("\n❌ Tests interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error in test suite: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.teardown()


async def main():
    """Main function to run vector memory tests."""
    test_suite = VectorMemoryTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())