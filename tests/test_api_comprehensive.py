"""Comprehensive API tests for AgenticFlow."""

import asyncio
import os
import tempfile
from pathlib import Path
import pytest
from agenticflow import (
    Flow, Agent, Team, 
    FilesystemAgent, PythonAgent, ExcelAgent, DataAgent, SSISAnalysisAgent,
    create_file, search_web, read_file, list_directory,
    EventLogger, ConsoleSubscriber, FileSubscriber, MetricsCollector
)
from agenticflow.tools import (
    parse_dtsx_file, extract_data_flows, extract_connections,
    extract_tasks, extract_variables, create_package_summary,
    search_package_content
)


class TestCoreAPI:
    """Test core API functionality."""
    
    def test_flow_creation(self):
        """Test Flow creation and basic properties."""
        flow = Flow("test_flow")
        assert flow.name == "test_flow"
        assert len(flow.teams) == 0
        assert len(flow.agents) == 0
        assert flow._graph is None
    
    def test_agent_creation(self):
        """Test Agent creation and basic properties."""
        agent = Agent("test_agent", tools=[create_file], description="Test agent")
        assert agent.name == "test_agent"
        assert len(agent.tools) == 1
        assert agent.description == "Test agent"
        assert agent._react_agent is not None
    
    def test_team_creation(self):
        """Test Team creation and basic properties."""
        team = Team("test_team")
        assert team.name == "test_team"
        assert len(team.agents) == 0
    
    def test_flow_add_agent(self):
        """Test adding agents to flow."""
        flow = Flow("test_flow")
        agent = Agent("test_agent", tools=[create_file])
        
        flow.add_agent(agent)
        assert len(flow.agents) == 1
        assert "test_agent" in flow.agents
        assert flow.agents["test_agent"] == agent
    
    def test_flow_add_team(self):
        """Test adding teams to flow."""
        flow = Flow("test_flow")
        team = Team("test_team")
        
        flow.add_team(team)
        assert len(flow.teams) == 1
        assert "test_team" in flow.teams
        assert flow.teams["test_team"] == team
    
    def test_team_add_agent(self):
        """Test adding agents to team."""
        team = Team("test_team")
        agent = Agent("test_agent", tools=[create_file])
        
        team.add_agent(agent)
        assert len(team.agents) == 1
        assert "test_agent" in team.agents
        assert team.agents["test_agent"] == agent
    
    def test_flow_build_graph(self):
        """Test building flow graph."""
        flow = Flow("test_flow")
        agent = Agent("test_agent", tools=[create_file])
        flow.add_agent(agent)
        
        graph = flow.build_graph()
        assert graph is not None
        assert flow._graph == graph
    
    def test_flow_build_graph_no_agents(self):
        """Test building flow graph with no agents raises error."""
        flow = Flow("test_flow")
        
        with pytest.raises(ValueError, match="No teams or agents added to flow"):
            flow.build_graph()


class TestSpecializedAgents:
    """Test specialized agent functionality."""
    
    def test_filesystem_agent_creation(self):
        """Test FilesystemAgent creation."""
        agent = FilesystemAgent("fs_agent")
        assert agent.name == "fs_agent"
        assert len(agent.tools) > 0
        assert any("create_file" in str(tool) for tool in agent.tools)
    
    def test_python_agent_creation(self):
        """Test PythonAgent creation."""
        agent = PythonAgent("py_agent")
        assert agent.name == "py_agent"
        assert len(agent.tools) > 0
        assert any("execute" in str(tool) for tool in agent.tools)
    
    def test_excel_agent_creation(self):
        """Test ExcelAgent creation."""
        agent = ExcelAgent("excel_agent")
        assert agent.name == "excel_agent"
        assert len(agent.tools) > 0
        assert any("excel" in str(tool) for tool in agent.tools)
    
    def test_data_agent_creation(self):
        """Test DataAgent creation."""
        agent = DataAgent("data_agent")
        assert agent.name == "data_agent"
        assert len(agent.tools) > 0
        assert any("json" in str(tool) for tool in agent.tools)
    
    def test_ssis_agent_creation(self):
        """Test SSISAnalysisAgent creation."""
        agent = SSISAnalysisAgent("ssis_agent")
        assert agent.name == "ssis_agent"
        assert len(agent.tools) > 0
        assert any("dtsx" in str(tool) for tool in agent.tools)


