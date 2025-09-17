#!/usr/bin/env python3
"""
AgenticFlow MCP Integration Example

This example demonstrates how to integrate external MCP servers with AgenticFlow agents.
It shows the complete workflow from configuration to tool usage.

Prerequisites:
- AgenticFlow installed
- An external MCP server running (we'll use our test calculator server)
- Ollama installed with a compatible model (optional, can use any LLM)

Usage:
    python examples/mcp_integration_example.py
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add AgenticFlow to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agenticflow import Agent, LLMProviderConfig
from agenticflow.config.settings import AgentConfig, LLMProvider
from agenticflow.mcp.config import MCPServerConfig, MCPConfig
from agenticflow.mcp.manager import MCPServerManager

import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def create_example_calculator_mcp_server() -> Path:
    """
    Create an example calculator MCP server for demonstration.
    
    In practice, you would connect to external MCP servers.
    """
    calculator_script = '''#!/usr/bin/env python3
import json
import sys
import ast
import operator

ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
}

def safe_eval(expression):
    try:
        node = ast.parse(expression, mode='eval')
        return _eval_node(node.body)
    except:
        raise ValueError(f"Invalid expression: {expression}")

def _eval_node(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        return ALLOWED_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    elif isinstance(node, ast.UnaryOp):
        return ALLOWED_OPS[type(node.op)](_eval_node(node.operand))
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
                "description": "Safely calculate mathematical expressions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression"}
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
        else:
            result = {"error": {"code": -1, "message": f"Unknown tool: {tool_name}"}}
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
'''
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='_mcp_calc.py', delete=False) as f:
        f.write(calculator_script)
        server_path = Path(f.name)
    
    server_path.chmod(0o755)
    return server_path


async def example_basic_mcp_integration():
    """Basic MCP integration example."""
    logger.info("🚀 Basic MCP Integration Example")
    logger.info("=" * 50)
    
    # Step 1: Create an example MCP server (normally you'd connect to existing ones)
    calc_server_path = create_example_calculator_mcp_server()
    logger.info(f"📝 Created example calculator server: {calc_server_path}")
    
    # Step 2: Configure the MCP server
    calc_server_config = MCPServerConfig(
        name="calculator",
        command=[sys.executable, str(calc_server_path)],
        description="Example calculator MCP server",
        expected_tools=["calculate"],
        timeout=10.0
    )
    
    # Step 3: Create MCP configuration
    mcp_config = MCPConfig(
        servers=[calc_server_config],
        auto_register_tools=True,
        tool_namespace=True  # Tools will be named like "calculator.calculate"
    )
    
    # Step 4: Create agent configuration with MCP integration
    agent_config = AgentConfig(
        name="mcp_math_agent",
        description="Math agent with MCP calculator integration",
        instructions="""You are a helpful math assistant with access to external calculator tools via MCP.
        
