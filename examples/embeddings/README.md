# AgenticFlow Embedding Examples

This directory demonstrates AgenticFlow's flexible embedding system, supporting multiple providers with seamless integration for semantic search and RAG applications.

## 📁 Examples

### [`embedding_providers_comparison.py`](./embedding_providers_comparison.py)
**Comprehensive embedding provider comparison**

```bash
uv run python examples/embeddings/embedding_providers_comparison.py
```

Compares different embedding providers across performance, quality, and cost metrics.

### [`factory_example.py`](./factory_example.py)
**Embedding factory usage patterns**

```bash
uv run python examples/embeddings/factory_example.py
```

Demonstrates factory patterns for creating and managing embedding providers.

### [`test_ollama_embeddings.py`](./test_ollama_embeddings.py)
**Local Ollama embedding integration**

```bash
uv run python examples/embeddings/test_ollama_embeddings.py
```

Shows how to use local Ollama models for embeddings without external API dependencies.

### [`test_huggingface_embeddings.py`](./test_huggingface_embeddings.py)
**HuggingFace embedding models**

```bash
uv run python examples/embeddings/test_huggingface_embeddings.py
```

Demonstrates integration with HuggingFace embedding models and transformers.

## 🤖 Supported Embedding Providers

### OpenAI Embeddings
- **High-quality** text embeddings (text-embedding-ada-002, text-embedding-3-small/large)
- **Consistent performance** across domains
- **Best for** production applications with API budget

### Ollama Embeddings
- **Local deployment** with complete privacy
- **Multiple models** (nomic-embed-text, all-minilm, etc.)
- **Best for** privacy-sensitive applications and development

### HuggingFace Embeddings
- **Open-source models** with extensive selection
- **Fine-tuned options** for specific domains
- **Best for** customization and research applications

### Groq Embeddings
- **Fast inference** with specialized hardware
- **Cost-effective** for high-volume applications
- **Best for** real-time applications requiring speed

## 🚀 Quick Start

### Basic Embedding Usage

```python
from agenticflow.llm_providers import OpenAIEmbeddings

# Create embedding provider
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key="your-openai-api-key"
)

# Generate embeddings
text = "Machine learning enables computers to learn from data"
embedding = await embeddings.aembed_query(text)
print(f"Embedding dimension: {len(embedding)}")

# Batch embeddings
texts = ["AI research", "Deep learning", "Neural networks"]
embeddings_batch = await embeddings.aembed_documents(texts)
```

### Local Ollama Setup

```python
from agenticflow.llm_providers import OllamaEmbeddings

# Use local Ollama instance
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# Generate embeddings locally (no API calls)
embedding = await embeddings.aembed_query("Local embedding generation")
```

### Provider Comparison

```python
from agenticflow.llm_providers import (
    OpenAIEmbeddings, OllamaEmbeddings, HuggingFaceEmbeddings
)

# Setup multiple providers
providers = {
    "openai": OpenAIEmbeddings(model="text-embedding-3-small"),
    "ollama": OllamaEmbeddings(model="nomic-embed-text"),
    "huggingface": HuggingFaceEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2")
}

# Compare embeddings
text = "Compare embedding quality"
for name, provider in providers.items():
    embedding = await provider.aembed_query(text)
    print(f"{name}: {len(embedding)} dimensions")
```

## 🎯 Key Features Demonstrated

### 🔄 Provider Flexibility
- **Multiple providers** with consistent API
- **Easy switching** between providers
- **Provider-specific optimizations**
- **Automatic failover** support

### ⚡ Performance Optimization
- **Batch processing** for efficiency
- **Async operations** for scalability
- **Caching strategies** for repeated embeddings
- **Connection pooling** for high throughput

### 📊 Quality Metrics
- **Embedding quality** comparison across providers
- **Performance benchmarking** for different models
- **Cost analysis** for production planning
- **Accuracy evaluation** on test datasets

### 🛠️ Production Features
- **Error handling** with retries and fallbacks
- **Rate limiting** and quota management
- **Monitoring** and logging capabilities
- **Security** with API key management

## 📊 Provider Comparison

| Provider | Speed | Cost | Quality | Privacy | Best Use Case |
|----------|-------|------|---------|---------|---------------|
| **OpenAI** | Fast | High | Excellent | API-dependent | Production apps |
| **Ollama** | Medium | Free | Good | Complete | Local/private apps |
| **HuggingFace** | Variable | Free/Low | Variable | Configurable | Research/custom |
| **Groq** | Very Fast | Medium | Good | API-dependent | Real-time apps |

## 🔧 Configuration Examples

### OpenAI Configuration
```python
from agenticflow.llm_providers import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",  # Higher quality, more expensive
    api_key="your-api-key",
    max_retries=3,
    timeout=30,
    batch_size=100,
    enable_caching=True
)
```

### Ollama Configuration
```python
from agenticflow.llm_providers import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
    timeout=60,
    keep_alive="5m",
    enable_gpu=True
)
```

