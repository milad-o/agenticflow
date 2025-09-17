"""
MCP Tool Integration for AgenticFlow

This module extends the existing tool system to support MCP-based tools
that communicate with MCP servers for execution.
"""

import asyncio
from typing import Any, Dict, List, Optional

import structlog

from ..tools.base_tool import AsyncTool, ToolResult, ToolType
from .client import MCPClient, MCPError

logger = structlog.get_logger(__name__)


class MCPTool(AsyncTool):
    """
    A tool that executes via Model Context Protocol server.
    
    This tool acts as a bridge between AgenticFlow's tool system
    and MCP servers, handling the communication and result formatting.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        mcp_client: MCPClient,
        parameters_schema: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize MCP tool.
        
        Args:
            name: Tool name
            description: Tool description
            mcp_client: MCP client for server communication
            parameters_schema: JSON schema for tool parameters
        """
        super().__init__(name, description, ToolType.MCP)
        self.mcp_client = mcp_client
        self._parameters_schema = parameters_schema or {}
        
        self.logger = logger.bind(tool_name=name, mcp_server=mcp_client.name)
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Get the parameters schema for this tool."""
        return self._parameters_schema
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool via MCP server.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.debug("Executing MCP tool", parameters=parameters)
            
            # Ensure MCP server is running
            if not self.mcp_client.is_running:
                await self.mcp_client.start()
            
            # Call tool on MCP server
            result = await self.mcp_client.call_tool(self.name, parameters)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Extract result content
            result_text = self._extract_result_content(result)
            
            self.logger.info("MCP tool executed successfully", 
                           execution_time=execution_time,
                           result_length=len(str(result_text)))
            
            return ToolResult.success_result(
                result=result_text,
                metadata={
                    "mcp_server": self.mcp_client.name,
                    "tool_type": "mcp",
                    "raw_result": result
                },
                execution_time=execution_time
            )
            
        except MCPError as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"MCP tool execution failed: {e}"
            
            self.logger.error("MCP tool execution failed", 
                            error=str(e), 
                            execution_time=execution_time)
            
            return ToolResult.error_result(
                error=error_msg,
                metadata={
                    "mcp_server": self.mcp_client.name,
                    "tool_type": "mcp",
                    "error_type": type(e).__name__
                },
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Unexpected error in MCP tool: {e}"
            
            self.logger.error("Unexpected error in MCP tool", 
                            error=str(e), 
                            execution_time=execution_time,
                            exc_info=True)
            
            return ToolResult.error_result(
                error=error_msg,
                metadata={
                    "mcp_server": self.mcp_client.name,
                    "tool_type": "mcp",
                    "error_type": type(e).__name__
                },
                execution_time=execution_time
            )
    
    def _extract_result_content(self, result: Any) -> str:
        """
        Extract human-readable content from MCP server result.
        
        Args:
            result: Raw result from MCP server
            
        Returns:
            Formatted result string
        """
        if isinstance(result, dict):
            # Handle MCP content format
            if "content" in result:
                content = result["content"]
                if isinstance(content, list) and content:
                    # Get first content item
                    first_content = content[0]
                    if isinstance(first_content, dict):
                        return first_content.get("text", str(result))
                elif isinstance(content, str):
                    return content
            
            # Handle other dict formats
            if "text" in result:
                return result["text"]
            
            # Fallback to string representation
            return str(result)
        
        elif isinstance(result, str):
            return result
        
        else:
            return str(result)


class MCPToolRegistry:
    """
    Registry for managing MCP tools and their associated clients.
    
    This registry helps manage the lifecycle of MCP clients and
    automatically creates tools from MCP server capabilities.
    """
    
    def __init__(self):
        """Initialize MCP tool registry."""
        self.clients: Dict[str, MCPClient] = {}
        self.tools: Dict[str, MCPTool] = {}
        
        self.logger = logger.bind(component="mcp_tool_registry")
    
    async def register_client(self, client: MCPClient) -> List[MCPTool]:
        """
        Register an MCP client and discover its tools.
        
        Args:
            client: MCP client to register
            
        Returns:
            List of discovered tools
        """
        self.logger.info("Registering MCP client", client_name=client.name)
        
        try:
            # Start client if not already running
            if not client.is_running:
                await client.start()
            
            # Store client
            self.clients[client.name] = client
            
            # Discover tools
            tools = await self._discover_tools(client)
            
            # Register discovered tools
            for tool in tools:
                self.tools[f"{client.name}.{tool.name}"] = tool
            
            self.logger.info("MCP client registered successfully", 
                           client_name=client.name, 
                           tools_count=len(tools))
            
            return tools
            
        except Exception as e:
            self.logger.error("Failed to register MCP client", 
                            client_name=client.name, 
                            error=str(e))
            raise
    
    async def _discover_tools(self, client: MCPClient) -> List[MCPTool]:
        """
        Discover available tools from an MCP client.
        
        Args:
            client: MCP client to query
            
        Returns:
            List of available tools
        """
        try:
            # Get tool list from server
            tool_definitions = await client.list_tools()
            
            tools = []
            for tool_def in tool_definitions:
                name = tool_def.get("name", "unknown")
                description = tool_def.get("description", f"MCP tool: {name}")
                
                # Extract parameters schema
                input_schema = tool_def.get("inputSchema", {})
                
                # Create MCP tool
                tool = MCPTool(
                    name=name,
                    description=description,
                    mcp_client=client,
                    parameters_schema=input_schema
                )
                
                tools.append(tool)
                
                self.logger.debug("Discovered MCP tool", 
                                tool_name=name,
                                client_name=client.name)
            
            return tools
            
        except Exception as e:
            self.logger.error("Failed to discover tools from MCP client",
                            client_name=client.name,
                            error=str(e))
            return []
    
    async def unregister_client(self, client_name: str) -> None:
        """
        Unregister an MCP client and remove its tools.
        
        Args:
            client_name: Name of client to unregister
        """
        if client_name not in self.clients:
            return
        
        self.logger.info("Unregistering MCP client", client_name=client_name)
        
        try:
            # Stop client
            client = self.clients[client_name]
            await client.stop()
            
            # Remove client
            del self.clients[client_name]
            
            # Remove associated tools
            tools_to_remove = [
                tool_key for tool_key in self.tools.keys() 
                if tool_key.startswith(f"{client_name}.")
            ]
            
            for tool_key in tools_to_remove:
                del self.tools[tool_key]
            
            self.logger.info("MCP client unregistered", 
                           client_name=client_name,
                           removed_tools=len(tools_to_remove))
            
        except Exception as e:
            self.logger.error("Failed to unregister MCP client",
                            client_name=client_name,
                            error=str(e))
    
    async def stop_all_clients(self) -> None:
        """Stop all registered MCP clients."""
        self.logger.info("Stopping all MCP clients", count=len(self.clients))
        
        for client_name in list(self.clients.keys()):
            await self.unregister_client(client_name)
    
    def get_tools(self) -> List[MCPTool]:
        """Get all registered MCP tools."""
        return list(self.tools.values())
    
    def get_client(self, name: str) -> Optional[MCPClient]:
        """Get MCP client by name."""
        return self.clients.get(name)