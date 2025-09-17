# 🧪 AgenticFlow Examples & Demonstrations

This directory contains comprehensive examples demonstrating the capabilities of the AgenticFlow framework, including tool calling, memory systems, MCP integration, and advanced orchestration patterns.

## 🚀 Quick Start Examples

### 1. **Agent & Tool Calling** ⭐
- **`agent/final_tool_calling_validation.py`** - Comprehensive tool calling system validation
- **`agent/complex_orchestration_test.py`** - Advanced multi-agent workflow orchestration
- **`tools/direct_llm_tool_test.py`** - Direct LLM tool integration tests

```bash
# Test the enhanced tool calling system (requires Ollama with qwen2.5:7b)
python examples/agent/final_tool_calling_validation.py

# Test direct LLM tool integration  
python examples/tools/direct_llm_tool_test.py

# Advanced orchestration
python examples/agent/complex_orchestration_test.py
```

### 2. **Memory Systems** ⭐
- **`memory/memory_demo.py`** - Comprehensive memory backends demo (Buffer, SQLite, PostgreSQL)
- **`memory/memory_backends_test.py`** - Memory backend testing and validation
- **`memory/memory_chunking_integration_test.py`** - Advanced chunking and memory integration
- **`memory/advanced_memory_chunking_demo.py`** - Enhanced memory with chunking and analytics
- **`memory/test_vector_memory.py`** - Comprehensive vector memory testing suite
- **`memory/vector_store_memory_demo.py`** - Vector-enabled memory demonstrations

```bash
# Demonstrate different memory backends
python examples/memory/memory_demo.py

# Test comprehensive vector memory system
python examples/memory/test_vector_memory.py

# Vector store and memory integration
python examples/memory/vector_store_memory_demo.py
```

### 3. **Vector Stores & Embeddings** ⭐
- **`vector_stores/test_vector_stores.py`** - Vector store backend testing (FAISS, Chroma, In-memory)
- **`vector_stores/rag_demo.py`** - Retrieval-Augmented Generation demonstration
- **`embeddings/test_ollama_embeddings.py`** - Ollama embedding provider testing
- **`embeddings/test_huggingface_embeddings.py`** - HuggingFace embedding provider testing
- **`embeddings/embedding_providers_comparison.py`** - Compare different embedding providers
- **`embeddings/factory_example.py`** - Embedding factory usage examples

```bash
# Test vector stores
python examples/vector_stores/test_vector_stores.py

# RAG demo with embeddings
python examples/vector_stores/rag_demo.py

# Test embedding providers
python examples/embeddings/test_ollama_embeddings.py
```

### 4. **MCP Integration** ⭐
- **`mcp/mcp_integration_example.py`** - Complete MCP server integration examples
- **`mcp/validate_mcp_integration.py`** - MCP integration validation tests

```bash
# Run MCP integration examples (requires Ollama)
python examples/mcp/mcp_integration_example.py

# Validate MCP integration
python examples/mcp/validate_mcp_integration.py
```

### 5. **LLM Providers** ⭐
- **`llm_providers/custom_provider_example.py`** - Custom LLM provider implementation

```bash
# Custom provider example
python examples/llm_providers/custom_provider_example.py
```

### 6. **Realistic Workflows** ⭐
- **`workflows/realistic_data_analysis.py`** - Data analysis workflow demonstration
- **`workflows/realistic_content_workflow.py`** - Content creation and management workflow  
- **`workflows/realistic_ecommerce_processing.py`** - E-commerce order processing workflow
- **`workflows/real_web_search_example.py`** - Real web search using external MCP server

```bash
# Run workflow examples
python examples/workflows/realistic_data_analysis.py
python examples/workflows/real_web_search_example.py
```

---

## 🔧 Tool Calling System

AgenticFlow features an enhanced tool calling system that allows agents to automatically detect and execute tools based on natural language requests.

### **Key Features:**
- ✅ **Natural Language Detection**: "What time is it?" → `get_time` tool → "2025-09-17 01:23:01"
- ✅ **Multiple Patterns**: JSON tool calls, explicit mentions, and implicit detection
- ✅ **Parameter Extraction**: Automatic parameter extraction for complex tools
- ✅ **Real-time Execution**: Complete LLM → Parser → Tool → Response pipeline

