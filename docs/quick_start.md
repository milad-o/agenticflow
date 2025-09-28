# Quick Start Guide

Get up and running with AgenticFlow in just a few minutes!

## 🚀 Installation

```bash
# Install with uv (recommended)
uv add agenticflow

# Or with pip
pip install agenticflow
```

## 📦 Dependencies

AgenticFlow requires Python 3.8+ and the following optional dependencies for full functionality:

```bash
# For LLM-powered features
uv add langchain-openai langchain-core langgraph

# For web search tools
uv add tavily-python

# For development and testing
uv add pytest pytest-asyncio
```

## 🎯 Your First Flow

Here's the simplest possible AgenticFlow example:

```python
import asyncio
from agenticflow import Flow, Orchestrator, Supervisor, SimpleAgent

async def main():
    # Create a flow
    flow = Flow("my_first_flow")
    
    # Add an orchestrator
    orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
    flow.add_orchestrator(orchestrator)
    
    # Create a team
    team = Supervisor("my_team", initialize_llm=False)
    
    # Add an agent
    agent = SimpleAgent("my_agent", description="A helpful agent")
    team.add_agent(agent)
    
    # Add team to orchestrator
    orchestrator.add_team(team)
    
    # Run the flow
    await flow.start("Hello, AgenticFlow!")
    
    # Get results
    messages = await flow.get_messages()
    for msg in messages:
        print(f"{msg.sender}: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔗 Method Chaining

AgenticFlow supports beautiful method chaining:

```python
# Create everything in one go
flow = (Flow("chaining_flow")
        .add_orchestrator(Orchestrator("main", initialize_llm=False)))

team = (Supervisor("research_team", initialize_llm=False)
        .add_agent(SimpleAgent("researcher", description="Research specialist")))

orchestrator.add_team(team)
```

## 🛠️ Adding Tools

Add tools to your agents:

```python
from agenticflow.tools import WriteFileTool, ReadFileTool

agent = (SimpleAgent("writer", description="Content writer")
         .add_tool(WriteFileTool())
         .add_tool(ReadFileTool()))
```

## 🤖 LLM-Powered Agents

For intelligent agents with LLM capabilities:

```python
from agenticflow import ReActAgent

# Set your OpenAI API key
export OPENAI_API_KEY="your_key_here"

# Create LLM-powered agent
agent = ReActAgent("smart_agent", description="An intelligent agent")
agent.add_tool(WriteFileTool())

# Add to team
team.add_agent(agent)
```

## 🏗️ Complex Workflows

Build sophisticated multi-team workflows:

```python
# Research team
research_team = Supervisor("research_team", description="Research specialists")
research_team.add_agent(ReActAgent("searcher").add_tool(WebSearchTool()))

# Writing team  
writing_team = Supervisor("writing_team", description="Writing specialists")
writing_team.add_agent(ReActAgent("writer").add_tool(WriteFileTool()))

# Add teams to orchestrator
orchestrator.add_team(research_team)
orchestrator.add_team(writing_team)

# Run complex workflow
await flow.start("Research AI trends and write a report")
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/

# Run with coverage
uv run pytest --cov=agenticflow
```

## 📚 Next Steps

- Check out the [Basic Examples](../examples/basic/) for more examples
- Read the [Concepts Guide](concepts.md) to understand the architecture
- Explore [Advanced Examples](../examples/advanced/) for complex workflows
- Learn about [LangGraph Integration](langgraph_integration.md) for advanced features

## 🆘 Need Help?

- Check the [FAQ](faq.md) for common questions
- Browse the [Examples](../examples/) for code samples
- Open an issue on GitHub for bugs or feature requests
- Join our community discussions

Happy building with AgenticFlow! 🎉
