# Specialized Agents Reference

This document provides a comprehensive reference for all specialized agents in AgenticFlow.

## Table of Contents

1. [FilesystemAgent](#filesystemagent)
2. [PythonAgent](#pythonagent)
3. [ExcelAgent](#excelagent)
4. [DataAgent](#dataagent)
5. [SSISAnalysisAgent](#ssisanalysisagent)
6. [Creating Custom Agents](#creating-custom-agents)

## FilesystemAgent

### Overview
The FilesystemAgent provides comprehensive file and directory operations for managing filesystem resources.

### Tools (16 tools)
- `_create_file` - Create files with content
- `_read_file` - Read file contents
- `_write_file` - Write content to files
- `_append_file` - Append content to files
- `_delete_file` - Delete files
- `_copy_file` - Copy files
- `_move_file` - Move/rename files
- `_create_directory` - Create directories
- `_delete_directory` - Delete directories
- `_list_directory` - List directory contents
- `_find_files` - Find files by pattern
- `_grep_files` - Search for text in files
- `_get_file_info` - Get file metadata
- `_search_files` - Search files by content
- `_backup_file` - Backup files
- `terminal` - Shell tool for interactive execution

### Usage
```python
from agenticflow import Flow
from agenticflow import FilesystemAgent

async def main():
    flow = Flow("filesystem_workflow")
    
    fs_agent = FilesystemAgent("file_manager")
    flow.add_agent(fs_agent)
    
    result = await flow.run("Create a project structure with src, docs, and tests directories")
    print(result)

asyncio.run(main())
```

### Example Tasks
- "Create a directory structure for a Python project"
- "Find all Python files in the project"
- "Backup important files to a backup directory"
- "Search for specific text across all files"

## PythonAgent

### Overview
The PythonAgent specializes in Python code analysis, execution, and generation.

### Tools (15 tools)
- `_execute_python` - Execute Python code safely
- `_validate_python` - Validate Python syntax
- `_generate_python` - Generate Python code
- `_convert_to_python` - Convert other scripts to Python
- `_format_python` - Format Python code
- `_analyze_python` - Analyze code complexity
- `_test_python` - Run Python tests
- `_install_package` - Install Python packages
- `_create_script` - Create Python scripts
- `_run_script` - Run Python scripts
- `_debug_python` - Debug Python code
- `_optimize_python` - Optimize Python code
- `_document_python` - Generate documentation
- `_refactor_python` - Refactor Python code
- `_python_repl` - Interactive Python shell

### Usage
```python
from agenticflow import Flow
from agenticflow import PythonAgent

async def main():
    flow = Flow("python_workflow")
    
    py_agent = PythonAgent("code_analyst")
    flow.add_agent(py_agent)
    
    result = await flow.run("Write a Python function to calculate fibonacci numbers and test it")
    print(result)

asyncio.run(main())
```

### Example Tasks
- "Write a data processing script for CSV files"
- "Debug this Python code and fix the errors"
- "Optimize this Python function for better performance"
- "Generate unit tests for this Python module"

## ExcelAgent

### Overview
The ExcelAgent handles Excel and spreadsheet operations including creation, manipulation, and analysis.

### Tools (20 tools)
- `_create_excel` - Create Excel files
- `_read_excel` - Read Excel data
- `_write_excel` - Write data to Excel
- `_append_excel` - Append data to Excel
- `_update_excel` - Update Excel cells
- `_delete_excel` - Delete Excel files
- `_copy_sheet` - Copy worksheets
- `_merge_excel` - Merge Excel files
- `_split_excel` - Split Excel files
- `_format_excel` - Format Excel cells
- `_calculate_excel` - Perform calculations
- `_filter_excel` - Filter Excel data
- `_sort_excel` - Sort Excel data
- `_pivot_excel` - Create pivot tables
- `_chart_excel` - Create charts
- `_export_excel` - Export to other formats
- `_import_excel` - Import from other formats
- `_validate_excel` - Validate Excel data
- `_analyze_excel` - Analyze Excel data
- `_convert_excel` - Convert Excel formats

### Usage
```python
from agenticflow import Flow
from agenticflow import ExcelAgent

async def main():
    flow = Flow("excel_workflow")
    
    excel_agent = ExcelAgent("spreadsheet_processor")
    flow.add_agent(excel_agent)
    
    result = await flow.run("Create an Excel file with sales data and generate a summary report")
    print(result)

asyncio.run(main())
```

### Example Tasks
- "Create a budget spreadsheet with formulas"
- "Analyze sales data and create charts"
- "Merge multiple Excel files into one"
- "Convert CSV data to Excel format"

## DataAgent

### Overview
The DataAgent specializes in processing various data formats including JSON, XML, YAML, CSV, and databases.

### Tools (22 tools)
- `_read_json` - Read JSON files
- `_write_json` - Write JSON files
- `_validate_json` - Validate JSON syntax
- `_transform_json` - Transform JSON data
- `_merge_json` - Merge JSON objects
- `_read_xml` - Read XML files
- `_write_xml` - Write XML files
- `_validate_xml` - Validate XML syntax
- `_transform_xml` - Transform XML data
- `_read_yaml` - Read YAML files
- `_write_yaml` - Write YAML files
- `_read_csv` - Read CSV files
- `_write_csv` - Write CSV files
- `_read_toml` - Read TOML files
- `_write_toml` - Write TOML files
- `_read_ini` - Read INI files
- `_write_ini` - Write INI files
- `_create_sqlite` - Create SQLite databases
- `_query_sqlite` - Query SQLite databases
- `_convert_data` - Convert between data formats
- `_analyze_data` - Analyze data patterns
- `_clean_data` - Clean and validate data

### Usage
```python
from agenticflow import Flow
from agenticflow import DataAgent

async def main():
    flow = Flow("data_workflow")
    
    data_agent = DataAgent("data_processor")
    flow.add_agent(data_agent)
    
    result = await flow.run("Process this JSON data and convert it to CSV format")
    print(result)

asyncio.run(main())
```

### Example Tasks
- "Convert this XML data to JSON format"
- "Validate and clean this CSV file"
- "Create a SQLite database from this data"
- "Merge multiple JSON files into one"

## SSISAnalysisAgent

### Overview
The SSISAnalysisAgent provides comprehensive analysis of Microsoft SSIS DTSX packages with vector storage capabilities.

### Tools (18 tools)
- `_parse_dtsx_file` - Parse DTSX file structure
- `_extract_data_flows` - Extract data flow information
- `_extract_connections` - Extract connection managers
- `_extract_tasks` - Extract all tasks
- `_extract_variables` - Extract package variables
- `_analyze_package_structure` - Analyze overall structure
- `_find_data_sources` - Find data sources
- `_find_data_destinations` - Find data destinations
- `_trace_data_lineage` - Trace data lineage
- `_validate_package` - Validate package integrity
- `_create_package_summary` - Create comprehensive summary
- `_search_package_content` - Search package content
- `_index_package_for_search` - Index for vector search
- `_query_package_semantic` - Semantic search queries
- `_export_package_analysis` - Export analysis to JSON
- `_compare_packages` - Compare two packages
- `_extract_error_handling` - Extract error handling
- `_analyze_performance_implications` - Performance analysis

### Vector Storage Options
- **ChromaDB**: Semantic search with embeddings
- **SQLite**: Fast text-based search
- **None**: Basic analysis without vector storage

### Usage
```python
from agenticflow import Flow
from agenticflow import SSISAnalysisAgent

async def main():
    flow = Flow("ssis_workflow")
    
    # ChromaDB backend
    ssis_agent = SSISAnalysisAgent(
        "ssis_analyst",
        vector_backend="chroma",
        persistent=True
    )
    flow.add_agent(ssis_agent)
    
    result = await flow.run("Analyze the SSIS package and find all data transformations")
    print(result)

asyncio.run(main())
```

### Example Tasks
- "Parse this DTSX file and show its structure"
- "Find all data sources and destinations"
- "Trace the data lineage through the package"
- "Search for all SQL statements in the package"

## Creating Custom Agents

### Basic Custom Agent
```python
from agenticflow import Agent
from langchain_core.tools import tool

@tool
def custom_tool(input_data: str) -> str:
    """Custom tool description."""
    # Your custom logic here
    return f"Processed: {input_data}"

# Create custom agent
custom_agent = Agent(
    name="custom_agent",
    description="Custom agent for specific tasks",
    tools=[custom_tool]
)
```

### Specialized Custom Agent
```python
from agenticflow import Agent
from langchain_core.tools import tool
from typing import List

class CustomSpecializedAgent(Agent):
    def __init__(self, name: str = "custom_agent", description: str = "Custom specialized agent"):
        tools = self._create_tools()
        super().__init__(name, tools=tools, description=description)
    
    def _create_tools(self) -> List:
        return [
            self._custom_tool_1,
            self._custom_tool_2,
            # Add more tools
        ]
    
    @tool
    def _custom_tool_1(self, input_data: str) -> str:
        """Custom tool 1."""
        # Your logic here
        return f"Tool 1 result: {input_data}"
    
    @tool
    def _custom_tool_2(self, input_data: str) -> str:
        """Custom tool 2."""
        # Your logic here
        return f"Tool 2 result: {input_data}"
```

### Agent with Vector Storage
```python
from agenticflow import Agent
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

class CustomVectorAgent(Agent):
    def __init__(self, name: str = "vector_agent", vector_backend: str = "chroma"):
        tools = self._create_tools()
        super().__init__(name, tools=tools, description="Custom agent with vector storage")
        self._vector_backend = vector_backend
        self._vector_store = None
        self._embeddings = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        if self._vector_backend == "chroma":
            self._embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
    
    def _create_tools(self) -> List:
        return [
            self._index_data,
            self._search_data,
        ]
    
    @tool
    def _index_data(self, data: str) -> str:
        """Index data for search."""
        # Your indexing logic here
        return "Data indexed successfully"
    
    @tool
    def _search_data(self, query: str) -> str:
        """Search indexed data."""
        # Your search logic here
        return f"Search results for: {query}"
```

## Best Practices

### 1. Tool Design
- Use descriptive tool names and docstrings
- Include proper type hints
- Handle errors gracefully
- Return meaningful results

### 2. Agent Organization
- Group related tools together
- Use clear, specific descriptions
- Keep agents focused on single domains
- Document agent capabilities

### 3. Error Handling
- Validate inputs in tools
- Provide helpful error messages
- Implement fallback mechanisms
- Log errors appropriately

### 4. Performance
- Use async operations when possible
- Implement caching for expensive operations
- Optimize tool execution
- Monitor resource usage

### 5. Testing
- Test individual tools
- Test agent interactions
- Test error scenarios
- Test performance under load

## Integration Examples

### Multi-Agent Workflow
```python
from agenticflow import Flow
from agenticflow import FilesystemAgent, PythonAgent, DataAgent

async def main():
    flow = Flow("multi_agent_workflow")
    
    # Add specialized agents
    flow.add_agent(FilesystemAgent("file_manager"))
    flow.add_agent(DataAgent("data_processor"))
    flow.add_agent(PythonAgent("code_analyst"))
    
    result = await flow.run("Process data files, analyze them, and generate Python reports")
    print(result)

asyncio.run(main())
```

### Team with Specialized Agents
```python
from agenticflow import Flow, Team
from agenticflow import FilesystemAgent, PythonAgent

async def main():
    flow = Flow("team_specialized_workflow")
    
    # Data Processing Team
    data_team = Team("data_team")
    data_team.add_agent(FilesystemAgent("file_manager"))
    data_team.add_agent(PythonAgent("data_analyst"))
    flow.add_team(data_team)
    
    result = await flow.run("Process and analyze data files")
    print(result)

asyncio.run(main())
```

This reference provides comprehensive information about all specialized agents in AgenticFlow. For more detailed examples and usage patterns, see the [Examples](EXAMPLES.md) guide.
