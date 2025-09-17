# Web Search MCP Server

A Model Context Protocol (MCP) server that enables free web searching using Google search results, with no API keys required.

**Part of AgenticFlow** - This MCP server is designed to work with the [AgenticFlow framework](../../README.md) and is demonstrated in the [`real_web_search_example.py`](../real_web_search_example.py) example.

## Features

- Search the web using Google search results
- No API keys or authentication required
- Returns structured results with titles, URLs, and descriptions
- Configurable number of results per search

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
npm install
```
3. Build the server:
```bash
npm run build
```
4. Add the server to your MCP configuration:

For VSCode (Claude Dev Extension):
```json
{
  "mcpServers": {
    "web-search": {
      "command": "node",
      "args": ["/path/to/web-search/build/index.js"]
    }
  }
}
```

For Claude Desktop:
```json
{
  "mcpServers": {
    "web-search": {
      "command": "node",
      "args": ["/path/to/web-search/build/index.js"]
    }
  }
}
```

## Usage

The server provides a single tool named `search` that accepts the following parameters:

```typescript
{
  "query": string,    // The search query
  "limit": number     // Optional: Number of results to return (default: 5, max: 10)
}
```

Example usage:
```typescript
use_mcp_tool({
  server_name: "web-search",
  tool_name: "search",
  arguments: {
    query: "your search query",
    limit: 3  // optional
  }
})
```

Example response:
```json
[
  {
    "title": "Example Search Result",
    "url": "https://example.com",
    "description": "Description of the search result..."
  }
]
```

## Limitations

Since this tool uses web scraping of Google search results, there are some important limitations to be aware of:

1. **Rate Limiting**: Google may temporarily block requests if too many searches are performed in a short time. To avoid this:
   - Keep searches to a reasonable frequency
   - Use the limit parameter judiciously
   - Consider implementing delays between searches if needed

2. **Result Accuracy**: 
   - The tool relies on Google's HTML structure, which may change
   - Some results might be missing descriptions or other metadata
   - Complex search operators may not work as expected

3. **Legal Considerations**:
   - This tool is intended for personal use
   - Respect Google's terms of service
   - Consider implementing appropriate rate limiting for your use case

## AgenticFlow Integration

This MCP server integrates seamlessly with AgenticFlow. Here's a quick example:

```python
from agenticflow import Agent, AgentConfig, LLMProviderConfig, LLMProvider
from agenticflow.mcp.config import MCPServerConfig, MCPConfig

# Configure MCP with this web search server
mcp_config = MCPConfig(
    servers=[
        MCPServerConfig(
            name="web-search",
            command=["node", "./build/index.js"],  # Path to built server
            expected_tools=["search"]
        )
    ],
    auto_register_tools=True
)

# Create agent with web search capability
agent = Agent(AgentConfig(
    name="web_search_agent",
    llm=LLMProviderConfig(
        provider=LLMProvider.OLLAMA,
        model="qwen2.5:7b"
    ),
    mcp_config=mcp_config
))

# Use web search in natural language
result = await agent.execute_task("Search for Python best practices and summarize")
```

For a complete example, see [`../real_web_search_example.py`](../real_web_search_example.py).

## Contributing

Feel free to submit issues and enhancement requests!
