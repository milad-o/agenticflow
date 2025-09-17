#!/usr/bin/env python3
"""
Test script for HuggingFace embedding provider.

This script demonstrates:
1. Creating a HuggingFace embedding provider
2. Embedding single and batch texts
3. Using different HuggingFace models
4. Performance and dimension reporting
"""

import asyncio
import sys
import os
import time
from typing import List

# Add the src directory to the path so we can import agenticflow
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

try:
    from agenticflow.embeddings import (
        HuggingFaceEmbeddingProvider,
        create_huggingface_embedding_provider,
        EmbeddingConfig,
        EmbeddingProvider
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you have sentence-transformers installed: pip install sentence-transformers")
    sys.exit(1)


async def test_basic_embedding():
    """Test basic embedding functionality."""
    print("🧪 Testing Basic HuggingFace Embedding...")
    
    # Create provider with a lightweight model
    provider = create_huggingface_embedding_provider(
        model="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Check availability
    is_available = await provider.is_available()
    print(f"✓ Provider available: {is_available}")
    
    if not is_available:
        print("❌ Provider not available. Install with: pip install sentence-transformers")
        return
    
    # Get model info
    model_info = provider.get_model_info()
    print(f"✓ Model info: {model_info['model']}")
    print(f"✓ Dimension: {model_info['dimension']}")
    print(f"✓ Device: {model_info['device']}")
    
    # Test single text embedding
    text = "Hello, this is a test sentence for embedding."
    start_time = time.time()
    
    embedding = await provider.embed_text(text)
    latency = time.time() - start_time
    
    print(f"✓ Single embedding dimension: {len(embedding)}")
    print(f"✓ Embedding latency: {latency:.3f}s")
    print(f"✓ First few values: {embedding[:5]}")


async def test_batch_embedding():
    """Test batch embedding functionality."""
    print("\n🧪 Testing Batch HuggingFace Embedding...")
    
    provider = create_huggingface_embedding_provider(
        model="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Test batch embedding
    texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Python is a great programming language.",
        "Machine learning is revolutionizing technology.",
        "Natural language processing enables AI understanding.",
        "Vector embeddings capture semantic meaning."
    ]
    
    start_time = time.time()
    embeddings = await provider.embed_texts(texts)
    latency = time.time() - start_time
    
    print(f"✓ Batch embedding count: {len(embeddings)}")
    print(f"✓ Each embedding dimension: {len(embeddings[0])}")
    print(f"✓ Total latency: {latency:.3f}s")
    print(f"✓ Average per text: {latency/len(texts):.3f}s")
    
    # Test similarity (embeddings should be closer for related texts)
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        import math
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))
        return dot_product / (magnitude_a * magnitude_b)
    
    # Compare ML-related texts (indices 2 and 3)
    ml_similarity = cosine_similarity(embeddings[2], embeddings[3])
    
    # Compare unrelated texts (indices 0 and 2)
    unrelated_similarity = cosine_similarity(embeddings[0], embeddings[2])
    
    print(f"✓ ML texts similarity: {ml_similarity:.3f}")
    print(f"✓ Unrelated texts similarity: {unrelated_similarity:.3f}")
    print(f"✓ ML texts are {'more' if ml_similarity > unrelated_similarity else 'less'} similar")


async def test_different_models():
    """Test different HuggingFace models."""
    print("\n🧪 Testing Different HuggingFace Models...")
    
    models = [
        "sentence-transformers/all-MiniLM-L6-v2",  # Fast, small
        "sentence-transformers/all-mpnet-base-v2",  # Better quality
        # "BAAI/bge-small-en-v1.5",  # BGE model (commented out as might not be available)
    ]
    
    test_text = "This is a test sentence for comparing different models."
    
    for model_name in models:
        try:
            print(f"\n📊 Testing model: {model_name}")
            
            provider = create_huggingface_embedding_provider(model=model_name)
            
            # Check availability
            if not await provider.is_available():
                print(f"❌ Model {model_name} not available")
                continue
            
            # Get model info
            model_info = provider.get_model_info()
            print(f"✓ Dimension: {model_info['dimension']}")
            print(f"✓ Max input length: {model_info.get('max_input_length', 'unknown')}")
            
            # Time the embedding
            start_time = time.time()
            embedding = await provider.embed_text(test_text)
            latency = time.time() - start_time
            
            print(f"✓ Embedding latency: {latency:.3f}s")
            print(f"✓ Actual dimension: {len(embedding)}")
            
        except Exception as e:
            print(f"❌ Error with model {model_name}: {e}")


async def test_error_handling():
    """Test error handling and edge cases."""
    print("\n🧪 Testing Error Handling...")
    
    # Test with invalid model
    try:
        invalid_provider = create_huggingface_embedding_provider(
            model="non-existent-model-12345"
        )
        await invalid_provider.embed_text("test")
        print("❌ Should have failed with invalid model")
    except Exception as e:
        print(f"✓ Correctly handled invalid model: {type(e).__name__}")
    
    # Test with empty text
    try:
        provider = create_huggingface_embedding_provider()
        if await provider.is_available():
            embedding = await provider.embed_text("")
            print(f"✓ Empty text embedding dimension: {len(embedding)}")
    except Exception as e:
        print(f"❌ Failed on empty text: {e}")
    
    # Test with very long text
    try:
        provider = create_huggingface_embedding_provider()
        if await provider.is_available():
            long_text = "This is a test. " * 1000  # Very long text
            embedding = await provider.embed_text(long_text)
            print(f"✓ Long text embedding dimension: {len(embedding)}")
    except Exception as e:
        print(f"✓ Correctly handled long text: {type(e).__name__}")


async def test_performance_metrics():
    """Test performance metrics tracking."""
    print("\n🧪 Testing Performance Metrics...")
    
    provider = create_huggingface_embedding_provider()
    
    if not await provider.is_available():
        print("❌ Provider not available for metrics test")
        return
    
    # Perform several operations
    texts = ["Test sentence " + str(i) for i in range(10)]
    
    for text in texts:
        await provider.embed_text(text)
    
    # Check metrics
    metrics = provider.metrics
    print(f"✓ Total requests: {metrics.total_requests}")
    print(f"✓ Total tokens (approx): {metrics.total_tokens}")
    print(f"✓ Average latency: {metrics.average_latency:.3f}s")
    print(f"✓ Error count: {metrics.error_count}")
    
    if provider.config.enable_caching:
        print(f"✓ Cache hits: {metrics.cache_hits}")
        print(f"✓ Cache misses: {metrics.cache_misses}")


async def main():
    """Run all tests."""
    print("🚀 Starting HuggingFace Embedding Provider Tests\\n" + "="*50)
    
    try:
        await test_basic_embedding()
        await test_batch_embedding()
        await test_different_models()
        await test_error_handling()
        await test_performance_metrics()
        
        print("\\n" + "="*50)
        print("✅ All HuggingFace embedding tests completed!")
        
    except KeyboardInterrupt:
        print("\\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())