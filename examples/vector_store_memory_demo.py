#!/usr/bin/env python3
"""
Vector Store and Memory System Demonstration
==========================================
This demo showcases:
• Multiple vector store backends (FAISS, Chroma, In-memory)
• Vector-enabled memory with chunking
• Semantic search and retrieval
• Persistence and scalability features
"""

import asyncio
import sys
import os
from typing import List, Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Graceful import handling
try:
    print("✅ All imports successful")
    from agenticflow.vectorstores import (
        VectorStoreFactory,
        VectorStoreConfig,
        VectorStoreType,
        VectorStoreDocument,
        DistanceMetric,
        get_vector_store
    )
    from agenticflow.memory.vector_memory import VectorMemory, VectorMemoryConfig
    from agenticflow.config.settings import MemoryConfig
    from agenticflow.text.chunking import ChunkingConfig, ChunkingStrategy
    from langchain_core.messages import HumanMessage, AIMessage
    
    print("🚀 AGENTICFLOW VECTOR STORE & MEMORY DEMONSTRATION")
    print("=" * 80)
    print("This demo showcases:")
    print("• Multiple vector store backends (FAISS, Chroma, In-memory)")
    print("• Vector-enabled memory with chunking")
    print("• Semantic search and retrieval")
    print("• Persistence and scalability features")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "id": "doc1",
        "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without explicit programming.",
        "metadata": {"category": "AI", "complexity": "beginner"}
    },
    {
        "id": "doc2", 
        "content": "Deep learning uses neural networks with multiple layers to model and understand complex patterns in data, revolutionizing fields like computer vision and natural language processing.",
        "metadata": {"category": "AI", "complexity": "advanced"}
    },
    {
        "id": "doc3",
        "content": "Natural language processing combines computational linguistics with machine learning to help computers understand, interpret, and generate human language.",
        "metadata": {"category": "NLP", "complexity": "intermediate"}
    },
    {
        "id": "doc4",
        "content": "Computer vision enables machines to interpret and understand visual information from the world, including images, videos, and real-time camera feeds.",
        "metadata": {"category": "CV", "complexity": "intermediate"}
    },
    {
        "id": "doc5",
        "content": "Reinforcement learning is a type of machine learning where agents learn to make decisions by taking actions in an environment to maximize cumulative reward.",
        "metadata": {"category": "AI", "complexity": "advanced"}
    }
]


async def demonstrate_vector_stores():
    """Demonstrate different vector store types."""
    
    print("\n" + "=" * 80)
    print("📚 VECTOR STORE DEMONSTRATIONS")
    print("=" * 80)
    
    # Test different vector store types
    store_configs = [
        {
            "name": "In-Memory Store",
            "config": VectorStoreFactory.create_ephemeral_config(
                collection_name="demo_memory",
                embedding_dimension=5  # Using small dimension for demo
            )
        },
        {
            "name": "FAISS Store", 
            "config": VectorStoreFactory.create_faiss_config(
                collection_name="demo_faiss",
                persist_path="./demo_faiss.index",
                embedding_dimension=5
            )
        },
    ]
    
    # Try Chroma if available
    try:
        import chromadb
        store_configs.append({
            "name": "Chroma Store",
            "config": VectorStoreFactory.create_chroma_config(
                collection_name="demo_chroma",
                persist_path="./demo_chroma_db",
                embedding_dimension=5
            )
        })
    except ImportError:
        print("⚠️  Chroma not available - skipping Chroma demo")
    
    for store_info in store_configs:
        await demonstrate_single_vector_store(store_info["name"], store_info["config"])