Use the calculator tool for any mathematical computations to ensure accuracy.
Always explain your calculations clearly.""",
        llm=LLMProviderConfig(
            provider=LLMProvider.OLLAMA,
            model="granite3.2:8b",
            temperature=0.1,
            max_tokens=500
        ),
        mcp_config=mcp_config,
        enable_self_verification=False
    )
    
    # Step 5: Create and start the agent
    agent = Agent(agent_config)
    await agent.start()
    
    try:
        logger.info("✅ Agent started with MCP integration")
        logger.info(f"🔧 Available tools: {agent._tool_registry.list_tools()}")
        
        # Test tasks
        test_tasks = [
            "What is 15 + 27?",
            "Calculate 123 * 456",
            "What's 2 to the power of 10?",
            "Help me solve (25 + 75) / 4"
        ]
        
        for i, task in enumerate(test_tasks, 1):
            logger.info(f"\n--- Task {i}: {task} ---")
            
            try:
                result = await agent.execute_task(task)
                
                if result.get('response'):
                    logger.info(f"✅ Response: {result['response']}")
                    
                    tool_results = result.get('tool_results', [])
                    if tool_results:
                        logger.info(f"🛠️  Tool calls: {len(tool_results)}")
                        for tr in tool_results:
                            if tr.get('success'):
                                logger.info(f"   ✅ {tr['tool']}: {tr['result']}")
                            else:
                                logger.info(f"   ❌ {tr['tool']}: {tr['error']}")
                else:
                    logger.warning(f"⚠️  No response received")
                    
            except Exception as e:
                logger.error(f"❌ Task failed: {e}")
    
    finally:
        await agent.stop()
        # Cleanup
        try:
            calc_server_path.unlink()
        except:
            pass


async def example_multiple_mcp_servers():
    """Example with multiple MCP servers."""
    logger.info("\n🚀 Multiple MCP Servers Example")
    logger.info("=" * 50)
    
    # Create multiple example servers
    calc_server_path = create_example_calculator_mcp_server()
    
    # Configure multiple servers
    mcp_config = MCPConfig(
        servers=[
            MCPServerConfig(
                name="calculator",
                command=[sys.executable, str(calc_server_path)],
                description="Calculator server",
                expected_tools=["calculate"]
            ),
            # Add more servers here as needed
            # MCPServerConfig(
            #     name="weather",
            #     command=["python", "path/to/weather_server.py"],
            #     expected_tools=["get_weather"]
            # )
        ],
        auto_register_tools=True,
        tool_namespace=True
    )
    
    # Create agent with multiple MCP servers
    agent_config = AgentConfig(
        name="multi_mcp_agent",
        description="Agent with multiple MCP servers",
        instructions="You have access to multiple external services via MCP. Use them as needed.",
        llm=LLMProviderConfig(
            provider=LLMProvider.OLLAMA,
            model="granite3.2:8b",
            temperature=0.1
        ),
        mcp_config=mcp_config,
        enable_self_verification=False
    )
    
    agent = Agent(agent_config)
    await agent.start()
    
    try:
        logger.info("✅ Agent started with multiple MCP servers")
        logger.info(f"🔧 Available tools: {agent._tool_registry.list_tools()}")
        
        # Get server status
        if agent._mcp_manager:
            status = agent._mcp_manager.server_status()
            logger.info("🖥️  Server Status:")
            for server_name, info in status.items():
                running_status = "✅ Running" if info['running'] else "❌ Stopped"
                logger.info(f"   {server_name}: {running_status} ({info['tool_count']} tools)")
        
        # Test with available tools
        result = await agent.execute_task("Calculate 50 * 8 + 25")
        logger.info(f"📊 Result: {result.get('response', 'No response')}")
        
    finally:
        await agent.stop()
        try:
            calc_server_path.unlink()
        except:
            pass


async def example_mcp_server_management():
    """Example of MCP server management operations."""
    logger.info("\n🚀 MCP Server Management Example")
    logger.info("=" * 50)
    
    # Create MCP manager directly
    calc_server_path = create_example_calculator_mcp_server()
    
    server_config = MCPServerConfig(
        name="calculator",
        command=[sys.executable, str(calc_server_path)],
        description="Calculator server for management demo",
        expected_tools=["calculate"]
    )
    
    mcp_config = MCPConfig(servers=[server_config])
    manager = MCPServerManager(mcp_config)
    
    try:
        # Start servers
        logger.info("🚀 Starting MCP servers...")
        await manager.start()
        
        # Get server status
        status = manager.server_status()
        logger.info("📊 Server Status:")
        for name, info in status.items():
            logger.info(f"   {name}: {'✅ Running' if info['running'] else '❌ Stopped'}")
            logger.info(f"      Tools: {info['tools']}")
        
        # Health check
        health = await manager.health_check()
        logger.info("💓 Health Check:")
        for name, healthy in health.items():
            logger.info(f"   {name}: {'✅ Healthy' if healthy else '❌ Unhealthy'}")
        
        # Get tools
        tools = manager.get_tools()
        logger.info(f"🔧 Available tools: {[tool.name for tool in tools]}")
        
        # Test direct tool execution
        if tools:
            tool = tools[0]
            logger.info(f"🧪 Testing tool '{tool.name}' directly...")
            result = await tool.execute({"expression": "10 + 5"})
            if result.success:
                logger.info(f"✅ Direct tool result: {result.result}")
            else:
                logger.info(f"❌ Direct tool failed: {result.error}")
        
    finally:
        await manager.stop()
        try:
            calc_server_path.unlink()
        except:
            pass


async def main():
    """Run all MCP integration examples."""
    logger.info("🎯 AgenticFlow MCP Integration Examples")
    logger.info("This demonstrates connecting external MCP servers to AgenticFlow agents")
    logger.info("")
    
    try:
        # Run examples
        await example_basic_mcp_integration()
        await example_multiple_mcp_servers()
        await example_mcp_server_management()
        
        logger.info("\n🎉 All MCP integration examples completed successfully!")
        logger.info("")
        logger.info("💡 Key Takeaways:")
        logger.info("   ✅ MCP servers can be easily integrated with AgenticFlow agents")
        logger.info("   ✅ Tools from MCP servers are automatically registered and available")
        logger.info("   ✅ Multiple MCP servers can be used simultaneously")
        logger.info("   ✅ Server management operations are available for monitoring")
        logger.info("   ✅ Framework handles MCP server lifecycle automatically")
        
    except Exception as e:
        logger.error(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())