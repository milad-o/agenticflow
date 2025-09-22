import pytest

from agenticflow.tools.base.registry import ToolRegistry
from agenticflow.tools.builtin.echo import EchoTool
from agenticflow.security.context import SecurityContext
from agenticflow.core.exceptions.base import SecurityError


@pytest.mark.asyncio
async def test_tool_invoke_allowed(capsys):
    reg = ToolRegistry()
    reg.register(EchoTool())
    sec = SecurityContext(principal="u1", permissions={"invoke:tool:echo": True})

    result = await reg.invoke("echo", {"text": "hi"}, security=sec)
    assert result["echo"] == "hi"

    out = capsys.readouterr().out
    assert "granted" in out
    assert "status': 'success" in out or '"status": "success"' in out


@pytest.mark.asyncio
async def test_tool_invoke_denied(capsys):
    reg = ToolRegistry()
    reg.register(EchoTool())
    sec = SecurityContext(principal="u1", permissions={})

    with pytest.raises(SecurityError):
        await reg.invoke("echo", {"text": "hi"}, security=sec)

    out = capsys.readouterr().out
    assert "denied" in out