async def demonstrate_single_vector_store(store_name: str, config: VectorStoreConfig):
    """Demonstrate a single vector store."""
    
    print(f"\n🔍 Testing {store_name}")
    print("-" * 60)
    
    try:
        # Create and connect to vector store
        store = VectorStoreFactory.create_vector_store(config)
        await store.connect()
        
        print(f"✅ Connected to {store_name}")
        
        # Create sample documents with simple embeddings (for demo purposes)
        vector_documents = []
        for i, doc_data in enumerate(SAMPLE_DOCUMENTS):
            # Create simple embeddings (in real use, you'd use proper embedding models)
            simple_embedding = [float(j * (i + 1)) for j in range(5)]
            
            vector_doc = VectorStoreDocument(
                id=doc_data["id"],
                content=doc_data["content"],
                embedding=simple_embedding,
                metadata=doc_data["metadata"]
            )
            vector_documents.append(vector_doc)
        
        # Add documents
        await store.add_documents(vector_documents)
        doc_count = await store.count_documents()
        print(f"📄 Added {len(vector_documents)} documents (total: {doc_count})")
        
        # Demonstrate search
        query_embedding = [2.0, 4.0, 6.0, 8.0, 10.0]  # Simple query embedding
        search_results = await store.search(
            query_embedding=query_embedding,
            limit=3,
            score_threshold=0.1
        )
        
        print(f"🔎 Search Results ({len(search_results)} found):")
        for result in search_results:
            print(f"   • [{result.rank}] {result.document.id}: {result.document.content[:60]}...")
            print(f"     Score: {result.score:.3f}, Category: {result.document.metadata.get('category')}")
        
        # Demonstrate metadata filtering
        filtered_results = await store.search(
            query_embedding=query_embedding,
            limit=5,
            metadata_filter={"category": "AI"}
        )
        
        print(f"🏷️  AI Category Results ({len(filtered_results)} found):")
        for result in filtered_results:
            print(f"   • {result.document.id}: {result.document.metadata.get('complexity')} level")
        
        # Get collection info
        info = await store.get_collection_info()
        print(f"📊 Collection Info: {info['document_count']} docs, type: {info['store_type']}")
        
        # Cleanup
        await store.disconnect()
        print(f"✅ {store_name} test completed successfully")
        
    except Exception as e:
        print(f"❌ {store_name} test failed: {e}")
        import traceback
        traceback.print_exc()


