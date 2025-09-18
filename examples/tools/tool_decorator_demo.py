#!/usr/bin/env python3
"""
Tool Decorator Demo: Automatic Function Introspection
=====================================================

This example demonstrates how the @tool decorator automatically extracts:
- Function name
- Function docstring (description)
- Parameter names and types from type hints
- Required vs optional parameters (based on default values)
"""

import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agenticflow.tools import tool
from agenticflow.tools.base_tool import get_tool_registry

# ===================================================================
# EXAMPLES OF WHAT THE @tool DECORATOR EXTRACTS AUTOMATICALLY
# ===================================================================

# 1. Minimal tool - decorator extracts everything
@tool
def get_current_time():
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 2. Tool with parameters - decorator extracts parameter schema
@tool
def calculate(a: int, b: int, operation: str = "add") -> str:
    """Perform mathematical operations on two numbers.
    
    Supports add, subtract, multiply, divide operations.
    """
    if operation == "add":
        return f"{a} + {b} = {a + b}"
    elif operation == "subtract":
        return f"{a} - {b} = {a - b}"
    elif operation == "multiply":
        return f"{a} * {b} = {a * b}"
    elif operation == "divide":
        if b == 0:
            return "Error: Cannot divide by zero"
        return f"{a} / {b} = {a / b}"
    else:
        return f"Error: Unknown operation '{operation}'"


# 3. Tool with complex types - decorator handles various type hints
@tool
def process_data(
    data_list: List[str], 
    config: Dict[str, Any], 
    optional_filter: Optional[str] = None,
    include_metadata: bool = True
) -> str:
    """Process a list of data with configuration options.
    
    Filters and processes data according to the provided configuration.
    """
    processed_count = len(data_list)
    
    # Apply optional filter
    if optional_filter:
        data_list = [item for item in data_list if optional_filter.lower() in item.lower()]
        filtered_count = len(data_list)
    else:
        filtered_count = processed_count
    
    result = {
        "processed_items": filtered_count,
        "total_items": processed_count,
        "config_applied": config,
        "filter_applied": optional_filter
    }
    
    if include_metadata:
        result["timestamp"] = datetime.now().isoformat()
        result["processor"] = "process_data_tool"
    
    return json.dumps(result, indent=2)


# 4. Override defaults - provide custom name and description
@tool(name="weather_api", description="Get weather information for any city worldwide")
def get_weather_info(city: str, units: str = "celsius") -> str:
    """This docstring is ignored because description was provided in decorator."""
    # Mock weather API response
    temp = "22°C" if units == "celsius" else "72°F"
    return f"Weather in {city}: Sunny, {temp} (Mock data for demo)"


# 5. Tool with no parameters
@tool
def system_info():
    """Get basic system information."""
    import platform
    return f"System: {platform.system()} {platform.release()}, Python: {platform.python_version()}"


