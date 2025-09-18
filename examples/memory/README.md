# AgenticFlow Memory System Examples

This directory contains comprehensive examples demonstrating AgenticFlow's advanced memory systems, including different backends, chunking strategies, and persistence mechanisms.

## 📁 Examples

### [`memory_demo.py`](./memory_demo.py)
**Basic memory system demonstration**

```bash
uv run python examples/memory/memory_demo.py
```

Shows fundamental memory operations across different backends.

### [`memory_guide.py`](./memory_guide.py)
**Comprehensive memory system guide**

```bash
uv run python examples/memory/memory_guide.py
```

Complete walkthrough of memory features and best practices.

### [`memory_backends_test.py`](./memory_backends_test.py)
**Memory backend comparison**

```bash
uv run python examples/memory/memory_backends_test.py
```

Performance and feature comparison across all memory backends.

### [`advanced_memory_chunking_demo.py`](./advanced_memory_chunking_demo.py)
**Advanced text chunking strategies**

```bash
uv run python examples/memory/advanced_memory_chunking_demo.py
```

Demonstrates sophisticated text chunking and fragment management.

### [`memory_chunking_integration_test.py`](./memory_chunking_integration_test.py)
**Chunking integration validation**

```bash
uv run python examples/memory/memory_chunking_integration_test.py
```

Validates chunking across different memory systems and configurations.

## 🧠 Memory Backends Supported

### Buffer Memory
- **In-memory storage** for development and testing
- **Fast access** with automatic cleanup
- **Perfect for** prototyping and short sessions

### SQLite Memory
- **Persistent local storage** with SQL capabilities
- **Full-text search** support
- **Perfect for** single-user applications and development

### PostgreSQL Memory
- **Production-grade** relational storage
- **Advanced querying** and indexing
- **Perfect for** multi-user applications and analytics

### Vector Memory
- **Semantic search** with embeddings
- **Multiple vector stores** (FAISS, Chroma, Pinecone)
- **Perfect for** RAG applications and semantic search

### Enhanced Memory
- **Hybrid approach** combining text and vector storage
- **Advanced chunking** with overlap and metadata
- **Perfect for** complex document processing

## 🔧 Quick Start

### Basic Memory Usage
```python
from agenticflow.memory import BufferMemory, MemoryMessage

# Create memory instance
memory = BufferMemory()

# Add messages
await memory.add_message(MemoryMessage(
    role="user",
    content="What is machine learning?",
    metadata={"topic": "AI"}
))

# Retrieve messages
messages = await memory.get_messages(limit=10)
```

### Vector Memory with Embeddings
```python
from agenticflow.memory import VectorMemory
from agenticflow.llm_providers import OpenAIEmbeddings

# Create vector memory
memory = VectorMemory(
    embedding_provider=OpenAIEmbeddings(),
    vector_store_config={"collection_name": "my_docs"}
)

# Add content with automatic embedding
await memory.add_message("Machine learning enables computers to learn from data")

# Semantic search
results = await memory.search("AI learning algorithms", limit=5)
```

### Enhanced Memory with Chunking
```python
from agenticflow.memory import EnhancedMemory
from agenticflow.text.chunking import RecursiveCharacterTextSplitter

# Create enhanced memory with chunking
memory = EnhancedMemory(
    chunking_strategy=RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    ),
    enable_vector_search=True
)

# Add large document with automatic chunking
await memory.add_message("Large document content...")
```

## 🎯 Key Features Demonstrated

### 📚 Multiple Backends
- **Buffer**, **SQLite**, **PostgreSQL**, **Vector**, and **Enhanced** memory
- **Seamless switching** between backends
- **Consistent API** across all implementations

### 🔍 Advanced Search
- **Keyword search** for exact matches
- **Semantic search** with embeddings
- **Hybrid search** combining multiple strategies
- **Metadata filtering** and content filtering

### 📄 Text Processing
- **Smart chunking** with overlap and boundaries
- **Multiple chunking strategies** (character, token, semantic)
- **Fragment management** with metadata preservation
- **Cross-reference support** between chunks

### 🔄 Persistence & Performance
- **Cross-session persistence** with databases
- **Efficient querying** with indexes and optimization
- **Memory usage optimization** with cleanup strategies
- **Concurrent access** support

## 📊 Performance Characteristics

From the examples, typical performance:
- **Buffer Memory**: Instant access, no persistence
- **SQLite Memory**: ~1-5ms queries, local file storage
- **PostgreSQL Memory**: ~5-20ms queries, networked database
- **Vector Memory**: ~10-50ms semantic search, depends on embedding model
- **Enhanced Memory**: ~20-100ms complex queries, full-featured

## 🔧 Configuration Examples

### Memory with Custom Settings
```python
from agenticflow.memory import SQLiteMemory, MemoryConfig

config = MemoryConfig(
    max_messages=10000,
    enable_full_text_search=True,
    auto_cleanup=True,
    cleanup_threshold=0.8
)

memory = SQLiteMemory(
    database_path="./my_app.db",
    config=config
)
```

### Vector Memory with Multiple Stores
```python
from agenticflow.memory import VectorMemory
from agenticflow.vectorstores import ChromaVectorStore, FAISVectorStore

# Chroma backend
memory_chroma = VectorMemory(
    vector_store=ChromaVectorStore(
        collection_name="docs",
        persist_directory="./chroma_db"
    )
)

# FAISS backend  
memory_faiss = VectorMemory(
    vector_store=FAISVectorStore(
        dimension=1536,
        index_path="./faiss.index"
    )
)
```

### Enhanced Memory with Advanced Chunking
```python
from agenticflow.memory import EnhancedMemory
from agenticflow.text.chunking import SemanticTextSplitter

memory = EnhancedMemory(
    chunking_strategy=SemanticTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "],
        semantic_threshold=0.7
    ),
    enable_cross_references=True,
    max_fragments_per_message=20
)
```

## 🤝 Integration Examples

### With Retrievers
```python
from agenticflow.memory import VectorMemory
from agenticflow.retrievers import create_from_memory

# Memory with retriever integration
memory = VectorMemory(embedding_provider=embeddings)
retriever = create_from_memory(memory)  # Auto-detects semantic retrieval

# Combined search capabilities
results = await retriever.retrieve("machine learning concepts")
```

### With Agents
```python
from agenticflow import Agent, AgentConfig
from agenticflow.memory import EnhancedMemory

agent = Agent(AgentConfig(
    name="research_agent",
    instructions="You are a research assistant",
    memory=EnhancedMemory(
        enable_vector_search=True,
        chunking_strategy=RecursiveCharacterTextSplitter(chunk_size=1000)
    )
))
```

## 📚 Learn More

- **[AgenticFlow Documentation](../../README.md)**: Main project documentation
- **[Retriever Examples](../retrievers/README.md)**: Search and retrieval integration
- **[Vector Store Examples](../vector_stores/README.md)**: Vector storage backends
- **[Text Processing](../../src/agenticflow/text/)**: Chunking and processing utilities

---

**🧠 AgenticFlow Memory Systems provide flexible, scalable, and intelligent memory management for any AI application!**