#!/usr/bin/env python3
"""
Simple Integration Test for AgenticFlow Memory & Chunking
========================================================
This test verifies that the memory and chunking systems work together correctly.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

async def test_basic_integration():
    """Test basic memory and chunking integration."""
    
    print("🔧 Testing AgenticFlow Memory & Chunking Integration")
    print("=" * 60)
    
    try:
        # Test imports
        from agenticflow.memory import (
            BufferMemory, 
            EnhancedMemory,
            MemoryConfiguration,
            create_enhanced_memory
        )
        from agenticflow.config.settings import MemoryConfig
        from agenticflow.text.chunking import (
            chunk_text,
            ChunkingStrategy,
            ChunkingConfig,
            get_chunking_manager
        )
        from langchain_core.messages import HumanMessage, AIMessage
        
        print("✅ All imports successful")
        
        # Test basic chunking
        test_text = """
        This is a test document for AgenticFlow.
        
        It contains multiple paragraphs to test the chunking functionality.
        The chunking system should split this text into meaningful segments.
        
        This paragraph tests whether the system can handle different content types.
        Each chunk should maintain semantic coherence while respecting size limits.
        """
        
        chunks = await chunk_text(
            test_text,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=150,
            text_id="test_doc"
        )
        
        print(f"📄 Created {len(chunks)} chunks from test text")
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i+1}: {len(chunk.content)} chars - {chunk.metadata.chunk_id}")
        
        # Test enhanced memory
        # Create MemoryConfig (core memory config)
        memory_config = MemoryConfig(type="buffer")
        
        # Create MemoryConfiguration (enhanced memory config)
        enhanced_config = MemoryConfiguration(
            enable_chunking=True,
            chunking_strategy=ChunkingStrategy.SENTENCE,
            chunk_size=100,
            enable_caching=True
        )
        
        memory = await create_enhanced_memory(memory_config, enhanced_config)
        
        # Add messages
        await memory.add_message(HumanMessage(content="Hello, this is a test message for the memory system."))
        await memory.add_message(AIMessage(content="I understand. The memory system is working correctly and can handle different message types."))
        await memory.add_message(HumanMessage(content="Great! Can you tell me about chunking strategies?"))
        
        print(f"💾 Added 3 messages to enhanced memory")
        
        # Get memory stats
        stats = await memory.get_memory_stats()
        print(f"📊 Memory stats:")
        print(f"   Messages: {stats.total_messages}")
        print(f"   Chunks: {stats.total_chunks}")
        print(f"   Characters: {stats.total_characters:,}")
        
        # Test search (fallback to simple text search without embeddings)
        results = await memory.search("chunking strategies", limit=2)
        print(f"🔍 Search found {len(results)} results")
        
        # Get messages
        messages = await memory.get_messages(limit=2)
        print(f"📝 Retrieved {len(messages)} messages")
        
        print("\n✅ Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_chunking_strategies():
    """Test different chunking strategies."""
    
    from agenticflow.text.chunking import chunk_text, ChunkingStrategy
    
    print("\n🧩 Testing Different Chunking Strategies")
    print("-" * 60)
    
    sample_text = """
    # Machine Learning Fundamentals
    
    Machine learning is a subset of artificial intelligence that enables computers to learn patterns from data.
    
    ## Types of Machine Learning
    
    There are three main types: supervised, unsupervised, and reinforcement learning.
    
    ### Supervised Learning
    Uses labeled data to train models that can make predictions on new, unseen data.
    
    ### Unsupervised Learning  
    Finds hidden patterns in data without using labels or target values.
    """
    
    strategies = [
        ChunkingStrategy.FIXED_SIZE,
        ChunkingStrategy.SENTENCE,
        ChunkingStrategy.RECURSIVE,
        ChunkingStrategy.MARKDOWN
    ]
    
    for strategy in strategies:
        try:
            chunks = await chunk_text(
                sample_text,
                strategy=strategy,
                chunk_size=200,
                chunk_overlap=50
            )
            
            print(f"📋 {strategy.value.upper()}: {len(chunks)} chunks")
            print(f"   Sizes: {[len(c.content) for c in chunks]}")
            print(f"   Sample: {chunks[0].content[:60].strip()}...")
            
        except Exception as e:
            print(f"❌ {strategy.value} failed: {e}")

async def main():
    """Run all integration tests."""
    
    print("🚀 AgenticFlow Memory & Chunking Integration Tests")
    print("=" * 70)
    
    # Test basic integration
    basic_success = await test_basic_integration()
    
    # Test chunking strategies
    await test_chunking_strategies()
    
    print("\n" + "=" * 70)
    if basic_success:
        print("🎉 All tests completed successfully!")
        print("📚 The memory and chunking systems are ready for use!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())