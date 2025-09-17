"""
Tool registry and decorator utilities for AgenticFlow.

Provides decorators and utilities for easy tool registration.
"""

import inspect
from typing import Any, Dict, List, Callable, get_type_hints, Union, Optional
from functools import wraps

from .base_tool import ToolRegistry, FunctionTool, global_tool_registry


def generate_schema_from_function(func: Callable) -> Dict[str, Any]:
    """Generate JSON schema from function signature."""
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    properties = {}
    required = []
    
    for param_name, param in signature.parameters.items():
        param_type = type_hints.get(param_name, str)
        
        # Convert Python types to JSON schema types
        if param_type == str:
            prop_type = "string"
        elif param_type == int:
            prop_type = "integer"
        elif param_type == float:
            prop_type = "number"
        elif param_type == bool:
            prop_type = "boolean"
        elif param_type == list or (hasattr(param_type, '__origin__') and param_type.__origin__ == list):
            prop_type = "array"
        elif param_type == dict or (hasattr(param_type, '__origin__') and param_type.__origin__ == dict):
            prop_type = "object"
        else:
            prop_type = "string"  # Default fallback
        
        properties[param_name] = {
            "type": prop_type,
            "description": f"Parameter {param_name}"
        }
        
        # Check if parameter is required (no default value)
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters_schema: Optional[Dict[str, Any]] = None,
    registry: Optional[ToolRegistry] = None
):
    """
    Decorator to register a function as a tool.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        parameters_schema: JSON schema for parameters (auto-generated if not provided)
        registry: Tool registry to use (defaults to global registry)
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_description = description or (func.__doc__ or f"Tool: {tool_name}")
        tool_registry = registry or global_tool_registry
        
        # Generate schema from function if not provided
        schema = parameters_schema or generate_schema_from_function(func)
        
        # Register the function as a tool
        tool_registry.register_function(
            name=tool_name,
            description=tool_description,
            func=func,
            parameters_schema=schema
        )
        
        # Return the original function unchanged
        return func
    
    return decorator


# Re-export from base_tool for convenience
ToolRegistry = ToolRegistry
__all__ = ['tool', 'ToolRegistry', 'generate_schema_from_function']