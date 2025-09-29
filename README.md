# AgenticFlow

A powerful framework for building hierarchical multi-agent workflows with specialized domain agents and advanced vector storage capabilities.

## 🚀 Features

- **Hierarchical Teams**: Organize agents into teams with supervisors for complex workflows
- **Direct Agents**: Use agents directly without team structure for simple tasks
- **Specialized Agents**: Pre-built agents for specific domains (Filesystem, Python, Excel, Data, SSIS)
- **Advanced Observability**: Real-time monitoring with rich console output and event logging
- **Vector Storage**: Multiple backends (ChromaDB, SQLite) for semantic and text search
- **LangGraph Integration**: Built on LangGraph for robust state management
- **Tool Integration**: Easy integration with LangChain tools and custom tools
- **Async Support**: Full async/await support for concurrent operations
- **Configurable Storage**: Ephemeral and persistent storage options

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/milad-o/agenticflow.git
cd agenticflow

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## 🏃 Quick Start

### Basic Agent Workflow

```python
import asyncio
from agenticflow import Flow, Agent, create_file, search_web

async def main():
    flow = Flow("simple_workflow")
    
    researcher = Agent(
        name="researcher",
        description="Researches topics using web search.",
        tools=[search_web]
    )
    
    writer = Agent(
        name="writer", 
        description="Writes reports and documents.",
        tools=[create_file]
    )
    
    flow.add_agent(researcher)
    flow.add_agent(writer)
    
    # Enable observability with rich console output
    flow.enable_observability(rich_console=True)
    
    result = await flow.run("Research AI trends and create a report")
    print(result)

asyncio.run(main())
```

### Team-based Workflows

```python
import asyncio
from agenticflow import Flow, Agent, Team, create_file, search_web

async def main():
    flow = Flow("team_workflow")
    
    # Create Research Team
    research_team = Team("research_team")
    researcher = Agent(name="researcher", tools=[search_web])
    research_team.add_agent(researcher)
    flow.add_team(research_team)
    
    # Create Writing Team  
    writing_team = Team("writing_team")
    writer = Agent(name="writer", tools=[create_file])
    writing_team.add_agent(writer)
    flow.add_team(writing_team)
    
    # Enable rich console observability
    flow.enable_observability(rich_console=True)
    
    result = await flow.run("Research AI trends and create a report")
    print(result)

asyncio.run(main())
```

### Specialized Agents

```python
import asyncio
from agenticflow import Flow
from agenticflow import FilesystemAgent, PythonAgent, ExcelAgent, DataAgent, SSISAnalysisAgent

async def main():
    flow = Flow("specialized_workflow")
    
    # Add specialized agents
    flow.add_agent(FilesystemAgent("file_manager"))
    flow.add_agent(PythonAgent("code_analyst"))
    flow.add_agent(ExcelAgent("spreadsheet_processor"))
    flow.add_agent(DataAgent("data_processor"))
    flow.add_agent(SSISAnalysisAgent("ssis_analyst", vector_backend="chroma"))
    
    result = await flow.run("Process data files and create analysis reports")
    print(result)

asyncio.run(main())
```

## 🔍 Observability & Monitoring

AgenticFlow provides comprehensive observability features to monitor and debug your agent workflows:

### Rich Console Output
Beautiful, real-time terminal output with tree structures, colors, and detailed progress tracking:

```python
# Enable rich console output
flow.enable_observability(rich_console=True)

# Or use standard console output
flow.enable_observability(console_output=True)
```

### Event Logging
Track all agent activities, tool calls, and workflow events:

```python
# Enable persistent event logging
flow.enable_observability(
    persistent=True,
    file_logging=True,
    log_file="workflow_events.log"
)

# Get flow metrics
metrics = flow.get_metrics()
print(f"Total duration: {metrics['total_duration_ms']}ms")
print(f"Tools executed: {metrics['tool_executions']}")
```

### Event Types
- **Flow Events**: Start, completion, errors
- **Agent Events**: Start, completion, thinking, working, errors
- **Tool Events**: Arguments, execution, results, errors
- **Team Events**: Supervisor decisions, agent routing
- **Custom Events**: User-defined events

### Console Output Features
- **Tree Structure**: Hierarchical view of teams and agents
- **Role Indicators**: Clear identification of orchestrators, supervisors, agents, tools
- **Real-time Progress**: Live updates during execution
- **Tool Details**: Arguments, execution status, and results
- **Color Coding**: Visual distinction between different event types
- **Performance Metrics**: Duration, tool usage, and completion statistics

## 🛠️ Specialized Agents

### FilesystemAgent
Comprehensive file and directory operations:
- Create, read, write, delete files and directories
- Search and grep operations
- File information and metadata
- Backup and restore operations

### PythonAgent
Python code analysis and execution:
- Execute Python code safely
- Validate and format code
- Generate and refactor code
- Debug and optimize Python scripts

### ExcelAgent
Excel and spreadsheet processing:
- Create, read, and modify Excel files
- Data manipulation and analysis
- Charts and formatting
- Import/export operations

### DataAgent
Data format processing:
- JSON, XML, YAML, CSV processing
- Data validation and transformation
- SQLite database operations
- Data cleaning and analysis

### SSISAnalysisAgent
Microsoft SSIS package analysis:
- Parse complex DTSX files
- Extract data flows and connections
- Semantic search with vector storage
- Package validation and documentation

## 🔍 Vector Storage

### ChromaDB Backend
```python
ssis_agent = SSISAnalysisAgent(
    "ssis_analyst", 
    vector_backend="chroma", 
    persistent=True
)
```

### SQLite Backend
```python
ssis_agent = SSISAnalysisAgent(
    "ssis_analyst", 
    vector_backend="sqlite", 
    persistent=True
)
```

## 📚 Documentation

- [Usage Guide](docs/USAGE.md) - Detailed usage instructions
- [Specialized Agents](docs/SPECIALIZED_AGENTS.md) - Complete agent reference
- [API Reference](docs/API_REFERENCE.md) - Full API documentation
- [Examples](docs/EXAMPLES.md) - Comprehensive examples and tutorials
- [SSIS Agent](docs/SSIS_AGENT_SUMMARY.md) - SSIS analysis capabilities

## 🧪 Examples

See the `examples/` directory for comprehensive examples:

- `simple_workflow.py` - Basic agent workflow
- `team_workflow.py` - Team-based workflow
- `rich_console_demo.py` - Rich console output demonstration
- `rich_teams_demo.py` - Team workflow with rich console
- `console_comparison_demo.py` - Compare console output styles
- `researcher_writer_teams.py` - Multi-team coordination example

## 🔧 Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
TAVILY_API_KEY=your_tavily_api_key  # For web search
```

### Vector Storage Options
- **ChromaDB**: Semantic search with embeddings
- **SQLite**: Fast text-based search
- **None**: Basic analysis without vector storage

## 🚀 Advanced Features

- **Hierarchical Teams**: Complex organizational structures
- **Advanced Observability**: Real-time monitoring and debugging
- **Rich Console Output**: Beautiful terminal visualization
- **Event Logging**: Comprehensive activity tracking
- **Vector Search**: Semantic and text-based search
- **Persistent Storage**: Save analysis results
- **Tool Integration**: Extend with custom tools
- **Async Operations**: Concurrent agent execution

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📞 Support

For questions and support, please open an issue on GitHub.