### HuggingFace Configuration
```python
from agenticflow.llm_providers import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
    cache_folder="./models",
    device="cuda",  # or "cpu"
    normalize_embeddings=True,
    batch_size=32
)
```

## 🤝 Integration Examples

### With Vector Stores
```python
from agenticflow.vectorstores import ChromaVectorStore
from agenticflow.llm_providers import OpenAIEmbeddings

# Vector store with custom embeddings
vector_store = ChromaVectorStore(
    collection_name="documents",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")
)

# Add documents with automatic embedding
await vector_store.add_documents([
    "Machine learning document",
    "AI research paper",
    "Deep learning tutorial"
])
```

### With Memory Systems
```python
from agenticflow.memory import VectorMemory
from agenticflow.llm_providers import OllamaEmbeddings

# Memory with local embeddings
memory = VectorMemory(
    embedding_provider=OllamaEmbeddings(model="nomic-embed-text"),
    vector_store_config={"persist_directory": "./memory_db"}
)

# Store conversation with embeddings
await memory.add_message("User question about AI")
relevant = await memory.search("AI questions", limit=5)
```

### With Retrievers
```python
from agenticflow.retrievers import SemanticRetriever, create_from_memory
from agenticflow.memory import VectorMemory
from agenticflow.llm_providers import HuggingFaceEmbeddings

# Create memory with custom embeddings
memory = VectorMemory(
    embedding_provider=HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
)

# Create retriever with semantic search
retriever = create_from_memory(memory)
results = await retriever.retrieve("machine learning concepts")
```

## 🧪 Testing and Benchmarking

### Performance Benchmarking
```python
import time
from agenticflow.llm_providers import OpenAIEmbeddings, OllamaEmbeddings

async def benchmark_provider(provider, texts, name):
    start_time = time.time()
    embeddings = await provider.aembed_documents(texts)
    duration = time.time() - start_time
    
    print(f"{name}:")
    print(f"  Time: {duration:.2f}s")
    print(f"  Throughput: {len(texts)/duration:.2f} texts/s")
    print(f"  Dimensions: {len(embeddings[0])}")

# Test with sample texts
test_texts = ["AI research", "Machine learning", "Deep learning"] * 10

await benchmark_provider(OpenAIEmbeddings(), test_texts, "OpenAI")
await benchmark_provider(OllamaEmbeddings(), test_texts, "Ollama")
```

### Quality Evaluation
```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

async def evaluate_embedding_quality(provider, test_pairs):
    """Test semantic similarity preservation"""
    results = []
    
    for text1, text2, expected_similarity in test_pairs:
        emb1 = await provider.aembed_query(text1)
        emb2 = await provider.aembed_query(text2)
        
        # Calculate similarity
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        results.append((similarity, expected_similarity))
    
    # Calculate correlation with expected similarities
    actual = [r[0] for r in results]
    expected = [r[1] for r in results]
    correlation = np.corrcoef(actual, expected)[0, 1]
    
    return correlation

# Test semantic relationships
test_pairs = [
    ("dog", "puppy", 0.8),
    ("car", "vehicle", 0.7),
    ("happy", "sad", 0.2),
    ("king", "queen", 0.6)
]

correlation = await evaluate_embedding_quality(embeddings, test_pairs)
print(f"Semantic correlation: {correlation:.3f}")
```

### Cost Analysis
```python
# Calculate embedding costs for different providers
def calculate_embedding_cost(provider_name, num_tokens, model_name=None):
    """Calculate approximate cost for embedding generation"""
    costs_per_1k_tokens = {
        "openai_ada_002": 0.0001,
        "openai_3_small": 0.00002,
        "openai_3_large": 0.00013,
        "ollama": 0.0,  # Local deployment
        "huggingface": 0.0  # Open source
    }
    
    cost_key = f"{provider_name}_{model_name}" if model_name else provider_name
    rate = costs_per_1k_tokens.get(cost_key, 0)
    
    return (num_tokens / 1000) * rate

# Example cost calculation
document_tokens = 500_000  # 500K tokens to embed
print("Cost comparison for 500K tokens:")
print(f"OpenAI ada-002: ${calculate_embedding_cost('openai', document_tokens, 'ada_002'):.2f}")
print(f"OpenAI 3-small: ${calculate_embedding_cost('openai', document_tokens, '3_small'):.2f}")
print(f"Ollama (local): ${calculate_embedding_cost('ollama', document_tokens):.2f}")
```

## 📚 Learn More

- **[AgenticFlow Documentation](../../README.md)**: Main project documentation
- **[Vector Store Examples](../vector_stores/README.md)**: Vector storage integration
- **[Memory Examples](../memory/README.md)**: Memory system integration
- **[Retriever Examples](../retrievers/README.md)**: Search and retrieval systems

---

**🤖 AgenticFlow Embeddings provide flexible, high-performance text embedding capabilities for any semantic AI application!**