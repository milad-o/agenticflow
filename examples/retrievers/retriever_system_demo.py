"""
AgenticFlow Retriever System Demo

Comprehensive demonstration of the modular retriever system, showcasing:
- All retriever types (text, semantic, composite)
- Factory usage patterns
- Integration with memory systems
- Performance comparison between different strategies
"""

import asyncio
import time
from typing import List, Dict, Any

from agenticflow.retrievers import (
    # Factory and convenience functions
    RetrieverFactory, create_retriever, create_from_memory,
    
    # Retriever types and configurations
    RetrieverType, DistanceMetric,
    KeywordRetrieverConfig, BM25RetrieverConfig, SemanticRetrieverConfig,
    EnsembleRetrieverConfig, HybridRetrieverConfig, FusionRetrieverConfig,
    
    # Individual retrievers for advanced usage
    KeywordRetriever, BM25Retriever, SemanticRetriever,
    EnsembleRetriever, HybridRetriever, FusionRetriever
)

from agenticflow.memory.core import MemoryDocument


class DemoMemorySystem:
    """Demo memory system with sample AI/ML content."""
    
    def __init__(self):
        self.documents = self._create_sample_documents()
        self._setup_embeddings()
    
    def _create_sample_documents(self) -> List[MemoryDocument]:
        """Create comprehensive sample documents about AI/ML."""
        return [
            MemoryDocument(
                id="doc1",
                content="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed. It uses algorithms to find patterns in data.",
                metadata={"topic": "ML", "difficulty": "basic", "keywords": ["machine learning", "AI", "algorithms"]},
                timestamp=time.time()
            ),
            MemoryDocument(
                id="doc2",
                content="Deep learning is a specialized branch of machine learning that uses neural networks with multiple layers to model complex patterns. It excels at tasks like image recognition and natural language processing.",
                metadata={"topic": "Deep Learning", "difficulty": "advanced", "keywords": ["deep learning", "neural networks", "layers"]},
                timestamp=time.time()
            ),
            MemoryDocument(
                id="doc3",
                content="Natural language processing (NLP) focuses on the interaction between computers and human language. It involves understanding, interpreting, and generating human language in a meaningful way.",
                metadata={"topic": "NLP", "difficulty": "intermediate", "keywords": ["NLP", "language", "text processing"]},
                timestamp=time.time()
            ),
            MemoryDocument(
                id="doc4",
                content="Computer vision enables machines to interpret and understand visual information from the world. It combines techniques from machine learning, image processing, and pattern recognition.",
                metadata={"topic": "Computer Vision", "difficulty": "intermediate", "keywords": ["computer vision", "images", "visual"]},
                timestamp=time.time()
            ),
            MemoryDocument(
                id="doc5",
                content="Reinforcement learning is an area of machine learning where agents learn to make decisions by interacting with an environment. The agent receives rewards or penalties for its actions.",
                metadata={"topic": "RL", "difficulty": "advanced", "keywords": ["reinforcement learning", "agents", "rewards"]},
                timestamp=time.time()
            ),
            MemoryDocument(
                id="doc6",
                content="Supervised learning uses labeled training data to learn a mapping from inputs to outputs. Common examples include classification and regression problems.",
                metadata={"topic": "Supervised Learning", "difficulty": "basic", "keywords": ["supervised", "labeled data", "classification"]},
                timestamp=time.time()
            ),
            MemoryDocument(
                id="doc7",
                content="Unsupervised learning finds hidden patterns in data without labeled examples. Clustering and dimensionality reduction are common unsupervised techniques.",
                metadata={"topic": "Unsupervised Learning", "difficulty": "intermediate", "keywords": ["unsupervised", "clustering", "patterns"]},
                timestamp=time.time()
            ),
            MemoryDocument(
                id="doc8",
                content="Transformers revolutionized natural language processing with their attention mechanism. Models like BERT, GPT, and T5 are all based on the transformer architecture.",
                metadata={"topic": "Transformers", "difficulty": "advanced", "keywords": ["transformers", "attention", "BERT", "GPT"]},
                timestamp=time.time()
            ),
            MemoryDocument(
                id="doc9",
                content="Convolutional Neural Networks (CNNs) are particularly effective for image processing tasks. They use convolutional layers to detect local features in images.",
                metadata={"topic": "CNN", "difficulty": "intermediate", "keywords": ["CNN", "convolutional", "image processing"]},
                timestamp=time.time()
            ),
            MemoryDocument(
                id="doc10",
                content="Large Language Models (LLMs) like GPT-4 demonstrate emergent capabilities at scale. They can perform various tasks through prompt engineering and in-context learning.",
                metadata={"topic": "LLM", "difficulty": "advanced", "keywords": ["LLM", "GPT", "prompt engineering"]},
                timestamp=time.time()
            )
        ]
    
    def _setup_embeddings(self):
        """Mock embeddings provider for semantic search."""
        from unittest.mock import Mock, AsyncMock
        
        self.embeddings = Mock()
        # Mock different embeddings for different content
        embedding_map = {
            "machine learning": [0.8, 0.2, 0.1, 0.3, 0.5],
            "deep learning": [0.7, 0.8, 0.2, 0.1, 0.4],
            "natural language": [0.3, 0.1, 0.9, 0.2, 0.1],
            "computer vision": [0.2, 0.3, 0.1, 0.8, 0.6],
            "reinforcement learning": [0.6, 0.4, 0.2, 0.3, 0.9],
            "transformers": [0.4, 0.2, 0.8, 0.1, 0.3],
            "neural networks": [0.7, 0.6, 0.3, 0.4, 0.8],
        }
        
        def mock_embed(query):
            query_lower = query.lower()
            # Find best matching embedding or return default
            for key, embedding in embedding_map.items():
                if key in query_lower:
                    return embedding
            return [0.5, 0.5, 0.5, 0.5, 0.5]  # Default
        
        self.embeddings.embed_query = mock_embed
        self.embeddings.aembed_query = AsyncMock(side_effect=mock_embed)
    
    async def search(self, query: str, limit: int = 10) -> List[MemoryDocument]:
        """Basic text search."""
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            # Check content and metadata for matches
            content_match = any(word in doc.content.lower() for word in query_lower.split())
            keyword_match = any(
                keyword.lower() in query_lower or query_lower in keyword.lower()
                for keyword in doc.metadata.get("keywords", [])
            )
            
            if content_match or keyword_match:
                results.append(doc)
        
        return results[:limit]
    
    async def similarity_search(self, query: str, limit: int = 10) -> List[MemoryDocument]:
        """Mock semantic similarity search."""
        # Add similarity scores to metadata
        for doc in self.documents:
            # Mock similarity based on content relevance
            if "learning" in query.lower() and "learning" in doc.content.lower():
                doc.metadata["similarity_score"] = 0.85
            elif any(word in doc.content.lower() for word in query.lower().split()):
                doc.metadata["similarity_score"] = 0.75
            else:
                doc.metadata["similarity_score"] = 0.3
        
        # Sort by similarity and return top results
        sorted_docs = sorted(self.documents, key=lambda d: d.metadata.get("similarity_score", 0), reverse=True)
        return sorted_docs[:limit]


