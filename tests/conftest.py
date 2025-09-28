"""Pytest configuration and shared fixtures for AgenticFlow tests."""

import asyncio
import pytest
import tempfile
import os
from pathlib import Path
from typing import Generator, AsyncGenerator

from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent, SimpleAgent
from agenticflow.tools import WriteFileTool, ReadFileTool


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
async def simple_flow() -> AsyncGenerator[Flow, None]:
    """Create a simple flow for testing."""
    flow = Flow("test_flow")
    orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
    flow.add_orchestrator(orchestrator)
    
    # Add a simple team
    team = Supervisor("test_team", initialize_llm=False)
    agent = SimpleAgent("test_agent", description="A simple test agent")
    team.add_agent(agent)
    orchestrator.add_team(team)
    
    yield flow


@pytest.fixture
async def react_flow() -> AsyncGenerator[Flow, None]:
    """Create a flow with ReAct agents for testing."""
    flow = Flow("react_test_flow")
    orchestrator = Orchestrator("react_orchestrator", initialize_llm=False)
    flow.add_orchestrator(orchestrator)
    
    # Add a team with ReAct agent
    team = Supervisor("react_team", initialize_llm=False)
    agent = ReActAgent("react_agent", description="A ReAct test agent", initialize_llm=False)
    agent.add_tool(WriteFileTool())
    team.add_agent(agent)
    orchestrator.add_team(team)
    
    yield flow


@pytest.fixture
def sample_data_dir() -> Path:
    """Get the sample data directory."""
    return Path(__file__).parent.parent / "data" / "sample"


@pytest.fixture
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent.parent / "data" / "test"