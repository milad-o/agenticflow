# AgenticFlow Usage Guide

This guide provides detailed instructions for using AgenticFlow in various scenarios.

## Table of Contents

1. [Basic Concepts](#basic-concepts)
2. [Installation & Setup](#installation--setup)
3. [Core Components](#core-components)
4. [Basic Workflows](#basic-workflows)
5. [Team-based Workflows](#team-based-workflows)
6. [Specialized Agents](#specialized-agents)
7. [Vector Storage](#vector-storage)
8. [Advanced Features](#advanced-features)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Basic Concepts

### Flow
The main orchestrator that manages agents and teams. It routes messages and coordinates execution.

### Agent
Individual workers that perform specific tasks using tools. Agents can be:
- **Direct agents**: Added directly to a flow
- **Team agents**: Part of a team managed by a supervisor

### Team
A collection of agents managed by a supervisor. Teams provide hierarchical organization for complex workflows.

### Tools
Functions that agents can use to perform tasks. Tools can be:
- **Built-in tools**: Provided by AgenticFlow
- **LangChain tools**: From the LangChain ecosystem
- **Custom tools**: User-defined functions

## Installation & Setup

### Prerequisites
- Python 3.9+
- OpenAI API key (required)
- Optional: Tavily API key (for web search)

### Installation
```bash
# Clone repository
git clone https://github.com/milad-o/agenticflow.git
cd agenticflow

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Environment Setup
Create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key  # Optional
```

## Core Components

### Flow
```python
from agenticflow import Flow

# Create a flow
flow = Flow("my_workflow")

# Add agents directly
flow.add_agent(agent)

# Add teams
flow.add_team(team)

# Run workflow
result = await flow.run("Your message here")
```

### Agent
```python
from agenticflow import Agent
from agenticflow.tools import create_file, search_web

# Create agent with tools
agent = Agent(
    name="my_agent",
    description="Agent description",
    tools=[create_file, search_web]
)
```

### Team
```python
from agenticflow import Team

# Create team
team = Team("my_team")

# Add agents to team
team.add_agent(agent1)
team.add_agent(agent2)

# Add team to flow
flow.add_team(team)
```

## Basic Workflows

### Simple Agent Workflow
```python
import asyncio
from agenticflow import Flow, Agent, create_file, search_web

async def main():
    # Create flow
    flow = Flow("research_workflow")
    
    # Create agents
    researcher = Agent("researcher", tools=[search_web])
    writer = Agent("writer", tools=[create_file])
    
    # Add agents
    flow.add_agent(researcher)
    flow.add_agent(writer)
    
    # Run workflow
    result = await flow.run("Research AI trends and create a report")
    print(result)

asyncio.run(main())
```

### Multi-step Workflow
```python
import asyncio
from agenticflow import Flow, Agent, create_file, search_web, read_file

async def main():
    flow = Flow("analysis_workflow")
    
    # Create specialized agents
    researcher = Agent("researcher", tools=[search_web])
    analyzer = Agent("analyzer", tools=[read_file])
    writer = Agent("writer", tools=[create_file])
    
    flow.add_agent(researcher)
    flow.add_agent(analyzer)
    flow.add_agent(writer)
    
    result = await flow.run("Research, analyze, and write a comprehensive report on machine learning trends")
    print(result)

asyncio.run(main())
```

## Team-based Workflows

### Research and Writing Team
```python
import asyncio
from agenticflow import Flow, Agent, Team, create_file, search_web

async def main():
    flow = Flow("research_team_workflow")
    
    # Research Team
    research_team = Team("research_team")
    researcher = Agent("researcher", tools=[search_web])
    research_team.add_agent(researcher)
    flow.add_team(research_team)
    
    # Writing Team
    writing_team = Team("writing_team")
    writer = Agent("writer", tools=[create_file])
    writing_team.add_agent(writer)
    flow.add_team(writing_team)
    
    result = await flow.run("Research AI trends and create a comprehensive report")
    print(result)

asyncio.run(main())
```

### Complex Multi-team Workflow
```python
import asyncio
from agenticflow import Flow, Agent, Team, create_file, search_web, read_file

async def main():
    flow = Flow("complex_workflow")
    
    # Data Collection Team
    data_team = Team("data_team")
    web_researcher = Agent("web_researcher", tools=[search_web])
    file_reader = Agent("file_reader", tools=[read_file])
    data_team.add_agent(web_researcher)
    data_team.add_agent(file_reader)
    flow.add_team(data_team)
    
    # Analysis Team
    analysis_team = Team("analysis_team")
    data_analyzer = Agent("data_analyzer", tools=[read_file])
    analysis_team.add_agent(data_analyzer)
    flow.add_team(analysis_team)
    
    # Output Team
    output_team = Team("output_team")
    writer = Agent("writer", tools=[create_file])
    output_team.add_agent(writer)
    flow.add_team(output_team)
    
    result = await flow.run("Collect data, analyze it, and create a comprehensive report")
    print(result)

asyncio.run(main())
```

## Specialized Agents

### FilesystemAgent
```python
from agenticflow import Flow
from agenticflow import FilesystemAgent

async def main():
    flow = Flow("filesystem_workflow")
    
    # Create filesystem agent
    fs_agent = FilesystemAgent("file_manager")
    flow.add_agent(fs_agent)
    
    result = await flow.run("Create a directory structure and organize files")
    print(result)

asyncio.run(main())
```

### PythonAgent
```python
from agenticflow import Flow
from agenticflow import PythonAgent

async def main():
    flow = Flow("python_workflow")
    
    # Create Python agent
    py_agent = PythonAgent("code_analyst")
    flow.add_agent(py_agent)
    
    result = await flow.run("Write and execute Python code to analyze data")
    print(result)

asyncio.run(main())
```

### ExcelAgent
```python
from agenticflow import Flow
from agenticflow import ExcelAgent

async def main():
    flow = Flow("excel_workflow")
    
    # Create Excel agent
    excel_agent = ExcelAgent("spreadsheet_processor")
    flow.add_agent(excel_agent)
    
    result = await flow.run("Create an Excel file with data analysis")
    print(result)

asyncio.run(main())
```

### DataAgent
```python
from agenticflow import Flow
from agenticflow import DataAgent

async def main():
    flow = Flow("data_workflow")
    
    # Create data agent
    data_agent = DataAgent("data_processor")
    flow.add_agent(data_agent)
    
    result = await flow.run("Process JSON data and create reports")
    print(result)

asyncio.run(main())
```

### SSISAnalysisAgent
```python
from agenticflow import Flow
from agenticflow import SSISAnalysisAgent

async def main():
    flow = Flow("ssis_workflow")
    
    # Create SSIS agent with ChromaDB
    ssis_agent = SSISAnalysisAgent(
        "ssis_analyst",
        vector_backend="chroma",
        persistent=True
    )
    flow.add_agent(ssis_agent)
    
    result = await flow.run("Analyze the SSIS package and extract data flows")
    print(result)

asyncio.run(main())
```

## Vector Storage

### ChromaDB Backend
```python
from agenticflow import SSISAnalysisAgent

# Ephemeral ChromaDB
ssis_agent = SSISAnalysisAgent(
    "ssis_analyst",
    vector_backend="chroma",
    persistent=False
)

# Persistent ChromaDB
ssis_agent = SSISAnalysisAgent(
    "ssis_analyst",
    vector_backend="chroma",
    persistent=True
)
```

### SQLite Backend
```python
from agenticflow import SSISAnalysisAgent

# Ephemeral SQLite
ssis_agent = SSISAnalysisAgent(
    "ssis_analyst",
    vector_backend="sqlite",
    persistent=False
)

# Persistent SQLite
ssis_agent = SSISAnalysisAgent(
    "ssis_analyst",
    vector_backend="sqlite",
    persistent=True
)
```

### Using Vector Search
```python
async def main():
    flow = Flow("vector_search_workflow")
    
    ssis_agent = SSISAnalysisAgent("ssis_analyst", vector_backend="chroma")
    flow.add_agent(ssis_agent)
    
    # Index package
    await flow.run("Index sample_complex_package.dtsx for search")
    
    # Semantic search
    result = await flow.run("Find all data transformations in the package")
    print(result)

asyncio.run(main())
```

## Advanced Features

### Custom Tools
```python
from langchain_core.tools import tool

@tool
def custom_analysis_tool(data: str) -> str:
    """Custom analysis tool."""
    # Your custom logic here
    return f"Analysis result: {data}"

# Use in agent
agent = Agent("custom_agent", tools=[custom_analysis_tool])
```

### Error Handling
```python
async def main():
    try:
        flow = Flow("error_handling_workflow")
        flow.add_agent(agent)
        result = await flow.run("Your message")
    except Exception as e:
        print(f"Error: {e}")
        # Handle error appropriately
```

### Async Operations
```python
import asyncio

async def run_multiple_workflows():
    tasks = []
    
    # Create multiple flows
    for i in range(5):
        flow = Flow(f"workflow_{i}")
        flow.add_agent(agent)
        tasks.append(flow.run(f"Task {i}"))
    
    # Run concurrently
    results = await asyncio.gather(*tasks)
    return results

asyncio.run(run_multiple_workflows())
```

## Best Practices

### 1. Agent Design
- Give agents clear, specific descriptions
- Use appropriate tools for each agent's role
- Keep agents focused on single responsibilities

### 2. Team Organization
- Use teams for related agents
- Keep team sizes manageable (2-5 agents)
- Use clear team names and descriptions

### 3. Message Design
- Be specific in your messages
- Include context and requirements
- Use clear, actionable language

### 4. Error Handling
- Always wrap flow.run() in try-catch
- Provide meaningful error messages
- Implement retry logic for critical operations

### 5. Performance
- Use async/await properly
- Consider using concurrent flows for independent tasks
- Monitor memory usage with large datasets

## Troubleshooting

### Common Issues

#### 1. API Key Not Set
```
Error: The api_key client option must be set
```
**Solution**: Set `OPENAI_API_KEY` in your environment or `.env` file.

#### 2. Agent Not Using Tools
```
Result: Sorry, need more steps to process this request.
```
**Solution**: Ensure tools are properly imported and passed to the agent.

#### 3. Vector Storage Issues
```
Error: Embeddings not initialized
```
**Solution**: Check that the vector backend is properly configured and dependencies are installed.

#### 4. Memory Issues
```
Error: Out of memory
```
**Solution**: Use persistent storage, reduce batch sizes, or use simpler vector backends.

### Debug Tips

1. **Enable Debug Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Check Agent Tools**:
```python
print(f"Agent tools: {[tool.name for tool in agent.tools]}")
```

3. **Verify Flow Structure**:
```python
print(f"Flow agents: {list(flow.agents.keys())}")
print(f"Flow teams: {list(flow.teams.keys())}")
```

4. **Test Individual Tools**:
```python
# Test tool directly
result = tool.invoke({"input": "test"})
print(result)
```

### Getting Help

1. Check the [API Reference](API_REFERENCE.md)
2. Look at [Examples](EXAMPLES.md)
3. Open an issue on GitHub
4. Check the troubleshooting section above

## Next Steps

1. Explore the [Specialized Agents](SPECIALIZED_AGENTS.md) guide
2. Check out the [API Reference](API_REFERENCE.md)
3. Try the [Examples](EXAMPLES.md)
4. Build your own custom agents and tools
