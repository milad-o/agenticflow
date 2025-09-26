# AgenticFlow

Fast, practical multi-agent orchestration built on LangGraph. AgenticFlow provides:
- Clean hierarchical teams with supervisor-worker pattern
- Specialized worker agents for filesystem, analysis, and reporting
- LangGraph-based state management and coordination
- Direct tool assignment (no complex registries)
- OpenAI integration with smart task routing

Status: Production Ready — hierarchical multi-agent coordination that works.

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
from agenticflow import Flow
from agenticflow.agents import FileSystemWorker, AnalysisWorker, ReportingWorker

# Create hierarchical team
flow = Flow()
flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
flow.add_worker("analysis", AnalysisWorker())
flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))

# Execute complex task
result = flow.run("Find CSV files, analyze their patterns, and generate a report")
print(f"Success: {result['success']}")
print(f"Workers used: {result['workers_used']}")
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

## License

MIT