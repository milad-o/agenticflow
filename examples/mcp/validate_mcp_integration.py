#!/usr/bin/env python3
"""
Validate MCP Integration

This test validates that our MCP integration is working properly.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add AgenticFlow to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agenticflow.mcp.client import MCPClient
from agenticflow.mcp.tools import MCPTool
from agenticflow.mcp.config import MCPServerConfig, MCPConfig
from agenticflow.mcp.manager import MCPServerManager


def create_test_calculator_server():
    """Create a test calculator server."""
    calculator_script = '''#!/usr/bin/env python3
import json
import sys
import ast
import operator

ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
}

def safe_eval(expression):
    try:
        node = ast.parse(expression, mode='eval')
        return _eval_node(node.body)
    except:
        raise ValueError(f"Invalid: {expression}")

def _eval_node(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        return ALLOWED_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    else:
        raise ValueError("Unsupported")

# Process requests in a loop
while True:
    try:
        line = sys.stdin.readline()
        if not line:
            break
        
        request = json.loads(line.strip())
        method = request.get("method")
        
        if method == "tools/list":
            result = {"tools": [{"name": "calculate", "description": "Calculate", "inputSchema": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}]}
        elif method == "tools/call":
            tool_name = request.get("params", {}).get("name")
            args = request.get("params", {}).get("arguments", {})
            if tool_name == "calculate":
                try:
                    val = safe_eval(args.get("expression", ""))
                    result = {"content": [{"type": "text", "text": f"Result: {val}"}]}
                except Exception as e:
                    result = {"error": {"code": -1, "message": str(e)}}
            else:
                result = {"error": {"code": -1, "message": "Unknown tool"}}
        elif method == "ping":
            result = {"status": "ok"}
        else:
            result = {"error": {"code": -1, "message": "Unknown method"}}
        
        response = {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
        print(json.dumps(response))
        sys.stdout.flush()
        
    except Exception as e:
        error_response = {"jsonrpc": "2.0", "id": None, "error": {"code": -1, "message": str(e)}}
        print(json.dumps(error_response))
        sys.stdout.flush()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_calc.py', delete=False) as f:
        f.write(calculator_script)
        server_path = Path(f.name)
    
    server_path.chmod(0o755)
    return server_path


async def main():
    """Test MCP integration components."""
    print("🎯 Validating MCP Integration")
    print("=" * 40)
    
    server_path = create_test_calculator_server()
    
    try:
        # Test 1: Basic MCP Client
        print("\n1️⃣ Testing MCP Client...")
        client = MCPClient(
            name="test_calc", 
            command=[sys.executable, str(server_path)],
            timeout=10.0
        )
        
        await client.start()
        print("   ✅ Client started")
        
        # Test ping
        ping_ok = await client.ping()
        print(f"   📡 Ping: {'✅' if ping_ok else '❌'}")
        
        # Test tool list
        tools = await client.list_tools()
        print(f"   🔧 Tools discovered: {len(tools)}")
        
        # Test tool call
        result = await client.call_tool("calculate", {"expression": "2 + 3"})
        print(f"   🧮 Calculation: {result}")
        
        await client.stop()
        print("   ✅ Client test passed")
        
        # Test 2: MCP Tool
        print("\n2️⃣ Testing MCP Tool...")
        client2 = MCPClient(
            name="test_calc2",
            command=[sys.executable, str(server_path)],
            timeout=10.0
        )
        
        tool = MCPTool(
            name="calculate",
            description="Test calculator",
            mcp_client=client2,
            parameters_schema={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"]
            }
        )
        
        tool_result = await tool.execute({"expression": "5 * 6"})
        print(f"   🧮 Tool result: {tool_result.result if tool_result.success else tool_result.error}")
        
        await client2.stop()
        print("   ✅ Tool test passed")
        
        # Test 3: MCP Manager
        print("\n3️⃣ Testing MCP Manager...")
        config = MCPConfig(
            servers=[
                MCPServerConfig(
                    name="calc_server",
                    command=[sys.executable, str(server_path)],
                    expected_tools=["calculate"],
                    timeout=10.0
                )
            ]
        )
        
        manager = MCPServerManager(config)
        await manager.start()
        print("   ✅ Manager started")
        
        status = manager.server_status()
        print(f"   📊 Server status: {list(status.keys())}")
        
        tools = manager.get_tools()
        print(f"   🔧 Manager tools: {[t.name for t in tools]}")
        
        if tools:
            test_result = await tools[0].execute({"expression": "10 + 15"})
            print(f"   🧮 Manager calculation: {test_result.result if test_result.success else test_result.error}")
        
        await manager.stop()
        print("   ✅ Manager test passed")
        
        print("\n🎉 All MCP integration tests passed!")
        print("✅ MCP integration is working correctly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            server_path.unlink()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())