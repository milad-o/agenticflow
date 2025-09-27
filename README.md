# AgenticFlow

Fast, practical multi-agent orchestration built on LangGraph with **real-time observability**. AgenticFlow provides:
- Clean hierarchical teams with supervisor-worker pattern
- Specialized worker agents for filesystem, analysis, and reporting
- LangGraph-based state management and coordination
- **Real-time observability with beautiful Streamlit UIs**
- **Comprehensive event tracking and monitoring**
- Direct tool assignment (no complex registries)
- OpenAI integration with smart task routing

Status: Production Ready — hierarchical multi-agent coordination with enterprise-grade observability.

## Quick Start

**Prerequisites**
- Python 3.10+
- uv (recommended) or pip

**Install**
```bash
uv venv
uv pip install -e .
```

**Set up OpenAI API**
```bash
export OPENAI_API_KEY=your_api_key_here
```

**Try it now**
```python
from agenticflow import ObservableFlow
from agenticflow.agents import FileSystemWorker, AnalysisWorker, ReportingWorker

# Create hierarchical team with observability
flow = ObservableFlow()
flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
flow.add_worker("analysis", AnalysisWorker())
flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))

# Execute complex task with real-time monitoring
result = flow.run("Find CSV files, analyze their patterns, and generate a report")
print(f"Success: {result['success']}")
print(f"Workers used: {result['workers_used']}")
print(f"Events tracked: {len(flow.get_event_tracker().events)}")
```

**🎨 Launch Beautiful UI**
```bash
# Launch real-time monitoring dashboard
uv run streamlit run agenticflow/ui.py
```

## Architecture

**Hierarchical Teams**
- **Flow**: Main orchestration container with worker management
- **SupervisorAgent**: LLM-powered coordination and task routing
- **TeamGraph**: LangGraph state management and execution flow
- **TeamState**: Centralized state tracking with execution monitoring

**Specialized Workers**
- **FileSystemWorker**: File discovery, reading, and directory operations
- **AnalysisWorker**: Data analysis, statistics, and pattern recognition
- **ReportingWorker**: Report generation and content creation

**Key Benefits**
- ✅ Clean supervisor-workers pattern (no complex registries)
- ✅ LangGraph-based coordination with state management
- ✅ **Real-time observability with beautiful Streamlit UIs**
- ✅ **Comprehensive event tracking and agent monitoring**
- ✅ **Progress visualization and execution analytics**
- ✅ Direct tool assignment to specialized workers
- ✅ Intelligent task routing with LLM decision making
- ✅ Safety mechanisms to prevent infinite loops
- ✅ Comprehensive error handling and recovery

## Examples

The framework includes sample CSV data in `examples/data/` for testing:

```python
# Simple file analysis
flow = Flow()
flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
result = flow.run("Find all CSV files and list their contents")

# Multi-step data pipeline
flow = Flow()
flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
flow.add_worker("analysis", AnalysisWorker())
flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))

result = flow.run("Perform comprehensive data analysis: find CSV files, analyze patterns, create detailed report")
```

**Output Locations**
- Reports: Generated in `examples/artifact/`
- Data: Sample files in `examples/data/`

## LLM Configuration

**OpenAI (Recommended)**
```bash
export OPENAI_API_KEY=your_key_here
```

**Custom LLM**
```python
from langchain_openai import ChatOpenAI

# Custom model configuration
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
flow = Flow(llm=llm)
```

## Core Components

**Flow Management**
```python
flow = Flow()                                    # Create with default OpenAI LLM
flow.add_worker("name", worker_instance)        # Add specialized worker
flow.remove_worker("name")                      # Remove worker
flow.list_workers()                             # List all workers
flow.describe_team()                            # Get team configuration
```

**Worker Coordination**
- Supervisor analyzes task requirements
- Routes to appropriate workers in sequence
- Tracks execution state and results
- Decides when task is complete
- Handles errors and retries

**State Management**
- TeamState tracks messages, results, and progress
- Execution counter prevents infinite loops
- Worker results stored for supervisor decision making
- Global context shared across workers

## 🔍 Real-time Observability

AgenticFlow includes comprehensive observability features with beautiful Streamlit UIs for monitoring multi-agent workflows.

**🎨 Beautiful Monitoring Dashboard**
```bash
# Launch the main monitoring interface
uv run streamlit run agenticflow_ui.py
```

**📊 Key Observability Features**
- **Real-time Progress Tracking**: Step-by-step execution visualization
- **Agent Activity Monitoring**: Live agent status and tool usage
- **Interactive Chat Interface**: Chat-style monitoring with message bubbles
- **Performance Analytics**: Success rates, execution times, metrics
- **Event Stream**: Live feed of all system events
- **Tool Usage Visualization**: Interactive charts and analytics

**🤖 ObservableFlow**
```python
from agenticflow import ObservableFlow

# Create flow with observability enabled
flow = ObservableFlow()
flow.add_worker("filesystem", FileSystemWorker())

# Execute with automatic event tracking
result = flow.run("Your task here")

# Access observability data
events = flow.get_event_tracker().events
analytics = flow.get_observer().get_flow_analytics()
```

**📈 Monitor Everything**
- Agent reflections and decision-making
- Tool calls and responses
- Execution progress and bottlenecks
- Error tracking and recovery
- Performance metrics and trends