async def demonstrate_automatic_extraction():
    """Demonstrate what the @tool decorator extracts automatically."""
    
    print("🔧 Tool Decorator Automatic Extraction Demo")
    print("=" * 60)
    print()
    
    # Get the global tool registry where @tool registered our functions
    registry = get_tool_registry()
    tool_names = registry.list_tools()
    
    print(f"📋 Found {len(tool_names)} tools registered by @tool decorator:")
    for name in sorted(tool_names):
        print(f"  • {name}")
    
    print("\n" + "=" * 60)
    print("🔍 DETAILED TOOL ANALYSIS")
    print("=" * 60)
    
    # Examine each tool to see what the decorator extracted
    demo_tools = [
        "get_current_time",
        "calculate", 
        "process_data",
        "weather_api",
        "system_info"
    ]
    
    for tool_name in demo_tools:
        if tool_name in tool_names:
            print(f"\n🛠️  Tool: {tool_name}")
            print("-" * 40)
            
            try:
                # Get tool from registry
                tool_info = registry._tools.get(tool_name)
                if tool_info:
                    func = tool_info.get("func")
                    schema = tool_info.get("parameters_schema", {})
                    description = tool_info.get("description", "")
                    
                    # Show what was automatically extracted
                    print(f"✅ Name: {tool_name}")
                    print(f"✅ Description: {description}")
                    
                    # Show parameter schema
                    properties = schema.get("properties", {})
                    required = schema.get("required", [])
                    
                    print(f"✅ Parameters extracted:")
                    if properties:
                        for param_name, param_info in properties.items():
                            param_type = param_info.get("type", "unknown")
                            is_required = param_name in required
                            default_val = param_info.get("default")
                            
                            status = "REQUIRED" if is_required else f"OPTIONAL (default: {default_val})"
                            print(f"   • {param_name}: {param_type} - {status}")
                    else:
                        print("   • No parameters")
                    
                    # Show the actual function signature for comparison
                    import inspect
                    sig = inspect.signature(func)
                    print(f"📝 Original function signature: {tool_name}{sig}")
                    
                else:
                    print("❌ Tool not found in registry")
            except Exception as e:
                print(f"❌ Error analyzing tool: {e}")
    
    print("\n" + "=" * 60)
    print("🧪 TESTING AUTOMATIC TOOL EXECUTION")
    print("=" * 60)
    
    # Test calling tools through the registry
    test_cases = [
        {
            "tool": "get_current_time",
            "params": {},
            "description": "No parameters - should work directly"
        },
        {
            "tool": "calculate", 
            "params": {"a": 15, "b": 7, "operation": "multiply"},
            "description": "All parameters provided"
        },
        {
            "tool": "calculate",
            "params": {"a": 20, "b": 5},
            "description": "Optional parameter uses default (add)"
        },
        {
            "tool": "weather_api",
            "params": {"city": "Tokyo"},
            "description": "Required + optional parameter with default"
        },
        {
            "tool": "process_data",
            "params": {
                "data_list": ["apple", "banana", "cherry", "date"],
                "config": {"sort": True, "case_sensitive": False},
                "optional_filter": "a"
            },
            "description": "Complex types - list, dict, optional string"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        tool_name = test_case["tool"]
        params = test_case["params"]
        description = test_case["description"]
        
        print(f"\n🧪 Test {i}: {description}")
        print(f"   Tool: {tool_name}")
        print(f"   Parameters: {params}")
        
        try:
            # Execute through registry (simulating what an agent would do)
            tool_info = registry._tools.get(tool_name)
            if tool_info:
                func = tool_info["func"]
                result = func(**params)
                print(f"   ✅ Result: {result}")
            else:
                print(f"   ❌ Tool {tool_name} not found")
        except Exception as e:
            print(f"   ❌ Execution failed: {e}")

    print("\n" + "=" * 60)
    print("📋 SUMMARY: What @tool Decorator Extracts Automatically")
    print("=" * 60)
    print("""
✅ AUTOMATICALLY EXTRACTED:
   • Function name (unless overridden with name parameter)
   • Function docstring as description (unless overridden)
   • Parameter names from function signature
   • Parameter types from type hints (int, str, bool, list, dict, etc.)
   • Required vs optional parameters (based on default values)
   • Default values for optional parameters

🎯 USAGE PATTERNS:
   @tool                                    # Minimal - uses function name & docstring
   @tool("custom_name", "Custom description")  # Override name & description
   @tool(name="api_tool")                   # Override just name
   @tool(description="Custom description")  # Override just description

💡 PARAMETER TYPE MAPPING:
   • int → "integer"
   • float → "number" 
   • str → "string"
   • bool → "boolean"
   • List[T] → "array"
   • Dict[K,V] → "object"
   • Optional[T] → same as T but not required

🔧 AGENT INTEGRATION:
   Once decorated, just reference by name in agent config:
   tools=["get_current_time", "calculate", "weather_api"]
    """)


if __name__ == "__main__":
    asyncio.run(demonstrate_automatic_extraction())