"""
Base tool wrapper for AgenticFlow.

Provides a unified interface for regular tools and MCP tools with async support,
error handling, and integration with the agent system.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ToolType(str, Enum):
    """Types of tools."""
    REGULAR = "regular"
    MCP = "mcp"
    CUSTOM = "custom"


class ToolError(Exception):
    """Base exception for tool-related errors."""
    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""
    pass


class ToolResult(BaseModel):
    """Result of tool execution."""
    
    success: bool = Field(..., description="Whether execution was successful")
    result: Any = Field(None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    execution_time: float = Field(0.0, description="Execution time in seconds")
    
    @classmethod
    def success_result(cls, result: Any, metadata: Optional[Dict[str, Any]] = None, execution_time: float = 0.0) -> "ToolResult":
        """Create a successful result."""
        return cls(
            success=True,
            result=result,
            metadata=metadata or {},
            execution_time=execution_time
        )
    
    @classmethod
    def error_result(cls, error: str, metadata: Optional[Dict[str, Any]] = None, execution_time: float = 0.0) -> "ToolResult":
        """Create an error result."""
        return cls(
            success=False,
            error=error,
            metadata=metadata or {},
            execution_time=execution_time
        )


class AsyncTool(ABC):
    """Abstract base class for async tools."""
    
    def __init__(self, name: str, description: str, tool_type: ToolType = ToolType.CUSTOM) -> None:
        """Initialize the tool."""
        self.name = name
        self.description = description
        self.tool_type = tool_type
        self.logger = logger.bind(tool_name=name, tool_type=tool_type.value)
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema."""
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the tool asynchronously."""
        pass
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters."""
        # Basic validation - can be overridden by subclasses
        required_params = self.parameters.get("required", [])
        for param in required_params:
            if param not in parameters:
                raise ToolError(f"Required parameter '{param}' is missing")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation."""
        data = {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": self.parameters,
        }
        
        # Add category and tags if they exist
        if hasattr(self, 'category') and self.category:
            data["category"] = self.category
        if hasattr(self, 'tags') and self.tags:
            data["tags"] = self.tags
            
        return data


class LangChainToolWrapper(AsyncTool):
    """Wrapper for LangChain tools to make them async."""
    
    def __init__(self, langchain_tool: Any) -> None:
        """Initialize with a LangChain tool."""
        super().__init__(
            name=langchain_tool.name,
            description=langchain_tool.description,
            tool_type=ToolType.REGULAR
        )
        self.langchain_tool = langchain_tool
        self._parameters = self._extract_parameters()
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Get parameters schema from LangChain tool."""
        return self._parameters
    
    def _extract_parameters(self) -> Dict[str, Any]:
        """Extract parameters schema from LangChain tool."""
        try:
            # Try to get schema from LangChain tool
            if hasattr(self.langchain_tool, 'args_schema') and self.langchain_tool.args_schema:
                return self.langchain_tool.args_schema.schema()
            elif hasattr(self.langchain_tool, 'args') and self.langchain_tool.args:
                # Handle case where args might be a dict-like object
                args = self.langchain_tool.args
                if isinstance(args, dict):
                    return {"type": "object", "properties": args}
                else:
                    return {"type": "object", "properties": {}}
            else:
                return {"type": "object", "properties": {}}
        except Exception:
            # Fallback for any issues with parameter extraction
            return {"type": "object", "properties": {}}
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Custom validation for LangChain tools."""
        # For LangChain tools, we do minimal validation since they handle their own
        try:
            param_schema = self.parameters
            if isinstance(param_schema, dict) and "required" in param_schema:
                required_params = param_schema.get("required", [])
                if isinstance(required_params, (list, tuple)):
                    for param in required_params:
                        if param not in parameters:
                            raise ToolError(f"Required parameter '{param}' is missing")
            return True
        except Exception as e:
            # If validation fails, just log and continue
            self.logger.debug(f"Parameter validation skipped: {e}")
            return True
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the LangChain tool."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            await self.validate_parameters(parameters)
            
            # Execute the tool
            # First check for async methods
            if (hasattr(self.langchain_tool, 'arun') and 
                callable(getattr(self.langchain_tool, 'arun')) and 
                asyncio.iscoroutinefunction(getattr(self.langchain_tool, 'arun'))):
                # True async execution
                result = await self.langchain_tool.arun(**parameters)
            elif (hasattr(self.langchain_tool, '_arun') and 
                  callable(getattr(self.langchain_tool, '_arun')) and 
                  asyncio.iscoroutinefunction(getattr(self.langchain_tool, '_arun'))):
                result = await self.langchain_tool._arun(**parameters)
            elif hasattr(self.langchain_tool, 'run') and callable(getattr(self.langchain_tool, 'run')):
                # Sync execution - run in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.langchain_tool.run(**parameters)
                )
            else:
                # Fallback - no execution method found
                raise ToolExecutionError(f"No valid execution method found on tool {self.name}")
            
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"Tool executed successfully in {execution_time:.2f}s")
            
            return ToolResult.success_result(
                result=result,
                metadata={"tool_type": "langchain"},
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Tool execution failed: {e}"
            self.logger.error(error_msg)
            
            return ToolResult.error_result(
                error=error_msg,
                metadata={"tool_type": "langchain", "exception": str(type(e).__name__)},
                execution_time=execution_time
            )


class FunctionTool(AsyncTool):
    """Tool that wraps a Python function."""
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        func: callable, 
        parameters_schema: Dict[str, Any],
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """Initialize with a function and parameters schema."""
        super().__init__(name, description, ToolType.CUSTOM)
        self.func = func
        self.function = func  # Alias for backward compatibility
        self._parameters = parameters_schema
        self.category = category
        self.tags = tags or []
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Get parameters schema."""
        return self._parameters
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the function."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            await self.validate_parameters(parameters)
            
            # Execute the function
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**parameters)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: self.func(**parameters))
            
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"Function tool executed successfully in {execution_time:.2f}s")
            
            return ToolResult.success_result(
                result=result,
                metadata={"tool_type": "function"},
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Function execution failed: {e}"
            self.logger.error(error_msg)
            
            # Re-raise the original exception for proper error handling
            raise


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self) -> None:
        """Initialize the registry."""
        self.tools: Dict[str, AsyncTool] = {}
        self.categories: Dict[str, List[str]] = {}  # category -> list of tool names
        self.logger = logger.bind(component="tool_registry")
    
    def register_tool(self, tool: AsyncTool) -> None:
        """Register a tool."""
        if tool.name in self.tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
            
        self.tools[tool.name] = tool
        
        # Handle categories
        if hasattr(tool, 'category') and tool.category:
            if tool.category not in self.categories:
                self.categories[tool.category] = []
            self.categories[tool.category].append(tool.name)
            
        self.logger.info(f"Registered tool: {tool.name}")
    
    def register_langchain_tool(self, langchain_tool: Any) -> None:
        """Register a LangChain tool."""
        wrapper = LangChainToolWrapper(langchain_tool)
        self.register_tool(wrapper)
    
    def register_function(
        self, 
        name: str, 
        description: str = None, 
        func: callable = None, 
        parameters_schema: Dict[str, Any] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        """Register a function as a tool. Can be used as decorator or direct call."""
        
        # Validate tool name
        if not name or not name.strip():
            raise ValueError("Tool name cannot be empty")
        
        def decorator(f: callable):
            nonlocal description, parameters_schema
            
            # Validate function
            if not callable(f):
                raise ValueError("Function must be callable")
            
            # Use function docstring as description if not provided
            if description is None:
                description = f.__doc__ or f"Tool: {name}"
            
            # Auto-generate schema if not provided
            if parameters_schema is None:
                from .registry import generate_schema_from_function
                parameters_schema = generate_schema_from_function(f)
            
            tool = FunctionTool(name, description, f, parameters_schema, category, tags)
            self.register_tool(tool)
            return f
        
        # If used as direct call with all parameters
        if func is not None:
            if not callable(func):
                raise ValueError("Function must be callable")
                
            if description is None:
                description = func.__doc__ or f"Tool: {name}"
            if parameters_schema is None:
                from .registry import generate_schema_from_function  
                parameters_schema = generate_schema_from_function(func)
                
            tool = FunctionTool(name, description, func, parameters_schema, category, tags)
            self.register_tool(tool)
            return func
        
        # Check for explicit None func (invalid)
        # If description is provided and func is None, it's likely a direct call with None func
        if func is None and description is not None:
            raise ValueError("Function must be callable")
            
        # Used as decorator
        return decorator
    
    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool."""
        if name in self.tools:
            tool = self.tools[name]
            
            # Remove from categories
            if hasattr(tool, 'category') and tool.category:
                if tool.category in self.categories:
                    if name in self.categories[tool.category]:
                        self.categories[tool.category].remove(name)
                    # Remove category if empty
                    if not self.categories[tool.category]:
                        del self.categories[tool.category]
            
            del self.tools[name]
            self.logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[AsyncTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(
        self, 
        category: Optional[str] = None, 
        tags: Optional[List[str]] = None
    ) -> List[str]:
        """List tool names, optionally filtered by category or tags."""
        if category is None and tags is None:
            return list(self.tools.keys())
        
        filtered_tools = []
        
        for name, tool in self.tools.items():
            # Filter by category if specified
            if category is not None:
                if not (hasattr(tool, 'category') and tool.category == category):
                    continue
            
            # Filter by tags if specified
            if tags is not None:
                if not hasattr(tool, 'tags') or not tool.tags:
                    continue
                # Check if any of the specified tags match
                if not any(tag in tool.tags for tag in tags):
                    continue
            
            filtered_tools.append(name)
        
        return filtered_tools
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self.tools
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """Get information about all tools."""
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, parameters: Dict[str, Any] = None, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        # Support both dictionary parameters and keyword arguments
        if parameters is None:
            parameters = kwargs
        elif kwargs:
            # If both provided, merge kwargs into parameters
            parameters = {**parameters, **kwargs}
        
        result = await tool.execute(parameters)
        
        # If tool returns a ToolResult, use it directly
        if isinstance(result, ToolResult):
            return result
        # Otherwise wrap the raw result in a ToolResult
        else:
            return ToolResult.success_result(
                result=result,
                metadata={"tool_name": name, "tool_type": tool.tool_type.value}
            )
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool by name. Alias for unregister_tool."""
        return self.unregister_tool(name)
    
    def get_tool_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific tool."""
        tool = self.get_tool(name)
        if tool:
            return tool.to_dict()
        return None
    
    def search_tools(self, query: str) -> List[str]:
        """Search tools by name or description."""
        query_lower = query.lower()
        matches = []
        
        for name, tool in self.tools.items():
            if (query_lower in name.lower() or 
                query_lower in tool.description.lower()):
                matches.append(name)
        
        return matches
    
    def get_categories(self) -> Dict[str, List[str]]:
        """Get all categories and their associated tool names."""
        return dict(self.categories)
    
    def bulk_register_functions(self, tools: List[Dict[str, Any]]) -> None:
        """Register multiple functions at once."""
        for tool_info in tools:
            name = tool_info["name"]
            function = tool_info["function"]
            description = tool_info.get("description", "")
            category = tool_info.get("category")
            tags = tool_info.get("tags")
            parameters_schema = tool_info.get("parameters_schema")
            
            # Auto-generate schema if not provided
            if parameters_schema is None:
                from .registry import generate_schema_from_function
                parameters_schema = generate_schema_from_function(function)
            
            self.register_function(name, description, function, parameters_schema, category, tags)
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self.tools.clear()
        self.categories.clear()
        self.logger.info("Cleared all tools")


# Global tool registry
global_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return global_tool_registry


def register_tool(tool: AsyncTool) -> None:
    """Register a tool in the global registry."""
    global_tool_registry.register_tool(tool)


def register_langchain_tool(langchain_tool: Any) -> None:
    """Register a LangChain tool in the global registry."""
    global_tool_registry.register_langchain_tool(langchain_tool)


def register_function(
    name: str, 
    description: str, 
    func: callable, 
    parameters_schema: Dict[str, Any]
) -> None:
    """Register a function as a tool in the global registry."""
    global_tool_registry.register_function(name, description, func, parameters_schema)