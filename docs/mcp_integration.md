# MCP Integration Guide

AgenticFlow provides seamless integration with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers, allowing agents to access external tools and services through standardized interfaces.

## Overview

The MCP integration enables AgenticFlow agents to:

- Connect to external MCP servers
- Automatically discover and register tools from MCP servers
- Execute tools via JSON-RPC communication
- Manage server lifecycle and health monitoring
- Handle multiple MCP servers simultaneously

## Quick Start

### Basic MCP Integration

```python
from agenticflow import Agent, LLMProviderConfig
from agenticflow.config.settings import AgentConfig, LLMProvider
from agenticflow.mcp.config import MCPServerConfig, MCPConfig

# Configure MCP server
mcp_server_config = MCPServerConfig(
    name="calculator",
    command=["python", "path/to/calculator_server.py"],
    description="External calculator service",
    expected_tools=["calculate"],
    timeout=30.0
)

# Create MCP configuration
mcp_config = MCPConfig(
    servers=[mcp_server_config],
    auto_register_tools=True,
    tool_namespace=True
)

# Create agent with MCP integration
agent_config = AgentConfig(
    name="mcp_agent",
    description="Agent with MCP integration",
    llm=LLMProviderConfig(
        provider=LLMProvider.OLLAMA,
        model="granite3.2:8b"
    ),
    mcp_config=mcp_config  # Enable MCP integration
)

# Create and start agent
agent = Agent(agent_config)
await agent.start()

# MCP tools are now automatically available
result = await agent.execute_task("Calculate 15 + 27")
print(result['response'])

await agent.stop()
```

## Configuration

### MCPServerConfig

Defines how to connect to an individual MCP server:

```python
from agenticflow.mcp.config import MCPServerConfig

config = MCPServerConfig(
    name="my_server",                    # Unique server name
    command=["python", "server.py"],    # Command to start server
    working_directory="/path/to/dir",   # Working directory (optional)
    timeout=30.0,                       # Communication timeout
    max_retries=3,                      # Max retry attempts
    auto_start=True,                    # Auto-start on agent init
    expected_tools=["tool1", "tool2"],  # Expected tools (for validation)
    environment={"VAR": "value"},       # Environment variables
    description="My MCP server"        # Human-readable description
)
```

### MCPConfig

Global MCP configuration for the agent:

```python
from agenticflow.mcp.config import MCPConfig

mcp_config = MCPConfig(
    servers=[server_config1, server_config2],  # List of server configs
    auto_register_tools=True,                  # Auto-register discovered tools
    startup_timeout=60.0,                      # Startup timeout for all servers
    shutdown_timeout=30.0,                     # Shutdown timeout
    tool_namespace=True                        # Namespace tools by server name
)
```

## Server Management

### Using MCPServerManager

For advanced server management:

```python
from agenticflow.mcp.manager import MCPServerManager
from agenticflow.mcp.config import MCPConfig, MCPServerConfig

# Create manager
manager = MCPServerManager(mcp_config)

# Start all configured servers
await manager.start()

# Get server status
status = manager.server_status()
for server_name, info in status.items():
    print(f"{server_name}: {'Running' if info['running'] else 'Stopped'}")
    print(f"  Tools: {info['tools']}")

# Health check
health = await manager.health_check()
for server_name, is_healthy in health.items():
    print(f"{server_name}: {'Healthy' if is_healthy else 'Unhealthy'}")

# Get all tools from all servers
tools = manager.get_tools()
print(f"Available tools: {[tool.name for tool in tools]}")

# Start/stop individual servers
await manager.start_server("calculator")
await manager.stop_server("calculator")

# Stop all servers
await manager.stop()
```

## Tool Usage

### Automatic Tool Registration

When `auto_register_tools=True`, MCP tools are automatically registered with the agent:

```python
# Tools are automatically available for the LLM to use
agent_config = AgentConfig(
    name="auto_mcp_agent",
    llm=llm_config,
    mcp_config=MCPConfig(
        servers=[calculator_server],
        auto_register_tools=True,    # Enable automatic registration
        tool_namespace=True          # Tools named like "calculator.add"
    )
)

agent = Agent(agent_config)
await agent.start()

# LLM can now use MCP tools automatically
result = await agent.execute_task("What's 25 * 8?")
```

### Manual Tool Access

You can also access MCP tools directly:

```python
# Get MCP tools from the agent
if agent._mcp_manager:
    tools = agent._mcp_manager.get_tools()
    calc_tool = next(tool for tool in tools if tool.name == "calculate")
    
    # Execute tool directly
    result = await calc_tool.execute({"expression": "10 + 5"})
    if result.success:
        print(f"Result: {result.result}")
    else:
        print(f"Error: {result.error}")
```

## Example MCP Servers

### Calculator Server

Here's a simple calculator MCP server:

```python
#!/usr/bin/env python3
import json
import sys
import ast
import operator

ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

def safe_eval(expression):
    node = ast.parse(expression, mode='eval')
    return eval_node(node.body)

def eval_node(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = eval_node(node.left)
        right = eval_node(node.right)
        return ALLOWED_OPS[type(node.op)](left, right)
    else:
        raise ValueError("Unsupported operation")

def handle_request():
    line = sys.stdin.readline()
    if not line:
        return
    
    request = json.loads(line)
    method = request.get("method")
    
    if method == "tools/list":
        result = {
            "tools": [{
                "name": "calculate",
                "description": "Calculate mathematical expressions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }]
        }
    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name")
        args = request.get("params", {}).get("arguments", {})
        
        if tool_name == "calculate":
            try:
                result_value = safe_eval(args.get("expression", ""))
                result = {
                    "content": [{
                        "type": "text",
                        "text": f"Result: {result_value}"
                    }]
                }
            except Exception as e:
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -1, "message": str(e)}
                }))
                return
    elif method == "ping":
        result = {"status": "ok"}
    else:
        result = {"error": {"code": -1, "message": f"Unknown method: {method}"}}
    
    response = {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": result
    }
    print(json.dumps(response))
    sys.stdout.flush()

if __name__ == "__main__":
    handle_request()
```

