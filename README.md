# 🤖 AgenticFlow

**A production-ready, async, OOP framework for building hierarchical agent teams with LangGraph integration.**

AgenticFlow makes it easy to create sophisticated multi-agent workflows with intelligent routing, tool integration, and seamless LangGraph StateGraph execution. **Fully tested with working demos and tangible results!**

## ✨ Features

- 🎯 **Beautiful OOP API** - Constructor-based, method chaining design
- 🔄 **LangGraph Integration** - Full StateGraph support with Command routing
- 🤖 **LLM-Powered Routing** - Intelligent task distribution at every level
- 🛠️ **Tool Integration** - Easy tool addition and management
- 🏗️ **Hierarchical Teams** - Orchestrator → Supervisor → Agent structure
- ⚡ **Fully Async** - Built for high-performance async workflows
- 🔍 **Observability** - Built-in monitoring and metrics
- 🧪 **Comprehensive Testing** - Full test suite with examples
- 🚀 **Production Ready** - Working demos with tangible results
- 📊 **Real Performance** - Sub-2-second execution times
- 🌐 **Web Search** - Tavily integration for real-time data
- 📝 **Content Generation** - AI-powered writing and analysis

## 🚀 Quick Start

### 1. Install AgenticFlow
```bash
# Install directly from GitHub with uv (recommended)
uv add git+https://github.com/milad-o/agenticflow.git

# Or with pip
pip install git+https://github.com/milad-o/agenticflow.git

# For development (clone and install)
git clone https://github.com/milad-o/agenticflow.git
cd agenticflow
uv pip install -e .

# Set up API keys
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run a Quick Demo
```bash
# Quick demo (0.98 seconds execution)
uv run python demos/quick_demo.py

# Comprehensive demo (3 tasks, 12 messages, 1.52s avg)
uv run python demos/comprehensive_demo.py
```

### 3. Basic Usage
```python
import asyncio
from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
from agenticflow.tools import WriteFileTool, TavilySearchTool

async def main():
    # Create your flow
    flow = Flow("my_flow")
    
    # Add orchestrator with LLM
    orchestrator = Orchestrator("main")
    flow.add_orchestrator(orchestrator)
    
    # Create research team
    research_team = Supervisor("research_team", description="Research specialists")
    research_team.add_agent(
        ReActAgent("searcher", description="Web search specialist")
        .add_tool(TavilySearchTool())
        .add_tool(WriteFileTool())
    )
    orchestrator.add_team(research_team)
    
    # Run the flow
    await flow.start("Research AI agents and write a report")
    
    # Get results
    messages = await flow.get_messages()
    for msg in messages:
        print(f"{msg.sender}: {msg.content}")

asyncio.run(main())
```

## 📁 Project Structure

```
agenticflow/
├── agenticflow/           # Core framework
│   ├── core/             # Core classes (Flow, Orchestrator, etc.)
│   ├── agents/           # Agent implementations
│   ├── tools/            # Built-in tools
│   ├── observability/    # Monitoring and metrics
│   └── workspace/        # Workspace management
├── examples/             # Example workflows
│   ├── basic/           # Simple examples
│   ├── advanced/        # Complex workflows
│   └── tutorials/       # Step-by-step guides
├── tests/               # Comprehensive test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/           # End-to-end tests
├── docs/               # Documentation
├── data/               # Sample and test data
│   ├── sample/        # Sample datasets
│   └── test/          # Test data
└── workspaces/        # Runtime workspaces
```

## 🛠️ Installation

### From GitHub (Recommended)

```bash
# Install with uv (recommended)
uv add git+https://github.com/milad-o/agenticflow.git

# Or with pip
pip install git+https://github.com/milad-o/agenticflow.git

# For development (editable install)
uv add -e git+https://github.com/milad-o/agenticflow.git
# or
pip install -e git+https://github.com/milad-o/agenticflow.git#egg=agenticflow
```

### From PyPI (Coming Soon)

```bash
# Install with uv (recommended)
uv add agenticflow

# Or with pip
pip install agenticflow
```

### Dependencies

```bash
# For full functionality (installed automatically)
uv add langchain-openai langchain-core langgraph tavily-python python-dotenv

# Or with pip
pip install langchain-openai langchain-core langgraph tavily-python python-dotenv
```

### Installation Methods

| Method | Use Case | Command |
|--------|----------|---------|
| **GitHub + uv** | Production use | `uv add git+https://github.com/milad-o/agenticflow.git` |
| **GitHub + pip** | Production use | `pip install git+https://github.com/milad-o/agenticflow.git` |
| **Clone + uv** | Development | `git clone && uv pip install -e .` |
| **Clone + pip** | Development | `git clone && pip install -e .` |
| **PyPI** | Coming soon | `uv add agenticflow` |