See [UI_FEATURES.md](UI_FEATURES.md) for complete UI documentation.

## Development

**Testing**
```bash
# Run framework tests
uv run python -c "
from agenticflow import Flow
from agenticflow.agents import FileSystemWorker
flow = Flow()
flow.add_worker('fs', FileSystemWorker())
print('✅ Framework working')
"
```

**Custom Workers**
```python
class CustomWorker:
    def __init__(self):
        self.capabilities = ["custom_task"]

    async def arun(self, task: str):
        return {"action": "custom", "result": "done"}

    def execute(self, task: str):
        return {"action": "custom", "result": "done"}

flow.add_worker("custom", CustomWorker())
```

## 🎨 Complete UI Suite

AgenticFlow includes multiple beautiful Streamlit interfaces for comprehensive monitoring:

### 🏠 Main Interface
```bash
# Launch the unified monitoring dashboard
uv run streamlit run agenticflow/ui.py
```
**Features:** Real-time overview, agent monitoring, chat interface, performance metrics

### 🎪 Specialized Interfaces
```bash
# Chat-style monitoring with message bubbles
uv run streamlit run examples/ui/chat_ui.py

# Real-time progress tracking with step visualization
uv run streamlit run examples/ui/progress_ui.py

# Launch specialized interfaces simultaneously
uv run python examples/ui/launch_ui.py
```

### 📊 UI Features
- **Real-time Progress Visualization**: Step-by-step execution tracking
- **Agent Activity Monitoring**: Live status updates and tool usage
- **Interactive Chat Interface**: Conversation-style monitoring
- **Performance Analytics**: Success rates, execution times, metrics
- **Event Stream**: Live feed of all system events
- **Tool Usage Charts**: Interactive visualizations
- **Agent Reflection Display**: Decision-making insights
- **Export Capabilities**: Save observability data

## 🔧 Advanced Features

### Multi-Agent Validation
```python
from agenticflow.agents.validation_agents import (
    StructureValidationAgent,
    ContentValidationAgent,
    ConsistencyValidationAgent
)

# Create validation team
flow = ObservableFlow()
flow.add_worker("structure_validator", StructureValidationAgent())
flow.add_worker("content_validator", ContentValidationAgent())
flow.add_worker("consistency_validator", ConsistencyValidationAgent())

# Validate CSV data against hierarchical reports
result = flow.run("Validate Q3 2024 CSV data against source report")
```

### Web Research Integration
```python
# Add Tavily API key to .env for web research capabilities
TAVILY_API_KEY=your_tavily_key

# Enhanced analysis with web research
flow = ObservableFlow()
flow.add_worker("filesystem", FileSystemWorker())
flow.add_worker("analysis", AnalysisWorker())
flow.add_worker("web_research", WebResearchWorker())
flow.add_worker("reporting", ReportingWorker())

result = flow.run("Analyze local data and combine with market research")
```

### Real-time Callbacks
```python
def monitoring_callback(event_data):
    if event_data["type"] == "agent_reflection":
        print(f"Agent thinking: {event_data['reflection']}")

observer = flow.get_observer()
observer.register_callback(monitoring_callback)
```

## 📚 Documentation

All documentation is integrated into this README. Key sections:
- **🔍 Real-time Observability** - Comprehensive monitoring guide
- **🎨 Complete UI Suite** - All available interfaces and features
- **🔧 Advanced Features** - Multi-agent validation, web research, callbacks
- **Examples:** Check `examples/` directory for sample data and demos

## 🚀 Production Usage

### Basic Production Flow
```python
from agenticflow import Flow  # Standard flow for production
flow = Flow()
# Add workers and execute tasks
```

### Development with Observability
```python
from agenticflow import ObservableFlow  # Enhanced flow for development
flow = ObservableFlow()
# Full monitoring and debugging capabilities
```

### Performance Monitoring
```python
# Access comprehensive metrics
analytics = flow.get_observer().get_flow_analytics()
performance = analytics["performance"]
print(f"Success rate: {performance['success_rate']:.1f}%")
print(f"Tool calls: {performance['total_tool_calls']}")
```

### Data Export
```python
# Export observability data for analysis
filename = flow.export_observability_data()
print(f"Data exported to: {filename}")
```

## 🎯 Use Cases

### Enterprise Applications
- **Business Intelligence**: Multi-source data analysis and reporting
- **Data Validation**: Automated data integrity verification
- **Market Research**: Combined local analysis with web intelligence
- **Report Generation**: Automated comprehensive business reports

### Development & Research
- **Multi-Agent Development**: Real-time debugging and optimization
- **Academic Research**: Agent behavior analysis and study
- **System Monitoring**: Production multi-agent system health
- **Performance Analysis**: Workflow optimization and bottleneck identification

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │  ObservableFlow  │    │   LangGraph     │
│   (Monitoring)  │◄──►│  (Orchestration) │◄──►│ (Coordination)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Event Tracking  │    │ Supervisor +    │
                       │ & Observability │    │ Specialized     │
                       │                 │    │ Workers         │
                       └─────────────────┘    └─────────────────┘
```

**Key Components:**
- **ObservableFlow**: Enhanced orchestration with monitoring
- **LangGraph**: State-based multi-agent coordination
- **Streamlit UI**: Real-time visualization and monitoring
- **Event System**: Comprehensive tracking and analytics
- **Specialized Workers**: Domain-specific agent capabilities

## License

MIT