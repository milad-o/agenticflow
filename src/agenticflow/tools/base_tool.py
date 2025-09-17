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
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": self.parameters,
        }


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
        parameters_schema: Dict[str, Any]
    ) -> None:
        """Initialize with a function and parameters schema."""
        super().__init__(name, description, ToolType.CUSTOM)
        self.func = func
        self._parameters = parameters_schema
    
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
            
            return ToolResult.error_result(
                error=error_msg,
                metadata={"tool_type": "function", "exception": str(type(e).__name__)},
                execution_time=execution_time
            )


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self) -> None:
        """Initialize the registry."""
        self.tools: Dict[str, AsyncTool] = {}
        self.logger = logger.bind(component="tool_registry")
    
    def register_tool(self, tool: AsyncTool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
    
    def register_langchain_tool(self, langchain_tool: Any) -> None:
        """Register a LangChain tool."""
        wrapper = LangChainToolWrapper(langchain_tool)
        self.register_tool(wrapper)
    
    def register_function(
        self, 
        name: str, 
        description: str, 
        func: callable, 
        parameters_schema: Dict[str, Any]
    ) -> None:
        """Register a function as a tool."""
        tool = FunctionTool(name, description, func, parameters_schema)
        self.register_tool(tool)
    
    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool."""
        if name in self.tools:
            del self.tools[name]
            self.logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[AsyncTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self.tools
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """Get information about all tools."""
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult.error_result(f"Tool '{name}' not found")
        
        try:
            return await tool.execute(parameters)
        except Exception as e:
            return ToolResult.error_result(f"Tool execution error: {e}")
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self.tools.clear()
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