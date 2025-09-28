"""Integration tests for LangGraph integration."""

import pytest
import asyncio
from pathlib import Path

from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent, SimpleAgent
from agenticflow.tools import WriteFileTool, ReadFileTool


class TestLangGraphIntegration:
    """Test cases for LangGraph integration."""

    @pytest.mark.asyncio
    async def test_simple_langgraph_flow(self):
        """Test basic LangGraph flow without LLM."""
        flow = Flow("test_flow")
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Create research team
        research_team = Supervisor(
            "research_team", 
            description="Web research specialists",
            keywords=["research", "web", "search"],
            initialize_llm=False
        )
        
        # Add agents to research team
        searcher = ReActAgent(
            "searcher",
            description="Web search specialist",
            keywords=["search", "web", "research"],
            initialize_llm=False
        ).add_tool(WriteFileTool())
        
        research_team.add_agent(searcher)
        orchestrator.add_team(research_team)
        
        # Create writing team
        writing_team = Supervisor(
            "writing_team",
            description="Document creation specialists", 
            keywords=["writing", "document", "content"],
            initialize_llm=False
        )
        
        # Add agents to writing team
        writer = ReActAgent(
            "writer",
            description="Content writer",
            keywords=["writing", "content", "document"],
            initialize_llm=False
        ).add_tool(WriteFileTool())
        
        writing_team.add_agent(writer)
        orchestrator.add_team(writing_team)
        
        # Test that the flow is set up correctly
        assert flow.name == "test_flow"
        assert orchestrator.name == "main_orchestrator"
        assert len(orchestrator.teams) == 2
        assert "research_team" in orchestrator.teams
        assert "writing_team" in orchestrator.teams
        assert len(research_team.agents) == 1
        assert len(writing_team.agents) == 1

    @pytest.mark.asyncio
    async def test_langgraph_stategraph_building(self):
        """Test that LangGraph StateGraph is built correctly."""
        flow = Flow("test_flow", enable_langgraph=True)
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Add a team
        team = Supervisor("test_team", initialize_llm=False)
        agent = SimpleAgent("test_agent", description="A test agent")
        team.add_agent(agent)
        orchestrator.add_team(team)
        
        if flow._enable_langgraph:
            assert flow._graph is not None
            assert flow._compiled_graph is not None
            assert "orchestrator" in flow._graph.nodes
            assert "test_team" in flow._graph.nodes
            assert "test_team_test_agent" in flow._graph.nodes
        else:
            assert flow._graph is None
            assert flow._compiled_graph is None

    @pytest.mark.asyncio
    async def test_flow_execution_with_langgraph(self):
        """Test flow execution using LangGraph."""
        flow = Flow("test_flow")
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Add a simple team
        team = Supervisor("test_team", initialize_llm=False)
        agent = SimpleAgent("test_agent", description="A test agent")
        team.add_agent(agent)
        orchestrator.add_team(team)
        
        if flow._enable_langgraph:
            assert flow._graph is not None
            assert flow._compiled_graph is not None
            await flow.start("Test message for LangGraph execution")
            await flow.stop()
            assert len(await flow.get_messages()) >= 1
        else:
            await flow.start("Test message for LangGraph execution")
            await flow.stop()
            assert isinstance(await flow.get_messages(), list)

    @pytest.mark.asyncio
    async def test_method_chaining_preservation(self):
        """Test that method chaining is preserved with LangGraph."""
        # Test flow method chaining
        flow = (Flow("test2", enable_langgraph=True)
                .add_orchestrator(Orchestrator("test_orchestrator", initialize_llm=False)))
        
        assert flow.name == "test2"
        assert flow.orchestrator.name == "test_orchestrator"
        
        # Test agent tool addition
        agent = (ReActAgent("test_agent", initialize_llm=False)
                .add_tool(WriteFileTool())
                .add_tool(ReadFileTool()))
        
        assert len(agent.tools) == 2
        assert "write_file" in agent.tools
        assert "read_file" in agent.tools
        
        # Test supervisor team building
        supervisor = (Supervisor("test_team", initialize_llm=False)
                    .add_agent(agent))
        
        assert len(supervisor.agents) == 1
        assert "test_agent" in supervisor.agents

    @pytest.mark.asyncio
    async def test_complex_workflow_structure(self):
        """Test complex workflow with multiple teams and agents."""
        flow = Flow("complex_flow", enable_langgraph=True)
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Research team
        research_team = Supervisor("research_team", initialize_llm=False)
        research_team.add_agent(SimpleAgent("researcher1", description="Researcher 1"))
        research_team.add_agent(SimpleAgent("researcher2", description="Researcher 2"))
        orchestrator.add_team(research_team)
        
        # Writing team
        writing_team = Supervisor("writing_team", initialize_llm=False)
        writing_team.add_agent(SimpleAgent("writer1", description="Writer 1"))
        writing_team.add_agent(SimpleAgent("writer2", description="Writer 2"))
        orchestrator.add_team(writing_team)
        
        # Direct agents
        orchestrator.add_agent(SimpleAgent("direct_agent1", description="Direct Agent 1"))
        orchestrator.add_agent(SimpleAgent("direct_agent2", description="Direct Agent 2"))
        
        assert len(orchestrator.teams) == 2
        assert len(orchestrator.agents) == 2
        assert len(research_team.agents) == 2
        assert len(writing_team.agents) == 2

        if flow._enable_langgraph:
            assert flow._compiled_graph is not None
            nodes = list(flow._graph.nodes.keys())
            assert "orchestrator" in nodes
            assert "research_team" in nodes
            assert "writing_team" in nodes
            assert "direct_agent1" in nodes
            assert "direct_agent2" in nodes
            assert "research_team_researcher1" in nodes
            assert "research_team_researcher2" in nodes
            assert "writing_team_writer1" in nodes
            assert "writing_team_writer2" in nodes
        else:
            assert flow._compiled_graph is None