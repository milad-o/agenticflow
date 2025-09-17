#!/usr/bin/env python3
"""
Embedding Providers Comparison
==============================

This example demonstrates how to use different embedding providers
with AgenticFlow and compare their performance and quality.

Supported providers:
- OpenAI (requires API key)
- HuggingFace (local models)
- Cohere (requires API key)
"""

import asyncio
import os
import sys
import time
from typing import Dict, List, Optional

# Add the src directory to the path so we can import agenticflow
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

try:
    from agenticflow.embeddings import (
        EmbeddingProvider,
        EmbeddingConfig,
        create_openai_embedding_provider,
        create_huggingface_embedding_provider,
        create_cohere_embedding_provider,
        create_ollama_embedding_provider,
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure AgenticFlow is properly installed")
    sys.exit(1)


class EmbeddingProviderComparison:
    """Class to compare different embedding providers."""
    
    def __init__(self):
        self.providers = {}
        self.test_texts = [
            "The quick brown fox jumps over the lazy dog.",
            "Python is a powerful programming language for data science.",
            "Machine learning algorithms can identify patterns in data.",
            "Natural language processing enables computers to understand text.",
            "Vector embeddings capture semantic meaning of words and phrases.",
            "Artificial intelligence is transforming various industries.",
            "Deep learning models require large amounts of training data.",
            "Text similarity can be measured using cosine similarity.",
        ]
    
    async def setup_providers(self):
        """Setup all available embedding providers."""
        print("🔧 Setting up embedding providers...")
        
        # OpenAI (if API key available)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                provider = create_openai_embedding_provider(
                    model="text-embedding-3-small",
                    api_key=openai_key
                )
                if await provider.is_available():
                    self.providers["OpenAI"] = provider
                    print("✅ OpenAI provider ready")
                else:
                    print("❌ OpenAI provider not available")
            except Exception as e:
                print(f"❌ OpenAI setup failed: {e}")
        else:
            print("⚠️ OpenAI API key not found (set OPENAI_API_KEY)")
        
        # HuggingFace (local models)
        try:
            provider = create_huggingface_embedding_provider(
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            if await provider.is_available():
                self.providers["HuggingFace"] = provider
                print("✅ HuggingFace provider ready")
            else:
                print("❌ HuggingFace provider not available")
        except Exception as e:
            print(f"❌ HuggingFace setup failed: {e}")
        
        # Cohere (if API key available)
        cohere_key = os.getenv("COHERE_API_KEY") or os.getenv("CO_API_KEY")
        if cohere_key:
            try:
                provider = create_cohere_embedding_provider(
                    model="embed-english-light-v3.0",
                    api_key=cohere_key
                )
                if await provider.is_available():
                    self.providers["Cohere"] = provider
                    print("✅ Cohere provider ready")
                else:
                    print("❌ Cohere provider not available")
            except Exception as e:
                print(f"❌ Cohere setup failed: {e}")
        else:
            print("⚠️ Cohere API key not found (set COHERE_API_KEY)")
        
        # Ollama (local server)
        try:
            provider = create_ollama_embedding_provider(
                model="nomic-embed-text"
            )
            if await provider.is_available():
                self.providers["Ollama"] = provider
                print("✅ Ollama provider ready")
            else:
                print("❌ Ollama provider not available")
        except Exception as e:
            print(f"❌ Ollama setup failed: {e}")
        
        if not self.providers:
            print("❌ No embedding providers available!")
            print("💡 Install sentence-transformers, set API keys, or start Ollama to proceed")
            return False
        
        print(f"🎯 {len(self.providers)} provider(s) ready for comparison")
        return True
    
    async def compare_basic_info(self):
        """Compare basic information about each provider."""
        print("\\n" + "="*60)
        print("📊 PROVIDER INFORMATION COMPARISON")
        print("="*60)
        
        for name, provider in self.providers.items():
            print(f"\\n🔍 {name} Provider:")
            
            try:
                info = provider.get_model_info()
                dimension = await provider.get_dimension()
                
                print(f"   Model: {info['model']}")
                print(f"   Dimension: {dimension}")
                print(f"   Max Batch Size: {info['max_batch_size']}")
                print(f"   Max Text Length: {info['max_text_length']} chars")
                print(f"   Local Model: {'Yes' if info['local_model'] else 'No'}")
                print(f"   Cost per 1K tokens: ${info['cost_per_1k_tokens']}")
                
            except Exception as e:
                print(f"   ❌ Error getting info: {e}")
    
    async def compare_performance(self):
        """Compare performance metrics of each provider."""
        print("\\n" + "="*60)
        print("⚡ PERFORMANCE COMPARISON")
        print("="*60)
        
        results = {}
        
        for name, provider in self.providers.items():
            print(f"\\n🧪 Testing {name}...")
            
            try:
                # Single embedding test
                start_time = time.time()
                single_embedding = await provider.embed_text(self.test_texts[0])
                single_latency = time.time() - start_time
                
                # Batch embedding test
                start_time = time.time()
                batch_embeddings = await provider.embed_texts(self.test_texts)
                batch_latency = time.time() - start_time
                
                results[name] = {
                    "single_latency": single_latency,
                    "batch_latency": batch_latency,
                    "batch_per_text": batch_latency / len(self.test_texts),
                    "dimension": len(single_embedding),
                    "embeddings": batch_embeddings,
                }
                
                print(f"   Single text: {single_latency:.3f}s")
                print(f"   Batch ({len(self.test_texts)} texts): {batch_latency:.3f}s")
                print(f"   Average per text: {results[name]['batch_per_text']:.3f}s")
                print(f"   Dimension: {results[name]['dimension']}")
                
            except Exception as e:
                print(f"   ❌ Performance test failed: {e}")
                results[name] = None
        
        # Performance summary
        print("\\n📈 Performance Summary:")
        valid_results = {k: v for k, v in results.items() if v is not None}
        
        if valid_results:
            fastest_single = min(valid_results.keys(), 
                                key=lambda k: valid_results[k]['single_latency'])
            fastest_batch = min(valid_results.keys(), 
                               key=lambda k: valid_results[k]['batch_per_text'])
            
            print(f"🏆 Fastest single embedding: {fastest_single}")
            print(f"🏆 Fastest batch processing: {fastest_batch}")
        
        return results
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))
        return dot_product / (magnitude_a * magnitude_b)
    
    async def compare_semantic_quality(self, results: Dict):
        """Compare semantic quality of embeddings."""
        print("\\n" + "="*60)
        print("🎯 SEMANTIC QUALITY COMPARISON")
        print("="*60)
        
        # Test semantic similarity with related texts
        similar_pairs = [
            (1, 2),  # Programming and ML
            (2, 3),  # ML and NLP
            (4, 5),  # Embeddings and AI
        ]
        
        dissimilar_pairs = [
            (0, 1),  # Fox and Programming
            (0, 7),  # Fox and Text similarity
        ]
        
        for name, result in results.items():
            if result is None:
                continue
                
            print(f"\\n🔍 {name} Semantic Analysis:")
            embeddings = result["embeddings"]
            
            # Calculate similarities for related pairs
            similar_scores = []
            for i, j in similar_pairs:
                sim = self.cosine_similarity(embeddings[i], embeddings[j])
                similar_scores.append(sim)
                text1 = self.test_texts[i][:30] + "..." if len(self.test_texts[i]) > 30 else self.test_texts[i]
                text2 = self.test_texts[j][:30] + "..." if len(self.test_texts[j]) > 30 else self.test_texts[j]
                print(f"   Related texts similarity: {sim:.3f}")
                print(f"     • \"{text1}\"")
                print(f"     • \"{text2}\"")
            
            # Calculate similarities for unrelated pairs
            dissimilar_scores = []
            for i, j in dissimilar_pairs:
                sim = self.cosine_similarity(embeddings[i], embeddings[j])
                dissimilar_scores.append(sim)
            
            avg_similar = sum(similar_scores) / len(similar_scores)
            avg_dissimilar = sum(dissimilar_scores) / len(dissimilar_scores)
            separation = avg_similar - avg_dissimilar
            
            print(f"   Average related similarity: {avg_similar:.3f}")
            print(f"   Average unrelated similarity: {avg_dissimilar:.3f}")
            print(f"   Semantic separation: {separation:.3f}")
    
    async def cross_provider_similarity(self, results: Dict):
        """Compare how similar embeddings are across providers."""
        print("\\n" + "="*60)
        print("🔄 CROSS-PROVIDER SIMILARITY")
        print("="*60)
        
        valid_results = {k: v for k, v in results.items() if v is not None}
        provider_names = list(valid_results.keys())
        
        if len(provider_names) < 2:
            print("❌ Need at least 2 providers for cross-comparison")
            return
        
        # Compare embeddings for the same text across providers
        test_text_idx = 0  # Use first test text
        print(f"Comparing embeddings for: \"{self.test_texts[test_text_idx]}\"\\n")
        
        for i, name1 in enumerate(provider_names):
            for j, name2 in enumerate(provider_names[i+1:], i+1):
                emb1 = valid_results[name1]["embeddings"][test_text_idx]
                emb2 = valid_results[name2]["embeddings"][test_text_idx]
                
                # Need to normalize embeddings to same dimension for comparison
                # This is a simplified approach - in practice you'd need more sophisticated alignment
                min_dim = min(len(emb1), len(emb2))
                emb1_norm = emb1[:min_dim]
                emb2_norm = emb2[:min_dim]
                
                similarity = self.cosine_similarity(emb1_norm, emb2_norm)
                print(f"{name1} vs {name2}: {similarity:.3f}")
    
    async def run_comparison(self):
        """Run the complete embedding provider comparison."""
        print("🚀 AgenticFlow Embedding Providers Comparison")
        print("="*60)
        
        # Setup providers
        if not await self.setup_providers():
            return
        
        # Run comparisons
        await self.compare_basic_info()
        results = await self.compare_performance()
        await self.compare_semantic_quality(results)
        await self.cross_provider_similarity(results)
        
        print("\\n" + "="*60)
        print("✅ Embedding provider comparison completed!")
        
        # Cleanup
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()


async def main():
    """Main function to run the comparison."""
    comparison = EmbeddingProviderComparison()
    
    try:
        await comparison.run_comparison()
    except KeyboardInterrupt:
        print("\\n❌ Comparison interrupted by user")
    except Exception as e:
        print(f"\\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())