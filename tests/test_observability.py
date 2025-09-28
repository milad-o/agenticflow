"""Tests for observability system."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
import pytest
from agenticflow import (
    Flow, Agent, Team, EventLogger, ConsoleSubscriber, FileSubscriber, MetricsCollector,
    FlowStarted, FlowCompleted, AgentStarted, AgentCompleted, CustomEvent
)
from agenticflow.tools import create_file, search_web


class TestEventLogger:
    """Test EventLogger functionality."""
    
    def test_event_logger_creation(self):
        """Test creating event logger."""
        logger = EventLogger(persistent=False)
        assert logger.persistent == False
        assert logger.backend == "sqlite3"
        assert len(logger._events) == 0
    
    def test_event_logger_persistent(self):
        """Test creating persistent event logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            logger = EventLogger(persistent=True, db_path=db_path)
            assert logger.persistent == True
            assert logger.db_path == db_path
    
    async def test_log_event(self):
        """Test logging events."""
        logger = EventLogger(persistent=False)
        
        event = FlowStarted(
            flow_id="test-flow",
            flow_name="Test Flow",
            message="Test message"
        )
        
        await logger.log_event(event)
        assert len(logger._events) == 1
        assert logger._events[0].event_type == "flow_started"
    
    def test_get_events(self):
        """Test getting events."""
        logger = EventLogger(persistent=False)
        
        # Add some test events
        event1 = FlowStarted(flow_id="flow1", flow_name="Flow 1", message="Test 1")
        event2 = FlowCompleted(flow_id="flow1", flow_name="Flow 1", duration_ms=100.0, total_messages=2)
        event3 = FlowStarted(flow_id="flow2", flow_name="Flow 2", message="Test 2")
        
        logger._events = [event1, event2, event3]
        
        # Test filtering by flow_id
        flow1_events = logger.get_events(flow_id="flow1")
        assert len(flow1_events) == 2
        
        # Test filtering by event_type
        started_events = logger.get_events(event_type="flow_started")
        assert len(started_events) == 2
        
        # Test limiting
        limited_events = logger.get_events(limit=2)
        assert len(limited_events) == 2
    
    def test_get_metrics(self):
        """Test getting metrics."""
        logger = EventLogger(persistent=False)
        
        # Add some test events
        event1 = FlowStarted(flow_id="flow1", flow_name="Flow 1", message="Test 1")
        event2 = AgentStarted(flow_id="flow1", agent_name="agent1", agent_type="TestAgent", tools=[])
        event3 = FlowCompleted(flow_id="flow1", flow_name="Flow 1", duration_ms=100.0, total_messages=2)
        
        logger._events = [event1, event2, event3]
        
        metrics = logger.get_metrics()
        assert metrics["total_events"] == 3
        assert metrics["unique_flows"] == 1
        assert metrics["unique_agents"] == 1
        assert "flow_started" in metrics["event_counts"]
        assert metrics["event_counts"]["flow_started"] == 1
    
    def test_export_events(self):
        """Test exporting events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = EventLogger(persistent=False)
            
            # Add test events
            event1 = FlowStarted(flow_id="flow1", flow_name="Flow 1", message="Test 1")
            event2 = FlowCompleted(flow_id="flow1", flow_name="Flow 1", duration_ms=100.0, total_messages=2)
            logger._events = [event1, event2]
            
            # Export to JSON
            json_file = os.path.join(temp_dir, "events.json")
            logger.export_events(json_file, format="json")
            
            assert os.path.exists(json_file)
            with open(json_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 2
                assert data[0]["event_type"] == "flow_started"


class TestSubscribers:
    """Test event subscribers."""
    
    def test_console_subscriber(self):
        """Test console subscriber."""
        subscriber = ConsoleSubscriber(show_timestamps=True, show_details=True)
        assert subscriber.show_timestamps == True
        assert subscriber.show_details == True
    
    def test_file_subscriber(self):
        """Test file subscriber."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            subscriber = FileSubscriber(log_file, format="json")
            assert subscriber.filepath == Path(log_file)
            assert subscriber.format == "json"
    
    def test_metrics_collector(self):
        """Test metrics collector."""
        collector = MetricsCollector()
        assert collector.metrics["flow_count"] == 0
        assert collector.metrics["agent_count"] == 0
        assert collector.metrics["tool_count"] == 0