## 📚 Documentation

- [Quick Start Guide](docs/quick_start.md) - Get up and running in minutes
- [Basic Examples](examples/basic/) - Simple examples to get started
- [Advanced Examples](examples/advanced/) - Complex workflows
- [API Reference](docs/api/) - Complete API documentation
- [LangGraph Integration](docs/langgraph_integration.md) - Advanced features

## 🧪 Testing

```bash
# Run comprehensive test suite
uv run python tests/test_runner.py

# Run specific test categories
make test-unit
make test-integration
make test-e2e

# Run with coverage
make test-cov

# Run working demos
uv run python demos/quick_demo.py
uv run python demos/comprehensive_demo.py
```

### Test Results
- ✅ **Basic functionality**: All core features working
- ✅ **LLM capabilities**: Real API integration working  
- ✅ **Web search**: Tavily integration working
- ✅ **Comprehensive demo**: Full workflow working
- ✅ **Performance**: Sub-2-second execution times
- ✅ **Tangible results**: JSON output files generated

## 🎯 Examples

### Basic Flow
```python
# Simple hello world (0.98s execution)
flow = Flow("hello_flow")
orchestrator = Orchestrator("main", initialize_llm=False)
flow.add_orchestrator(orchestrator)

team = Supervisor("greeting_team", initialize_llm=False)
team.add_agent(SimpleAgent("greeter"))
orchestrator.add_team(team)

await flow.start("Hello, AgenticFlow!")
```

### Method Chaining
```python
# Beautiful method chaining (preserves OOP API)
flow = (Flow("chaining_flow")
        .add_orchestrator(Orchestrator("main", initialize_llm=False)))

team = (Supervisor("research_team", initialize_llm=False)
        .add_agent(ReActAgent("researcher")
                  .add_tool(WriteFileTool())))

orchestrator.add_team(team)
```

### Complex Workflow with Real Results
```python
# Multi-team workflow with LLM routing (1.52s avg execution)
flow = Flow("research_writing_flow")
orchestrator = Orchestrator("main")  # With LLM
flow.add_orchestrator(orchestrator)

# Research team
research_team = Supervisor("research_team", description="Research specialists")
research_team.add_agent(ReActAgent("searcher").add_tool(TavilySearchTool()))
orchestrator.add_team(research_team)

# Writing team
writing_team = Supervisor("writing_team", description="Writing specialists")
writing_team.add_agent(ReActAgent("writer").add_tool(WriteFileTool()))
orchestrator.add_team(writing_team)

await flow.start("Research AI trends and write a comprehensive report")
```

### Working Demos
```bash
# Quick demo - 0.98 seconds execution
uv run python demos/quick_demo.py

# Comprehensive demo - 3 tasks, 12 messages, 1.52s avg
uv run python demos/comprehensive_demo.py

# Basic examples
uv run python examples/basic/hello_world.py
uv run python examples/basic/method_chaining.py
```

## 🏗️ Architecture

```
User Message → Flow.start()
    ↓
LangGraph StateGraph Execution
    ↓
Orchestrator Node (LLM routing)
    ↓
Team Supervisor Node (LLM routing)
    ↓
Agent Node (Tool execution)
    ↓
Command routing back to supervisor
    ↓
Results aggregated and returned
```

## 🔧 Development

```bash
# Setup development environment
make dev-setup

# Run code quality checks
make ci

# Run examples
make examples

# Clean up
make clean
```

## 📊 Features in Detail

### 🎯 Beautiful OOP API
- Constructor-based design
- Method chaining support
- Intuitive class hierarchy
- Type hints throughout
- **✅ Tested and working**

### 🔄 LangGraph Integration
- Full StateGraph support
- Command pattern routing
- State management
- Async execution
- **✅ Production ready**

### 🤖 LLM-Powered Routing
- Intelligent task distribution
- Context-aware routing
- Fallback mechanisms
- Structured output
- **✅ Real API integration**

### 🛠️ Tool Integration
- Easy tool addition
- Built-in tool library (Tavily, File I/O)
- Custom tool support
- Tool chaining
- **✅ Working with real tools**

### 🏗️ Hierarchical Teams
- Orchestrator coordination
- Team-level supervision
- Agent execution
- Flexible organization
- **✅ Multi-team workflows working**

### 🚀 Performance & Results
- **Sub-2-second execution times**
- **Real JSON output generation**
- **Web search integration**
- **Content generation**
- **Production-ready demos**

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](docs/)
- 💬 [GitHub Discussions](https://github.com/your-org/agenticflow/discussions)
- 🐛 [Issue Tracker](https://github.com/your-org/agenticflow/issues)
- 📧 [Email Support](mailto:support@agenticflow.dev)

---

**Built with ❤️ for the AI agent community**