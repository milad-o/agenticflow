# 🔧 Tools Examples

This directory contains examples demonstrating AgenticFlow's tool integration and calling capabilities.

## 🌟 Featured Examples

### 🛠️ Final Tool Calling Validation
**File:** `final_tool_calling_validation.py`

A comprehensive validation suite for AgenticFlow's tool calling system featuring:

## 🚀 Tool System Architecture

### Core Components
- **Tool Registry**: Global and per-agent tool registration
- **Tool Detection**: Natural language and explicit tool mention parsing
- **Parameter Extraction**: Intelligent parameter inference from user queries
- **Execution Engine**: Safe, sandboxed tool execution environment

### Tool Types Demonstrated

#### 🕐 Time Tool
- **Function**: `get_time`
- **Purpose**: Returns current date and time
- **Detection**: "What time is it?", "current time"
- **Parameters**: None required

#### 🖥️ System Info Tool
- **Function**: `system_info`  
- **Purpose**: Provides system platform and Python version
- **Detection**: "system info", "what system am I on?"
- **Parameters**: None required

#### 🧮 Precise Math Tool
- **Function**: `precise_math`
- **Purpose**: Evaluates mathematical expressions safely
- **Detection**: Math operations, calculations
- **Parameters**: `expression` (string) - mathematical expression to evaluate

#### 🌤️ Weather Info Tool
- **Function**: `weather_info`
- **Purpose**: Provides simulated weather information
- **Detection**: "weather", "temperature", location mentions
- **Parameters**: `location` (string) - city/location name

## 🧪 Validation Test Suite

### Test Categories

#### 1. 🔍 Natural Language Detection
```python
Query: "What time is it right now?"
Expected: get_time tool execution
Result: ✅ Tool correctly identified and executed
```

#### 2. 🎯 Explicit Tool Mention  
```python
Query: "Please use system_info tool"
Expected: system_info tool execution
Result: ✅ Tool correctly parsed and called
```

#### 3. 📊 Parameter Extraction
```python
Query: "Calculate 25 * 4 + 17"
Expected: precise_math tool with expression parameter
Result: ⚠️ Partial success (parameter extraction needs refinement)
```

#### 4. 🌍 Complex Parameter Extraction
```python
Query: "What's the weather like in Tokyo?"
Expected: weather_info tool with location="Tokyo"
Result: ⚠️ Parameter extraction needs enhancement
```

## 📈 Performance Metrics

### Tool Execution Statistics
- **Registration Success**: 100% (4/4 tools registered)
- **Detection Rate**: 75% (3/4 test cases)
- **Natural Language Parsing**: 100% success rate
- **Explicit Mentions**: 100% success rate
- **Parameter Extraction**: 50% success rate (needs improvement)

### Response Times
- **Tool Registration**: <1ms per tool
- **Query Processing**: 10-20s (LLM-dependent)
- **Tool Execution**: <1ms (local tools)
- **Result Integration**: <100ms

## 🔧 Tool Development Pattern

### Custom Tool Creation
```python
from agenticflow.tools import tool

@tool("my_custom_tool")
async def my_tool(parameter1: str, parameter2: int = 42) -> str:
    """
    Description of what the tool does.
    
    Args:
        parameter1: Required string parameter
        parameter2: Optional integer parameter
    
    Returns:
        Tool execution result
    """
    # Tool implementation
    result = f"Processing {parameter1} with {parameter2}"
    return result
```

### Tool Registration
```python
# Automatic registration via @tool decorator
# OR manual registration:
agent.register_tool("tool_name", tool_function)
```

### Memory Integration
Tools work seamlessly with different memory backends:
- **Buffer Memory**: In-memory tool results
- **SQLite Memory**: Persistent tool execution history
- **PostgreSQL Memory**: Enterprise tool audit trails
- **Vector Memory**: Semantic tool result indexing

## 🎯 Tool Detection Strategies

### 1. Natural Language Processing
- Semantic analysis of user queries
- Intent recognition for tool selection
- Context-aware parameter extraction

### 2. Explicit Mentions
- Direct tool name references
- "use X tool" patterns
- Command-style invocations

### 3. Pattern Matching
- Mathematical expressions → math tool
- Time-related queries → time tool
- System queries → system info tool
- Location + weather → weather tool

## 🚀 Quick Start

```bash
# Run the comprehensive tool validation
uv run python examples/tools/final_tool_calling_validation.py
```

The validation will:
1. Test tool registration and discovery
2. Create agent with tool integration
3. Run 4 different tool calling scenarios
4. Report success rates and performance metrics
5. Demonstrate natural language → tool execution flow

## 🔒 Security Features

### Sandboxed Execution
- Tools run in controlled environment
- Input validation and sanitization
- Resource limits and timeouts
- Error isolation and recovery

### Parameter Validation
- Type checking for tool parameters
- Required parameter validation
- Safe parameter parsing and conversion
- Input sanitization for security

## 🎯 Use Cases

Tool integration is ideal for:

- **API Integration**: External service calls
- **System Operations**: File system, network, database operations
- **Calculations**: Mathematical and statistical operations
- **Data Processing**: Text processing, format conversion
- **Information Retrieval**: Web search, database queries
- **Automation**: Task execution, workflow integration

## 🔧 Current Status

### ✅ Working Features
- Tool registration and discovery
- Natural language tool detection
- Explicit tool mention parsing
- Basic tool execution
- Memory system integration

### 🚧 Areas for Enhancement
- Parameter extraction accuracy (currently 50%)
- Complex query understanding
- Multi-tool coordination
- Advanced error handling
- Tool result post-processing

The tool system demonstrates AgenticFlow's extensibility and integration capabilities, providing a foundation for building sophisticated AI agents with external tool access.