async def demo_text_retrievers(memory_system: DemoMemorySystem):
    """Demo text-based retrievers."""
    print("=== TEXT-BASED RETRIEVERS ===\n")
    
    # Keyword Retriever
    print("1. Keyword Retriever:")
    keyword_config = KeywordRetrieverConfig(case_sensitive=False, word_boundaries=True)
    keyword_retriever = create_retriever(RetrieverType.KEYWORD, memory_system, keyword_config)
    
    results = await keyword_retriever.retrieve("neural networks", limit=3)
    print(f"Found {len(results)} results for 'neural networks':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [Score: {result.score:.2f}] {result.document.content[:80]}...")
    print()
    
    # BM25 Retriever
    print("2. BM25 Retriever:")
    bm25_config = BM25RetrieverConfig(k1=1.2, b=0.75)
    bm25_retriever = create_retriever(RetrieverType.BM25, memory_system, bm25_config)
    
    results = await bm25_retriever.retrieve("machine learning algorithms", limit=3)
    print(f"Found {len(results)} results for 'machine learning algorithms':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [Score: {result.score:.3f}] {result.document.content[:80]}...")
    print()
    
    # Regex Retriever
    print("3. Regex Retriever:")
    regex_retriever = create_retriever(RetrieverType.REGEX, memory_system)
    
    results = await regex_retriever.retrieve(r"\b\w*learning\w*\b", limit=3)
    print(f"Found {len(results)} results for pattern '\\b\\w*learning\\w*\\b':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [Score: {result.score:.2f}] {result.document.content[:80]}...")
    print()


