"""Unit tests for Supervisor functionality."""

import pytest
from agenticflow import Supervisor, SimpleAgent
from agenticflow.core.state import AgentMessage, MessageType


class TestSupervisor:
    """Test cases for Supervisor class."""

    def test_supervisor_creation(self):
        """Test basic supervisor creation."""
        supervisor = Supervisor("test_supervisor", initialize_llm=False)
        assert supervisor.name == "test_supervisor"
        assert supervisor.llm is None
        assert len(supervisor.agents) == 0

    def test_supervisor_with_llm(self):
        """Test supervisor creation with LLM (when API key available)."""
        try:
            supervisor = Supervisor("test_supervisor", initialize_llm=True)
            assert supervisor.name == "test_supervisor"
            assert supervisor.llm is not None
        except Exception:
            # Skip if no API key
            pytest.skip("OpenAI API key not available")

    def test_add_agent(self):
        """Test adding agent to supervisor."""
        supervisor = Supervisor("test_supervisor", initialize_llm=False)
        agent = SimpleAgent("test_agent", description="Test agent")
        
        result = supervisor.add_agent(agent)
        assert result == supervisor  # Method chaining
        assert "test_agent" in supervisor.agents
        assert supervisor.agents["test_agent"] == agent

    def test_supervisor_method_chaining(self):
        """Test method chaining on supervisor."""
        supervisor = (Supervisor("test_supervisor", initialize_llm=False)
                     .add_agent(SimpleAgent("agent1", description="Agent 1"))
                     .add_agent(SimpleAgent("agent2", description="Agent 2")))
        
        assert len(supervisor.agents) == 2
        assert "agent1" in supervisor.agents
        assert "agent2" in supervisor.agents

    def test_get_available_agents(self):
        """Test getting available agents."""
        supervisor = Supervisor("test_supervisor", initialize_llm=False)
        
        # Add some agents
        agent1 = SimpleAgent("agent1", description="Agent 1")
        agent2 = SimpleAgent("agent2", description="Agent 2")
        supervisor.add_agent(agent1)
        supervisor.add_agent(agent2)
        
        available = supervisor._get_available_agents()
        assert len(available) == 2
        assert "agent1" in available
        assert "agent2" in available

    def test_supervisor_str_representation(self):
        """Test string representation of supervisor."""
        supervisor = Supervisor("test_supervisor", initialize_llm=False)
        supervisor_str = str(supervisor)
        assert "test_supervisor" in supervisor_str
        assert "Supervisor" in supervisor_str

    def test_supervisor_repr(self):
        """Test repr of supervisor."""
        supervisor = Supervisor("test_supervisor", initialize_llm=False)
        supervisor_repr = repr(supervisor)
        assert "test_supervisor" in supervisor_repr
        assert "Supervisor" in supervisor_repr

    @pytest.mark.asyncio
    async def test_process_message_without_llm(self):
        """Test processing message without LLM."""
        supervisor = Supervisor("test_supervisor", initialize_llm=False)
        agent = SimpleAgent("test_agent", description="Test agent")
        supervisor.add_agent(agent)
        
        message = AgentMessage(
            type=MessageType.HUMAN,
            sender="user",
            content="Test message"
        )
        
        # This should not raise an error
        response = await supervisor.process_message(message)
        # Response might be None or an AgentMessage
        assert response is None or isinstance(response, AgentMessage)