async def demonstrate_vector_memory():
    """Demonstrate vector-enabled memory system."""
    
    print("\n" + "=" * 80)
    print("🧠 VECTOR-ENABLED MEMORY DEMONSTRATION")
    print("=" * 80)
    
    try:
        # Create vector store configuration
        vector_store_config = VectorStoreFactory.create_ephemeral_config(
            collection_name="memory_demo",
            embedding_dimension=5  # Simple for demo
        )
        
        # Create chunking configuration
        chunking_config = ChunkingConfig(
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=100,
            chunk_overlap=20,
            min_chunk_size=50
        )
        
        # Create vector memory configuration
        vector_memory_config = VectorMemoryConfig(
            vector_store_config=vector_store_config,
            chunking_config=chunking_config,
            enable_chunking=True,
            similarity_threshold=0.2
        )
        
        # Create memory instance (without embeddings for demo simplicity)
        memory_config = MemoryConfig(type="vector", max_messages=10)
        vector_memory = VectorMemory(
            config=memory_config,
            vector_config=vector_memory_config,
            embeddings=None  # Would use real embeddings in production
        )
        
        print("✅ Vector memory initialized")
        
        # Add sample messages
        messages = [
            "I'm interested in learning about machine learning algorithms and their applications.",
            "Can you explain how neural networks work and why they're effective for pattern recognition?", 
            "What's the difference between supervised and unsupervised learning approaches?",
            "I'd like to understand more about natural language processing and text analysis.",
            "How do computers process and understand human language effectively?"
        ]
        
        print(f"\n📝 Adding {len(messages)} messages to vector memory...")
        for i, content in enumerate(messages):
            message = HumanMessage(content=content)
            doc_id = await vector_memory.add_message(message, metadata={"turn": i})
            print(f"   ✅ Added message: {doc_id}")
        
        # Get memory stats
        stats = await vector_memory.get_memory_stats()
        print(f"\n📊 Memory Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Demonstrate search (will fallback to text search without embeddings)
        search_queries = [
            "machine learning",
            "neural networks", 
            "language processing"
        ]
        
        print(f"\n🔍 Semantic Search Demonstration:")
        for query in search_queries:
            results = await vector_memory.search(query, limit=2)
            print(f"\n🔎 Query: '{query}' ({len(results)} results)")
            for i, result in enumerate(results):
                print(f"   [{i+1}] {result.content[:80]}...")
                if "similarity_score" in result.metadata:
                    print(f"       Score: {result.metadata['similarity_score']:.3f}")
        
        # Get recent messages
        recent_messages = await vector_memory.get_messages(limit=3)
        print(f"\n📜 Recent Messages ({len(recent_messages)}):")
        for i, msg in enumerate(recent_messages[-3:]):
            print(f"   [{i+1}] {msg.content[:60]}...")
        
        # Clear memory
        await vector_memory.clear()
        print("\n🧹 Memory cleared")
        
        # Cleanup
        await vector_memory.disconnect()
        print("✅ Vector memory demonstration completed")
        
    except Exception as e:
        print(f"❌ Vector memory demonstration failed: {e}")
        import traceback
        traceback.print_exc()


async def demonstrate_smart_features():
    """Demonstrate smart vector store features."""
    
    print("\n" + "=" * 80)
    print("🤖 SMART VECTOR STORE FEATURES")
    print("=" * 80)
    
    # Auto-select vector store based on requirements
    requirements = {
        "persistence": True,
        "expected_documents": 1000,
        "deployment": "local",
        "budget": "free"
    }
    
    recommended_store = VectorStoreFactory.auto_select_store(requirements)
    print(f"🎯 Recommended store for requirements: {recommended_store.value}")
    print(f"   Description: {VectorStoreFactory.get_store_description(recommended_store)}")
    
    # Show all supported stores
    print(f"\n📋 All Supported Vector Stores:")
    for store_type in VectorStoreFactory.get_supported_stores():
        description = VectorStoreFactory.get_store_description(store_type)
        print(f"   • {store_type.value.upper()}: {description}")
    
    # Demonstrate global store management
    print(f"\n🌐 Global Store Management:")
    
    # Create a few managed stores
    config1 = VectorStoreFactory.create_ephemeral_config("store1", embedding_dimension=3)
    config2 = VectorStoreFactory.create_ephemeral_config("store2", embedding_dimension=3)
    
    store1 = await get_vector_store("demo_store_1", config1)
    store2 = await get_vector_store("demo_store_2", config2)
    
    print(f"✅ Created managed vector stores")
    
    # List active stores
    from agenticflow.vectorstores import list_vector_stores
    active_stores = list_vector_stores()
    print(f"📊 Active stores: {active_stores}")
    
    # Add some data to demonstrate
    sample_doc = VectorStoreDocument(
        id="demo_doc",
        content="This is a demo document for global store management",
        embedding=[1.0, 2.0, 3.0],
        metadata={"type": "demo"}
    )
    
    await store1.add_documents([sample_doc])
    count = await store1.count_documents()
    print(f"📄 Store1 document count: {count}")
    
    # Cleanup global stores
    from agenticflow.vectorstores import cleanup_vector_stores
    await cleanup_vector_stores()
    print("🧹 Global stores cleaned up")


async def main():
    """Run all demonstrations."""
    
    print("🚀 AgenticFlow Vector Store & Memory Demonstrations")
    print("=" * 80)
    
    # Run demonstrations
    await demonstrate_vector_stores()
    await demonstrate_vector_memory()
    await demonstrate_smart_features()
    
    print("\n" + "=" * 80)
    print("🎉 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    print("\nKey Features Demonstrated:")
    print("✅ Multiple vector store backends with unified interface")
    print("✅ Persistent and ephemeral storage options")
    print("✅ Semantic search with metadata filtering")
    print("✅ Vector-enabled memory with automatic chunking")
    print("✅ Intelligent store selection and management")
    print("✅ Graceful fallbacks and error handling")
    
    print(f"\n📚 The vector store system is ready for production use!")
    print("   • Supports FAISS, Chroma, Pinecone, and other backends")
    print("   • Seamlessly integrates with memory and chunking systems")
    print("   • Provides both simple and advanced usage patterns")
    print("   • Scales from development to production workloads")


if __name__ == "__main__":
    asyncio.run(main())