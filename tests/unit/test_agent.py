"""Tests for agent functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock

from agenticflow.core.agent import Agent, SimpleAgent, Tool
from agenticflow.core.state import AgentMessage, AgentStatus, MessageType


@pytest.mark.asyncio
class TestTool:
    """Test Tool functionality."""

    def test_tool_creation(self):
        """Test basic tool creation."""
        def test_func(x: int, y: int) -> int:
            return x + y

        tool = Tool(
            name="add",
            description="Add two numbers",
            func=test_func,
            parameters={"x": "int", "y": "int"},
        )

        assert tool.name == "add"
        assert tool.description == "Add two numbers"
        assert tool.func == test_func

    async def test_tool_execution_sync(self):
        """Test executing synchronous tool."""
        def add_func(x: int, y: int) -> int:
            return x + y

        tool = Tool(name="add", description="Add", func=add_func)
        result = await tool.execute(x=2, y=3)
        assert result == 5

    async def test_tool_execution_async(self):
        """Test executing asynchronous tool."""
        async def async_add(x: int, y: int) -> int:
            await asyncio.sleep(0.01)  # Simulate async work
            return x + y

        tool = Tool(name="async_add", description="Async add", func=async_add)
        result = await tool.execute(x=2, y=3)
        assert result == 5


@pytest.mark.asyncio
class TestSimpleAgent:
    """Test SimpleAgent functionality."""

    async def test_agent_creation(self, simple_agent):
        """Test basic agent creation."""
        assert simple_agent.name == "test_agent"
        assert simple_agent.description == "A test agent"
        assert simple_agent.keywords == ["test", "hello"]
        assert simple_agent.status == AgentStatus.IDLE
        assert simple_agent.is_available()

    async def test_agent_tool_management(self, simple_agent, echo_tool):
        """Test adding and using tools."""
        simple_agent.add_tool(echo_tool)

        assert "echo" in simple_agent.tools
        assert simple_agent.tools["echo"] == echo_tool

        # Test using the tool
        result = await simple_agent.use_tool("echo", message="Hello")
        assert result == "Echo: Hello"

    async def test_agent_static_resources(self, simple_agent):
        """Test adding static resources."""
        resource = {"config": "value"}
        simple_agent.add_static_resource("config", resource)

        assert "config" in simple_agent.static_resources
        assert simple_agent.static_resources["config"] == resource

    async def test_agent_message_processing(self, simple_agent):
        """Test processing messages."""
        message = AgentMessage(
            type=MessageType.USER,
            sender="user",
            content="Hello agent",
        )

        response = await simple_agent.process_message(message)

        assert response is not None
        assert response.type == MessageType.AGENT
        assert response.sender == simple_agent.name
        assert "test_agent processed: Hello agent" in response.content
        assert simple_agent.execution_count == 1
        assert len(simple_agent.message_history) == 1

    async def test_agent_status_changes(self, simple_agent):
        """Test agent status changes during execution."""
        message = AgentMessage(sender="user", content="Test")

        # Initial status should be IDLE
        assert simple_agent.status == AgentStatus.IDLE

        # Process message (status will change during execution)
        await simple_agent.process_message(message)

        # Should return to IDLE after processing
        assert simple_agent.status == AgentStatus.IDLE

    async def test_agent_error_handling(self, simple_agent):
        """Test agent error handling."""
        # Create an agent that will raise an error
        class ErrorAgent(SimpleAgent):
            async def execute(self, message):
                raise ValueError("Test error")

        error_agent = ErrorAgent("error_agent")
        message = AgentMessage(sender="user", content="Test")

        response = await error_agent.process_message(message)

        assert response.type == MessageType.ERROR
        assert error_agent.status == AgentStatus.ERROR
        assert "Error processing message" in response.content

    async def test_agent_stop_and_reset(self, simple_agent):
        """Test stopping and resetting agent."""
        message = AgentMessage(sender="user", content="Test")
        await simple_agent.process_message(message)

        assert simple_agent.execution_count == 1
        assert len(simple_agent.message_history) == 1

        # Stop agent
        await simple_agent.stop()
        assert simple_agent.status == AgentStatus.IDLE

        # Reset agent
        await simple_agent.reset()
        assert simple_agent.execution_count == 0
        assert len(simple_agent.message_history) == 0
        assert simple_agent.status == AgentStatus.IDLE

    async def test_agent_get_status(self, simple_agent, echo_tool):
        """Test getting agent status."""
        simple_agent.add_tool(echo_tool)
        simple_agent.add_static_resource("test", "value")

        status = await simple_agent.get_status()

        assert status["name"] == "test_agent"
        assert status["description"] == "A test agent"
        assert status["status"] == "idle"
        assert status["execution_count"] == 0
        assert "echo" in status["available_tools"]
        assert "test" in status["static_resources"]

    async def test_agent_tool_not_found(self, simple_agent):
        """Test error when using non-existent tool."""
        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            await simple_agent.use_tool("nonexistent")

    async def test_agent_availability(self, simple_agent):
        """Test agent availability checks."""
        assert simple_agent.is_available()

        # Set agent to busy
        await simple_agent._set_status(AgentStatus.BUSY)
        assert not simple_agent.is_available()

        # Set agent to error
        await simple_agent._set_status(AgentStatus.ERROR)
        assert not simple_agent.is_available()

        # Stop agent
        await simple_agent.stop()
        simple_agent._stop_event.set()
        assert not simple_agent.is_available()

    async def test_agent_custom_response_template(self):
        """Test agent with custom response template."""
        agent = SimpleAgent(
            name="custom_agent",
            response_template="Custom: {content} from {sender}",
        )

        message = AgentMessage(sender="user", content="Hello")
        response = await agent.process_message(message)

        assert "Custom: Hello from user" in response.content