async def demo_semantic_retrievers(memory_system: DemoMemorySystem):
    """Demo semantic/vector retrievers."""
    print("=== SEMANTIC RETRIEVERS ===\n")
    
    # Semantic Retriever with Cosine similarity
    print("1. Semantic Retriever (Cosine):")
    semantic_config = SemanticRetrieverConfig(
        distance_metric=DistanceMetric.COSINE,
        normalize_embeddings=True,
        similarity_threshold=0.7
    )
    semantic_retriever = create_retriever(RetrieverType.SEMANTIC, memory_system, semantic_config)
    
    results = await semantic_retriever.retrieve("AI and neural networks", limit=3)
    print(f"Found {len(results)} results for 'AI and neural networks':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [Score: {result.score:.3f}] {result.document.content[:80]}...")
    print()
    
    # Euclidean Distance Retriever
    print("2. Euclidean Distance Retriever:")
    euclidean_retriever = create_retriever(RetrieverType.EUCLIDEAN, memory_system)
    
    results = await euclidean_retriever.retrieve("language processing", limit=3)
    print(f"Found {len(results)} results for 'language processing':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [Score: {result.score:.3f}] {result.document.content[:80]}...")
    print()
    
    # Sparse Retriever (TF-IDF style)
    print("3. Sparse Vector Retriever:")
    sparse_retriever = create_retriever(RetrieverType.SPARSE, memory_system)
    
    results = await sparse_retriever.retrieve("computer vision tasks", limit=3)
    print(f"Found {len(results)} results for 'computer vision tasks':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [Score: {result.score:.3f}] {result.document.content[:80]}...")
    print()


async def demo_composite_retrievers(memory_system: DemoMemorySystem):
    """Demo composite retrievers that combine multiple strategies."""
    print("=== COMPOSITE RETRIEVERS ===\n")
    
    # Ensemble Retriever
    print("1. Ensemble Retriever (Keyword + BM25 + Semantic):")
    ensemble = RetrieverFactory.create_ensemble_from_memory(
        memory_system,
        retriever_types=[RetrieverType.KEYWORD, RetrieverType.BM25, RetrieverType.SEMANTIC],
        config=EnsembleRetrieverConfig(
            fusion_method="weighted_sum",
            normalize_scores=True,
            enable_diversity=True
        )
    )
    
    results = await ensemble.retrieve("deep learning and transformers", limit=3)
    print(f"Found {len(results)} results for 'deep learning and transformers':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [Score: {result.score:.3f}] {result.document.content[:80]}...")
        if "fusion_method" in result.metadata:
            print(f"      Fusion: {result.metadata['fusion_method']}")
    print()
    
    # Hybrid Dense-Sparse Retriever
    print("2. Hybrid Dense-Sparse Retriever:")
    hybrid = RetrieverFactory.create_hybrid_from_memory(
        memory_system,
        dense_type=RetrieverType.SEMANTIC,
        sparse_type=RetrieverType.SPARSE,
        config=HybridRetrieverConfig(dense_weight=0.7, sparse_weight=0.3)
    )
    
    results = await hybrid.retrieve("supervised learning classification", limit=3)
    print(f"Found {len(results)} results for 'supervised learning classification':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [Score: {result.score:.3f}] {result.document.content[:80]}...")
        if "dense_score" in result.metadata and "sparse_score" in result.metadata:
            print(f"      Dense: {result.metadata['dense_score']:.3f}, Sparse: {result.metadata['sparse_score']:.3f}")
    print()
    
    # Fusion Retriever with RRF
    print("3. Fusion Retriever (RRF + Weighted Sum):")
    fusion = FusionRetriever(
        retrievers=[
            create_retriever(RetrieverType.KEYWORD, memory_system),
            create_retriever(RetrieverType.BM25, memory_system),
            create_retriever(RetrieverType.SEMANTIC, memory_system)
        ],
        config=FusionRetrieverConfig(
            fusion_strategies=["rrf", "weighted_sum"],
            rrf_k=60
        )
    )
    
    results = await fusion.retrieve("reinforcement learning agents", limit=3)
    print(f"Found {len(results)} results for 'reinforcement learning agents':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [Score: {result.score:.3f}] {result.document.content[:80]}...")
    print()


async def demo_factory_patterns(memory_system: DemoMemorySystem):
    """Demo various factory usage patterns."""
    print("=== FACTORY USAGE PATTERNS ===\n")
    
    # Auto-detection
    print("1. Auto-Detection:")
    auto_retriever = create_from_memory(memory_system)
    print(f"   Auto-detected retriever type: {auto_retriever.retriever_type}")
    
    results = await auto_retriever.retrieve("artificial intelligence", limit=2)
    print(f"   Found {len(results)} results with auto-detected retriever")
    print()
    
    # List supported types
    print("2. Supported Retriever Types:")
    supported = RetrieverFactory.list_supported_types()
    print(f"   Total supported types: {len(supported)}")
    for retriever_type in supported[:8]:  # Show first 8
        print(f"   - {retriever_type}")
    print(f"   ... and {len(supported) - 8} more")
    print()
    
    # Configuration classes
    print("3. Configuration Classes:")
    for retriever_type in [RetrieverType.KEYWORD, RetrieverType.SEMANTIC, RetrieverType.ENSEMBLE]:
        config_class = RetrieverFactory.get_config_class(retriever_type)
        print(f"   {retriever_type}: {config_class.__name__}")
    print()


