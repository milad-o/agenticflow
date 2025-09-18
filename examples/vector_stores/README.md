# AgenticFlow Vector Stores Examples

This directory demonstrates AgenticFlow's flexible vector storage system, supporting multiple backends with seamless integration for RAG and semantic search applications.

## 📁 Examples

### [`test_vector_stores.py`](./test_vector_stores.py)
**Comprehensive vector store comparison**

```bash
uv run python examples/vector_stores/test_vector_stores.py
```

Tests and compares different vector store backends with performance metrics.

### [`rag_demo.py`](./rag_demo.py)
**Retrieval-Augmented Generation demonstration**

```bash
uv run python examples/vector_stores/rag_demo.py
```

Complete RAG implementation using vector stores with real-world document processing.

## 🗄️ Supported Vector Stores

### FAISS Vector Store
- **High-performance** similarity search
- **Local storage** with persistent indexes
- **Perfect for** development and single-machine deployments
- **Memory efficient** with quantization support

### Chroma Vector Store
- **Easy setup** with minimal configuration  
- **Persistent storage** with metadata filtering
- **Perfect for** prototyping and small-scale applications
- **Built-in embedding** support

### Pinecone Vector Store
- **Cloud-native** managed service
- **Massive scale** with distributed architecture
- **Perfect for** production applications
- **Advanced filtering** and namespaces

## 🚀 Quick Start

### Basic Vector Store Usage

```python
from agenticflow.vectorstores import ChromaVectorStore
from agenticflow.llm_providers import OpenAIEmbeddings

# Create vector store
vector_store = ChromaVectorStore(
    collection_name="my_documents",
    persist_directory="./chroma_db",
    embedding_function=OpenAIEmbeddings()
)

# Add documents
documents = ["AI is transforming technology", "Machine learning enables automation"]
await vector_store.add_documents(documents)

# Semantic search
results = await vector_store.similarity_search("artificial intelligence", k=5)
```

### RAG Implementation

```python
from agenticflow.vectorstores import FAISVectorStore
from agenticflow.llm_providers import OpenAILLM, OpenAIEmbeddings
from agenticflow import Agent

# Setup vector store for knowledge base
knowledge_base = FAISVectorStore(
    dimension=1536,
    index_path="./knowledge.faiss",
    embedding_provider=OpenAIEmbeddings()
)

# Add knowledge documents
await knowledge_base.add_documents([
    "Machine learning is a subset of AI focused on algorithms that learn from data",
    "Neural networks are inspired by biological neurons and process information in layers",
    # ... more documents
])

# Create RAG agent
rag_agent = Agent({
    "name": "knowledge_assistant", 
    "llm": OpenAILLM(),
    "instructions": "Answer using the provided knowledge base",
    "tools": [knowledge_base.as_tool()]  # Vector store as retrieval tool
})

# Query with retrieval-augmented generation
response = await rag_agent.run("Explain machine learning concepts")
```

### Multi-Vector Store Setup

```python
from agenticflow.vectorstores import ChromaVectorStore, PineconeVectorStore, FAISVectorStore

# Different stores for different use cases
local_store = FAISVectorStore(dimension=768, index_path="./local.faiss")
dev_store = ChromaVectorStore(collection_name="dev_docs")
prod_store = PineconeVectorStore(
    api_key="your-key",
    environment="us-west1-gcp",
    index_name="production-index"
)

# Use based on environment
if environment == "development":
    vector_store = dev_store
elif environment == "production":
    vector_store = prod_store
else:
    vector_store = local_store
```

## 🎯 Key Features Demonstrated

### 🏗️ Multiple Backends
- **FAISS**, **Chroma**, and **Pinecone** support
- **Consistent API** across all implementations
- **Easy switching** between backends
- **Environment-specific** configurations

### 🔍 Advanced Search
- **Similarity search** with configurable distance metrics
- **Metadata filtering** for precise results
- **Batch operations** for efficiency
- **Score thresholding** for quality control

### ⚡ Performance Optimization
- **Efficient indexing** with optimized algorithms
- **Batch processing** for large document sets
- **Memory management** with streaming support
- **Concurrent operations** for high throughput

### 🛠️ Production Features
- **Persistence** with automatic saves
- **Backup and restore** capabilities
- **Monitoring** with health checks
- **Error handling** with retries

## 📊 Performance Comparison