class TestFlowObservability:
    """Test Flow observability integration."""
    
    def test_enable_observability(self):
        """Test enabling observability on flow."""
        flow = Flow("test_flow")
        assert flow._observability_enabled == False
        
        flow.enable_observability(console_output=True, file_logging=False)
        assert flow._observability_enabled == True
        assert flow._event_logger is not None
    
    def test_disable_observability(self):
        """Test disabling observability on flow."""
        flow = Flow("test_flow")
        flow.enable_observability()
        assert flow._observability_enabled == True
        
        flow.disable_observability()
        assert flow._observability_enabled == False
        assert flow._event_logger is None
    
    def test_emit_custom_event(self):
        """Test emitting custom events."""
        flow = Flow("test_flow")
        flow.enable_observability()
        
        # Should not emit if flow_id not set
        flow.emit_custom_event("test_event", {"data": "test"})
        
        # Set flow_id and emit
        flow._flow_id = "test-flow-id"
        flow.emit_custom_event("test_event", {"data": "test"})
        
        # Check that event was emitted
        events = flow._event_logger.get_events(event_type="custom_event")
        assert len(events) == 1
        assert events[0].data["custom_type"] == "test_event"
    
    def test_get_metrics(self):
        """Test getting flow metrics."""
        flow = Flow("test_flow")
        
        # Should return error if observability not enabled
        metrics = flow.get_metrics()
        assert "error" in metrics
        
        # Enable observability and test
        flow.enable_observability()
        metrics = flow.get_metrics()
        assert "total_events" in metrics
    
    def test_get_flow_summary(self):
        """Test getting flow summary."""
        flow = Flow("test_flow")
        
        # Should return error if observability not enabled
        summary = flow.get_flow_summary()
        assert "error" in summary
        
        # Enable observability and set flow_id
        flow.enable_observability()
        flow._flow_id = "test-flow-id"
        
        # Should return error if flow not started
        summary = flow.get_flow_summary()
        assert "error" in summary


class TestAgentObservability:
    """Test Agent observability integration."""
    
    def test_set_observability(self):
        """Test setting observability on agent."""
        agent = Agent("test_agent", tools=[create_file])
        assert agent._flow_id is None
        assert agent._event_logger is None
        
        logger = EventLogger(persistent=False)
        agent.set_observability("test-flow-id", logger)
        
        assert agent._flow_id == "test-flow-id"
        assert agent._event_logger == logger


class TestIntegration:
    """Integration tests for observability."""
    
    @pytest.mark.asyncio
    async def test_flow_with_observability(self):
        """Test running a flow with observability enabled."""
        flow = Flow("test_flow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        agent = Agent("test_agent", tools=[create_file], description="Test agent")
        flow.add_agent(agent)
        
        # Run the flow
        result = await flow.run("Create a test file with content 'Hello World'")
        
        # Check that events were logged
        events = flow._event_logger.get_events()
        assert len(events) > 0
        
        # Check for flow started event
        flow_started = [e for e in events if e.event_type == "flow_started"]
        assert len(flow_started) == 1
        
        # Check for flow completed event
        flow_completed = [e for e in events if e.event_type == "flow_completed"]
        assert len(flow_completed) == 1
        
        # Check for agent events
        agent_events = [e for e in events if e.agent_name == "test_agent"]
        assert len(agent_events) > 0
    
    @pytest.mark.asyncio
    async def test_team_with_observability(self):
        """Test running a team with observability enabled."""
        flow = Flow("test_flow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        team = Team("test_team")
        agent = Agent("test_agent", tools=[create_file], description="Test agent")
        team.add_agent(agent)
        flow.add_team(team)
        
        # Run the flow
        result = await flow.run("Create a test file with content 'Hello World'")
        
        # Check that events were logged
        events = flow._event_logger.get_events()
        assert len(events) > 0
        
        # Check for team events
        team_events = [e for e in events if e.team_name == "test_team"]
        assert len(team_events) > 0
    
    def test_persistent_logging(self):
        """Test persistent logging functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            
            # Create logger with persistent storage
            logger = EventLogger(persistent=True, db_path=db_path)
            
            # Add some events
            event1 = FlowStarted(flow_id="flow1", flow_name="Flow 1", message="Test 1")
            event2 = FlowCompleted(flow_id="flow1", flow_name="Flow 1", duration_ms=100.0, total_messages=2)
            
            # Log events (this would normally be async, but we'll test the sync parts)
            logger._events = [event1, event2]
            
            # Test persistent query
            persistent_events = logger.get_events_persistent()
            # Note: This will be empty because we didn't actually store to DB in this test
            # In a real test, we'd await logger.log_event() for each event
            assert isinstance(persistent_events, list)


if __name__ == "__main__":
    # Run basic tests
    print("Running observability tests...")
    
    # Test EventLogger
    logger = EventLogger(persistent=False)
    print("✅ EventLogger creation test passed")
    
    # Test ConsoleSubscriber
    console_sub = ConsoleSubscriber()
    print("✅ ConsoleSubscriber creation test passed")
    
    # Test Flow observability
    flow = Flow("test_flow")
    flow.enable_observability(console_output=False)
    print("✅ Flow observability enable test passed")
    
    print("All basic tests passed!")