async def performance_comparison(memory_system: DemoMemorySystem):
    """Compare performance of different retriever strategies."""
    print("=== PERFORMANCE COMPARISON ===\n")
    
    query = "machine learning neural networks"
    
    retrievers = [
        ("Keyword", create_retriever(RetrieverType.KEYWORD, memory_system)),
        ("BM25", create_retriever(RetrieverType.BM25, memory_system)),
        ("Semantic", create_retriever(RetrieverType.SEMANTIC, memory_system)),
        ("Ensemble", RetrieverFactory.create_ensemble_from_memory(
            memory_system, [RetrieverType.KEYWORD, RetrieverType.BM25, RetrieverType.SEMANTIC]
        ))
    ]
    
    print(f"Query: '{query}'\n")
    
    for name, retriever in retrievers:
        start_time = time.time()
        results = await retriever.retrieve(query, limit=5)
        end_time = time.time()
        
        print(f"{name} Retriever:")
        print(f"  Time: {(end_time - start_time) * 1000:.1f}ms")
        print(f"  Results: {len(results)}")
        if results:
            print(f"  Top score: {results[0].score:.3f}")
            print(f"  Top result: {results[0].document.content[:60]}...")
        print()


async def demo_advanced_features(memory_system: DemoMemorySystem):
    """Demo advanced retriever features."""
    print("=== ADVANCED FEATURES ===\n")
    
    # Caching
    print("1. Caching Demo:")
    cached_retriever = create_retriever(
        RetrieverType.KEYWORD,
        memory_system,
        KeywordRetrieverConfig(enable_caching=True, cache_size=5)
    )
    
    # First query
    start_time = time.time()
    results1 = await cached_retriever.retrieve("learning", limit=3)
    time1 = (time.time() - start_time) * 1000
    
    # Second query (cached)
    start_time = time.time()
    results2 = await cached_retriever.retrieve("learning", limit=3)
    time2 = (time.time() - start_time) * 1000
    
    print(f"   First query: {time1:.1f}ms, Results: {len(results1)}")
    print(f"   Cached query: {time2:.1f}ms, Results: {len(results2)}")
    print(f"   Cache size: {len(cached_retriever._cache)}")
    print()
    
    # Filtering
    print("2. Metadata Filtering:")
    filtered_retriever = create_retriever(
        RetrieverType.KEYWORD,
        memory_system,
        KeywordRetrieverConfig(
            metadata_filters={"difficulty": "advanced"},
            similarity_threshold=0.1
        )
    )
    
    results = await filtered_retriever.retrieve("learning", limit=5)
    print(f"   Results with difficulty='advanced': {len(results)}")
    for result in results:
        print(f"   - {result.document.metadata['topic']} (difficulty: {result.document.metadata['difficulty']})")
    print()
    
    # Health checks and stats
    print("3. Health Check and Statistics:")
    retriever = create_retriever(RetrieverType.KEYWORD, memory_system)
    
    is_healthy = await retriever.health_check()
    stats = retriever.get_stats()
    
    print(f"   Health: {'Healthy' if is_healthy else 'Unhealthy'}")
    print(f"   Type: {stats['retriever_type']}")
    print(f"   Cache size: {stats['cache_size']}")
    print()


async def main():
    """Run comprehensive retriever system demonstration."""
    print("🔍 AgenticFlow Retriever System Demo")
    print("=" * 50)
    print()
    
    # Initialize demo system
    memory_system = DemoMemorySystem()
    print(f"Initialized demo system with {len(memory_system.documents)} documents")
    print()
    
    # Run all demos
    await demo_text_retrievers(memory_system)
    await demo_semantic_retrievers(memory_system)
    await demo_composite_retrievers(memory_system)
    await demo_factory_patterns(memory_system)
    await performance_comparison(memory_system)
    await demo_advanced_features(memory_system)
    
    print("🎉 Demo completed! The retriever system offers:")
    print("   ✅ Multiple search strategies (text, semantic, hybrid)")
    print("   ✅ Modular, composable architecture")
    print("   ✅ Factory patterns for easy instantiation")
    print("   ✅ Advanced features (caching, filtering, metrics)")
    print("   ✅ High performance with async support")


if __name__ == "__main__":
    asyncio.run(main())