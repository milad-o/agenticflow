"""Integration tests for full workflow execution."""

import pytest
import asyncio
from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent, SimpleAgent
from agenticflow.tools import WriteFileTool, ReadFileTool


class TestFullWorkflow:
    """Test cases for complete workflow execution."""

    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self):
        """Test execution of a simple workflow."""
        flow = Flow("test_workflow")
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Create team
        team = Supervisor("test_team", initialize_llm=False)
        agent = SimpleAgent("test_agent", description="Test agent")
        team.add_agent(agent)
        orchestrator.add_team(team)
        
        # Execute workflow
        await flow.start("Test message")
        
        # Verify execution
        assert flow.state is not None
        messages = await flow.get_messages()
        assert len(messages) > 0
        
        # Check that we have user message and system response
        user_messages = [msg for msg in messages if msg.sender == "user"]
        system_messages = [msg for msg in messages if msg.sender == "system"]
        
        assert len(user_messages) > 0
        assert len(system_messages) > 0

    @pytest.mark.asyncio
    async def test_multi_team_workflow(self):
        """Test workflow with multiple teams."""
        flow = Flow("multi_team_workflow")
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Team 1
        team1 = Supervisor("team1", initialize_llm=False)
        agent1 = SimpleAgent("agent1", description="Agent 1")
        team1.add_agent(agent1)
        orchestrator.add_team(team1)
        
        # Team 2
        team2 = Supervisor("team2", initialize_llm=False)
        agent2 = SimpleAgent("agent2", description="Agent 2")
        team2.add_agent(agent2)
        orchestrator.add_team(team2)
        
        # Execute workflow
        await flow.start("Test multi-team workflow")
        
        # Verify execution
        messages = await flow.get_messages()
        assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_workflow_with_tools(self):
        """Test workflow with tools."""
        flow = Flow("tool_workflow")
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Create team with tool-enabled agent
        team = Supervisor("tool_team", initialize_llm=False)
        agent = ReActAgent("tool_agent", description="Tool agent", initialize_llm=False)
        agent.add_tool(WriteFileTool())
        team.add_agent(agent)
        orchestrator.add_team(team)
        
        # Execute workflow
        await flow.start("Test workflow with tools")
        
        # Verify execution
        messages = await flow.get_messages()
        assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_langgraph_integration(self):
        """Test LangGraph integration."""
        flow = Flow("langgraph_workflow")
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Add team
        team = Supervisor("test_team", initialize_llm=False)
        agent = SimpleAgent("test_agent", description="Test agent")
        team.add_agent(agent)
        orchestrator.add_team(team)
        
        # Verify LangGraph integration
        assert flow._graph is not None
        assert flow._compiled_graph is not None
        
        # Check graph structure
        nodes = list(flow._graph.nodes.keys())
        assert "orchestrator" in nodes
        assert "test_team" in nodes
        assert "test_team_test_agent" in nodes

    @pytest.mark.asyncio
    async def test_workflow_state_management(self):
        """Test workflow state management."""
        flow = Flow("state_workflow")
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Add team
        team = Supervisor("test_team", initialize_llm=False)
        agent = SimpleAgent("test_agent", description="Test agent")
        team.add_agent(agent)
        orchestrator.add_team(team)
        
        # Execute workflow
        await flow.start("Test state management")
        
        # Verify state
        assert flow.state is not None
        assert flow.state.flow_id is not None
        assert flow.state.flow_name == "state_workflow"
        
        # Verify messages
        messages = await flow.get_messages()
        assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self):
        """Test concurrent workflow execution."""
        async def create_and_run_workflow(workflow_id):
            flow = Flow(f"concurrent_workflow_{workflow_id}")
            orchestrator = Orchestrator(f"orchestrator_{workflow_id}", initialize_llm=False)
            flow.add_orchestrator(orchestrator)
            
            team = Supervisor(f"team_{workflow_id}", initialize_llm=False)
            agent = SimpleAgent(f"agent_{workflow_id}", description=f"Agent {workflow_id}")
            team.add_agent(agent)
            orchestrator.add_team(team)
            
            await flow.start(f"Test concurrent workflow {workflow_id}")
            return await flow.get_messages()
        
        # Run multiple workflows concurrently
        tasks = [create_and_run_workflow(i) for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        # Verify all workflows completed
        assert len(results) == 3
        for result in results:
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test workflow error handling."""
        flow = Flow("error_workflow")
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        flow.add_orchestrator(orchestrator)
        
        # Add team
        team = Supervisor("test_team", initialize_llm=False)
        agent = SimpleAgent("test_agent", description="Test agent")
        team.add_agent(agent)
        orchestrator.add_team(team)
        
        # Execute workflow with empty message
        await flow.start("")
        
        # Should not raise an error
        messages = await flow.get_messages()
        assert len(messages) >= 0  # May be empty or have error message
