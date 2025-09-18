# 🤖 RAGAgent & Multi-Agent Chatbot Examples

This directory contains examples demonstrating AgenticFlow's RAGAgent capabilities and the new `.as_tool()` API for natural multi-agent supervision and coordination.

## 🌟 Current Examples

### 🎯 RAGAgent Natural Supervision
**File:** `rag_supervision_example.py`

Demonstrates how RAGAgent can naturally supervise specialist agents using the clean `.as_tool()` API:

- **Project Manager (RAGAgent)**: Knowledge-powered supervisor that coordinates specialists
- **Specialist Agents**: Data Analyst, Report Writer, Research Specialist
- **Natural Delegation**: Uses `.as_tool()` to convert agents into delegation tools
- **Clean Architecture**: No complex inheritance, just composition

```bash
uv run python examples/chatbots/rag_supervision_example.py
```

**Key Features:**
- ✅ RAGAgent as natural supervisor through behavior, not inheritance
- ✅ Clean `.as_tool()` API for agent-to-tool conversion  
- ✅ Automatic error handling and metadata tracking
- ✅ Works with existing workflow orchestration systems
- ✅ Leverages existing tool infrastructure

### 🔧 Multi-Agent Coordination Patterns
**File:** `simple_rag_with_tools.py`

Shows three powerful patterns for building sophisticated RAG systems:

1. **Traditional Tools**: RAGAgent with APIs, calculators, web search
2. **Agent Tools**: Using `.as_tool()` for multi-agent coordination
3. **Hybrid Approach**: Knowledge base + traditional tools + agent tools

```bash
uv run python examples/chatbots/simple_rag_with_tools.py
```

**Demonstrates:**
- 🏗️ Team coordination via RAGAgent
- 🔧 Clean `.as_tool()` delegation API
- 💡 Intelligent source selection (knowledge vs tools vs agents)
- 🚀 Recommended architecture patterns

### 🧪 .as_tool() Method Testing
**File:** `test_as_tool_method.py`

Comprehensive testing of the new `.as_tool()` method:

- **Basic Functionality**: Agent-to-tool conversion
- **Supervision Scenarios**: Realistic multi-agent coordination
- **API Comparison**: Old proxy approach vs new `.as_tool()` method

```bash
uv run python examples/chatbots/test_as_tool_method.py
```

**Testing Coverage:**
- ✅ Tool creation and registration
- ✅ Schema generation and metadata
- ✅ Delegation execution and results
- ✅ Error handling and cleanup

### 📊 Performance Testing
**File:** `performance_test.py`

Performance benchmarking suite for RAG chatbots:

- **Retrieval Latency**: Measures search performance
- **Response Generation**: Full end-to-end timing
- **Memory Usage**: Resource consumption tracking
- **Concurrent Load**: Throughput under load

```bash
uv run python examples/chatbots/performance_test.py
```

## 🎨 Architecture Patterns

### 1. Natural Supervision via .as_tool()

```python
# Create specialists
data_analyst = Agent(AgentConfig(...))
report_writer = Agent(AgentConfig(...))

# Create RAGAgent supervisor
supervisor = RAGAgent(ChatbotConfig(...))

# Convert agents to tools
analyst_tool = data_analyst.as_tool("data_analysis", "Handle data tasks")
writer_tool = report_writer.as_tool("report_writing", "Create reports")

# Register with supervisor
supervisor.register_async_tool(analyst_tool)
supervisor.register_async_tool(writer_tool)

# Supervisor now delegates via tools naturally!
```

### 2. Hybrid RAG System

```python
# RAGAgent with everything
hybrid_rag = RAGAgent(ChatbotConfig(
    knowledge_sources=[...],        # Static documents
    tools=["web_search", "calc"],   # Traditional tools
    # + Agent tools via .as_tool()  # Dynamic delegation
))
```

### 3. Intelligent Source Selection

The RAGAgent automatically chooses the best information source:
- 📚 **Knowledge Base**: For curated facts, policies, procedures
- 🌐 **Traditional Tools**: For real-time data, calculations, APIs
- 🤖 **Agent Tools**: For complex analysis requiring specialist expertise
- 🧠 **LLM Knowledge**: As fallback for general questions

## 📁 Knowledge Base

The `knowledge_base/` directory contains curated scientific content for testing:

- `biology_life_sciences.txt` - Cell biology, evolution, ecosystems
- `ocean_life.txt` - Marine ecosystems, deep sea exploration  
- `physics_chemistry.txt` - Quantum physics, chemical reactions
- `space_exploration.txt` - Solar system, cosmic phenomena
- `wildlife_behavior.txt` - Animal intelligence, adaptations

## 🚀 Key Benefits of New API

### .as_tool() vs Legacy Approaches

**OLD (Complex Inheritance):**
```python
class RAGSupervisorAgent(SupervisorAgent, RAGAgent):
    # Complex multiple inheritance
    # Hard to maintain and extend
```

**NEW (Clean Composition):**
```python
# Simple, clean delegation via .as_tool()
agent_tool = specialist.as_tool("task_name", "description")
supervisor.register_async_tool(agent_tool)
```

**Benefits:**
- ✅ **Discoverable**: IDE autocomplete support
- ✅ **Standard**: Part of core Agent interface  
- ✅ **Flexible**: Works with any Agent subclass
- ✅ **Maintainable**: No complex inheritance hierarchies
- ✅ **Extensible**: Leverages existing tool infrastructure

## 🔧 Usage Patterns

### Basic Agent Supervision
```python
# Convert any agent to a delegation tool
tool = agent.as_tool(
    name="delegation_task",
    description="Delegate specific tasks to this specialist"
)

# Use with any agent that supports tools
supervisor.register_async_tool(tool)
```

### Multi-Specialist Coordination  
```python
# Create team of specialists
analysts = [create_analyst(domain) for domain in domains]

# Convert all to tools
analyst_tools = [
    agent.as_tool(f"{domain}_analysis", f"Analyze {domain} data")
    for agent, domain in zip(analysts, domains)
]

# Register with coordinator
for tool in analyst_tools:
    coordinator.register_async_tool(tool)
```

## 🎯 Recommended Architecture

For production RAG systems, we recommend:

1. **RAGAgent as Intelligent Coordinator**
   - Uses knowledge base for documented information
   - Has access to traditional tools for real-time data
   - Coordinates specialist agents via `.as_tool()` delegation

2. **Specialist Agents for Complex Tasks**
   - Domain-specific expertise (analysis, writing, research)
   - Converted to tools via `.as_tool()` for clean integration
   - Maintain their own tools and capabilities

3. **Layered Information Sources**
   - Static knowledge (curated documents)
   - Dynamic tools (APIs, calculations)  
   - Expert agents (complex analysis)
   - LLM fallback (general knowledge)

## 🧪 Testing Your Implementation

Use the provided examples to test your own RAGAgent implementations:

1. **Start Simple**: Try traditional tools with RAGAgent
2. **Add Agents**: Convert specialist agents to tools via `.as_tool()`
3. **Test Delegation**: Verify task routing and result synthesis
4. **Measure Performance**: Use performance testing suite
5. **Scale Up**: Add more specialists and knowledge sources

The examples provide a complete foundation for building production-ready multi-agent RAG systems with AgenticFlow.