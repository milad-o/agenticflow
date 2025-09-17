# MCP (Model Context Protocol) Integration Examples

This directory contains comprehensive examples demonstrating how to integrate MCP servers with AgenticFlow agents, allowing agents to access external tools and resources through the Model Context Protocol.

## 📁 Files Overview

### 1. `test_mcp_server.py` 
**Complete MCP Server Implementation**
- A fully functional MCP server using the official MCP SDK
- Provides 5 test tools: get_user, list_projects, create_task, search_data, get_stats
- Runs over stdio transport for easy testing
- Sample data included for immediate testing

### 2. `test_mcp_integration.py`
**Full MCP Integration with Official SDK**
- Demonstrates complete MCP integration using the official MCP Python SDK
- Shows how to connect AgenticFlow agents to real MCP servers
- Tests both direct tool calling and agent-mediated tool usage
- Requires MCP SDK installation: `pip install mcp`

### 3. `test_mcp_simple.py`
**Simple MCP Integration (No External Dependencies)**
- Uses AgenticFlow's built-in simple MCP client
- No external MCP SDK required - works out of the box
- Great for understanding MCP concepts and prototyping
- Simulates research and data analysis MCP servers

### 4. `README_MCP.md` (this file)
**Documentation and Usage Guide**

## 🚀 Quick Start

### Option A: Full MCP Integration (Recommended)

**Requirements:**
```bash
pip install mcp  # Install official MCP SDK
export OPENAI_API_KEY="your-openai-api-key"
```

**Run the example:**
```bash
# Terminal 1: Start the MCP server
python examples/test_mcp_server.py

# Terminal 2: Run the integration test
python examples/test_mcp_integration.py
```

### Option B: Simple Integration (No Dependencies)

**Requirements:**
```bash
export OPENAI_API_KEY="your-openai-api-key"  # Optional but recommended
```

**Run the example:**
```bash
python examples/test_mcp_simple.py
```

## 🔧 What These Examples Demonstrate

### Core MCP Concepts
- **Server Connection**: How to connect to MCP servers via different transports (stdio, HTTP, WebSocket)
- **Tool Discovery**: Automatically discovering available tools from MCP servers
- **Tool Execution**: Calling MCP tools with proper parameter validation
- **Error Handling**: Graceful handling of connection and execution errors

### AgenticFlow Integration
- **Tool Registration**: Registering MCP tools with AgenticFlow agents
- **Agent Usage**: How agents can automatically use MCP tools in conversations
- **Parameter Mapping**: Converting between AgenticFlow tool formats and MCP protocols
- **Result Processing**: Handling and interpreting MCP tool results

## 📊 Example Workflow

```
1. MCP Server Startup
   └── Exposes tools: get_user, list_projects, create_task, search_data, get_stats

2. AgenticFlow Agent Connection
   ├── Connects to MCP server via stdio/HTTP/WebSocket
   ├── Discovers available tools
   └── Registers tools in agent's tool registry

3. Agent Task Execution
   ├── User: "Get information about user 1"
   ├── Agent: Identifies need for get_user tool
   ├── Agent: Calls MCP server with get_user(user_id=1)
   ├── MCP Server: Returns user data as JSON
   └── Agent: Interprets results and responds to user

4. Cleanup
   └── Graceful disconnection from MCP servers
```

## 🛠️ Available Test Tools

The test MCP server provides these tools:

| Tool | Parameters | Description |
|------|------------|-------------|
| `get_user` | `user_id: int` | Get user information by ID |
| `list_projects` | `status?: string` | List projects, optionally filtered by status |
| `create_task` | `title: string, project: string, status?: string` | Create a new task |
| `search_data` | `query: string, data_type?: string` | Search across all data types |
| `get_stats` | none | Get statistics about all data |

## 📝 Example Usage

### Direct MCP Tool Usage
```python
# Connect to MCP server
mcp_client = register_mcp_server(server_config, "test_server")
await mcp_client.connect()

# Call tool directly
result = await mcp_client.call_tool("get_user", {"user_id": 1})
print(result)  # User information as JSON
```

### Agent-Mediated Usage
```python
# Create agent with MCP tools
agent = create_mcp_agent()
await agent.start()
register_mcp_tools_with_agent(agent)

# Agent automatically uses MCP tools
result = await agent.execute_task("Get information about user 1 and tell me about them")
print(result["response"])  # Natural language response with user details
```

## 🔍 Testing Different Scenarios

### Test User Tasks
```python
test_tasks = [
    "Get information about user 1 and tell me about them",
    "List all active projects and summarize what you find", 
    "Search for anything related to 'Beta' and explain the results",
    "Show me the current statistics and give me insights",
    "Create a new task called 'Update documentation' for 'Project Alpha'"
]
```

### Expected Outputs
- **get_user**: Returns user details (name, email, department)
- **list_projects**: Returns filtered project list with status and lead
- **search_data**: Returns matching items across users, projects, and tasks
- **get_stats**: Returns comprehensive statistics about all data
- **create_task**: Creates new task and returns confirmation

## 🐛 Troubleshooting

### Common Issues

**"MCP SDK not available"**
```bash
pip install mcp
```

**"Failed to connect to MCP server"**
- Ensure the MCP server is running (`python examples/test_mcp_server.py`)
- Check that the server hasn't crashed or exited
- Verify the connection configuration (stdio/HTTP/WebSocket)

**"Tool not found" errors**
- Verify the MCP server is exposing the expected tools
- Check tool discovery completed successfully
- Ensure tool names match between server and client

**Agent not using tools**
- Verify OPENAI_API_KEY is set for actual LLM usage
- Check that tools are properly registered with the agent
- Ensure the agent's instructions mention the available tools

### Debug Mode
Add these environment variables for verbose logging:
```bash
export AGENTICFLOW_DEBUG=true
export AGENTICFLOW_LOG_LEVEL=debug
```

## 🌟 Next Steps

### Real-World Integration
1. **Replace Test Server**: Connect to actual MCP servers (databases, APIs, file systems)
2. **Custom Tools**: Implement domain-specific MCP tools for your use case
3. **Multi-Agent**: Use MCP tools across multiple specialized agents
4. **Production**: Deploy with proper error handling, monitoring, and scaling

### Advanced Features
- **Resource Access**: Use MCP resources for file/data access
- **Streaming**: Implement streaming MCP tool responses
- **Authentication**: Add security and authentication layers
- **Caching**: Implement tool result caching for performance

## 📚 Further Reading

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [AgenticFlow Tool Integration Guide](../docs/tools.md)
- [AgenticFlow Agent Configuration](../docs/agents.md)

---

**Happy MCP Integration! 🚀**

These examples provide a solid foundation for integrating any MCP server with AgenticFlow agents, enabling powerful tool-augmented AI workflows.