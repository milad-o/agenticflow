"""
MCP Server Manager for AgenticFlow

This module manages connections to external MCP servers and provides
lifecycle management for MCP clients and their tools.
"""

import asyncio
from typing import Dict, List, Optional
from pathlib import Path

import structlog

from .client import MCPClient
from .tools import MCPToolRegistry, MCPTool
from .config import MCPServerConfig, MCPConfig

logger = structlog.get_logger(__name__)


class MCPServerManager:
    """
    Manager for external MCP servers and their tool integration.
    
    This class handles connecting to external MCP servers, managing their
    lifecycle, and automatically registering their tools with AgenticFlow.
    """
    
    def __init__(self, config: Optional[MCPConfig] = None):
        """
        Initialize MCP server manager.
        
        Args:
            config: MCP configuration, defaults to empty config
        """
        self.config = config or MCPConfig()
        self.clients: Dict[str, MCPClient] = {}
        self.tool_registry = MCPToolRegistry()
        
        self.logger = logger.bind(component="mcp_server_manager")
    
    async def start(self) -> None:
        """Start all configured MCP servers."""
        self.logger.info("Starting MCP server manager", 
                        server_count=len(self.config.servers))
        
        if not self.config.servers:
            self.logger.info("No MCP servers configured")
            return
        
        # Start servers concurrently but with timeout
        try:
            await asyncio.wait_for(
                self._start_all_servers(),
                timeout=self.config.startup_timeout
            )
            
            self.logger.info("All MCP servers started successfully",
                           active_servers=len(self.clients),
                           total_tools=len(self.tool_registry.get_tools()))
            
        except asyncio.TimeoutError:
            self.logger.error("Timeout starting MCP servers", 
                            timeout=self.config.startup_timeout)
            # Continue with whatever servers we managed to start
        except Exception as e:
            self.logger.error("Error starting MCP servers", error=str(e))
            raise
    
    async def _start_all_servers(self) -> None:
        """Start all configured servers concurrently."""
        tasks = []
        
        for server_config in self.config.servers:
            if server_config.auto_start:
                task = asyncio.create_task(
                    self._start_server(server_config),
                    name=f"start_mcp_{server_config.name}"
                )
                tasks.append(task)
        
        if tasks:
            # Wait for all servers to start (or fail)
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _start_server(self, server_config: MCPServerConfig) -> None:
        """Start a single MCP server."""
        self.logger.info("Starting MCP server", server_name=server_config.name)
        
        try:
            # Create client
            client = MCPClient(
                name=server_config.name,
                command=server_config.command,
                working_directory=server_config.working_directory,
                timeout=server_config.timeout,
                max_retries=server_config.max_retries
            )
            
            # Register with tool registry (this will start the client)
            tools = await self.tool_registry.register_client(client)
            
            # Store client reference
            self.clients[server_config.name] = client
            
            # Validate expected tools if specified
            if server_config.expected_tools:
                tool_names = [tool.name for tool in tools]
                missing_tools = set(server_config.expected_tools) - set(tool_names)
                if missing_tools:
                    self.logger.warning("Expected tools not found on MCP server",
                                      server_name=server_config.name,
                                      missing_tools=list(missing_tools))
            
            self.logger.info("MCP server started successfully",
                           server_name=server_config.name,
                           tools_count=len(tools),
                           tools=[tool.name for tool in tools])
            
        except Exception as e:
            self.logger.error("Failed to start MCP server",
                            server_name=server_config.name,
                            error=str(e))
            # Don't re-raise - let other servers continue starting
    
    async def stop(self) -> None:
        """Stop all MCP servers."""
        self.logger.info("Stopping MCP server manager")
        
        try:
            await asyncio.wait_for(
                self.tool_registry.stop_all_clients(),
                timeout=self.config.shutdown_timeout
            )
            
            self.clients.clear()
            self.logger.info("All MCP servers stopped")
            
        except asyncio.TimeoutError:
            self.logger.error("Timeout stopping MCP servers",
                            timeout=self.config.shutdown_timeout)
        except Exception as e:
            self.logger.error("Error stopping MCP servers", error=str(e))
    
    def add_server(self, server_config: MCPServerConfig) -> None:
        """
        Add a new MCP server configuration.
        
        Args:
            server_config: Server configuration to add
        """
        self.config.add_server(server_config)
        self.logger.info("Added MCP server configuration", 
                        server_name=server_config.name)
    
    async def start_server(self, server_name: str) -> bool:
        """
        Start a specific MCP server by name.
        
        Args:
            server_name: Name of server to start
            
        Returns:
            True if server started successfully, False otherwise
        """
        server_config = self.config.get_server(server_name)
        if not server_config:
            self.logger.error("Unknown MCP server", server_name=server_name)
            return False
        
        if server_name in self.clients:
            self.logger.warning("MCP server already running", server_name=server_name)
            return True
        
        try:
            await self._start_server(server_config)
            return server_name in self.clients
        except Exception as e:
            self.logger.error("Failed to start MCP server",
                            server_name=server_name,
                            error=str(e))
            return False
    
    async def stop_server(self, server_name: str) -> bool:
        """
        Stop a specific MCP server by name.
        
        Args:
            server_name: Name of server to stop
            
        Returns:
            True if server stopped successfully, False otherwise
        """
        if server_name not in self.clients:
            self.logger.warning("MCP server not running", server_name=server_name)
            return True
        
        try:
            await self.tool_registry.unregister_client(server_name)
            del self.clients[server_name]
            
            self.logger.info("MCP server stopped", server_name=server_name)
            return True
        except Exception as e:
            self.logger.error("Failed to stop MCP server",
                            server_name=server_name,
                            error=str(e))
            return False
    
    def get_tools(self) -> List[MCPTool]:
        """Get all tools from all connected MCP servers."""
        return self.tool_registry.get_tools()
    
    def get_client(self, server_name: str) -> Optional[MCPClient]:
        """Get MCP client by server name."""
        return self.clients.get(server_name)
    
    def list_servers(self) -> List[str]:
        """Get list of all configured server names."""
        return self.config.list_server_names()
    
    def list_active_servers(self) -> List[str]:
        """Get list of currently running server names."""
        return list(self.clients.keys())
    
    def server_status(self) -> Dict[str, Dict]:
        """
        Get status of all servers.
        
        Returns:
            Dictionary mapping server names to their status info
        """
        status = {}
        
        for server_config in self.config.servers:
            server_name = server_config.name
            client = self.clients.get(server_name)
            
            if client:
                # Get tools for this server
                server_tools = [
                    tool.name for tool in self.tool_registry.get_tools()
                    if tool.mcp_client.name == server_name
                ]
                
                status[server_name] = {
                    "running": client.is_running,
                    "description": server_config.description,
                    "command": server_config.command,
                    "tools": server_tools,
                    "tool_count": len(server_tools)
                }
            else:
                status[server_name] = {
                    "running": False,
                    "description": server_config.description,
                    "command": server_config.command,
                    "tools": [],
                    "tool_count": 0
                }
        
        return status
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all active servers.
        
        Returns:
            Dictionary mapping server names to their health status
        """
        health_status = {}
        
        for server_name, client in self.clients.items():
            try:
                is_healthy = await client.ping()
                health_status[server_name] = is_healthy
            except Exception:
                health_status[server_name] = False
        
        return health_status