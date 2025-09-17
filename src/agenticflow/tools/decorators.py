"""
Decorators for super-simple tool registration in AgenticFlow.

Makes it incredibly easy to turn any function into an agent tool with just a decorator.
"""

import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from .base_tool import get_tool_registry


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    registry: Optional[Any] = None,
    agent: Optional[str] = None
) -> Callable:
    """
    Decorator to register any function as a tool.
    
    Super simple usage:
    
    @tool
    def calculate(a: int, b: int, operation: str = "add") -> str:
        '''Perform basic math operations'''
        if operation == "add":
            return f"{a} + {b} = {a + b}"
        # ... more operations
    
    @tool(name="weather_api", description="Get weather for any city")
    def get_weather(city: str) -> str:
        '''Get current weather'''
        # Implementation
        pass
    
    @tool(agent="my_agent")  # Register only to specific agent
    def specialized_function():
        pass
    """
    def decorator(func: Callable) -> Callable:
        # Extract metadata from function
        tool_name = name or func.__name__
        tool_description = description or (func.__doc__ or f"Tool: {func.__name__}")
        
        # Generate parameter schema from function signature
        params_schema = _generate_schema_from_function(func)
        
        # Get the registry to use
        target_registry = registry or get_tool_registry()
        
        # Register the function as a tool
        if agent:
            # Register to specific agent (implement later)
            # For now, add agent metadata
            params_schema["_agent_specific"] = agent
        
        target_registry.register_function(
            name=tool_name,
            description=tool_description,
            func=func,
            parameters_schema=params_schema
        )
        
        # Return the original function (can still be called normally)
        return func
    
    return decorator


def mcp_server(url: str, name: Optional[str] = None) -> Callable:
    """
    Decorator to register an MCP server as a tool source.
    
    @mcp_server("http://localhost:8000")
    class WeatherMCP:
        pass
    
    Or for functions that return MCP client:
    
    @mcp_server("stdio://weather-server")
    def weather_mcp():
        # Returns MCP client or connection info
        pass
    """
    def decorator(target: Union[Callable, type]) -> Union[Callable, type]:
        server_name = name or getattr(target, '__name__', 'mcp_server')
        
        # Register MCP server (implement in mcp_integration.py)
        from .mcp_integration import register_mcp_server
        register_mcp_server(url, server_name)
        
        return target
    
    return decorator


def resource(
    resource_type: str,
    connection_string: Optional[str] = None,
    **config
) -> Callable:
    """
    Decorator to register resources (databases, APIs, files) with agents.
    
    @resource("database", "postgresql://localhost/mydb")
    class DatabaseConnection:
        pass
    
    @resource("api", base_url="https://api.example.com", auth_token="...")
    def api_client():
        pass
    
    @resource("file", path="/path/to/data.csv")
    def csv_data():
        pass
    """
    def decorator(target: Union[Callable, type]) -> Union[Callable, type]:
        resource_name = getattr(target, '__name__', 'resource')
        
        # Register resource (implement in resource_manager.py)
        from .resource_manager import register_resource
        register_resource(
            name=resource_name,
            resource_type=resource_type,
            connection_string=connection_string,
            **config
        )
        
        return target
    
    return decorator


def _generate_schema_from_function(func: Callable) -> Dict[str, Any]:
    """Generate JSON schema from function signature using type hints."""
    sig = inspect.signature(func)
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name == 'self':  # Skip self parameter
            continue
            
        param_type = "string"  # Default type
        param_description = ""
        
        # Extract type from annotation
        if param.annotation != inspect.Parameter.empty:
            annotation = param.annotation
            if annotation == int:
                param_type = "integer"
            elif annotation == float:
                param_type = "number"
            elif annotation == bool:
                param_type = "boolean"
            elif annotation == str:
                param_type = "string"
            elif hasattr(annotation, '__origin__') and annotation.__origin__ == list:
                param_type = "array"
            elif hasattr(annotation, '__origin__') and annotation.__origin__ == dict:
                param_type = "object"
        
        # Check if parameter has default value
        has_default = param.default != inspect.Parameter.empty
        if not has_default:
            required.append(param_name)
        
        properties[param_name] = {
            "type": param_type,
            "description": param_description
        }
        
        # Add default value if present
        if has_default and param.default is not None:
            properties[param_name]["default"] = param.default
    
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


# Convenience function for programmatic registration
def register_as_tool(
    func: Callable,
    name: Optional[str] = None,
    description: Optional[str] = None,
    registry: Optional[Any] = None
) -> None:
    """Programmatically register a function as a tool without decorator."""
    tool_decorator = tool(name=name, description=description, registry=registry)
    tool_decorator(func)