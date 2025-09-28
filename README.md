# AgenticFlow

A simple, clean multi-agent framework with hierarchical team support.

## Features

- **Hierarchical Teams**: Flow → Teams → Supervisors → Agents
- **Direct Agents**: Flow → Agents (simple workflows)
- **Tool Integration**: Built-in tools for web search, file operations, and more
- **LangGraph Integration**: Built on LangGraph for reliable execution
- **Clean API**: Simple, intuitive interface

## Installation

```bash
pip install -e .
```

## Quick Start

### Simple Workflow

```python
import asyncio
from agenticflow import Flow, Agent, create_file, search_web

async def main():
    # Create flow
    flow = Flow("my_workflow")
    
    # Create agents
    researcher = Agent("researcher", tools=[search_web])
    writer = Agent("writer", tools=[create_file])
    
    # Add agents to flow
    flow.add_agent(researcher)
    flow.add_agent(writer)
    
    # Run workflow
    result = await flow.run("Research AI trends and create a report")
    print("Done!")

asyncio.run(main())
```

### Team Workflow

```python
import asyncio
from agenticflow import Flow, Agent, Team, create_file, search_web

async def main():
    # Create flow
    flow = Flow("team_workflow")
    
    # Create research team
    research_team = Team("research_team")
    researcher = Agent("researcher", tools=[search_web])
    research_team.add_agent(researcher)
    flow.add_team(research_team)
    
    # Create writing team
    writing_team = Team("writing_team")
    writer = Agent("writer", tools=[create_file])
    writing_team.add_agent(writer)
    flow.add_team(writing_team)
    
    # Run workflow
    result = await flow.run("Research AI trends and create a report")
    print("Done!")

asyncio.run(main())
```

## API Reference

### Core Classes

- **`Flow(name)`**: Main workflow orchestrator
- **`Agent(name, tools, description)`**: Individual agent with tools
- **`Team(name)`**: Team container with supervisor

### Methods

- **`flow.add_agent(agent)`**: Add agent directly to flow
- **`flow.add_team(team)`**: Add team to flow
- **`team.add_agent(agent)`**: Add agent to team
- **`flow.run(message)`**: Execute workflow

### Built-in Tools

- **`create_file(content, filename)`**: Create files
- **`search_web(query)`**: Web search
- **`read_file(filename)`**: Read files
- **`list_directory(path)`**: List directory contents

## Examples

See the `examples/` directory for:
- Simple agent workflows
- Team-based workflows
- Tool usage examples

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run examples
uv run python examples/simple_workflow.py
```

## License

MIT License - see LICENSE file for details.