### **Example Usage:**
```python
from agenticflow.tools import tool
from agenticflow import Agent

@tool("get_time", "Gets the current date and time")
def get_time_tool() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Agent automatically detects and uses tools
result = await agent.execute_task("What time is it right now?")
# Result: Tool executed → "Current time: 2025-09-17 01:23:01"
```

---

## 🧠 Memory & Vector Storage Systems

AgenticFlow provides comprehensive memory and vector storage capabilities:

### **Memory Backends:**
| Backend | Speed | Persistence | Sessions | Search | Use Case |
|---------|--------|-------------|----------|---------|----------|
| **Buffer** | ⚡⚡⚡ | ❌ | ❌ | Basic | Development, Chat |
| **Enhanced** | ⚡⚡ | ✅ | ✅ | Semantic | Advanced features |
| **Vector** | ⚡⚡ | ✅ | ✅ | Semantic | AI-powered search |
| **SQLite** | ⚡⚡ | ✅ | ✅ | Full-text | Personal, Local |
| **PostgreSQL** | ⚡ | ✅ | ✅ | Advanced | Enterprise, Multi-user |

### **Vector Store Backends:**
| Backend | Type | Persistence | Scale | Use Case |
|---------|------|-------------|-------|----------|
| **In-Memory** | Ephemeral | ❌ | Small | Development, Testing |
| **FAISS** | Local | ✅ | Large | Fast local search |
| **Chroma** | Local/Remote | ✅ | Medium | Versatile embedding DB |
| **Pinecone** | Cloud | ✅ | Massive | Managed enterprise |
| **Qdrant** | Self-hosted | ✅ | Large | Advanced filtering |

### **Example Usage:**
```python
# Traditional SQLite memory
config = AgentConfig(
    name="assistant_agent",
    memory=MemoryConfig(
        type="sqlite",
        connection_params={"database": "agent_memory.db"}
    )
)

# Vector-enabled memory with chunking
vector_config = VectorMemoryConfig(
    vector_store_config=VectorStoreFactory.create_faiss_config(
        persist_path="./agent_vectors.faiss",
        embedding_dimension=1536
    ),
    chunking_config=ChunkingConfig(
        strategy=ChunkingStrategy.SEMANTIC,
        chunk_size=1000
    )
)

vector_memory = VectorMemory(config, vector_config, embeddings)
# Semantic search across conversation history!
```

---

## 🧩 Text Chunking System

Advanced text chunking for handling long documents and enabling semantic search:

### **Chunking Strategies:**
| Strategy | Best For | Boundary | Use Case |
|----------|----------|----------|----------|
| **Fixed Size** | Uniform chunks | Character/Word | Simple processing |
| **Sentence** | Natural breaks | Sentence | Readable chunks |
| **Recursive** | Hierarchical | Paragraph → Sentence → Word | General purpose |
| **Markdown** | Structured docs | Headers/Sections | Documentation |
| **Semantic** | AI-powered | Meaning-based | Advanced search |

### **Smart Chunking:**
```python
# Automatic strategy selection based on content analysis
chunks = await chunking_manager.smart_chunk(
    text,
    auto_embeddings=True  # Generate embeddings automatically
)

# Manual strategy selection
chunks = await chunk_text(
    text,
    strategy=ChunkingStrategy.SEMANTIC,
    chunk_size=1000,
    chunk_overlap=200
)
```

### **Features:**
- ✅ **5 Chunking Strategies** - From simple to AI-powered semantic
- ✅ **Automatic Strategy Selection** - Analyzes content and suggests optimal approach
- ✅ **Embedding Integration** - Seamless with vector stores
- ✅ **Metadata Tracking** - Comprehensive chunk information and relationships
- ✅ **Overlap Management** - Smart overlap to maintain context
- ✅ **Boundary Detection** - Respects natural text boundaries

---

## 🔌 MCP (Model Context Protocol) Integration

Connect AgenticFlow agents to external MCP servers for extended tool capabilities.

### **Core MCP Concepts:**
- **Server Connection**: Connect via stdio, HTTP, or WebSocket transports
- **Tool Discovery**: Automatically discover available tools from MCP servers
- **Tool Execution**: Call MCP tools with proper parameter validation
- **Error Handling**: Graceful handling of connection and execution errors

