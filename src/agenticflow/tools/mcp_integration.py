"""
MCP (Model Context Protocol) integration for AgenticFlow.

Provides simple integration with MCP servers and tools using the official MCP Python SDK.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union

import structlog

# Import official MCP SDK components
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client
    from mcp.types import Tool, CallToolRequest, CallToolResult
    MCP_AVAILABLE = True
except ImportError:
    # Fallback when MCP SDK is not available
    MCP_AVAILABLE = False
    ClientSession = None
    StdioServerParameters = None

# Optional: Try to import FastMCP for easier server creation
try:
    import fastmcp
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

logger = structlog.get_logger(__name__)


class MCPClient:
    """
    AgenticFlow wrapper for MCP clients using the official MCP Python SDK.
    
    Supports stdio and SSE-based MCP servers using the official SDK.
    """
    
    def __init__(self, server_config: Union[str, Dict], name: str = "mcp_client"):
        """Initialize MCP client."""
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK not available. Install with: pip install mcp")
            
        self.name = name
        self.logger = logger.bind(component="mcp_client", name=name)
        
        # Parse server configuration
        if isinstance(server_config, str):
            self.server_config = self._parse_server_string(server_config)
        else:
            self.server_config = server_config
        
        # Connection state
        self._session: Optional[ClientSession] = None
        self._client_context = None
        self._connected = False
        
    def _parse_server_string(self, server_str: str) -> Dict[str, Any]:
        """Parse server string into configuration."""
        if server_str.startswith('stdio://'):
            # stdio://command or stdio:///path/to/executable
            command = server_str[8:]  # Remove 'stdio://'
            return {
                "type": "stdio",
                "command": command.split(),
                "args": []
            }
        elif server_str.startswith(('http://', 'https://')):
            # HTTP SSE endpoint
            return {
                "type": "sse",
                "url": server_str
            }
        else:
            # Assume it's a command to execute
            return {
                "type": "stdio", 
                "command": server_str.split(),
                "args": []
            }
        
    async def connect(self) -> bool:
        """Connect to the MCP server using official MCP SDK."""
        if self._connected:
            return True
            
        try:
            if self.server_config["type"] == "stdio":
                await self._connect_stdio()
            elif self.server_config["type"] == "sse":
                await self._connect_sse()
            else:
                raise ValueError(f"Unsupported server type: {self.server_config['type']}")
            
            self._connected = True
            self.logger.info(f"Connected to MCP server: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def _connect_stdio(self) -> None:
        """Connect to stdio-based MCP server using official SDK."""
        server_params = StdioServerParameters(
            command=self.server_config["command"][0],
            args=self.server_config["command"][1:] + self.server_config.get("args", []),
            env=self.server_config.get("env")
        )
        
        # Create client context
        self._client_context = stdio_client(server_params)
        
        # Enter the context to get the session
        self._session = await self._client_context.__aenter__()
        
        # Initialize the session
        await self._session.initialize()
    
    async def _connect_sse(self) -> None:
        """Connect to SSE-based MCP server using official SDK."""
        # Create SSE client context
        self._client_context = sse_client(self.server_config["url"])
        
        # Enter the context to get the session  
        self._session = await self._client_context.__aenter__()
        
        # Initialize the session
        await self._session.initialize()
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._connected:
            return
            
        try:
            # Exit the client context if it exists
            if self._client_context:
                await self._client_context.__aexit__(None, None, None)
        except Exception as e:
            self.logger.warning(f"Error closing MCP session: {e}")
        finally:
            self._connected = False
            self._session = None
            self._client_context = None
            self.logger.info("Disconnected from MCP server")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server using official SDK."""
        if not self._connected:
            await self.connect()
        
        if not self._session:
            raise RuntimeError("No active MCP session")
        
        try:
            # Use official SDK to list tools
            response = await self._session.list_tools()
            
            # Convert Tool objects to dicts for compatibility
            tools_list = []
            for tool in response.tools:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description,
                }
                if hasattr(tool, 'inputSchema'):
                    tool_dict["inputSchema"] = tool.inputSchema
                tools_list.append(tool_dict)
            
            return tools_list
                
        except Exception as e:
            self.logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server using official SDK."""
        if not self._connected:
            await self.connect()
        
        if not self._session:
            raise RuntimeError("No active MCP session")
        
        try:
            # Create the tool call request using official SDK types
            request = CallToolRequest(
                name=tool_name,
                arguments=parameters
            )
            
            # Call the tool using the session
            response = await self._session.call_tool(request)
            
            # Extract result from response
            if hasattr(response, 'content'):
                return response.content
            elif hasattr(response, 'result'):
                return response.result
            else:
                return response
                
        except Exception as e:
            self.logger.error(f"Failed to call tool {tool_name}: {e}")
            raise
    
# Global MCP server registry
_mcp_servers: Dict[str, MCPClient] = {}


def register_mcp_server(server_config: Union[str, Dict], name: str) -> MCPClient:
    """
    Register an MCP server for use with agents using official MCP SDK.
    
    Examples:
    
    # Stdio server (command)
    register_mcp_server("stdio://weather-mcp-server", "weather_stdio")
    
    # Subprocess command  
    register_mcp_server("python -m weather_mcp_server", "weather_cmd")
    
    # SSE server
    register_mcp_server("https://localhost:8000/sse", "weather_sse")
    
    # Advanced configuration
    register_mcp_server({
        "type": "stdio",
        "command": ["python", "-m", "weather_server"],
        "args": ["--port", "8000"],
        "env": {"API_KEY": "secret"}
    }, "weather_advanced")
    """
    if not MCP_AVAILABLE:
        logger.warning("MCP SDK not available. MCP server registration skipped.")
        return None
        
    client = MCPClient(server_config, name)
    _mcp_servers[name] = client
    
    config_str = server_config if isinstance(server_config, str) else server_config.get("type", "custom")
    logger.info(f"Registered MCP server: {name} -> {config_str}")
    return client


def get_mcp_server(name: str) -> Optional[MCPClient]:
    """Get registered MCP server by name."""
    return _mcp_servers.get(name)


async def auto_register_mcp_tools(server_name: str, registry=None) -> int:
    """
    Automatically register all tools from an MCP server as AgenticFlow tools.
    
    Returns number of tools registered.
    """
    from .base_tool import get_tool_registry
    
    if registry is None:
        registry = get_tool_registry()
    
    mcp_client = get_mcp_server(server_name)
    if not mcp_client:
        raise ValueError(f"MCP server {server_name} not found")
    
    tools = await mcp_client.list_tools()
    registered_count = 0
    
    for tool_info in tools:
        tool_name = f"mcp_{server_name}_{tool_info['name']}"
        
        # Create wrapper function for MCP tool
        async def mcp_tool_wrapper(**params):
            return await mcp_client.call_tool(tool_info['name'], params)
        
        # Register as AgenticFlow tool
        registry.register_function(
            name=tool_name,
            description=tool_info.get('description', f"MCP tool: {tool_info['name']}"),
            func=mcp_tool_wrapper,
            parameters_schema=tool_info.get('inputSchema', {
                "type": "object",
                "properties": {},
                "required": []
            })
        )
        
        registered_count += 1
        logger.info(f"Registered MCP tool: {tool_name}")
    
    return registered_count


async def discover_and_register_mcp_servers(search_paths: List[str] = None) -> Dict[str, MCPClient]:
    """
    Discover and register MCP servers from common locations.
    
    # Discover from default locations
    servers = await discover_and_register_mcp_servers()
    
    # Discover from specific paths
    servers = await discover_and_register_mcp_servers(["/usr/local/bin", "~/.local/mcp"])
    """
    import os
    import glob
    
    if search_paths is None:
        search_paths = [
            "/usr/local/bin",
            os.path.expanduser("~/.local/bin"),
            os.path.expanduser("~/.local/mcp"),
            "./mcp_servers"
        ]
    
    discovered = {}
    
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
        
        # Look for MCP server executables
        pattern = os.path.join(search_path, "*mcp*")
        for executable in glob.glob(pattern):
            if os.path.isfile(executable) and os.access(executable, os.X_OK):
                server_name = os.path.basename(executable)
                client = register_mcp_server(executable, server_name)
                discovered[server_name] = client
                
                # Try to auto-register tools
                try:
                    tool_count = await auto_register_mcp_tools(server_name)
                    logger.info(f"Auto-registered {tool_count} tools from {server_name}")
                except Exception as e:
                    logger.warning(f"Failed to auto-register tools from {server_name}: {e}")
    
    return discovered


def list_mcp_servers() -> Dict[str, str]:
    """List all registered MCP servers."""
    return {name: client.server_url for name, client in _mcp_servers.items()}


async def cleanup_mcp_servers() -> None:
    """Clean up all MCP server connections."""
    for client in _mcp_servers.values():
        try:
            await client.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting MCP client {client.name}: {e}")
    
    _mcp_servers.clear()
    logger.info("Cleaned up all MCP server connections")