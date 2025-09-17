"""
MCP Client for JSON-RPC communication with Model Context Protocol servers.

This client handles the low-level communication with MCP servers, including:
- Process management for MCP server subprocesses
- JSON-RPC protocol implementation
- Error handling and retries
- Tool discovery and invocation
"""

import asyncio
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


class MCPError(Exception):
    """Base exception for MCP-related errors."""
    pass


class MCPServerError(MCPError):
    """Exception raised when MCP server returns an error."""
    
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Server Error {code}: {message}")


class MCPCommunicationError(MCPError):
    """Exception raised when communication with MCP server fails."""
    pass


class MCPClient:
    """
    Client for communicating with Model Context Protocol servers.
    
    This client manages a subprocess running an MCP server and provides
    methods to call tools and manage the server lifecycle.
    """
    
    def __init__(
        self,
        name: str,
        command: List[str],
        working_directory: Optional[Path] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize MCP client.
        
        Args:
            name: Human-readable name for this MCP server
            command: Command to start the MCP server (e.g., ["python", "server.py"])
            working_directory: Working directory for the server process
            timeout: Timeout for server communication in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.name = name
        self.command = command
        self.working_directory = working_directory
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0
        self._is_running = False
        
        self.logger = logger.bind(mcp_server=name)
    
    async def start(self) -> None:
        """Start the MCP server process."""
        if self._is_running:
            return
        
        try:
            self.logger.info("Starting MCP server", command=self.command)
            
            self._process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_directory
            )
            
            self._is_running = True
            self.logger.info("MCP server started successfully", pid=self._process.pid)
            
        except Exception as e:
            self.logger.error("Failed to start MCP server", error=str(e))
            raise MCPCommunicationError(f"Failed to start MCP server '{self.name}': {e}")
    
    async def stop(self) -> None:
        """Stop the MCP server process."""
        if not self._is_running or not self._process:
            return
        
        try:
            self.logger.info("Stopping MCP server")
            
            # Try graceful shutdown first
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                # Force kill if graceful shutdown fails
                self._process.kill()
                await self._process.wait()
            
            self._is_running = False
            self._process = None
            
            self.logger.info("MCP server stopped")
            
        except Exception as e:
            self.logger.error("Error stopping MCP server", error=str(e))
            raise MCPCommunicationError(f"Failed to stop MCP server '{self.name}': {e}")
    
    def _next_request_id(self) -> int:
        """Generate next request ID."""
        self._request_id += 1
        return self._request_id
    
    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Send a JSON-RPC request to the MCP server.
        
        Args:
            method: JSON-RPC method name
            params: Method parameters
            
        Returns:
            Response data from the server
            
        Raises:
            MCPCommunicationError: If communication fails
            MCPServerError: If server returns an error
        """
        if not self._is_running or not self._process:
            raise MCPCommunicationError(f"MCP server '{self.name}' is not running")
        
        request_id = self._next_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        
        if params is not None:
            request["params"] = params
        
        request_json = json.dumps(request) + "\n"
        
        self.logger.debug("Sending MCP request", method=method, request_id=request_id)
        
        try:
            # Send request
            self._process.stdin.write(request_json.encode())
            await self._process.stdin.drain()
            
            # Read response with timeout
            response_line = await asyncio.wait_for(
                self._process.stdout.readline(), 
                timeout=self.timeout
            )
            
            if not response_line:
                raise MCPCommunicationError("MCP server closed connection")
            
            response_text = response_line.decode().strip()
            if not response_text:
                raise MCPCommunicationError("Empty response from MCP server")
            
            response = json.loads(response_text)
            
            # Check for JSON-RPC error
            if "error" in response:
                error = response["error"]
                raise MCPServerError(
                    code=error.get("code", -1),
                    message=error.get("message", "Unknown error"),
                    data=error.get("data")
                )
            
            # Verify response ID matches
            if response.get("id") != request_id:
                raise MCPCommunicationError(f"Response ID mismatch: expected {request_id}, got {response.get('id')}")
            
            self.logger.debug("Received MCP response", request_id=request_id)
            return response.get("result")
            
        except asyncio.TimeoutError:
            raise MCPCommunicationError(f"MCP server '{self.name}' response timeout")
        except json.JSONDecodeError as e:
            raise MCPCommunicationError(f"Invalid JSON response from MCP server: {e}")
        except Exception as e:
            if isinstance(e, (MCPCommunicationError, MCPServerError)):
                raise
            raise MCPCommunicationError(f"Communication error with MCP server '{self.name}': {e}")
    
    async def call_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        for attempt in range(self.max_retries):
            try:
                result = await self._send_request(
                    method="tools/call",
                    params={
                        "name": tool_name,
                        "arguments": arguments
                    }
                )
                
                self.logger.info("Tool called successfully", tool=tool_name, attempt=attempt + 1)
                return result
                
            except (MCPCommunicationError, MCPServerError) as e:
                if attempt == self.max_retries - 1:
                    # Last attempt failed
                    self.logger.error("Tool call failed after all retries", 
                                    tool=tool_name, error=str(e), attempts=self.max_retries)
                    raise
                
                self.logger.warning("Tool call failed, retrying", 
                                  tool=tool_name, error=str(e), attempt=attempt + 1)
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools from the MCP server.
        
        Returns:
            List of tool definitions
        """
        try:
            result = await self._send_request("tools/list")
            return result.get("tools", [])
        except Exception as e:
            self.logger.error("Failed to list tools", error=str(e))
            return []
    
    async def ping(self) -> bool:
        """
        Ping the MCP server to check if it's responsive.
        
        Returns:
            True if server is responsive, False otherwise
        """
        try:
            await self._send_request("ping")
            return True
        except Exception:
            return False
    
    @property
    def is_running(self) -> bool:
        """Check if the MCP server is running."""
        return self._is_running and self._process is not None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()