### **Available Test Tools:**
| Tool | Parameters | Description |
|------|------------|-------------|
| `get_user` | `user_id: int` | Get user information by ID |
| `list_projects` | `status?: string` | List projects, optionally filtered |
| `create_task` | `title: string, project: string` | Create a new task |
| `search_data` | `query: string, data_type?: string` | Search across data types |
| `get_stats` | none | Get comprehensive statistics |

### **Example Workflow:**
```
1. MCP Server Startup → Exposes tools
2. Agent Connection → Discovers and registers tools  
3. Agent Execution → "Get user 1" → Calls get_user(user_id=1)
4. Result Processing → Returns formatted response
```

---

## ⚙️ Prerequisites & Setup

### **Environment Setup:**
```bash
# Core requirements
export OPENAI_API_KEY="your-openai-api-key"  # For OpenAI models
export GROQ_API_KEY="your-groq-api-key"      # For Groq models

# For Ollama (recommended for testing)
# Install Ollama and pull models:
ollama pull qwen2.5:7b
ollama pull granite3.2:8b
```

### **Optional Dependencies:**
```bash
# Memory backends
pip install agenticflow[memory]  # SQLite + PostgreSQL support

# MCP integration  
pip install mcp fastmcp          # Official MCP SDK

# All features
pip install agenticflow[all]     # Everything included
```

---

## 🧪 Running Examples

### **Quick Tests:**
```bash
# Basic functionality
python examples/agent/final_tool_calling_validation.py

# Memory systems
python examples/memory/memory_demo.py

# Vector memory comprehensive test
python examples/memory/test_vector_memory.py

# MCP integration
python examples/mcp/mcp_integration_example.py
```

### **Comprehensive Testing:**
```bash
# Run all major examples
examples=(
    "agent/final_tool_calling_validation.py"
    "memory/memory_demo.py" 
    "memory/test_vector_memory.py"
    "mcp/mcp_integration_example.py"
    "agent/complex_orchestration_test.py"
)

for example in "${examples[@]}"; do
    echo "🧪 Running $example"
    python "examples/$example"
    echo "✅ Completed $example"
    echo "---"
done
```

---

## 📈 Performance & Validation Results

### **Tool Calling System:**
- ✅ **50% Success Rate Improvement** (0% → 50% validated)
- ✅ **Natural Language Detection** working with multiple patterns
- ✅ **Real-time Tool Execution** in agent workflows
- ✅ **Parameter Extraction** for complex tools

### **Memory System:**
- ✅ **Circular Import Issues** completely resolved
- ✅ **Cross-Session Persistence** working with database backends
- ✅ **Multi-Backend Support** with automatic fallbacks
- ✅ **Session Management** with statistics and analytics

### **MCP Integration:**
- ✅ **Multi-Server Support** with automatic discovery
- ✅ **Tool Registration** seamless with AgenticFlow
- ✅ **Error Resilience** with retry logic and health monitoring
- ✅ **Production Ready** with process isolation

---

## 🛠️ Development & Contribution

### **Adding New Examples:**
1. Follow naming convention: `feature_demo.py` or `feature_test.py`
2. Include comprehensive docstrings and comments
3. Add validation and error handling
4. Update this README with example description
5. Ensure examples work with minimal setup

### **Best Practices:**
- Use clear, descriptive filenames
- Include both success and error scenarios
- Provide realistic use cases and data
- Document prerequisites and expected outputs
- Test with multiple LLM providers when possible

---

## 🔍 Troubleshooting

### **Common Issues:**

**"No module named 'agenticflow'"**
```bash
# Ensure you're in the project directory
cd agenticflow
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**"Tool calling not working"**
- Ensure LLM provider is properly configured
- Check that tools are registered with the agent
- Verify the LLM model supports function calling patterns

**"Memory backend errors"**
```bash
# Install memory dependencies
pip install agenticflow[memory]
```

**"MCP server connection failed"**
- Ensure MCP server is running
- Check connection configuration (stdio/HTTP/WebSocket)
- Verify MCP SDK installation: `pip install mcp`

---

**Ready to explore AgenticFlow?** 🚀

Start with the **Quick Start Examples** above, then dive into the advanced features that interest you most!
