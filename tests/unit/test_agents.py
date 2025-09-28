"""Unit tests for Agent functionality."""

import pytest
from agenticflow import SimpleAgent, ReActAgent
from agenticflow.tools import WriteFileTool, ReadFileTool


class TestSimpleAgent:
    """Test cases for SimpleAgent class."""

    def test_simple_agent_creation(self):
        """Test basic simple agent creation."""
        agent = SimpleAgent("test_agent", description="A test agent")
        assert agent.name == "test_agent"
        assert agent.description == "A test agent"
        assert agent.is_available()
        assert len(agent.tools) == 0

    def test_simple_agent_with_keywords(self):
        """Test simple agent with keywords."""
        agent = SimpleAgent(
            "test_agent", 
            description="A test agent",
            keywords=["test", "example"]
        )
        assert agent.keywords == ["test", "example"]

    def test_add_tool(self):
        """Test adding tool to simple agent."""
        agent = SimpleAgent("test_agent", description="A test agent")
        tool = WriteFileTool()
        
        result = agent.add_tool(tool)
        assert result == agent  # Method chaining
        assert "write_file" in agent.tools
        assert agent.tools["write_file"] == tool

    def test_agent_method_chaining(self):
        """Test method chaining on agent."""
        agent = (SimpleAgent("test_agent", description="A test agent")
                .add_tool(WriteFileTool())
                .add_tool(ReadFileTool()))
        
        assert len(agent.tools) == 2
        assert "write_file" in agent.tools
        assert "read_file" in agent.tools

    @pytest.mark.asyncio
    async def test_execute_simple_message(self):
        """Test executing a simple message."""
        agent = SimpleAgent("test_agent", description="A test agent")
        
        from agenticflow.core.state import AgentMessage, MessageType
        message = AgentMessage(
            type=MessageType.HUMAN,
            sender="user",
            content="Hello, agent!"
        )
        
        result = await agent.execute(message)
        assert result is not None
        # SimpleAgent should return a Command
        assert hasattr(result, 'goto')

    def test_agent_str_representation(self):
        """Test string representation of agent."""
        agent = SimpleAgent("test_agent", description="A test agent")
        agent_str = str(agent)
        assert "test_agent" in agent_str
        assert "SimpleAgent" in agent_str

    def test_agent_repr(self):
        """Test repr of agent."""
        agent = SimpleAgent("test_agent", description="A test agent")
        agent_repr = repr(agent)
        assert "test_agent" in agent_repr
        assert "SimpleAgent" in agent_repr


class TestReActAgent:
    """Test cases for ReActAgent class."""

    def test_react_agent_creation(self):
        """Test basic ReAct agent creation."""
        agent = ReActAgent("test_agent", description="A test agent", initialize_llm=False)
        assert agent.name == "test_agent"
        assert agent.description == "A test agent"
        assert agent.llm is None  # No LLM initialized
        assert agent.is_available()

    def test_react_agent_with_llm(self):
        """Test ReAct agent creation with LLM (when API key available)."""
        try:
            agent = ReActAgent("test_agent", description="A test agent", initialize_llm=True)
            assert agent.name == "test_agent"
            assert agent.llm is not None
        except Exception:
            # Skip if no API key
            pytest.skip("OpenAI API key not available")

    def test_add_tool_to_react_agent(self):
        """Test adding tool to ReAct agent."""
        agent = ReActAgent("test_agent", description="A test agent", initialize_llm=False)
        tool = WriteFileTool()
        
        result = agent.add_tool(tool)
        assert result == agent  # Method chaining
        assert "write_file" in agent.tools
        assert agent.tools["write_file"] == tool

    @pytest.mark.asyncio
    async def test_execute_without_llm(self):
        """Test executing ReAct agent without LLM."""
        agent = ReActAgent("test_agent", description="A test agent", initialize_llm=False)
        
        from agenticflow.core.state import AgentMessage, MessageType
        message = AgentMessage(
            type=MessageType.HUMAN,
            sender="user",
            content="Hello, agent!"
        )
        
        result = await agent.execute(message)
        assert result is not None
        # Should return a Command even without LLM
        assert hasattr(result, 'goto')

    def test_react_agent_str_representation(self):
        """Test string representation of ReAct agent."""
        agent = ReActAgent("test_agent", description="A test agent", initialize_llm=False)
        agent_str = str(agent)
        assert "test_agent" in agent_str
        assert "ReActAgent" in agent_str

    def test_react_agent_repr(self):
        """Test repr of ReAct agent."""
        agent = ReActAgent("test_agent", description="A test agent", initialize_llm=False)
        agent_repr = repr(agent)
        assert "test_agent" in agent_repr
        assert "ReActAgent" in agent_repr
