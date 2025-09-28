# AgenticFlow API Reference

Complete API reference for all AgenticFlow components.

## Table of Contents

1. [Core Classes](#core-classes)
2. [Specialized Agents](#specialized-agents)
3. [Tools](#tools)
4. [Vector Storage](#vector-storage)
5. [Examples](#examples)

## Core Classes

### Flow

Main orchestrator for managing agents and teams.

```python
class Flow:
    def __init__(self, name: str)
    def add_agent(self, agent: Agent) -> None
    def add_team(self, team: Team) -> None
    def build_graph(self) -> StateGraph
    async def run(self, message: str, recursion_limit: int = 50) -> Dict[str, Any]
```

#### Parameters
- `name` (str): Name of the flow

#### Methods
- `add_agent(agent)`: Add an agent directly to the flow
- `add_team(team)`: Add a team to the flow
- `build_graph()`: Build the LangGraph execution graph
- `run(message, recursion_limit)`: Execute the flow with a message

#### Example
```python
flow = Flow("my_workflow")
flow.add_agent(agent)
result = await flow.run("Your message")
```

### Agent

Individual worker that performs tasks using tools.

```python
class Agent:
    def __init__(self, name: str, tools: List[Any] = None, description: str = "")
    def create_node(self) -> Callable
```

#### Parameters
- `name` (str): Name of the agent
- `tools` (List[Any], optional): List of tools the agent can use
- `description` (str, optional): Description of the agent's purpose

#### Methods
- `create_node()`: Create a LangGraph node for the agent

#### Example
```python
agent = Agent("my_agent", tools=[tool1, tool2], description="My agent")
```

### Team

Collection of agents managed by a supervisor.

```python
class Team:
    def __init__(self, name: str)
    def add_agent(self, agent: Agent) -> None
    def create_supervisor_node(self) -> Callable
```

#### Parameters
- `name` (str): Name of the team

#### Methods
- `add_agent(agent)`: Add an agent to the team
- `create_supervisor_node()`: Create a supervisor node for the team

#### Example
```python
team = Team("my_team")
team.add_agent(agent1)
team.add_agent(agent2)
```

## Specialized Agents

### FilesystemAgent

Agent for comprehensive file and directory operations.

```python
class FilesystemAgent(Agent):
    def __init__(self, name: str = "filesystem_agent", description: str = "Filesystem operations specialist")
```

#### Tools
- `_create_file(content, filename, directory)` - Create files
- `_read_file(filename, directory)` - Read files
- `_write_file(content, filename, directory)` - Write files
- `_append_file(content, filename, directory)` - Append to files
- `_delete_file(filename, directory)` - Delete files
- `_copy_file(source, destination)` - Copy files
- `_move_file(source, destination)` - Move files
- `_create_directory(name, parent_dir)` - Create directories
- `_delete_directory(name, parent_dir)` - Delete directories
- `_list_directory(directory)` - List directory contents
- `_find_files(pattern, directory)` - Find files by pattern
- `_grep_files(pattern, directory)` - Search text in files
- `_get_file_info(filename, directory)` - Get file metadata
- `_search_files(query, directory)` - Search files by content
- `_backup_file(filename, backup_dir)` - Backup files
- `terminal` - Shell tool for interactive execution

#### Example
```python
fs_agent = FilesystemAgent("file_manager")
flow.add_agent(fs_agent)
```

### PythonAgent

Agent for Python code analysis and execution.

```python
class PythonAgent(Agent):
    def __init__(self, name: str = "python_agent", description: str = "Python code specialist")
```

#### Tools
- `_execute_python(code, timeout)` - Execute Python code
- `_validate_python(code)` - Validate Python syntax
- `_generate_python(description)` - Generate Python code
- `_convert_to_python(source_code, source_lang)` - Convert other languages to Python
- `_format_python(code)` - Format Python code
- `_analyze_python(code)` - Analyze code complexity
- `_test_python(code)` - Run Python tests
- `_install_package(package_name)` - Install Python packages
- `_create_script(filename, content)` - Create Python scripts
- `_run_script(filename)` - Run Python scripts
- `_debug_python(code)` - Debug Python code
- `_optimize_python(code)` - Optimize Python code
- `_document_python(code)` - Generate documentation
- `_refactor_python(code)` - Refactor Python code
- `_python_repl` - Interactive Python shell

#### Example
```python
py_agent = PythonAgent("code_analyst")
flow.add_agent(py_agent)
```

### ExcelAgent

Agent for Excel and spreadsheet operations.

```python
class ExcelAgent(Agent):
    def __init__(self, name: str = "excel_agent", description: str = "Excel and spreadsheet specialist")
```

#### Tools
- `_create_excel(filename, sheet_name, data, directory)` - Create Excel files
- `_read_excel(filename, sheet_name, directory)` - Read Excel data
- `_write_excel(filename, sheet_name, data, directory)` - Write Excel data
- `_append_excel(filename, sheet_name, data, directory)` - Append to Excel
- `_update_excel(filename, sheet_name, updates, directory)` - Update Excel cells
- `_delete_excel(filename, directory)` - Delete Excel files
- `_copy_sheet(filename, source_sheet, dest_sheet, directory)` - Copy worksheets
- `_merge_excel(filenames, output_filename, directory)` - Merge Excel files
- `_split_excel(filename, sheet_names, directory)` - Split Excel files
- `_format_excel(filename, sheet_name, formatting, directory)` - Format Excel
- `_calculate_excel(filename, sheet_name, formulas, directory)` - Perform calculations
- `_filter_excel(filename, sheet_name, criteria, directory)` - Filter data
- `_sort_excel(filename, sheet_name, sort_by, directory)` - Sort data
- `_pivot_excel(filename, sheet_name, pivot_config, directory)` - Create pivot tables
- `_chart_excel(filename, sheet_name, chart_config, directory)` - Create charts
- `_export_excel(filename, format, directory)` - Export to other formats
- `_import_excel(filename, source_format, directory)` - Import from other formats
- `_validate_excel(filename, sheet_name, directory)` - Validate Excel data
- `_analyze_excel(filename, sheet_name, directory)` - Analyze Excel data
- `_convert_excel(filename, target_format, directory)` - Convert Excel formats

#### Example
```python
excel_agent = ExcelAgent("spreadsheet_processor")
flow.add_agent(excel_agent)
```

### DataAgent

Agent for data format processing and manipulation.

```python
class DataAgent(Agent):
    def __init__(self, name: str = "data_agent", description: str = "Data processing specialist")
```

#### Tools
- `_read_json(filename, directory)` - Read JSON files
- `_write_json(data, filename, directory)` - Write JSON files
- `_validate_json(data)` - Validate JSON syntax
- `_transform_json(data, transformation)` - Transform JSON data
- `_merge_json(files, output_file, directory)` - Merge JSON objects
- `_read_xml(filename, directory)` - Read XML files
- `_write_xml(data, filename, directory)` - Write XML files
- `_validate_xml(data)` - Validate XML syntax
- `_transform_xml(data, transformation)` - Transform XML data
- `_read_yaml(filename, directory)` - Read YAML files
- `_write_yaml(data, filename, directory)` - Write YAML files
- `_read_csv(filename, directory)` - Read CSV files
- `_write_csv(data, filename, directory)` - Write CSV files
- `_read_toml(filename, directory)` - Read TOML files
- `_write_toml(data, filename, directory)` - Write TOML files
- `_read_ini(filename, directory)` - Read INI files
- `_write_ini(data, filename, directory)` - Write INI files
- `_create_sqlite(filename, sql_schema, directory)` - Create SQLite databases
- `_query_sqlite(filename, query, directory)` - Query SQLite databases
- `_convert_data(data, source_format, target_format)` - Convert data formats
- `_analyze_data(data, analysis_type)` - Analyze data patterns
- `_clean_data(data, cleaning_rules)` - Clean and validate data

#### Example
```python
data_agent = DataAgent("data_processor")
flow.add_agent(data_agent)
```

### SSISAnalysisAgent

Agent for Microsoft SSIS package analysis with vector storage.

```python
class SSISAnalysisAgent(Agent):
    def __init__(self, name: str = "ssis_agent", description: str = "SSIS DTSX file analysis specialist", 
                 vector_backend: str = "chroma", persistent: bool = False)
```

#### Parameters
- `name` (str): Name of the agent
- `description` (str): Description of the agent
- `vector_backend` (str): Vector storage backend ("chroma", "sqlite", "none")
- `persistent` (bool): Whether to use persistent storage

#### Tools
- `_parse_dtsx_file(filepath, directory)` - Parse DTSX file structure
- `_extract_data_flows(filepath, directory)` - Extract data flow information
- `_extract_connections(filepath, directory)` - Extract connection managers
- `_extract_tasks(filepath, directory)` - Extract all tasks
- `_extract_variables(filepath, directory)` - Extract package variables
- `_analyze_package_structure(filepath, directory)` - Analyze overall structure
- `_find_data_sources(filepath, directory)` - Find data sources
- `_find_data_destinations(filepath, directory)` - Find data destinations
- `_trace_data_lineage(filepath, directory)` - Trace data lineage
- `_validate_package(filepath, directory)` - Validate package integrity
- `_create_package_summary(filepath, directory)` - Create comprehensive summary
- `_search_package_content(filepath, search_term, directory)` - Search package content
- `_index_package_for_search(filepath, directory)` - Index for vector search
- `_query_package_semantic(query, filepath, directory)` - Semantic search queries
- `_export_package_analysis(filepath, output_filename, directory)` - Export analysis
- `_compare_packages(filepath1, filepath2, directory)` - Compare packages
- `_extract_error_handling(filepath, directory)` - Extract error handling
- `_analyze_performance_implications(filepath, directory)` - Performance analysis

#### Example
```python
ssis_agent = SSISAnalysisAgent("ssis_analyst", vector_backend="chroma", persistent=True)
flow.add_agent(ssis_agent)
```

## Tools

### Built-in Tools

#### File Operations
```python
from agenticflow.tools import create_file, read_file, list_directory

# Create file
create_file(content="Hello World", filename="test.txt")

# Read file
read_file(filename="test.txt")

# List directory
list_directory(directory="examples/artifacts")
```

#### Web Search
```python
from agenticflow.tools import search_web

# Search web
search_web(query="Python programming")
```

### SSIS Tools
```python
from agenticflow.tools.ssis_tools import (
    parse_dtsx_file, extract_data_flows, extract_connections,
    extract_tasks, extract_variables, create_package_summary,
    search_package_content
)

# Parse DTSX file
parse_dtsx_file(filepath="package.dtsx")

# Extract data flows
extract_data_flows(filepath="package.dtsx")

# Search package content
search_package_content(filepath="package.dtsx", search_term="Customer")
```

### Custom Tools
```python
from langchain_core.tools import tool

@tool
def custom_tool(input_data: str) -> str:
    """Custom tool description."""
    # Your custom logic here
    return f"Processed: {input_data}"

# Use in agent
agent = Agent("custom_agent", tools=[custom_tool])
```

## Vector Storage

### ChromaDB Backend
```python
# Ephemeral ChromaDB
ssis_agent = SSISAnalysisAgent("ssis_analyst", vector_backend="chroma", persistent=False)

# Persistent ChromaDB
ssis_agent = SSISAnalysisAgent("ssis_analyst", vector_backend="chroma", persistent=True)
```

### SQLite Backend
```python
# Ephemeral SQLite
ssis_agent = SSISAnalysisAgent("ssis_analyst", vector_backend="sqlite", persistent=False)

# Persistent SQLite
ssis_agent = SSISAnalysisAgent("ssis_analyst", vector_backend="sqlite", persistent=True)
```

### No Vector Storage
```python
# Basic analysis without vector storage
ssis_agent = SSISAnalysisAgent("ssis_analyst", vector_backend="none")
```

## Examples

### Basic Workflow
```python
import asyncio
from agenticflow import Flow, Agent, create_file, search_web

async def main():
    flow = Flow("basic_workflow")
    
    agent = Agent("my_agent", tools=[create_file, search_web])
    flow.add_agent(agent)
    
    result = await flow.run("Research and create a report")
    print(result)

asyncio.run(main())
```

### Team Workflow
```python
import asyncio
from agenticflow import Flow, Agent, Team, create_file, search_web

async def main():
    flow = Flow("team_workflow")
    
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
    
    result = await flow.run("Research and create a report")
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
    
    result = await flow.run("Process data and create analysis reports")
    print(result)

asyncio.run(main())
```

### Vector Search
```python
import asyncio
from agenticflow import Flow
from agenticflow import SSISAnalysisAgent

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

## Error Handling

### Common Exceptions
```python
try:
    result = await flow.run("Your message")
except Exception as e:
    print(f"Error: {e}")
    # Handle error appropriately
```

### Tool Errors
```python
@tool
def safe_tool(input_data: str) -> str:
    """Safe tool with error handling."""
    try:
        # Your logic here
        return f"Success: {input_data}"
    except Exception as e:
        return f"Error: {e}"
```

## Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
TAVILY_API_KEY=your_tavily_api_key
```

### Flow Configuration
```python
# Set recursion limit
result = await flow.run("Your message", recursion_limit=100)

# Build graph manually
flow.build_graph()
```

This API reference provides comprehensive information about all AgenticFlow components. For more detailed examples and usage patterns, see the [Examples](EXAMPLES.md) guide.
