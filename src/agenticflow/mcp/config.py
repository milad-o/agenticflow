"""
MCP Configuration for AgenticFlow

This module provides configuration classes for defining MCP servers
that can be used by AgenticFlow agents.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class MCPServerConfig:
    """
    Configuration for an MCP server.
    
    This class defines how to start and connect to an MCP server,
    including the command to run and any additional settings.
    """
    
    name: str
    """Human-readable name for the MCP server"""
    
    command: List[str]
    """Command to start the MCP server (e.g., ['python', 'server.py'])"""
    
    working_directory: Optional[Path] = None
    """Working directory for the server process"""
    
    timeout: float = 30.0
    """Timeout for server communication in seconds"""
    
    max_retries: int = 3
    """Maximum number of retries for failed requests"""
    
    auto_start: bool = True
    """Whether to automatically start the server when needed"""
    
    expected_tools: List[str] = field(default_factory=list)
    """List of expected tool names (for validation)"""
    
    environment: Dict[str, str] = field(default_factory=dict)
    """Additional environment variables for the server process"""
    
    description: str = ""
    """Description of what this MCP server provides"""
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name:
            raise ValueError("MCP server name is required")
        
        if not self.command:
            raise ValueError("MCP server command is required")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")


@dataclass 
class MCPConfig:
    """
    Global MCP configuration for AgenticFlow.
    
    This class contains settings that apply to all MCP operations
    within an agent or application.
    """
    
    servers: List[MCPServerConfig] = field(default_factory=list)
    """List of MCP server configurations"""
    
    auto_register_tools: bool = True
    """Whether to automatically register discovered tools with agents"""
    
    startup_timeout: float = 60.0
    """Timeout for starting all MCP servers during initialization"""
    
    shutdown_timeout: float = 30.0
    """Timeout for shutting down all MCP servers"""
    
    enable_builtin_servers: bool = True
    """Whether to enable built-in MCP servers (calculator, etc.)"""
    
    builtin_servers: List[str] = field(default_factory=lambda: ["calculator"])
    """List of built-in servers to enable"""
    
    tool_namespace: bool = True
    """Whether to namespace tools with server name (e.g., 'calculator.add')"""
    
    def add_server(self, config: MCPServerConfig) -> None:
        """Add an MCP server configuration."""
        # Check for duplicate names
        existing_names = {server.name for server in self.servers}
        if config.name in existing_names:
            raise ValueError(f"MCP server with name '{config.name}' already exists")
        
        self.servers.append(config)
    
    def remove_server(self, name: str) -> bool:
        """
        Remove an MCP server configuration by name.
        
        Returns:
            True if server was removed, False if not found
        """
        for i, server in enumerate(self.servers):
            if server.name == name:
                del self.servers[i]
                return True
        return False
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get MCP server configuration by name."""
        for server in self.servers:
            if server.name == name:
                return server
        return None
    
    def list_server_names(self) -> List[str]:
        """Get list of all configured server names."""
        return [server.name for server in self.servers]