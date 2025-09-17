"""Tools module for AgenticFlow.

Provides super-simple tool registration with decorators and easy function wrappers.
"""

from .base_tool import (
    AsyncTool,
    ToolResult,
    ToolError,
    ToolExecutionError,
    ToolType,
    ToolRegistry,
    LangChainToolWrapper,
    FunctionTool,
    get_tool_registry,
    register_tool,
    register_langchain_tool,
    register_function,
)

# Import new simple registration tools
try:
    from .decorators import tool, mcp_server, resource, register_as_tool
    from .simple_tools import (
        register_lambda,
        register_method,
        create_tool_from_function,
        register_api_endpoint,
        register_shell_command
    )
    from .mcp_integration import (
        MCPClient, 
        register_mcp_server,
        auto_register_mcp_tools,
        list_mcp_servers
    )
    ENHANCED_TOOLS_AVAILABLE = True
except ImportError as e:
    # Fallback when enhanced tools are not available
    ENHANCED_TOOLS_AVAILABLE = False
    tool = None
    mcp_server = None
    resource = None

__all__ = [
    # Base tools
    "AsyncTool",
    "ToolResult",
    "ToolError",
    "ToolExecutionError", 
    "ToolType",
    "ToolRegistry",
    "LangChainToolWrapper",
    "FunctionTool",
    "get_tool_registry",
    "register_tool",
    "register_langchain_tool",
    "register_function",
]

# Add enhanced tools if available
if ENHANCED_TOOLS_AVAILABLE:
    __all__.extend([
        # Decorators (super simple)
        "tool",
        "mcp_server", 
        "resource",
        "register_as_tool",
        
        # Simple registration
        "register_lambda", 
        "register_method",
        "create_tool_from_function",
        "register_api_endpoint",
        "register_shell_command",
        
        # MCP integration
        "MCPClient",
        "register_mcp_server",
        "auto_register_mcp_tools",
        "list_mcp_servers",
    ])
