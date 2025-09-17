"""
Unit tests for ToolRegistry
===========================

Tests for tool registration, retrieval, and execution functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock

from agenticflow.tools.registry import ToolRegistry
from agenticflow.tools.base_tool import AsyncTool


@pytest.mark.unit
class TestToolRegistry:
    """Unit tests for ToolRegistry class."""
    
    def test_registry_initialization(self):
        """Test tool registry initialization."""
        registry = ToolRegistry()
        
        assert registry.tools == {}
        assert registry.categories == {}
        assert len(registry.list_tools()) == 0
    
    def test_register_function_tool(self):
        """Test registering a function as a tool."""
        registry = ToolRegistry()
        
        @registry.register_function("test_add")
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b
        
        assert "test_add" in registry.tools
        tool = registry.get_tool("test_add")
        assert tool is not None
        assert tool.name == "test_add"
        assert tool.description == "Add two numbers together."
    
    def test_register_function_with_metadata(self):
        """Test registering function with additional metadata."""
        registry = ToolRegistry()
        
        @registry.register_function("test_multiply", category="math", tags=["arithmetic", "basic"])
        def multiply_numbers(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b
        
        tool = registry.get_tool("test_multiply")
        assert tool.category == "math"
        assert tool.tags == ["arithmetic", "basic"]
        assert "math" in registry.categories
    
    def test_register_async_function(self):
        """Test registering async function as tool."""
        registry = ToolRegistry()
        
        @registry.register_function("async_operation")
        async def async_task(delay: float = 0.1) -> str:
            """Perform async operation with delay."""
            await asyncio.sleep(delay)
            return "completed"
        
        tool = registry.get_tool("async_operation")
        assert tool is not None
        assert asyncio.iscoroutinefunction(tool.function)
    
    def test_register_class_tool(self):
        """Test registering a class-based tool."""
        registry = ToolRegistry()
        
        class TestTool(AsyncTool):
            def __init__(self):
                super().__init__("test_class_tool", "A test class tool")
            
            @property
            def parameters(self):
                return {"type": "object", "properties": {}}
            
            async def execute(self, parameters):
                return {"result": "class_result"}
        
        test_tool = TestTool()
        registry.register_tool(test_tool)
        
        assert "test_class_tool" in registry.tools
        retrieved_tool = registry.get_tool("test_class_tool")
        assert retrieved_tool == test_tool
    
    def test_register_duplicate_tool_raises_error(self):
        """Test that registering duplicate tool names raises error."""
        registry = ToolRegistry()
        
        @registry.register_function("duplicate")
        def first_function():
            return "first"
        
        with pytest.raises(ValueError, match="already registered"):
            @registry.register_function("duplicate")
            def second_function():
                return "second"
    
    def test_get_nonexistent_tool_returns_none(self):
        """Test that getting non-existent tool returns None."""
        registry = ToolRegistry()
        
        tool = registry.get_tool("nonexistent")
        assert tool is None
    
    def test_list_tools(self):
        """Test listing all registered tools."""
        registry = ToolRegistry()
        
        @registry.register_function("tool1")
        def function1():
            return "result1"
        
        @registry.register_function("tool2", category="math")
        def function2():
            return "result2"
        
        tools = registry.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools
    
    def test_list_tools_by_category(self):
        """Test listing tools filtered by category."""
        registry = ToolRegistry()
        
        @registry.register_function("add", category="math")
        def add_func():
            return "add"
        
        @registry.register_function("multiply", category="math")  
        def multiply_func():
            return "multiply"
        
        @registry.register_function("read_file", category="io")
        def read_func():
            return "read"
        
        math_tools = registry.list_tools(category="math")
        assert len(math_tools) == 2
        assert "add" in math_tools
        assert "multiply" in math_tools
        assert "read_file" not in math_tools
    
    def test_list_tools_by_tag(self):
        """Test listing tools filtered by tags."""
        registry = ToolRegistry()
        
        @registry.register_function("tool1", tags=["basic", "math"])
        def func1():
            return "1"
        
        @registry.register_function("tool2", tags=["advanced", "math"])
        def func2():
            return "2"
        
        @registry.register_function("tool3", tags=["basic", "text"])
        def func3():
            return "3"
        
        basic_tools = registry.list_tools(tags=["basic"])
        assert len(basic_tools) == 2
        assert "tool1" in basic_tools
        assert "tool3" in basic_tools
        
        math_tools = registry.list_tools(tags=["math"])
        assert len(math_tools) == 2
        assert "tool1" in math_tools
        assert "tool2" in math_tools
    
    @pytest.mark.asyncio
    async def test_execute_sync_function_tool(self):
        """Test executing a synchronous function tool."""
        registry = ToolRegistry()
        
        @registry.register_function("sync_add")
        def add_numbers(a: int, b: int) -> int:
            return a + b
        
        result = await registry.execute_tool("sync_add", a=5, b=3)
        assert result.success is True
        assert result.result == 8
    
    @pytest.mark.asyncio
    async def test_execute_async_function_tool(self):
        """Test executing an asynchronous function tool."""
        registry = ToolRegistry()
        
        @registry.register_function("async_multiply")
        async def multiply_numbers(a: int, b: int) -> int:
            await asyncio.sleep(0.01)  # Small delay
            return a * b
        
        result = await registry.execute_tool("async_multiply", a=4, b=7)
        assert result.success is True
        assert result.result == 28
    
    @pytest.mark.asyncio
    async def test_execute_class_tool(self):
        """Test executing a class-based tool."""
        registry = ToolRegistry()
        
        class CalculatorTool(AsyncTool):
            def __init__(self):
                super().__init__("calculator", "Perform calculations")
            
            @property
            def parameters(self):
                return {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string"},
                        "a": {"type": "integer"},
                        "b": {"type": "integer"}
                    },
                    "required": ["operation", "a", "b"]
                }
            
            async def execute(self, parameters):
                operation = parameters["operation"]
                a = parameters["a"]
                b = parameters["b"]
                
                if operation == "add":
                    return {"result": a + b}
                elif operation == "multiply":
                    return {"result": a * b}
                else:
                    raise ValueError(f"Unknown operation: {operation}")
        
        calculator = CalculatorTool()
        registry.register_tool(calculator)
        
        result = await registry.execute_tool("calculator", operation="add", a=10, b=15)
        assert result.success is True
        assert result.result == {"result": 25}  # Class tool returns dict
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool_raises_error(self):
        """Test that executing non-existent tool raises error."""
        registry = ToolRegistry()
        
        with pytest.raises(ValueError, match="not found"):
            await registry.execute_tool("nonexistent", arg1="value")
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_error_handling(self):
        """Test tool execution with error handling."""
        registry = ToolRegistry()
        
        @registry.register_function("failing_tool")
        def failing_function():
            raise RuntimeError("Tool execution failed")
        
        with pytest.raises(RuntimeError, match="Tool execution failed"):
            await registry.execute_tool("failing_tool")
    
    def test_remove_tool(self):
        """Test removing a tool from registry."""
        registry = ToolRegistry()
        
        @registry.register_function("temporary_tool")
        def temp_function():
            return "temp"
        
        assert "temporary_tool" in registry.tools
        
        success = registry.remove_tool("temporary_tool")
        assert success is True
        assert "temporary_tool" not in registry.tools
        
        # Try to remove non-existent tool
        success = registry.remove_tool("nonexistent")
        assert success is False
    
    def test_clear_registry(self):
        """Test clearing all tools from registry."""
        registry = ToolRegistry()
        
        @registry.register_function("tool1")
        def func1():
            return "1"
        
        @registry.register_function("tool2")
        def func2():
            return "2"
        
        assert len(registry.tools) == 2
        
        registry.clear()
        assert len(registry.tools) == 0
        assert len(registry.categories) == 0
    
    def test_get_tool_metadata(self):
        """Test retrieving tool metadata."""
        registry = ToolRegistry()
        
        @registry.register_function("metadata_tool", category="test", tags=["meta", "data"])
        def metadata_function(arg1: str, arg2: int = 42) -> str:
            """A function for testing metadata."""
            return f"{arg1}_{arg2}"
        
        metadata = registry.get_tool_metadata("metadata_tool")
        assert metadata["name"] == "metadata_tool"
        assert metadata["description"] == "A function for testing metadata."
        assert metadata["category"] == "test"
        assert metadata["tags"] == ["meta", "data"]
        assert "parameters" in metadata
    
    def test_search_tools(self):
        """Test searching tools by name or description."""
        registry = ToolRegistry()
        
        @registry.register_function("file_reader")
        def read_file():
            """Read contents from a file."""
            return "content"
        
        @registry.register_function("file_writer") 
        def write_file():
            """Write data to a file."""
            return "written"
        
        @registry.register_function("calculator")
        def calculate():
            """Perform mathematical calculations."""
            return "result"
        
        # Search by name
        file_tools = registry.search_tools("file")
        assert len(file_tools) == 2
        assert "file_reader" in file_tools
        assert "file_writer" in file_tools
        
        # Search by description
        calc_tools = registry.search_tools("mathematical")
        assert len(calc_tools) == 1
        assert "calculator" in calc_tools
    
    def test_tool_categories_management(self):
        """Test category management functionality."""
        registry = ToolRegistry()
        
        @registry.register_function("add", category="math")
        def add_func():
            return "add"
        
        @registry.register_function("subtract", category="math")
        def subtract_func():
            return "subtract"
        
        @registry.register_function("read", category="io")
        def read_func():
            return "read"
        
        categories = registry.get_categories()
        assert "math" in categories
        assert "io" in categories
        assert len(categories["math"]) == 2
        assert len(categories["io"]) == 1
    
    def test_bulk_register_tools(self):
        """Test registering multiple tools at once."""
        registry = ToolRegistry()
        
        def func1():
            return "1"
        
        def func2():
            return "2"
        
        async def async_func():
            return "async"
        
        tools_to_register = [
            {"name": "bulk_tool1", "function": func1, "description": "Bulk tool 1"},
            {"name": "bulk_tool2", "function": func2, "description": "Bulk tool 2", "category": "bulk"},
            {"name": "bulk_async", "function": async_func, "description": "Bulk async tool"}
        ]
        
        registry.bulk_register_functions(tools_to_register)
        
        assert len(registry.tools) == 3
        assert "bulk_tool1" in registry.tools
        assert "bulk_tool2" in registry.tools
        assert "bulk_async" in registry.tools
        assert registry.get_tool("bulk_tool2").category == "bulk"
    
    def test_tool_validation(self):
        """Test tool validation during registration."""
        registry = ToolRegistry()
        
        # Test invalid tool name
        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            @registry.register_function("")
            def empty_name():
                pass
        
        # Test None function
        with pytest.raises(ValueError, match="Function must be callable"):
            registry.register_function("invalid", "Test", None)
    
    @pytest.mark.asyncio
    async def test_tool_execution_timeout(self):
        """Test tool execution with timeout."""
        registry = ToolRegistry()
        
        @registry.register_function("slow_tool")
        async def slow_function():
            await asyncio.sleep(2.0)  # Long operation
            return "slow_result"
        
        # Test with timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                registry.execute_tool("slow_tool", {}), 
                timeout=0.1
            )
    
    def test_thread_safety(self):
        """Test thread safety of registry operations."""
        import threading
        
        registry = ToolRegistry()
        results = []
        
        def register_tools(thread_id):
            for i in range(10):
                @registry.register_function(f"thread_{thread_id}_tool_{i}")
                def thread_function():
                    return f"result_{thread_id}_{i}"
                results.append(f"registered_thread_{thread_id}_tool_{i}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_tools, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all tools were registered
        assert len(registry.tools) == 50
        assert len(results) == 50