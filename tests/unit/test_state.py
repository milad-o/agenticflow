"""Tests for state management."""

import pytest
from datetime import datetime
from uuid import UUID

from agenticflow.core.state import AgentMessage, FlowState, MessageType, AgentStatus


@pytest.mark.asyncio
class TestAgentMessage:
    """Test AgentMessage functionality."""

    def test_message_creation(self):
        """Test basic message creation."""
        message = AgentMessage(
            type=MessageType.USER,
            sender="test_user",
            content="Hello, world!",
        )

        assert message.type == MessageType.USER
        assert message.sender == "test_user"
        assert message.content == "Hello, world!"
        assert isinstance(message.id, UUID)
        assert isinstance(message.timestamp, datetime)

    def test_message_to_dict(self):
        """Test message serialization."""
        message = AgentMessage(
            type=MessageType.AGENT,
            sender="test_agent",
            receiver="test_receiver",
            content="Test message",
            metadata={"key": "value"},
        )

        message_dict = message.to_dict()

        assert message_dict["type"] == "agent"
        assert message_dict["sender"] == "test_agent"
        assert message_dict["receiver"] == "test_receiver"
        assert message_dict["content"] == "Test message"
        assert message_dict["metadata"] == {"key": "value"}
        assert "id" in message_dict
        assert "timestamp" in message_dict


@pytest.mark.asyncio
class TestFlowState:
    """Test FlowState functionality."""

    async def test_state_creation(self):
        """Test basic state creation."""
        state = FlowState()

        assert isinstance(state.id, UUID)
        assert state.messages == []
        assert state.agent_statuses == {}
        assert state.shared_context == {}
        assert state.active_agents == {}
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.updated_at, datetime)

    async def test_add_message(self):
        """Test adding messages to state."""
        state = FlowState()
        message = AgentMessage(
            type=MessageType.USER,
            sender="user",
            content="Test message",
        )

        await state.add_message(message)

        assert len(state.messages) == 1
        assert state.messages[0] == message

    async def test_update_agent_status(self):
        """Test updating agent status."""
        state = FlowState()

        await state.update_agent_status("agent1", AgentStatus.BUSY)

        assert state.agent_statuses["agent1"] == AgentStatus.BUSY

    async def test_context_operations(self):
        """Test context get/set operations."""
        state = FlowState()

        await state.set_context("key1", "value1")
        await state.set_context("key2", {"nested": "value"})

        value1 = await state.get_context("key1")
        value2 = await state.get_context("key2")
        missing = await state.get_context("missing", "default")

        assert value1 == "value1"
        assert value2 == {"nested": "value"}
        assert missing == "default"

    async def test_get_messages_for_agent(self):
        """Test filtering messages for specific agent."""
        state = FlowState()

        # Add messages with different targets
        msg1 = AgentMessage(sender="user", receiver="agent1", content="For agent1")
        msg2 = AgentMessage(sender="user", receiver="agent2", content="For agent2")
        msg3 = AgentMessage(sender="agent1", content="From agent1")
        msg4 = AgentMessage(sender="user", content="Broadcast")

        await state.add_message(msg1)
        await state.add_message(msg2)
        await state.add_message(msg3)
        await state.add_message(msg4)

        agent1_messages = await state.get_messages_for_agent("agent1")

        # Should include: targeted to agent1, from agent1, and broadcast
        assert len(agent1_messages) == 3
        assert msg1 in agent1_messages
        assert msg3 in agent1_messages
        assert msg4 in agent1_messages

    async def test_state_serialization(self):
        """Test state serialization."""
        state = FlowState()
        state.workspace_path = "/test/path"

        message = AgentMessage(sender="user", content="Test")
        await state.add_message(message)
        await state.update_agent_status("agent1", AgentStatus.IDLE)
        await state.set_context("key", "value")

        state_dict = state.to_dict()

        assert "id" in state_dict
        assert len(state_dict["messages"]) == 1
        assert state_dict["agent_statuses"]["agent1"] == "idle"
        assert state_dict["shared_context"]["key"] == "value"
        assert state_dict["workspace_path"] == "/test/path"