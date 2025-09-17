"""
Model Context Protocol (MCP) Integration for AgenticFlow

This module provides complete MCP support for connecting to external MCP servers:
- MCP client for communicating with external MCP servers
- MCP-based tools that can be registered with agents
- MCP server management utilities
- Configuration system for external MCP servers

Usage:
    from agenticflow.mcp import MCPClient, MCPTool, MCPServerConfig, MCPServerManager
    
    # Configure external MCP server
    config = MCPServerConfig(
        name="calculator",
        command=["python", "path/to/calculator_server.py"],
        expected_tools=["calculate"]
    )
    
    # Create manager and start servers
    manager = MCPServerManager()
    manager.add_server(config)
    await manager.start()
    
    # Get tools and register with agent
    mcp_tools = manager.get_tools()
    for tool in mcp_tools:
        agent.register_tool(tool)
"""

from .client import MCPClient, MCPError
from .tools import MCPTool, MCPToolRegistry
from .config import MCPServerConfig, MCPConfig
from .manager import MCPServerManager

__all__ = [
    "MCPClient",
    "MCPError", 
    "MCPTool",
    "MCPToolRegistry",
    "MCPServerConfig",
    "MCPConfig",
    "MCPServerManager",
]
