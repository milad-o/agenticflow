# 🤖 AgenticFlow

> **Production-ready AI agent framework with embedded Interactive Task Control, unified orchestration, and enterprise-grade multi-agent coordination**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Async Support](https://img.shields.io/badge/async-native-green.svg)](https://docs.python.org/3/library/asyncio.html)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://spec.modelcontextprotocol.io/)
[![Examples](https://img.shields.io/badge/examples-100+-brightgreen.svg)](examples/)

> **🚀 New to AgenticFlow?** Start with our [**Quick Start Guide**](examples/README.md) and explore 100+ comprehensive examples!

---

## 🚀 What's New in v1.0.1 (Latest)

✨ **Pydantic v2 Compatibility** - Full migration to Pydantic v2 with ConfigDict patterns  
🔧 **API Cleanup** - Removed deprecated methods and streamlined current API  
🧪 **Enhanced Testing** - All tests passing with improved reliability  
🔄 **Unified Architecture** - Single TaskOrchestrator with embedded real-time streaming  
🎯 **Enhanced Performance** - Streamlined architecture with improved task throughput  

## 🚀 What's New in v1.0.0 (Major Release)

⚡ **Embedded Interactive Control** - Interactive features fully integrated into TaskOrchestrator  
👁️ **Simplified API** - Clean, intuitive interface with embedded coordination capabilities  
🔍 **Advanced Retrieval Systems** - 15+ retriever types with text, semantic, and composite strategies  
🧠 **Smart Memory Architecture** - Cross-session persistence with vector search capabilities  
🔗 **Production MCP Integration** - Multi-server support with custom tool development  
📈 **Production Ready** - Enterprise-grade orchestration with comprehensive testing  
🤖💬 **Interactive RAG Chatbots** - Production conversational AI with knowledge base retrieval

## ✨ Core Features

🏗️ **Multi-Agent Architecture** - Star, P2P, Hierarchical, Pipeline, Mesh, Custom topologies  
⚡ **Embedded Task Orchestration** - Unified TaskOrchestrator with built-in interactive control
🔍 **Intelligent Retrieval** - Text, semantic, and hybrid search with 15+ retriever types  
🧠 **Smart Memory Systems** - Buffer, SQLite, PostgreSQL, Vector with chunking strategies  
🔗 **MCP Integration** - Secure tool execution with multi-server coordination  
🛠️ **Production Tooling** - LLM providers, custom tools, monitoring, error recovery  
🔧 **Enterprise Ready** - Type-safe config, async-native, comprehensive testing

## 🚀 Quick Start

### Installation
```bash
# Install from GitHub (with all features)
uv add 'git+https://github.com/milad-o/agenticflow.git[all]'

# Verify installation
curl -s https://raw.githubusercontent.com/milad-o/agenticflow/main/scripts/test_installation.py | python
```

### Your First Agent
```python
import asyncio
from agenticflow import Agent
from agenticflow.config.settings import AgentConfig, LLMProviderConfig, LLMProvider

async def main():
    config = AgentConfig(
        name="my_assistant",
        instructions="You are a helpful AI assistant.",
        llm=LLMProviderConfig(
            provider=LLMProvider.GROQ,  # Free tier available
            model="llama-3.1-8b-instant"
        )
    )
    
    agent = Agent(config)
    await agent.start()
    
    result = await agent.execute_task("What is 2 + 2?")
    print(result["response"])
    
    await agent.stop()

asyncio.run(main())
```

### Multi-Agent System with .as_tool()
```python
from agenticflow import RAGAgent, Agent
from agenticflow.chatbots import ChatbotConfig

# Create specialist agents
researcher = Agent(researcher_config)  
writer = Agent(writer_config)

# Create RAGAgent supervisor
supervisor = RAGAgent(ChatbotConfig(
    name="Project Manager",
    llm=llm_config,
    instructions="Coordinate specialists for complex tasks"
))

# Convert agents to tools and register
research_tool = researcher.as_tool("research", "Delegate research tasks")
writing_tool = writer.as_tool("writing", "Delegate writing tasks")

supervisor.register_async_tool(research_tool)
supervisor.register_async_tool(writing_tool)

# Natural supervision through tool usage!
result = await supervisor.execute_task("Research and write about renewable energy")
```

## 🎯 Real-World Examples

### 🌟 **Enterprise Super Agentic Chatbot** 🆕✨
**File-focused multi-agent system** showcasing the ultimate AgenticFlow capabilities
```bash
cd examples/enterprise_chatbot
source ../../.env  # Set GROQ_API_KEY
uv run python enterprise_super_agent.py

# Try these commands:
# help - Show all file-focused capabilities
# "Create JSON file and analyze its structure"
# "Convert CSV to XML with validation"
# "Map Python file dependencies"
```
**🚀 Ultimate Features**:
- **🗂️ Multi-Format Analysis**: 15+ formats (JSON, XML, CSV, YAML, Python, SQL, etc.)
- **🔄 Advanced File Operations**: Conversion, editing, merging, pattern detection
- **🗃️ Database Integration**: SQLite queries, schema analysis, reporting
- **🤖 Multi-Agent Architecture**: Specialized FileAgent, DataAgent, CodeAgent, AnalyticsAgent
- **⚡ Real-time Monitoring**: Progress tracking, resource usage, tool analytics
- **💬 Conversational Interface**: Natural language for all file operations

### 🤖💬 **RAGAgent & Multi-Agent Coordination**
**Natural agent supervision** with the new `.as_tool()` API for clean multi-agent systems
```bash
# RAGAgent natural supervision demo
uv run python examples/chatbots/rag_supervision_example.py

# Multi-agent coordination patterns
uv run python examples/chatbots/simple_rag_with_tools.py

# .as_tool() method testing
uv run python examples/chatbots/test_as_tool_method.py
```
**🎆 New Features**: 
- **Natural Supervision**: RAGAgent coordinates specialists via `.as_tool()` delegation
- **Clean Architecture**: No complex inheritance, just composition patterns
- **Hybrid Intelligence**: Knowledge base + traditional tools + agent tools
- **Production Ready**: Works with existing workflow orchestration systems

### 🏢 **Complete Business Systems** ⭐
**Production-ready sales analysis** processing $96K+ revenue with multi-agent coordination
```bash
export GROQ_API_KEY="your-key"
uv run python examples/realistic_systems/sales_analysis/simple_sales_analysis.py
```

### 🔍 **Advanced Retrieval Systems**
**15+ retriever types** with text, semantic, and composite strategies
```bash
uv run python examples/retrievers/retriever_demo.py
```

### 🧠 **Smart Memory & Vector Search**
**Cross-session persistence** with semantic search across conversations
```bash
uv run python examples/memory/test_vector_memory.py
```

### 🔗 **MCP Integration**
**Multi-server coordination** with secure tool execution
```bash
uv run python examples/mcp/mcp_integration_example.py
```

### 🌊 **Multi-Agent Workflows**
**Complex orchestration** with multiple topology patterns
```bash
uv run python examples/workflows/realistic_data_analysis.py
```

### ⚡ **Task Orchestration with Embedded Interactive Control**
**Unified orchestration** with built-in real-time streaming and coordination
```bash
# Core orchestrator demo with embedded interactive control
uv run python examples/orchestration/task_orchestrator_demo.py

# Simple streaming example with embedded features
uv run python examples/orchestration/simple_streaming_example.py

# Complex workflows with advanced coordination
uv run python examples/orchestration/complex_orchestration_test.py
```

### 🛠️ **Tool Calling System**
**Enhanced natural language detection** with 50% success improvement
```bash
uv run python examples/tools/final_tool_calling_validation.py
```

## 📚 Documentation Hub

### 🚀 **Quick Start Paths**
| **Beginner** | **Advanced** | **Production** |
|--------------|--------------|----------------|
| [**Chatbots**](examples/chatbots/) | [**Retriever Systems**](examples/retrievers/) | [**Business Systems**](examples/realistic_systems/) |
| [**Tools**](examples/tools/) | [**MCP Integration**](examples/mcp/) | [**Performance Testing**](examples/performance/) |
| [**Orchestration**](examples/orchestration/) | [**Vector Stores**](examples/vector_stores/) | [**Production Deployment**](docs/) |
| [**Memory Systems**](examples/memory/) | [**Workflows**](examples/workflows/) |  |

### 📂 **Feature Documentation**
|| **System** | **Guide** | **Examples** | **API** |
||------------|-----------|--------------|----------|
|| **Orchestration** | [Task Management](examples/orchestration/README.md) | [Embedded Interactive Control](examples/orchestration/) | Streaming, Coordination |
|| **Chatbots** | [Multi-Agent RAG](examples/chatbots/README.md) | [Natural Supervision](examples/chatbots/) | .as_tool() API, Delegation |
|| **Tools** | [Tool Integration](examples/tools/README.md) | [Natural Language](examples/tools/) | LLM-Powered, Validation |
| **Retrievers** | [Advanced Search](examples/retrievers/README.md) | [15+ Types](examples/retrievers/) | Text, Semantic, Composite |
| **Memory** | [Smart Persistence](examples/memory/README.md) | [Vector Search](examples/memory/) | Buffer, SQLite, Vector |
| **Workflows** | [Multi-Agent](examples/workflows/README.md) | [Topologies](examples/workflows/) | Star, P2P, Hierarchical |
| **MCP** | [Tool Protocol](examples/mcp/README.md) | [Multi-Server](examples/mcp/) | Secure, Extensible |
| **Embeddings** | [Provider Comparison](examples/embeddings/README.md) | [Quality Analysis](examples/embeddings/) | OpenAI, Ollama, HF |

## 🛠️ Complete Feature Set

```
agenticflow/
├── 🔍 Advanced Retrieval Systems
│   ├── Text Retrievers: Keyword, BM25, Fuzzy, Regex, FullText
│   ├── Semantic Retrievers: Cosine, Euclidean, Dot Product, Manhattan
│   └── Composite Retrievers: Ensemble, Hybrid, Contextual, Fusion
├── 🧠 Smart Memory Architecture
│   ├── Backends: Buffer, SQLite, PostgreSQL, Vector
│   ├── Chunking: Fixed, Sentence, Recursive, Markdown, Semantic
│   └── Features: Cross-session persistence, semantic search
├── ⚡ Embedded Task Orchestration
│   ├── Unified TaskOrchestrator: Built-in interactive control and streaming
│   ├── Agent-to-Agent Communication: Embedded A2A messaging for coordination
│   ├── Real-time coordination: Live progress updates, task interruption
│   └── Event-driven architecture: Comprehensive coordination system
├── 🤖 Multi-Agent Coordination
│   ├── Topologies: Star, P2P, Hierarchical, Pipeline, Mesh, Custom
│   └── Orchestration: DAG workflows, task dependencies, priorities
├── 🔗 MCP Integration
│   ├── Multi-server support with automatic discovery
│   ├── Secure sandboxed tool execution
│   └── Custom server development framework
├── 💾 Vector Store Ecosystem
│   ├── Backends: FAISS, Chroma, Pinecone, Qdrant, In-Memory
│   └── Features: RAG, similarity search, performance optimization
├── 🧮 Embedding Providers
│   ├── Providers: OpenAI, Ollama, HuggingFace, Groq
│   └── Features: Quality comparison, cost analysis, local deployment
├── 🛠️ Production Tooling
│   ├── LLM Providers: OpenAI, Groq, Ollama, Azure with failover
│   ├── Tool System: Natural language detection, parameter extraction
│   └── Monitoring: Performance metrics, health checks, error recovery
└── 📚 Comprehensive Documentation
    ├── 100+ Examples: Step-by-step guides for all features
    ├── Business Systems: End-to-end production applications
    └── Performance Testing: Benchmarking and optimization guides
```

## 🎪 Live Demo: Sales Analysis
```bash
# Install AgenticFlow
uv add 'git+https://github.com/milad-o/agenticflow.git[all]'

# Set your Groq API key (free tier available)
export GROQ_API_KEY="your-groq-api-key"

# Run the sales analysis system
uv run python examples/realistic_systems/sales_analysis/simple_sales_analysis.py

# ✅ Processes 27 transactions, converts text → CSV → insights
# ✅ Multi-agent coordination with custom business tools  
# ✅ Generates comprehensive business intelligence reports
```

## 📈 Performance & Scale

### 🚀 **System Performance**
| Component | Throughput | Latency | Memory | Success Rate |
|-----------|------------|---------|--------|--------------|
| **Agents** | 65+ tasks/s | <200ms | <100MB | 99%+ |
| **Memory** | 1000+ ops/s | <50ms | <50MB | 100% |
| **Retrievers** | 500+ queries/s | <100ms | <200MB | 98%+ |
| **Workflows** | 20+ concurrent | <2s | <500MB | 95%+ |

### 📈 **Validated Features**
✅ **Tool Calling**: 50% success rate improvement over previous versions  
✅ **Memory Systems**: Cross-session persistence with vector search  
✅ **Retriever Systems**: 15+ types with composite strategies  
✅ **MCP Integration**: Multi-server support with health monitoring  
✅ **Production Ready**: Enterprise-grade error handling and monitoring  
✅ **Scalability**: Tested with 50+ agents in complex topologies

## 🤝 Community & Support

- 📖 **Documentation**: [Usage Guide](docs/usage-guide.md) | [API Reference](docs/api-reference.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/milad-o/agenticflow/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/milad-o/agenticflow/discussions)
- 🤝 **Contributing**: See [Contributing Guidelines](CONTRIBUTING.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ for the AI developer community** 

⭐ **Star this repo** if AgenticFlow helps you build amazing AI systems!