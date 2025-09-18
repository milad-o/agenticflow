# AgenticFlow Retriever System Examples

This directory contains examples demonstrating the powerful and modular **AgenticFlow Retriever System** - a cutting-edge, search strategy-first retrieval framework.

## 🎯 Core Philosophy: Search Strategy > Storage Type

The AgenticFlow Retriever System is designed with modularity and flexibility at its core, allowing you to mix and match any retrieval algorithm with any data source.

## 📁 Examples

### [`retriever_system_demo.py`](./retriever_system_demo.py)
**Comprehensive demonstration of all retriever capabilities**

```bash
uv run python examples/retrievers/retriever_system_demo.py
```

**What it demonstrates:**
- **Text-Based Retrievers**: Keyword, BM25, Full-text, Regex, and Fuzzy matching
- **Semantic Retrievers**: Dense vector search with multiple distance metrics (Cosine, Euclidean, Manhattan, Dot Product)
- **Composite Retrievers**: Ensemble, Hybrid (Dense+Sparse), Contextual, and Fusion strategies
- **Factory Patterns**: Auto-detection and easy instantiation
- **Performance Comparison**: Speed and accuracy metrics across strategies
- **Advanced Features**: Caching, filtering, health checks, and statistics

## 🚀 Retriever Types Supported

### Text-Based Retrievers
- **`KeywordRetriever`**: Simple keyword/text matching
- **`FullTextRetriever`**: Advanced text search with stemming and stopwords
- **`BM25Retriever`**: Best Matching 25 ranking algorithm
- **`FuzzyRetriever`**: Fuzzy text matching with edit distance
- **`RegexRetriever`**: Regular expression-based search

### Semantic/Vector Retrievers
- **`SemanticRetriever`**: Dense vector semantic search
- **`CosineRetriever`**: Cosine similarity search
- **`EuclideanRetriever`**: Euclidean distance search
- **`DotProductRetriever`**: Dot product similarity
- **`ManhattanRetriever`**: Manhattan distance search
- **`SparseRetriever`**: Sparse vector search (TF-IDF, SPLADE)

### Composite Retrievers
- **`EnsembleRetriever`**: Combines multiple search strategies with fusion
- **`HybridRetriever`**: Dense + sparse vector combination
- **`ContextualRetriever`**: Context-aware retrieval with conversation history
- **`FusionRetriever`**: Advanced score fusion and reranking

## 🔧 Quick Start

### Basic Usage

```python
from agenticflow.retrievers import create_retriever, RetrieverType

# Create a semantic retriever
retriever = create_retriever(
    RetrieverType.SEMANTIC,
    data_source=your_memory_or_vector_store
)

# Perform retrieval
results = await retriever.retrieve("your query", limit=10)
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.document.content[:100]}...")
```

### Auto-Detection

```python
from agenticflow.retrievers import create_from_memory

# Automatically detect best retriever for your data source
retriever = create_from_memory(memory_instance)
results = await retriever.retrieve("machine learning concepts")
```

### Advanced Composition

```python
from agenticflow.retrievers import RetrieverFactory

# Create hybrid dense-sparse retriever
hybrid = RetrieverFactory.create_hybrid_from_memory(
    memory_instance,
    dense_type=RetrieverType.SEMANTIC,
    sparse_type=RetrieverType.BM25,
    config=HybridRetrieverConfig(dense_weight=0.7, sparse_weight=0.3)
)

# Create ensemble retriever
ensemble = RetrieverFactory.create_ensemble_from_memory(
    memory_instance,
    retriever_types=[
        RetrieverType.SEMANTIC,
        RetrieverType.BM25, 
        RetrieverType.KEYWORD
    ]
)
```

## 🎯 Key Features Demonstrated

### ⚡ Performance
- **Sub-millisecond retrieval** for individual strategies
- **Intelligent caching** with immediate cache hits
- **Concurrent execution** of multiple retrievers

### 🔍 Search Strategies
- **15 different retriever types** with unique algorithms
- **Multiple distance metrics** for vector similarity
- **Advanced fusion methods** (RRF, weighted sum, max/min)

### 🏗️ Architecture
- **Data source agnostic** - works with any compatible backend
- **Modular composition** enabling complex search strategies
- **Factory patterns** for easy instantiation and auto-detection

### 🛡️ Production Features
- **Health monitoring** and statistics
- **Metadata filtering** and content filtering
- **Score normalization** and reranking
- **Comprehensive error handling**

## 📊 Performance Metrics

From the demo, you can expect:
- **Keyword Retriever**: ~0.1ms per query
- **BM25 Retriever**: ~0.1ms per query (after corpus building)
- **Semantic Retriever**: ~0.1ms per query (with cached embeddings)
- **Ensemble Retriever**: ~0.4ms per query (combined strategies)

## 🔧 Configuration Examples

### Text Retriever Configuration
```python
from agenticflow.retrievers import KeywordRetrieverConfig, BM25RetrieverConfig

keyword_config = KeywordRetrieverConfig(
    case_sensitive=False,
    whole_words_only=True,
    boost_exact_matches=True,
    similarity_threshold=0.7
)

bm25_config = BM25RetrieverConfig(
    k1=1.2,  # Term frequency saturation
    b=0.75,  # Length normalization
    similarity_threshold=0.6
)
```

### Semantic Retriever Configuration
```python
from agenticflow.retrievers import SemanticRetrieverConfig, DistanceMetric

semantic_config = SemanticRetrieverConfig(
    distance_metric=DistanceMetric.COSINE,
    normalize_embeddings=True,
    similarity_threshold=0.8,
    embedding_cache_size=1000
)
```

### Ensemble Configuration
```python
from agenticflow.retrievers import EnsembleRetrieverConfig

ensemble_config = EnsembleRetrieverConfig(
    fusion_method="weighted_sum",  # or "rank_fusion", "max", "min"
    normalize_scores=True,
    enable_diversity=True,
    diversity_threshold=0.8,
    retriever_weights={
        "semantic": 0.5,
        "bm25": 0.3,
        "keyword": 0.2
    }
)
```

## 📚 Learn More

- **[AgenticFlow Documentation](../../README.md)**: Main project documentation
- **[Memory Examples](../memory/README.md)**: Memory system integration
- **[Vector Store Examples](../vector_stores/README.md)**: Vector store backends
- **[API Reference](../../docs/)**: Detailed API documentation

## 🤝 Integration Examples

### With Memory Systems
```python
from agenticflow.memory import VectorMemory
from agenticflow.retrievers import create_from_memory

# Create vector memory
memory = VectorMemory(embedding_provider=your_embeddings)
await memory.add_message("AI content...")

# Create optimized retriever
retriever = create_from_memory(memory)  # Auto-detects semantic retrieval
```

### With Vector Stores
```python
from agenticflow.vectorstores import ChromaVectorStore
from agenticflow.retrievers import SemanticRetriever

# Use retriever directly with vector store
vector_store = ChromaVectorStore()
retriever = SemanticRetriever(vector_store)
```

### Custom Data Sources
```python
class CustomDataSource:
    def __init__(self, documents):
        self.documents = documents
    
    async def search(self, query, limit=10):
        # Your custom search logic
        return filtered_documents

# Works with any data source
retriever = KeywordRetriever(CustomDataSource(your_docs))
```

---

**🎉 The AgenticFlow Retriever System provides unmatched flexibility and performance for any search and retrieval use case!**