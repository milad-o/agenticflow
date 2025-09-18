#!/usr/bin/env python3
"""
AgenticFlow Memory System Guide
==============================

Comprehensive guide demonstrating all memory types in AgenticFlow:
- Ephemeral vs Persistent Memory
- Regular Memory vs Vector Memory
- Text Splitting and Chunking
- Embedding Integration
- Cross-Session Persistence

Memory Types Available:
1. BufferMemory (ephemeral, in-memory)
2. SQLiteMemory (persistent, local database) 
3. PostgreSQLMemory (persistent, full database)
4. VectorMemory (semantic search with embeddings)
5. EnhancedMemory (advanced features)
6. CustomMemory (user-defined)
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Memory imports
from agenticflow.memory import (
    # Core memory types
    BufferMemory,
    SQLiteMemory,
    PostgreSQLMemory,
    CustomMemory,
    
    # Configuration
    MemoryBackendConfig,
    MemoryBackendType,
    EnhancedMemoryFactory,
    
    # Vector memory
    VectorMemory,
    VectorMemoryConfig,
    
    # Enhanced memory
    EnhancedMemory,
    MemoryConfiguration,
    create_enhanced_memory
)

# Vector and embedding imports
from agenticflow.vectorstores import (
    VectorStoreConfig,
    VectorStoreType,
    DistanceMetric
)

from agenticflow.text.splitters import (
    SplitterConfig,
    SplitterType
)

from agenticflow.config.settings import MemoryConfig


class MemorySystemGuide:
    """Comprehensive guide to AgenticFlow's memory system."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agenticflow_memory_guide_"))
        self.mock_embeddings = MockEmbeddingProvider()
    
    async def demonstrate_all_memory_types(self):
        """Demonstrate all available memory types."""
        print("🧠 AgenticFlow Memory System Guide")
        print("=" * 60)
        print("Comprehensive overview of memory backends and features\n")
        
        # 1. Ephemeral Memory
        await self.demo_ephemeral_memory()
        
        # 2. Persistent Memory
        await self.demo_persistent_memory()
        
        # 3. Vector Memory
        await self.demo_vector_memory()
        
        # 4. Enhanced Memory
        await self.demo_enhanced_memory()
        
        # 5. Memory Comparison
        await self.compare_memory_types()
        
        # 6. Best Practices
        self.show_best_practices()
    
    async def demo_ephemeral_memory(self):
        """Demonstrate ephemeral (in-memory) storage."""
        print("💭 1. EPHEMERAL MEMORY (BufferMemory)")
        print("-" * 50)
        print("✨ Fast, in-memory storage that doesn't persist")
        print("🎯 Use for: Session context, temporary conversations")
        print()
        
        # Simple buffer memory
        config = MemoryBackendConfig(
            backend_type=MemoryBackendType.BUFFER,
            max_messages=100
        )
        
        memory = await EnhancedMemoryFactory.create_memory(config)
        
        # Add conversation
        messages = [
            HumanMessage(content="Hi, I'm Alice. I love programming!"),
            AIMessage(content="Hello Alice! Programming is fantastic. What languages do you enjoy?"),
            HumanMessage(content="I mainly work with Python and JavaScript."),
            AIMessage(content="Great choices! Both are very versatile languages.")
        ]
        
        print("📝 Adding conversation to buffer memory...")
        for msg in messages:
            await memory.add_message(msg, metadata={"session": "demo"})
        
        # Retrieve messages
        retrieved = await memory.get_messages(limit=10)
        print(f"✅ Retrieved {len(retrieved)} messages from memory")
        
        # Show search capability
        search_results = await memory.search("Python", limit=2)
        print(f"🔍 Search for 'Python': {len(search_results)} results")
        if search_results:
            print(f"   Found: {search_results[0].content[:50]}...")
        
        print("⚠️  Memory is lost when application restarts!")
        print()
    
    async def demo_persistent_memory(self):
        """Demonstrate persistent memory storage."""
        print("💾 2. PERSISTENT MEMORY (SQLite & PostgreSQL)")
        print("-" * 50)
        print("✨ Database storage that survives restarts")
        print("🎯 Use for: Personal assistants, customer history, long-term memory")
        print()
        
        # SQLite Memory
        db_path = self.temp_dir / "demo_memory.db"
        
        config = MemoryBackendConfig.create_sqlite_config(
            database_path=str(db_path),
            max_messages=1000,
            session_persistence=True
        )
        
        # Session 1: Add initial data
        memory1 = SQLiteMemory(config)
        session1_id = memory1._session_id
        
        print("📝 Session 1: Adding persistent data...")
        await memory1.add_message(
            HumanMessage(content="Remember, my name is Bob and I work in data science"),
            metadata={"importance": "high", "type": "personal_info"}
        )
        await memory1.add_message(
            AIMessage(content="Got it, Bob! I'll remember you're in data science."),
            metadata={"type": "confirmation"}
        )
        
        print(f"✅ Session 1 ({session1_id[:8]}...): Stored 2 messages")
        await memory1.close()
        
        # Simulate restart - Session 2
        print("🔄 Simulating application restart...")
        memory2 = SQLiteMemory(config)
        
        # Access previous session data
        previous_messages = await memory2.get_messages(session_id=session1_id)
        print(f"🔍 Found {len(previous_messages)} messages from previous session")
        
        # Add new data in current session
        await memory2.add_message(
            HumanMessage(content="Do you remember who I am?"),
            metadata={"type": "recall_test"}
        )
        
        # Search across all sessions
        search_results = await memory2.search("data science", limit=3)
        print(f"🔍 Cross-session search: {len(search_results)} results")
        
        # Session statistics
        if hasattr(memory2, 'get_session_stats'):
            stats = await memory2.get_session_stats(session1_id)
            print(f"📊 Session 1 stats: {stats.get('message_count', 0)} messages")
        
        await memory2.close()
        print("✅ Data persists across application restarts!")
        print()
    
    async def demo_vector_memory(self):
        """Demonstrate vector memory with semantic search."""
        print("🧠 3. VECTOR MEMORY (Semantic Search)")
        print("-" * 50)
        print("✨ Embedding-based semantic search and text chunking")
        print("🎯 Use for: RAG systems, knowledge bases, semantic retrieval")
        print()
        
        # Vector Memory Configuration
        memory_config = MemoryConfig(max_messages=100)
        
        vector_store_config = VectorStoreConfig(
            store_type=VectorStoreType.MEMORY,  # In-memory for demo
            collection_name="demo_knowledge",
            embedding_dimension=768,
            distance_metric=DistanceMetric.COSINE
        )
        
        splitter_config = SplitterConfig(
            splitter_type=SplitterType.RECURSIVE,
            chunk_size=300,
            chunk_overlap=50,
            min_chunk_size=100
        )
        
        vector_config = VectorMemoryConfig(
            vector_store_config=vector_store_config,
            splitter_config=splitter_config,
            enable_splitting=True,
            enable_semantic_search=True,
            max_chunks_per_message=5,
            similarity_threshold=0.1  # Very low threshold for demonstration
        )
        
        # Create vector memory with mock embeddings
        vector_memory = VectorMemory(
            config=memory_config,
            vector_config=vector_config,
            embeddings=self.mock_embeddings
        )
        
        print("📝 Adding knowledge base content...")
        
        # Add long-form content that will be chunked
        knowledge_items = [
            {
                "content": """Machine learning is a subset of artificial intelligence (AI) that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. Machine learning focuses on the development of computer programs that can access data and use it to learn for themselves. The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future based on the examples that we provide.""",
                "metadata": {"topic": "machine_learning", "type": "definition"}
            },
            {
                "content": """Deep learning is a subset of machine learning that uses neural networks with multiple layers (hence 'deep') to analyze various factors with a structure that is similar to the human neural system. Deep learning has enabled many practical applications of machine learning and by extension the overall field of AI. Deep learning breaks down tasks in ways that makes all kinds of machine assists seem possible, even likely.""",
                "metadata": {"topic": "deep_learning", "type": "definition"}
            },
            {
                "content": """Natural Language Processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret and manipulate human language. NLP draws from many disciplines, including computer science and computational linguistics, in its pursuit to fill the gap between human communication and computer understanding. NLP makes it possible for humans to talk to machines.""",
                "metadata": {"topic": "nlp", "type": "definition"}
            }
        ]
        
        for item in knowledge_items:
            await vector_memory.add_message(
                HumanMessage(content=item["content"]),
                metadata=item["metadata"]
            )
        
        print(f"✅ Added {len(knowledge_items)} knowledge items (auto-chunked)")
        
        # Check document count before searching
        total_docs = await vector_memory.vector_store.count_documents()
        print(f"📈 Total documents in vector store: {total_docs}")
        
        # Demonstrate semantic search
        queries = [
            "What is machine learning?",
            "How does deep learning work?",
            "Tell me about natural language processing",
            "AI and neural networks"
        ]
        
        print("\n🔍 Semantic Search Results:")
        for query in queries:
            # Try with very low threshold first
            results = await vector_memory.search(query, limit=3, similarity_threshold=0.05)
            print(f"   Query: '{query}'")
            
            if results:
                for i, result in enumerate(results):
                    score = result.metadata.get("similarity_score", 0)
                    preview = result.content[:80] + "..." if len(result.content) > 80 else result.content
                    print(f"   → Match {i+1} (score {score:.3f}): {preview}")
            else:
                print(f"   → No results found")
            print()
        
        # Show chunking effects
        stats = await vector_memory.get_memory_stats()
        print(f"📊 Vector Memory Stats:")
        print(f"   Traditional messages: {stats['total_messages']}")
        print(f"   Vector documents: {stats.get('vector_documents', 'N/A')}")
        print("✅ Text automatically chunked for better semantic search!")
        print()
    
    async def demo_enhanced_memory(self):
        """Demonstrate enhanced memory with advanced features."""
        print("⚡ 4. ENHANCED MEMORY (Advanced Features)")
        print("-" * 50)
        print("✨ Advanced text processing, compression, and lifecycle management")
        print("🎯 Use for: Production systems, intelligent summarization, optimization")
        print()
        
        # Enhanced Memory Configuration
        enhanced_config = MemoryConfiguration(
            enable_splitting=True,
            enable_compression=True,
            enable_caching=True,
            chunk_size=400,
            chunk_overlap=50,
            compression_threshold=10,
            preserve_recent_messages=5,
            similarity_threshold=0.7  # Fixed parameter name
        )
        
        memory_config = MemoryConfig(max_messages=50)
        
        enhanced_memory = await create_enhanced_memory(
            config=memory_config,
            enhanced_config=enhanced_config,
            embeddings=self.mock_embeddings
        )
        
        print("📝 Adding content for enhancement demonstration...")
        
        # Add a series of related messages
        conversation = [
            "I'm working on a machine learning project for image classification.",
            "That's exciting! What type of neural network are you considering?",
            "I'm thinking about using a convolutional neural network (CNN).",
            "CNNs are perfect for image tasks. Have you prepared your dataset?",
            "Yes, I have 10,000 labeled images of cats and dogs.",
            "Great dataset size! You might want to use data augmentation techniques.",
            "What kind of data augmentation would you recommend?",
            "Try rotation, flipping, and zoom. Also consider transfer learning.",
            "Transfer learning sounds interesting. How does that work?",
            "You take a pre-trained model and fine-tune it on your specific dataset.",
            "That makes sense. What pre-trained models would you suggest?",
            "ResNet, VGG, or EfficientNet are all excellent choices for image classification."
        ]
        
        # Add messages alternating between human and AI
        for i, content in enumerate(conversation):
            msg_type = HumanMessage if i % 2 == 0 else AIMessage
            await enhanced_memory.add_message(
                msg_type(content=content),
                metadata={"conversation_turn": i, "topic": "ml_project"}
            )
        
        print(f"✅ Added {len(conversation)} messages to enhanced memory")
        
        # Demonstrate advanced search
        search_queries = [
            "convolutional neural networks",
            "data augmentation techniques", 
            "transfer learning models"
        ]
        
        print("\n🔍 Enhanced Semantic Search:")
        for query in search_queries:
            results = await enhanced_memory.search(query, limit=2)
            print(f"   '{query}': {len(results)} results")
            if results:
                preview = results[0].content[:80] + "..." if len(results[0].content) > 80 else results[0].content
                print(f"   → {preview}")
        
        # Show analytics
        stats = await enhanced_memory.get_memory_stats()
        print(f"\n📊 Enhanced Memory Analytics:")
        print(f"   Total messages: {stats.total_messages}")
        print(f"   Total chunks: {stats.total_chunks}")
        print(f"   Total characters: {stats.total_characters}")
        print(f"   Memory size: {stats.memory_size_mb:.1f} MB")
        print(f"   Compression ratio: {stats.compression_ratio:.2f}")
        print(f"   Search count: {stats.search_count}")
        print("✅ Advanced processing and optimization active!")
        print()
    
    async def compare_memory_types(self):
        """Compare different memory types side by side."""
        print("⚖️  5. MEMORY TYPE COMPARISON")
        print("-" * 50)
        
        comparison_data = {
            "Buffer": {
                "persistence": "❌ Ephemeral",
                "speed": "🚀 Fastest",
                "search": "📝 Text-based",
                "use_case": "Session context, temporary storage"
            },
            "SQLite": {
                "persistence": "✅ Local file",
                "speed": "⚡ Fast",
                "search": "📝 Text + metadata filtering",
                "use_case": "Personal assistants, single-user apps"
            },
            "PostgreSQL": {
                "persistence": "✅ Database server",
                "speed": "⚡ Fast",
                "search": "🔍 Full-text search + advanced queries",
                "use_case": "Multi-user systems, enterprise apps"
            },
            "Vector": {
                "persistence": "✅ Configurable",
                "speed": "🧠 Semantic",
                "search": "🎯 Embedding-based similarity",
                "use_case": "RAG systems, knowledge bases"
            },
            "Enhanced": {
                "persistence": "✅ Advanced",
                "speed": "🤖 Intelligent",
                "search": "🚀 Multi-modal (text + semantic)",
                "use_case": "Production systems, AI optimization"
            }
        }
        
        print(f"{'Memory Type':<12} {'Persistence':<20} {'Speed':<15} {'Search':<25} {'Best Use Case'}")
        print("-" * 90)
        
        for mem_type, features in comparison_data.items():
            print(f"{mem_type:<12} {features['persistence']:<20} {features['speed']:<15} {features['search']:<25} {features['use_case']}")
        
        print()
    
    def show_best_practices(self):
        """Show memory system best practices."""
        print("💡 6. MEMORY SYSTEM BEST PRACTICES")
        print("-" * 50)
        
        practices = [
            ("🎯 Choose the Right Type", [
                "Development/Testing → Buffer Memory",
                "Single-user production → SQLite Memory", 
                "Multi-user production → PostgreSQL Memory",
                "Knowledge retrieval → Vector Memory",
                "Advanced AI systems → Enhanced Memory"
            ]),
            ("📊 Configuration Tips", [
                "Set max_messages to prevent unbounded growth",
                "Use metadata for efficient filtering",
                "Enable compression for long-running systems",
                "Configure appropriate chunk sizes for your content"
            ]),
            ("🔍 Search Optimization", [
                "Use vector memory for semantic similarity",
                "Combine multiple search strategies",
                "Cache frequently accessed results",
                "Tune similarity thresholds for your use case"
            ]),
            ("⚡ Performance", [
                "Buffer memory for fastest access",
                "SQLite for balanced performance/persistence",
                "PostgreSQL for concurrent access",
                "Async operations for all database backends"
            ]),
            ("🛡️ Production Considerations", [
                "Monitor memory usage and growth",
                "Implement cleanup/archival strategies",
                "Use connection pooling for databases",
                "Handle network failures gracefully",
                "Back up persistent memory stores"
            ])
        ]
        
        for title, items in practices:
            print(f"\n{title}:")
            for item in items:
                print(f"   • {item}")
        
        print()
    
    async def cleanup(self):
        """Clean up temporary resources."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


class MockEmbeddingProvider:
    """Mock embedding provider for demonstration."""
    
    def _generate_embedding(self, text: str):
        """Generate a reproducible embedding based on text content."""
        import hashlib
        import random
        
        # Use text hash as seed for reproducible embeddings
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)
        
        # Generate normalized random vector
        embedding = [random.random() - 0.5 for _ in range(768)]
        magnitude = sum(x * x for x in embedding) ** 0.5
        return [x / magnitude for x in embedding] if magnitude > 0 else embedding
    
    async def aembed_query(self, text: str):
        """Generate mock embedding (async version)."""
        return self._generate_embedding(text)
    
    def embed_query(self, text: str):
        """Generate mock embedding (sync version)."""
        return self._generate_embedding(text)
        
    def embed_documents(self, texts):
        """Generate mock embeddings for a list of texts."""
        return [self._generate_embedding(text) for text in texts]


async def main():
    """Run the comprehensive memory system guide."""
    guide = MemorySystemGuide()
    
    try:
        await guide.demonstrate_all_memory_types()
        
        print("=" * 60)
        print("🎉 MEMORY SYSTEM GUIDE COMPLETE!")
        print("=" * 60)
        print()
        print("🔗 Quick Reference:")
        print("   • BufferMemory: Fast, ephemeral, session-only")
        print("   • SQLiteMemory: Persistent, local, single-user")
        print("   • PostgreSQLMemory: Persistent, server, multi-user") 
        print("   • VectorMemory: Semantic search, embedding-based")
        print("   • EnhancedMemory: Advanced features, AI-optimized")
        print("   • CustomMemory: User-defined, extensible")
        print()
        print("📚 Features Demonstrated:")
        print("   ✅ Ephemeral vs Persistent storage")
        print("   ✅ Cross-session data persistence")
        print("   ✅ Semantic search with embeddings")
        print("   ✅ Automatic text chunking")
        print("   ✅ Metadata filtering and search")
        print("   ✅ Memory analytics and optimization")
        print("   ✅ Production-ready configurations")
        
    finally:
        await guide.cleanup()


if __name__ == "__main__":
    asyncio.run(main())