| Vector Store | Setup Time | Search Speed | Memory Usage | Best For |
|-------------|------------|--------------|--------------|----------|
| **FAISS** | Fast | Very Fast (~1-2ms) | Low | Local, High Performance |
| **Chroma** | Very Fast | Fast (~5-10ms) | Medium | Prototyping, Development |  
| **Pinecone** | Medium | Fast (~10-20ms) | N/A (Cloud) | Production, Scale |

## 🔧 Configuration Examples

### FAISS Configuration
```python
from agenticflow.vectorstores import FAISVectorStore

faiss_store = FAISVectorStore(
    dimension=1536,
    index_path="./my_index.faiss",
    metric="cosine",  # or "euclidean", "dot_product"
    enable_quantization=True,
    quantization_bits=8,
    enable_persistence=True,
    persist_interval=100  # Save every 100 additions
)
```

### Chroma Configuration  
```python
from agenticflow.vectorstores import ChromaVectorStore

chroma_store = ChromaVectorStore(
    collection_name="documents",
    persist_directory="./chroma_data",
    distance_function="cosine",
    metadata_filters={"source": "documentation"},
    enable_batching=True,
    batch_size=100
)
```

### Pinecone Configuration
```python
from agenticflow.vectorstores import PineconeVectorStore

pinecone_store = PineconeVectorStore(
    api_key="your-api-key",
    environment="us-west1-gcp",
    index_name="production-vectors",
    dimension=1536,
    metric="cosine",
    namespace="docs",
    enable_metadata=True,
    batch_size=100
)
```

## 🤝 Integration Examples

### With Memory Systems
```python
from agenticflow.memory import VectorMemory
from agenticflow.vectorstores import ChromaVectorStore

# Vector store as memory backend
vector_memory = VectorMemory(
    vector_store=ChromaVectorStore(collection_name="conversation_history"),
    enable_persistence=True
)

# Automatic embedding and retrieval
await vector_memory.add_message("User asked about machine learning")
relevant = await vector_memory.search("AI questions", limit=5)
```

### With Retrievers
```python
from agenticflow.retrievers import SemanticRetriever
from agenticflow.vectorstores import FAISVectorStore

# Vector store with retriever system
vector_store = FAISVectorStore(dimension=768)
retriever = SemanticRetriever(
    data_source=vector_store,
    config=SemanticRetrieverConfig(similarity_threshold=0.8)
)

# Advanced retrieval capabilities
results = await retriever.retrieve("machine learning concepts", limit=10)
```

### With Agents
```python
from agenticflow import Agent, AgentConfig
from agenticflow.vectorstores import PineconeVectorStore

agent = Agent(AgentConfig(
    name="research_assistant",
    instructions="Use the knowledge base to answer questions",
    tools=[
        PineconeVectorStore(
            index_name="research_papers",
            api_key=api_key
        ).as_retrieval_tool()
    ]
))
```

## 🧪 Testing and Validation

### Performance Testing
```python
import time
from agenticflow.vectorstores import ChromaVectorStore

# Performance benchmark
vector_store = ChromaVectorStore(collection_name="benchmark")

# Add documents
start_time = time.time()
await vector_store.add_documents(large_document_list)
add_time = time.time() - start_time

# Search performance
start_time = time.time()
results = await vector_store.similarity_search("test query", k=10)
search_time = time.time() - start_time

print(f"Add time: {add_time:.2f}s, Search time: {search_time:.2f}s")
```

### Quality Validation
```python
# Test search quality with known relevant documents
test_queries = [
    ("machine learning", ["ml_doc_1", "ml_doc_2"]),
    ("neural networks", ["nn_doc_1", "nn_doc_2"]),
]

for query, expected_docs in test_queries:
    results = await vector_store.similarity_search(query, k=5)
    retrieved_ids = [r.metadata["id"] for r in results]
    
    # Calculate precision/recall
    precision = len(set(retrieved_ids) & set(expected_docs)) / len(retrieved_ids)
    recall = len(set(retrieved_ids) & set(expected_docs)) / len(expected_docs)
    
    print(f"Query: {query} | Precision: {precision:.2f} | Recall: {recall:.2f}")
```

## 📚 Learn More

- **[AgenticFlow Documentation](../../README.md)**: Main project documentation  
- **[Memory Examples](../memory/README.md)**: Memory system integration
- **[Retriever Examples](../retrievers/README.md)**: Search and retrieval systems
- **[Embeddings Examples](../embeddings/README.md)**: Embedding providers

---

**🗄️ AgenticFlow Vector Stores provide scalable, high-performance semantic search for any AI application!**