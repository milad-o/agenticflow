"""
Simple tool registration utilities for AgenticFlow.

Provides one-liner functions to register tools without decorators.
"""

import inspect
from typing import Any, Callable, Dict, Optional

from .base_tool import get_tool_registry
from .decorators import _generate_schema_from_function


def register_lambda(
    name: str,
    lambda_func: Callable,
    description: Optional[str] = None,
    parameters_schema: Optional[Dict[str, Any]] = None
) -> None:
    """
    Register a lambda function as a tool.
    
    # Super simple one-liner
    register_lambda("add", lambda a, b: a + b, "Add two numbers")
    register_lambda("greet", lambda name: f"Hello {name}!")
    """
    registry = get_tool_registry()
    
    if parameters_schema is None:
        # Try to generate schema, but lambdas are limited
        if description is None:
            description = f"Lambda function: {name}"
        # For lambdas, we'll need manual parameter definition
        parameters_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    registry.register_function(
        name=name,
        description=description or f"Lambda function: {name}",
        func=lambda_func,
        parameters_schema=parameters_schema
    )


def register_method(
    obj: Any,
    method_name: str,
    tool_name: Optional[str] = None,
    description: Optional[str] = None
) -> None:
    """
    Register an object method as a tool.
    
    class Calculator:
        def add(self, a: int, b: int) -> int:
            return a + b
    
    calc = Calculator()
    register_method(calc, "add", "calculator_add", "Add two numbers")
    """
    method = getattr(obj, method_name)
    if not callable(method):
        raise ValueError(f"{method_name} is not a callable method")
    
    registry = get_tool_registry()
    name = tool_name or f"{obj.__class__.__name__.lower()}_{method_name}"
    desc = description or (method.__doc__ or f"Method: {obj.__class__.__name__}.{method_name}")
    
    # Generate schema from method signature
    params_schema = _generate_schema_from_function(method)
    
    registry.register_function(
        name=name,
        description=desc,
        func=method,
        parameters_schema=params_schema
    )


def create_tool_from_function(
    func: Callable,
    name: Optional[str] = None,
    description: Optional[str] = None,
    auto_register: bool = True
) -> Dict[str, Any]:
    """
    Create a tool configuration from any function.
    
    def my_function(x: int, y: str = "default") -> str:
        '''My function description'''
        return f"{x}: {y}"
    
    tool_config = create_tool_from_function(my_function)
    
    Returns:
        Dict with tool configuration that can be used programmatically
    """
    tool_name = name or func.__name__
    tool_description = description or (func.__doc__ or f"Function: {func.__name__}")
    params_schema = _generate_schema_from_function(func)
    
    tool_config = {
        "name": tool_name,
        "description": tool_description,
        "function": func,
        "parameters_schema": params_schema,
        "type": "function"
    }
    
    if auto_register:
        registry = get_tool_registry()
        registry.register_function(
            name=tool_name,
            description=tool_description,
            func=func,
            parameters_schema=params_schema
        )
    
    return tool_config


def register_api_endpoint(
    name: str,
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    description: Optional[str] = None
) -> None:
    """
    Register an API endpoint as a tool.
    
    register_api_endpoint(
        "weather_api",
        "https://api.weather.com/v1/current",
        method="GET",
        headers={"API-Key": "your-key"},
        description="Get current weather data"
    )
    """
    import aiohttp
    
    async def api_call(**params):
        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(url, headers=headers, params=params) as response:
                    return await response.json()
            elif method.upper() == "POST":
                async with session.post(url, headers=headers, json=params) as response:
                    return await response.json()
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
    
    registry = get_tool_registry()
    registry.register_function(
        name=name,
        description=description or f"API endpoint: {method} {url}",
        func=api_call,
        parameters_schema={
            "type": "object",
            "properties": {},  # API-specific parameters would be added here
            "required": []
        }
    )


def register_shell_command(
    name: str,
    command: str,
    description: Optional[str] = None,
    safe: bool = False
) -> None:
    """
    Register a shell command as a tool.
    
    register_shell_command("list_files", "ls -la", "List files in directory")
    register_shell_command("git_status", "git status", "Check git status", safe=True)
    """
    import asyncio
    
    async def run_command(**params):
        # Format command with parameters
        formatted_command = command
        for key, value in params.items():
            formatted_command = formatted_command.replace(f"{{{key}}}", str(value))
        
        if not safe:
            # Add basic safety check
            dangerous_commands = ["rm", "del", "format", "mkfs", "dd"]
            if any(cmd in formatted_command.lower() for cmd in dangerous_commands):
                return "Error: Dangerous command blocked for safety"
        
        try:
            proc = await asyncio.create_subprocess_shell(
                formatted_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            result = {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "return_code": proc.returncode
            }
            return result
        except Exception as e:
            return f"Command execution failed: {e}"
    
    registry = get_tool_registry()
    registry.register_function(
        name=name,
        description=description or f"Shell command: {command}",
        func=run_command,
        parameters_schema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )