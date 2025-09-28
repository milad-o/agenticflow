"""Simple observability tests without API dependencies."""

import asyncio
import os
import tempfile
from pathlib import Path
import pytest
from agenticflow import (
    Flow, Agent, Team, EventLogger, ConsoleSubscriber, FileSubscriber, MetricsCollector,
    FlowStarted, FlowCompleted, AgentStarted, AgentCompleted, CustomEvent
)


class TestObservabilityBasic:
    """Basic observability tests without API calls."""
    
    def test_event_creation(self):
        """Test creating events."""
        event = FlowStarted(
            flow_id="test-flow",
            flow_name="Test Flow",
            message="Test message"
        )
        assert event.event_type == "flow_started"
        assert event.flow_id == "test-flow"
        assert event.data["flow_name"] == "Test Flow"
    
    def test_event_to_dict(self):
        """Test event serialization."""
        event = FlowStarted(
            flow_id="test-flow",
            flow_name="Test Flow",
            message="Test message"
        )
        data = event.to_dict()
        assert "event_id" in data
        assert "timestamp" in data
        assert data["event_type"] == "flow_started"
        assert data["flow_id"] == "test-flow"
    
    def test_event_logger_creation(self):
        """Test creating event logger."""
        logger = EventLogger(persistent=False)
        assert logger.persistent == False
        assert len(logger._events) == 0
    
    def test_event_logger_persistent(self):
        """Test creating persistent event logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            logger = EventLogger(persistent=True, db_path=db_path)
            assert logger.persistent == True
            assert logger.db_path == db_path
    
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
    
    def test_flow_observability_enable(self):
        """Test enabling observability on flow."""
        flow = Flow("test_flow")
        assert flow._observability_enabled == False
        
        flow.enable_observability(console_output=False, file_logging=False)
        assert flow._observability_enabled == True
        assert flow._event_logger is not None
    
    def test_flow_observability_disable(self):
        """Test disabling observability on flow."""
        flow = Flow("test_flow")
        flow.enable_observability()
        assert flow._observability_enabled == True
        
        flow.disable_observability()
        assert flow._observability_enabled == False
        assert flow._event_logger is None
    
    def test_flow_custom_event_emission(self):
        """Test emitting custom events."""
        flow = Flow("test_flow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        # Set flow_id
        flow._flow_id = "test-flow-id"
        
        # Emit custom event
        flow.emit_custom_event("test_event", {"data": "test"})
        
        # Check that event was emitted
        events = flow._event_logger.get_events(event_type="custom_event")
        assert len(events) >= 1  # Should have at least one custom event
    
    def test_flow_metrics(self):
        """Test getting flow metrics."""
        flow = Flow("test_flow")
        
        # Should return error if observability not enabled
        metrics = flow.get_metrics()
        assert "error" in metrics
        
        # Enable observability and test
        flow.enable_observability(console_output=False, file_logging=False)
        metrics = flow.get_metrics()
        assert "total_events" in metrics
    
    def test_agent_observability_setup(self):
        """Test setting observability on agent."""
        agent = Agent("test_agent", tools=[], description="Test agent")
        assert agent._flow_id is None
        assert agent._event_logger is None
        
        logger = EventLogger(persistent=False)
        agent.set_observability("test-flow-id", logger)
        
        assert agent._flow_id == "test-flow-id"
        assert agent._event_logger == logger
    
    def test_event_logger_get_events(self):
        """Test getting events from logger."""
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
    
    def test_event_logger_metrics(self):
        """Test getting metrics from logger."""
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
    
    def test_event_export(self):
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
                import json
                data = json.load(f)
                assert len(data) == 2
                assert data[0]["event_type"] == "flow_started"


class TestObservabilityIntegration:
    """Integration tests without API calls."""
    
    def test_flow_with_observability_no_api(self):
        """Test flow setup with observability (no API calls)."""
        flow = Flow("test_flow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        # Create agent without tools to avoid API calls
        agent = Agent("test_agent", tools=[], description="Test agent")
        flow.add_agent(agent)
        
        # Test that observability context is set
        assert agent._flow_id is not None
        assert agent._event_logger is not None
        
        # Test custom event emission
        flow.emit_custom_event("test_event", {"data": "test"})
        
        # Check that events were logged
        events = flow._event_logger.get_events()
        assert len(events) > 0
        
        # Check for custom event
        custom_events = [e for e in events if e.event_type == "custom_event"]
        assert len(custom_events) > 0
    
    def test_team_with_observability_no_api(self):
        """Test team setup with observability (no API calls)."""
        flow = Flow("test_flow")
        flow.enable_observability(console_output=False, file_logging=False)
        
        team = Team("test_team")
        agent = Agent("test_agent", tools=[], description="Test agent")
        team.add_agent(agent)
        flow.add_team(team)
        
        # Test that observability context is set
        assert agent._flow_id is not None
        assert agent._event_logger is not None
        
        # Test custom event emission
        flow.emit_custom_event("team_event", {"team": "test_team"})
        
        # Check that events were logged
        events = flow._event_logger.get_events()
        assert len(events) > 0


if __name__ == "__main__":
    # Run basic tests
    print("Running simple observability tests...")
    
    # Test event creation
    event = FlowStarted(flow_id="test", flow_name="Test", message="Test")
    assert event.event_type == "flow_started"
    print("✅ Event creation test passed")
    
    # Test logger creation
    logger = EventLogger(persistent=False)
    assert len(logger._events) == 0
    print("✅ Logger creation test passed")
    
    # Test flow observability
    flow = Flow("test_flow")
    flow.enable_observability(console_output=False)
    assert flow._observability_enabled == True
    print("✅ Flow observability test passed")
    
    print("All simple tests passed!")
