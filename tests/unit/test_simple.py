"""Simple tests to validate the framework works."""

import pytest
import tempfile
import shutil
from agenticflow import Flow, Orchestrator, Agent
from agenticflow.core.agent import SimpleAgent
from agenticflow.core.state import AgentMessage, MessageType
from agenticflow.workspace.workspace import Workspace


@pytest.mark.asyncio
async def test_simple_agent():
    """Test that a simple agent works."""
    agent = SimpleAgent("test_agent")

    message = AgentMessage(
        type=MessageType.USER,
        sender="user",
        content="Hello",
    )

    response = await agent.process_message(message)

    assert response is not None
    assert response.sender == "test_agent"
    assert "test_agent processed: Hello" in response.content


@pytest.mark.asyncio
async def test_workspace():
    """Test basic workspace functionality."""
    temp_dir = tempfile.mkdtemp()
    try:
        workspace = Workspace(temp_dir)

        # Write and read a file
        await workspace.write_file("test.txt", "Hello World")
        content = await workspace.read_file("test.txt")

        assert content == "Hello World"

    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_flow_creation():
    """Test basic flow creation."""
    temp_dir = tempfile.mkdtemp()
    try:
        flow = Flow("test_flow", workspace_path=temp_dir)

        assert flow.name == "test_flow"
        assert flow.workspace is not None
        assert not flow.is_running()

    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_specialized_agents():
    """Test specialized agents."""
    from agenticflow.agents.research_agents import SearchAgent
    from agenticflow.agents.document_agents import DocumentWriterAgent

    # Test search agent
    search_agent = SearchAgent()
    assert search_agent.name == "search_agent"
    assert "search" in search_agent.keywords

    # Test document writer agent
    doc_agent = DocumentWriterAgent()
    assert doc_agent.name == "document_writer"
    assert "write" in doc_agent.keywords