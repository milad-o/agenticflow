"""Unit tests for Orchestrator functionality."""

import pytest
from agenticflow import Orchestrator, Supervisor, SimpleAgent, Flow


class TestOrchestrator:
    """Test cases for Orchestrator class."""

    def test_orchestrator_creation(self):
        """Test basic orchestrator creation."""
        orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
        assert orchestrator.name == "test_orchestrator"
        assert orchestrator.llm is None
        assert orchestrator.routing_strategy == "llm_based"
        assert len(orchestrator.teams) == 0
        assert len(orchestrator.agents) == 0

    def test_orchestrator_with_llm(self):
        """Test orchestrator creation with LLM (when API key available)."""
        # This will only work if OPENAI_API_KEY is set
        try:
            orchestrator = Orchestrator("test_orchestrator", initialize_llm=True)
            assert orchestrator.name == "test_orchestrator"
            assert orchestrator.llm is not None
        except Exception:
            # Skip if no API key
            pytest.skip("OpenAI API key not available")

    def test_add_team(self):
        """Test adding team to orchestrator."""
        orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
        team = Supervisor("test_team", initialize_llm=False)
        
        result = orchestrator.add_team(team)
        assert result == orchestrator  # Method chaining
        assert "test_team" in orchestrator.teams
        assert orchestrator.teams["test_team"] == team

    def test_add_agent(self):
        """Test adding agent to orchestrator."""
        orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
        agent = SimpleAgent("test_agent", description="Test agent")
        
        result = orchestrator.add_agent(agent)
        assert result == orchestrator  # Method chaining
        assert "test_agent" in orchestrator.agents
        assert orchestrator.agents["test_agent"] == agent

    def test_orchestrator_method_chaining(self):
        """Test method chaining on orchestrator."""
        orchestrator = (Orchestrator("test_orchestrator", initialize_llm=False)
                       .add_team(Supervisor("team1", initialize_llm=False))
                       .add_team(Supervisor("team2", initialize_llm=False))
                       .add_agent(SimpleAgent("agent1", description="Agent 1")))
        
        assert len(orchestrator.teams) == 2
        assert len(orchestrator.agents) == 1
        assert "team1" in orchestrator.teams
        assert "team2" in orchestrator.teams
        assert "agent1" in orchestrator.agents

    def test_get_available_targets(self):
        """Test getting available targets."""
        orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
        
        # Add some teams and agents
        team = Supervisor("test_team", initialize_llm=False)
        team.add_agent(SimpleAgent("team_agent", description="Team agent"))
        orchestrator.add_team(team)
        orchestrator.add_agent(SimpleAgent("direct_agent", description="Direct agent"))
        
        targets = orchestrator.get_available_targets()
        assert "test_team" in targets
        assert "direct_agent" in targets

    def test_orchestrator_str_representation(self):
        """Test string representation of orchestrator."""
        orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
        orchestrator_str = repr(orchestrator)
        assert orchestrator_str == "Orchestrator(name='test_orchestrator')"

    def test_orchestrator_repr(self):
        """Test repr of orchestrator."""
        orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
        orchestrator_repr = repr(orchestrator)
        assert orchestrator_repr == "Orchestrator(name='test_orchestrator')"
