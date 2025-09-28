# AgenticFlow Examples

Comprehensive examples and tutorials for using AgenticFlow.

## Table of Contents

1. [Basic Examples](#basic-examples)
2. [Team Workflows](#team-workflows)
3. [Specialized Agents](#specialized-agents)
4. [Vector Storage](#vector-storage)
5. [Advanced Examples](#advanced-examples)
6. [Real-world Scenarios](#real-world-scenarios)

## Basic Examples

### Simple Agent Workflow
```python
import asyncio
from agenticflow import Flow, Agent, create_file, search_web

async def main():
    print("🚀 Simple Agent Workflow")
    print("=" * 30)
    
    # Create flow
    flow = Flow("simple_workflow")
    
    # Create agents
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
    
    # Add agents to flow
    flow.add_agent(researcher)
    flow.add_agent(writer)
    
    print(f"✅ Created flow with {len(flow.agents)} agents")
    print(f"   Agents: {list(flow.agents.keys())}")
    
    # Run workflow
    print("\n🎯 Running workflow...")
    result = await flow.run("Research AI trends and create a simple report")
    
    print("✅ Workflow completed!")
    print(f"📝 Messages: {len(result['messages'])}")
    for i, msg in enumerate(result["messages"], 1):
        print(f"   {i}. [{getattr(msg, 'name', 'user')}]: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Multi-step Workflow
```python
import asyncio
from agenticflow import Flow, Agent, create_file, search_web, read_file

async def main():
    print("🔄 Multi-step Workflow")
    print("=" * 25)
    
    flow = Flow("multi_step_workflow")
    
    # Create specialized agents
    researcher = Agent("researcher", tools=[search_web])
    analyzer = Agent("analyzer", tools=[read_file])
    writer = Agent("writer", tools=[create_file])
    
    flow.add_agent(researcher)
    flow.add_agent(analyzer)
    flow.add_agent(writer)
    
    print(f"✅ Created flow with {len(flow.agents)} agents")
    
    # Run multi-step workflow
    result = await flow.run("Research machine learning trends, analyze the findings, and create a comprehensive report")
    
    print("✅ Multi-step workflow completed!")
    print(f"📝 Total messages: {len(result['messages'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Team Workflows

### Research and Writing Team
```python
import asyncio
from agenticflow import Flow, Agent, Team, create_file, search_web

async def main():
    print("🏢 Research and Writing Team")
    print("=" * 30)
    
    flow = Flow("research_team_workflow")
    
    # Create Research Team
    research_team = Team("research_team")
    researcher = Agent(
        name="researcher",
        description="Performs web searches to gather information.",
        tools=[search_web]
    )
    research_team.add_agent(researcher)
    flow.add_team(research_team)
    
    # Create Writing Team
    writing_team = Team("writing_team")
    writer = Agent(
        name="writer",
        description="Writes comprehensive reports based on research.",
        tools=[create_file]
    )
    writing_team.add_agent(writer)
    flow.add_team(writing_team)
    
    print(f"✅ Created team structure:")
    print(f"   Flow: {flow.name}")
    print(f"   Teams: {list(flow.teams.keys())}")
    for team_name, team in flow.teams.items():
        print(f"   {team.name.capitalize()} Team: {list(team.agents.keys())}")
    
    # Run team workflow
    print("\n🎯 Running team workflow...")
    result = await flow.run("Research AI trends and create a comprehensive report")
    
    print("✅ Team workflow completed!")
    print(f"📝 Messages: {len(result['messages'])}")
    for i, msg in enumerate(result["messages"], 1):
        print(f"   {i}. [{getattr(msg, 'name', 'user')}]: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Complex Multi-team Workflow
```python
import asyncio
from agenticflow import Flow, Agent, Team, create_file, search_web, read_file

async def main():
    print("🏗️ Complex Multi-team Workflow")
    print("=" * 35)
    
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
    
    print(f"✅ Created complex workflow with {len(flow.teams)} teams")
    
    # Run complex workflow
    result = await flow.run("Collect data from web and files, analyze the information, and create a comprehensive report")
    
    print("✅ Complex workflow completed!")
    print(f"📝 Total messages: {len(result['messages'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Specialized Agents

### FilesystemAgent Example
```python
import asyncio
from agenticflow import Flow
from agenticflow import FilesystemAgent

async def main():
    print("📁 FilesystemAgent Example")
    print("=" * 25)
    
    flow = Flow("filesystem_workflow")
    
    # Create filesystem agent
    fs_agent = FilesystemAgent("file_manager")
    flow.add_agent(fs_agent)
    
    print(f"✅ Created FilesystemAgent with {len(fs_agent.tools)} tools")
    
    # Test filesystem operations
    result = await flow.run("Create a project structure with src, docs, and tests directories")
    print(f"Result: {result['messages'][-1].content}")
    
    result = await flow.run("List the contents of the examples/artifacts directory")
    print(f"Result: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### PythonAgent Example
```python
import asyncio
from agenticflow import Flow
from agenticflow import PythonAgent

async def main():
    print("🐍 PythonAgent Example")
    print("=" * 20)
    
    flow = Flow("python_workflow")
    
    # Create Python agent
    py_agent = PythonAgent("code_analyst")
    flow.add_agent(py_agent)
    
    print(f"✅ Created PythonAgent with {len(py_agent.tools)} tools")
    
    # Test Python operations
    result = await flow.run("Write a Python function to calculate fibonacci numbers and test it")
    print(f"Result: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### ExcelAgent Example
```python
import asyncio
from agenticflow import Flow
from agenticflow import ExcelAgent

async def main():
    print("📊 ExcelAgent Example")
    print("=" * 20)
    
    flow = Flow("excel_workflow")
    
    # Create Excel agent
    excel_agent = ExcelAgent("spreadsheet_processor")
    flow.add_agent(excel_agent)
    
    print(f"✅ Created ExcelAgent with {len(excel_agent.tools)} tools")
    
    # Test Excel operations
    result = await flow.run("Create an Excel file with sales data and generate a summary report")
    print(f"Result: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### DataAgent Example
```python
import asyncio
from agenticflow import Flow
from agenticflow import DataAgent

async def main():
    print("📄 DataAgent Example")
    print("=" * 20)
    
    flow = Flow("data_workflow")
    
    # Create data agent
    data_agent = DataAgent("data_processor")
    flow.add_agent(data_agent)
    
    print(f"✅ Created DataAgent with {len(data_agent.tools)} tools")
    
    # Test data operations
    result = await flow.run("Process JSON data and convert it to CSV format")
    print(f"Result: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### SSISAnalysisAgent Example
```python
import asyncio
from agenticflow import Flow
from agenticflow import SSISAnalysisAgent

async def main():
    print("🔧 SSISAnalysisAgent Example")
    print("=" * 30)
    
    flow = Flow("ssis_workflow")
    
    # Create SSIS agent with ChromaDB
    ssis_agent = SSISAnalysisAgent(
        "ssis_analyst",
        vector_backend="chroma",
        persistent=True
    )
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSISAnalysisAgent with {len(ssis_agent.tools)} tools")
    
    # Test SSIS operations
    result = await flow.run("Parse the sample_complex_package.dtsx file and show its structure")
    print(f"Result: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Vector Storage

### ChromaDB Backend
```python
import asyncio
from agenticflow import Flow
from agenticflow import SSISAnalysisAgent

async def main():
    print("🧠 ChromaDB Vector Storage")
    print("=" * 25)
    
    flow = Flow("chroma_workflow")
    
    # Create SSIS agent with ChromaDB
    ssis_agent = SSISAnalysisAgent(
        "ssis_analyst",
        vector_backend="chroma",
        persistent=False  # Ephemeral for testing
    )
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSIS agent with ChromaDB backend")
    
    # Index package
    result = await flow.run("Index sample_complex_package.dtsx for semantic search")
    print(f"Indexing: {result['messages'][-1].content}")
    
    # Semantic search
    result = await flow.run("Find all data transformations using semantic search")
    print(f"Search: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### SQLite Backend
```python
import asyncio
from agenticflow import Flow
from agenticflow import SSISAnalysisAgent

async def main():
    print("🗄️ SQLite Vector Storage")
    print("=" * 25)
    
    flow = Flow("sqlite_workflow")
    
    # Create SSIS agent with SQLite
    ssis_agent = SSISAnalysisAgent(
        "ssis_analyst",
        vector_backend="sqlite",
        persistent=True
    )
    flow.add_agent(ssis_agent)
    
    print(f"✅ Created SSIS agent with SQLite backend")
    
    # Index package
    result = await flow.run("Index sample_complex_package.dtsx for text search")
    print(f"Indexing: {result['messages'][-1].content}")
    
    # Text search
    result = await flow.run("Search for 'Customer' in the package")
    print(f"Search: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Examples

### Multi-Agent Specialized Workflow
```python
import asyncio
from agenticflow import Flow
from agenticflow import FilesystemAgent, PythonAgent, ExcelAgent, DataAgent

async def main():
    print("🚀 Multi-Agent Specialized Workflow")
    print("=" * 40)
    
    flow = Flow("multi_agent_workflow")
    
    # Add specialized agents
    flow.add_agent(FilesystemAgent("file_manager"))
    flow.add_agent(DataAgent("data_processor"))
    flow.add_agent(PythonAgent("code_analyst"))
    flow.add_agent(ExcelAgent("spreadsheet_processor"))
    
    print(f"✅ Created workflow with {len(flow.agents)} specialized agents")
    
    # Run comprehensive workflow
    result = await flow.run("Process data files, analyze them with Python, and create Excel reports")
    
    print("✅ Multi-agent workflow completed!")
    print(f"📝 Total messages: {len(result['messages'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Team with Specialized Agents
```python
import asyncio
from agenticflow import Flow, Team
from agenticflow import FilesystemAgent, PythonAgent, ExcelAgent

async def main():
    print("👥 Team with Specialized Agents")
    print("=" * 35)
    
    flow = Flow("team_specialized_workflow")
    
    # Data Processing Team
    data_team = Team("data_team")
    data_team.add_agent(FilesystemAgent("file_manager"))
    data_team.add_agent(PythonAgent("data_analyst"))
    flow.add_team(data_team)
    
    # Reporting Team
    reporting_team = Team("reporting_team")
    reporting_team.add_agent(ExcelAgent("spreadsheet_processor"))
    flow.add_team(reporting_team)
    
    print(f"✅ Created team structure with specialized agents")
    
    # Run team workflow
    result = await flow.run("Process data files, analyze them, and create Excel reports")
    
    print("✅ Team specialized workflow completed!")
    print(f"📝 Total messages: {len(result['messages'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Concurrent Workflows
```python
import asyncio
from agenticflow import Flow, Agent, create_file, search_web

async def run_workflow(workflow_id: int):
    """Run a single workflow."""
    flow = Flow(f"workflow_{workflow_id}")
    
    agent = Agent(f"agent_{workflow_id}", tools=[create_file, search_web])
    flow.add_agent(agent)
    
    result = await flow.run(f"Research topic {workflow_id} and create a report")
    return result

async def main():
    print("⚡ Concurrent Workflows")
    print("=" * 25)
    
    # Create multiple workflows
    tasks = [run_workflow(i) for i in range(5)]
    
    # Run concurrently
    results = await asyncio.gather(*tasks)
    
    print(f"✅ Completed {len(results)} concurrent workflows")
    for i, result in enumerate(results):
        print(f"   Workflow {i}: {len(result['messages'])} messages")

if __name__ == "__main__":
    asyncio.run(main())
```

## Real-world Scenarios

### Data Pipeline Workflow
```python
import asyncio
from agenticflow import Flow, Team
from agenticflow import FilesystemAgent, DataAgent, PythonAgent, ExcelAgent

async def main():
    print("🔄 Data Pipeline Workflow")
    print("=" * 25)
    
    flow = Flow("data_pipeline")
    
    # Data Collection Team
    collection_team = Team("collection_team")
    collection_team.add_agent(FilesystemAgent("file_manager"))
    collection_team.add_agent(DataAgent("data_processor"))
    flow.add_team(collection_team)
    
    # Analysis Team
    analysis_team = Team("analysis_team")
    analysis_team.add_agent(PythonAgent("data_analyst"))
    flow.add_team(analysis_team)
    
    # Reporting Team
    reporting_team = Team("reporting_team")
    reporting_team.add_agent(ExcelAgent("report_generator"))
    flow.add_team(reporting_team)
    
    print("✅ Created data pipeline with 3 teams")
    
    # Run data pipeline
    result = await flow.run("""
    Collect data from files, process and clean the data, 
    perform analysis with Python, and generate Excel reports
    """)
    
    print("✅ Data pipeline completed!")
    print(f"📝 Total messages: {len(result['messages'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

### SSIS Package Analysis Workflow
```python
import asyncio
from agenticflow import Flow, Team
from agenticflow import SSISAnalysisAgent, FilesystemAgent, DataAgent

async def main():
    print("🔧 SSIS Package Analysis Workflow")
    print("=" * 35)
    
    flow = Flow("ssis_analysis")
    
    # Analysis Team
    analysis_team = Team("analysis_team")
    analysis_team.add_agent(SSISAnalysisAgent("ssis_analyst", vector_backend="chroma"))
    analysis_team.add_agent(FilesystemAgent("file_manager"))
    flow.add_team(analysis_team)
    
    # Documentation Team
    doc_team = Team("documentation_team")
    doc_team.add_agent(DataAgent("doc_processor"))
    flow.add_team(doc_team)
    
    print("✅ Created SSIS analysis workflow")
    
    # Run SSIS analysis
    result = await flow.run("""
    Analyze the SSIS package, extract data flows and connections,
    and create comprehensive documentation
    """)
    
    print("✅ SSIS analysis completed!")
    print(f"📝 Total messages: {len(result['messages'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling Example
```python
import asyncio
from agenticflow import Flow, Agent, create_file, search_web

async def main():
    print("⚠️ Error Handling Example")
    print("=" * 25)
    
    try:
        flow = Flow("error_handling_workflow")
        
        agent = Agent("test_agent", tools=[create_file, search_web])
        flow.add_agent(agent)
        
        # This might fail
        result = await flow.run("Perform a complex task that might fail")
        
        print("✅ Workflow completed successfully")
        print(f"📝 Messages: {len(result['messages'])}")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        # Handle error appropriately
        print("🔄 Implementing fallback strategy...")

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Tool Integration
```python
import asyncio
from agenticflow import Flow, Agent
from langchain_core.tools import tool

@tool
def custom_analysis_tool(data: str) -> str:
    """Custom analysis tool."""
    # Your custom logic here
    return f"Custom analysis of: {data}"

@tool
def custom_reporting_tool(analysis: str) -> str:
    """Custom reporting tool."""
    # Your custom logic here
    return f"Custom report: {analysis}"

async def main():
    print("🛠️ Custom Tool Integration")
    print("=" * 25)
    
    flow = Flow("custom_tool_workflow")
    
    # Create agent with custom tools
    agent = Agent(
        "custom_agent",
        tools=[custom_analysis_tool, custom_reporting_tool]
    )
    flow.add_agent(agent)
    
    print(f"✅ Created agent with {len(agent.tools)} custom tools")
    
    # Run workflow with custom tools
    result = await flow.run("Analyze data using custom tools and generate a report")
    
    print("✅ Custom tool workflow completed!")
    print(f"📝 Messages: {len(result['messages'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Running Examples

### From Command Line
```bash
# Run basic example
uv run python examples/simple_workflow.py

# Run team example
uv run python examples/team_workflow.py

# Run specialized agent example
uv run python examples/test_ssis_agent.py
```

### From Python
```python
# Import and run
from examples.simple_workflow import main
import asyncio

asyncio.run(main())
```

## Best Practices

1. **Start Simple**: Begin with basic workflows and gradually add complexity
2. **Use Teams**: Organize related agents into teams for better structure
3. **Handle Errors**: Always wrap workflows in try-catch blocks
4. **Monitor Performance**: Keep an eye on memory usage and execution time
5. **Test Thoroughly**: Test individual agents and complete workflows
6. **Document**: Document your workflows and agent purposes
7. **Optimize**: Use appropriate tools and configurations for your use case

This examples guide provides comprehensive patterns for using AgenticFlow in various scenarios. For more detailed information, see the [API Reference](API_REFERENCE.md) and [Usage Guide](USAGE.md).