## Advanced Features

### Multiple Server Configuration

```python
mcp_config = MCPConfig(
    servers=[
        MCPServerConfig(
            name="calculator",
            command=["python", "calculator_server.py"],
            expected_tools=["calculate"]
        ),
        MCPServerConfig(
            name="weather", 
            command=["node", "weather_server.js"],
            expected_tools=["get_weather"]
        ),
        MCPServerConfig(
            name="database",
            command=["python", "db_server.py"],
            environment={"DB_URL": "postgresql://..."},
            expected_tools=["query", "insert", "update"]
        )
    ],
    auto_register_tools=True,
    tool_namespace=True  # Tools: calculator.calculate, weather.get_weather, etc.
)
```

### Custom Tool Registration

Disable automatic registration and manually control tools:

```python
mcp_config = MCPConfig(
    servers=[server_config],
    auto_register_tools=False  # Disable automatic registration
)

agent = Agent(AgentConfig(
    name="custom_agent",
    llm=llm_config,
    mcp_config=mcp_config
))

await agent.start()

# Manually register specific tools
if agent._mcp_manager:
    tools = agent._mcp_manager.get_tools()
    calc_tool = next(tool for tool in tools if tool.name == "calculate")
    agent._tool_registry.register_tool(calc_tool)
```

### Server Health Monitoring

```python
# Regular health checks
async def monitor_servers(agent):
    while agent._running:
        if agent._mcp_manager:
            health = await agent._mcp_manager.health_check()
            for server, is_healthy in health.items():
                if not is_healthy:
                    print(f"Warning: {server} is unhealthy!")
        
        await asyncio.sleep(60)  # Check every minute

# Start monitoring
asyncio.create_task(monitor_servers(agent))
```

## Error Handling

MCP integration includes robust error handling:

```python
# Server startup errors are logged but don't prevent agent initialization
# Tool execution errors are returned as ToolResult.error_result()
# Network timeouts and communication errors are handled automatically
# Server failures are logged and can be monitored via health checks

# Check for MCP-specific errors
result = await agent.execute_task("Calculate something")
tool_results = result.get('tool_results', [])
for tr in tool_results:
    if not tr['success']:
        error_metadata = tr.get('metadata', {})
        if error_metadata.get('tool_type') == 'mcp':
            print(f"MCP error in {tr['tool']}: {tr['error']}")
```

## Best Practices

### 1. Server Configuration

- Use descriptive server names
- Set appropriate timeouts based on server complexity
- Specify expected tools for validation
- Use working directories for server-relative paths

### 2. Tool Management

- Enable tool namespacing for multiple servers
- Use auto-registration for simple setups
- Manual registration for fine-grained control
- Monitor server health in production

### 3. Error Handling

- Handle server startup failures gracefully
- Implement retry logic for critical operations
- Log MCP errors for debugging
- Provide fallbacks for missing tools

### 4. Performance

- Start servers concurrently where possible
- Use connection pooling for high-throughput scenarios
- Cache tool schemas to reduce overhead
- Monitor server response times

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Check command path and permissions
   - Verify working directory exists
   - Check environment variables
   - Review server logs

2. **Tools not found**
   - Verify `tools/list` response from server
   - Check tool name spelling
   - Ensure server implements required methods

3. **Communication timeouts**
   - Increase timeout values
   - Check server responsiveness
   - Verify network connectivity

4. **Tool execution fails**
   - Check parameter schema matches
   - Verify tool parameters are correct
   - Review server error responses

### Debug Mode

Enable debug logging to troubleshoot MCP issues:

```python
import structlog
structlog.configure(
    processors=[structlog.dev.ConsoleRenderer()],
    level=structlog.DEBUG
)

# Debug logs will show:
# - Server startup/shutdown
# - Tool discovery
# - JSON-RPC communication
# - Error details
```

## Integration with Existing Tools

MCP tools work alongside regular AgenticFlow tools:

```python
# Agent can have both regular tools and MCP tools
agent_config = AgentConfig(
    name="hybrid_agent",
    llm=llm_config,
    tools=["web_search", "email"],  # Regular tools
    mcp_config=mcp_config           # MCP tools
)

# All tools are available to the LLM automatically
```

## Security Considerations

- MCP servers run as separate processes with their own permissions
- No direct file system access from framework to server
- Communication is via stdin/stdout only
- Server code is isolated from agent process
- Use appropriate process permissions and sandboxing

## Examples

See `examples/mcp_integration_example.py` for comprehensive examples including:

- Basic MCP integration
- Multiple server configuration
- Server management operations
- Error handling patterns
- Tool usage patterns

## API Reference

### Classes

- `MCPServerConfig`: Configuration for individual MCP servers
- `MCPConfig`: Global MCP configuration
- `MCPClient`: Low-level MCP server communication
- `MCPTool`: Tool implementation for MCP-based tools
- `MCPServerManager`: High-level server management
- `MCPToolRegistry`: Registry for MCP tools

### Methods

- `agent.start()`: Automatically starts configured MCP servers
- `agent.stop()`: Stops all MCP servers
- `manager.server_status()`: Get server status information
- `manager.health_check()`: Check server health
- `manager.get_tools()`: Get all available tools