class TestToolsAPI:
    """Test tools API functionality."""
    
    def test_basic_tools_import(self):
        """Test that basic tools can be imported."""
        from agenticflow.tools import create_file, search_web, read_file, list_directory
        assert create_file is not None
        assert search_web is not None
        assert read_file is not None
        assert list_directory is not None
    
    def test_ssis_tools_import(self):
        """Test that SSIS tools can be imported."""
        from agenticflow.tools import (
            parse_dtsx_file, extract_data_flows, extract_connections,
            extract_tasks, extract_variables, create_package_summary,
            search_package_content
        )
        assert parse_dtsx_file is not None
        assert extract_data_flows is not None
        assert extract_connections is not None
        assert extract_tasks is not None
        assert extract_variables is not None
        assert create_package_summary is not None
        assert search_package_content is not None


class TestObservabilityAPI:
    """Test observability API functionality."""
    
    def test_observability_imports(self):
        """Test that observability components can be imported."""
        from agenticflow.observability import (
            EventLogger, ConsoleSubscriber, FileSubscriber, MetricsCollector,
            FlowStarted, FlowCompleted, AgentStarted, AgentCompleted,
            CustomEvent
        )
        assert EventLogger is not None
        assert ConsoleSubscriber is not None
        assert FileSubscriber is not None
        assert MetricsCollector is not None
        assert FlowStarted is not None
        assert FlowCompleted is not None
        assert AgentStarted is not None
        assert AgentCompleted is not None
        assert CustomEvent is not None
    
    def test_flow_observability_methods(self):
        """Test Flow observability methods."""
        flow = Flow("test_flow")
        
        # Test enable_observability
        flow.enable_observability(console_output=False, file_logging=False)
        assert flow._observability_enabled == True
        assert flow._event_logger is not None
        
        # Test disable_observability
        flow.disable_observability()
        assert flow._observability_enabled == False
        assert flow._event_logger is None
        
        # Test emit_custom_event (should not error when disabled)
        flow.emit_custom_event("test", {"data": "test"})
        
        # Test get_metrics (should return error when disabled)
        metrics = flow.get_metrics()
        assert "error" in metrics
        
        # Test get_flow_summary (should return error when disabled)
        summary = flow.get_flow_summary()
        assert "error" in summary


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_simple_workflow(self):
        """Test a simple workflow with direct agents."""
        flow = Flow("simple_workflow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        # Create agents
        researcher = Agent("researcher", tools=[search_web], description="Researcher")
        writer = Agent("writer", tools=[create_file], description="Writer")
        
        # Add agents to flow
        flow.add_agent(researcher)
        flow.add_agent(writer)
        
        # Run workflow
        result = await flow.run("Research AI trends and create a simple report")
        
        # Verify result
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        # Verify observability
        events = flow._event_logger.get_events()
        assert len(events) > 0
        
        # Check for flow events
        flow_events = [e for e in events if e.event_type in ["flow_started", "flow_completed"]]
        assert len(flow_events) >= 2
    
    @pytest.mark.asyncio
    async def test_team_workflow(self):
        """Test a workflow with teams."""
        flow = Flow("team_workflow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        # Create teams
        research_team = Team("research_team")
        writing_team = Team("writing_team")
        
        # Add agents to teams
        research_team.add_agent(Agent("researcher", tools=[search_web], description="Researcher"))
        writing_team.add_agent(Agent("writer", tools=[create_file], description="Writer"))
        
        # Add teams to flow
        flow.add_team(research_team)
        flow.add_team(writing_team)
        
        # Run workflow
        result = await flow.run("Research AI trends and create a simple report")
        
        # Verify result
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        # Verify observability
        events = flow._event_logger.get_events()
        assert len(events) > 0
    
    @pytest.mark.asyncio
    async def test_specialized_agent_workflow(self):
        """Test workflow with specialized agents."""
        flow = Flow("specialized_workflow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        # Create specialized agents
        fs_agent = FilesystemAgent("file_manager")
        py_agent = PythonAgent("code_analyst")
        
        # Add agents to flow
        flow.add_agent(fs_agent)
        flow.add_agent(py_agent)
        
        # Run workflow
        result = await flow.run("Create a Python script that calculates fibonacci numbers")
        
        # Verify result
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        # Verify observability
        events = flow._event_logger.get_events()
        assert len(events) > 0
        
        # Check for agent events
        agent_events = [e for e in events if e.agent_name in ["file_manager", "code_analyst"]]
        assert len(agent_events) > 0
    
    @pytest.mark.asyncio
    async def test_ssis_analysis_workflow(self):
        """Test SSIS analysis workflow."""
        flow = Flow("ssis_workflow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        # Create SSIS agent
        ssis_agent = SSISAnalysisAgent("ssis_analyst")
        flow.add_agent(ssis_agent)
        
        # Create a sample DTSX file for testing
        sample_dtsx = """<?xml version="1.0"?>
        <DTS:Executable xmlns:DTS="www.microsoft.com/SqlServer/Dts"
            DTS:refId="Package"
            DTS:CreationName="Microsoft.Package"
            DTS:ObjectName="TestPackage">
            <DTS:ConnectionManagers>
                <DTS:ConnectionManager
                    DTS:refId="Package.ConnectionManagers[TestConn]"
                    DTS:CreationName="OLEDB"
                    DTS:ObjectName="TestConn">
                </DTS:ConnectionManager>
            </DTS:ConnectionManagers>
        </DTS:Executable>"""
        
        # Write sample file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write(sample_dtsx)
            temp_file = f.name
        
        try:
            # Run workflow
            result = await flow.run(f"Analyze the SSIS package at {temp_file}")
            
            # Verify result
            assert "messages" in result
            assert len(result["messages"]) > 0
            
            # Verify observability
            events = flow._event_logger.get_events()
            assert len(events) > 0
            
        finally:
            # Clean up
            os.unlink(temp_file)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_flow_with_invalid_message(self):
        """Test flow behavior with invalid message."""
        flow = Flow("error_test_flow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        agent = Agent("test_agent", tools=[create_file])
        flow.add_agent(agent)
        
        # This should not raise an exception
        result = await flow.run("")
        assert "messages" in result
    
    def test_flow_with_no_agents(self):
        """Test flow behavior with no agents."""
        flow = Flow("empty_flow")
        
        with pytest.raises(ValueError):
            flow.build_graph()
    
    def test_agent_with_no_tools(self):
        """Test agent behavior with no tools."""
        agent = Agent("no_tools_agent", tools=[])
        assert agent._react_agent is None
        assert len(agent.tools) == 0


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_flow_execution_time(self):
        """Test flow execution time."""
        import time
        
        flow = Flow("perf_test_flow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        agent = Agent("perf_agent", tools=[create_file])
        flow.add_agent(agent)
        
        start_time = time.time()
        result = await flow.run("Create a simple test file")
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 30.0  # Should complete within 30 seconds
        
        # Check that observability captured timing
        events = flow._event_logger.get_events()
        flow_completed = [e for e in events if e.event_type == "flow_completed"]
        if flow_completed:
            assert flow_completed[0].data["duration_ms"] > 0


if __name__ == "__main__":
    # Run basic tests
    print("Running comprehensive API tests...")
    
    # Test core API
    flow = Flow("test_flow")
    agent = Agent("test_agent", tools=[create_file])
    team = Team("test_team")
    print("✅ Core API creation tests passed")
    
    # Test specialized agents
    fs_agent = FilesystemAgent("fs_agent")
    py_agent = PythonAgent("py_agent")
    excel_agent = ExcelAgent("excel_agent")
    data_agent = DataAgent("data_agent")
    ssis_agent = SSISAnalysisAgent("ssis_agent")
    print("✅ Specialized agents creation tests passed")
    
    # Test observability
    flow.enable_observability(console_output=False)
    print("✅ Observability enable test passed")
    
    # Test tools import
    from agenticflow.tools import create_file, search_web
    print("✅ Tools import test passed")
    
    print("All basic API tests passed!")
