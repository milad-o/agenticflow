#!/usr/bin/env python3
"""
Comprehensive tests for ITC streaming and background functionality.
Tests both foreground demo patterns and background automatic streaming.
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from agenticflow.core.itc import (
    ITCManager, ITCConfig, ITCEventType, InterruptedError,
    get_itc_manager, initialize_itc
)
from agenticflow import Agent, AgentConfig, LLMProviderConfig, LLMProvider


class TestITCStreaming:
    """Test suite for ITC streaming functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        # Reset global ITC manager
        import agenticflow.core.itc as itc_module
        itc_module._itc_manager = None
        
        # Initialize with streaming enabled
        self.config = ITCConfig(
            enable_streaming=True,
            stream_interval=0.1,  # Fast for testing
            enable_agent_coordination=True,
            coordination_timeout=5
        )
        self.itc = initialize_itc(self.config)
    
    def teardown_method(self):
        """Cleanup after each test."""
        if self.itc._background_streaming_task:
            self.itc._background_streaming_task.cancel()
    
    @pytest.mark.asyncio
    async def test_coordinator_connection(self):
        """Test coordinator connection and disconnection."""
        coordinator_id = "test_coordinator"
        
        # Connect coordinator
        coordinator = await self.itc.connect_coordinator(
            coordinator_id=coordinator_id,
            coordinator_type="agent",
            capabilities={"streaming": True}
        )
        
        assert coordinator.coordinator_id == coordinator_id
        assert coordinator.coordinator_type == "agent"
        assert coordinator_id in self.itc._connected_coordinators
        assert coordinator_id in self.itc._stream_queues
        
        # Check background monitoring is enabled
        assert self.itc._background_monitoring_enabled
        assert self.itc._background_streaming_task is not None
        
        # Disconnect coordinator
        success = await self.itc.disconnect_coordinator(coordinator_id)
        assert success
        assert coordinator_id not in self.itc._connected_coordinators
        assert coordinator_id not in self.itc._stream_queues
    
    @pytest.mark.asyncio
    async def test_stream_subscription(self):
        """Test stream subscription creation and cancellation."""
        coordinator_id = "test_coordinator"
        
        # Connect coordinator first
        await self.itc.connect_coordinator(coordinator_id, "agent")
        
        # Create subscription
        subscription_id = self.itc.create_stream_subscription(
            coordinator_id=coordinator_id,
            event_types={ITCEventType.TASK_PROGRESS, ITCEventType.REAL_TIME_UPDATE}
        )
        
        assert subscription_id in self.itc._stream_subscriptions
        subscription = self.itc._stream_subscriptions[subscription_id]
        assert subscription.subscriber_id == coordinator_id
        assert ITCEventType.TASK_PROGRESS in subscription.event_types
        
        # Cancel subscription
        success = self.itc.cancel_stream_subscription(subscription_id)
        assert success
        assert subscription_id not in self.itc._stream_subscriptions
    
    @pytest.mark.asyncio
    async def test_real_time_updates(self):
        """Test real-time update sending and receiving."""
        coordinator_id = "test_coordinator"
        task_id = "test_task"
        agent_id = "test_agent"
        
        # Setup coordinator and subscription
        await self.itc.connect_coordinator(coordinator_id, "agent")
        subscription_id = self.itc.create_stream_subscription(
            coordinator_id=coordinator_id,
            event_types={ITCEventType.REAL_TIME_UPDATE}
        )
        
        # Send real-time update
        update_data = {"test": "data", "update_type": "test"}
        await self.itc.send_real_time_update(
            update_data=update_data,
            task_id=task_id,
            agent_id=agent_id
        )
        
        # Check if update was queued
        queue = self.itc._stream_queues[coordinator_id]
        assert not queue.empty()
        
        # Get the update
        update = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert update["type"] == "real_time_update"
        assert update["task_id"] == task_id
        assert update["agent_id"] == agent_id
        assert update["data"] == update_data
    
    @pytest.mark.asyncio
    async def test_task_coordination(self):
        """Test task coordination functionality."""
        coordinator_id = "coordinator"
        task_id = "test_task"
        agent_id = "test_agent"
        
        # Connect coordinator
        await self.itc.connect_coordinator(coordinator_id, "coordinator_agent")
        
        # Start a task
        task = await self.itc.start_task(task_id, "Test task", agent_id)
        assert task.task_id == task_id
        
        # Coordinate the task
        coordination_data = {"action": "boost_priority", "level": "high"}
        result = await self.itc.coordinate_task(
            task_id=task_id,
            coordinator_id=coordinator_id,
            coordination_data=coordination_data
        )
        
        assert result["success"] is True
        assert result["task_id"] == task_id
        assert result["coordinator_id"] == coordinator_id
        
        # Check task was updated
        updated_task = self.itc.active_tasks[task_id]
        assert updated_task.controlling_coordinator == coordinator_id
        assert updated_task.metadata["action"] == "boost_priority"
    
    @pytest.mark.asyncio
    async def test_background_monitoring(self):
        """Test background monitoring and automatic updates."""
        coordinator_id = "background_coordinator"
        task_id = "background_task"
        agent_id = "background_agent"
        
        # Setup coordinator and subscription
        await self.itc.connect_coordinator(coordinator_id, "agent")
        subscription_id = self.itc.create_stream_subscription(
            coordinator_id=coordinator_id,
            event_types={ITCEventType.REAL_TIME_UPDATE}
        )
        
        # Start a task
        task = await self.itc.start_task(task_id, "Background test", agent_id)
        
        # Set last update time to past to trigger background update
        from datetime import timedelta
        past_time = datetime.now(timezone.utc) - timedelta(seconds=10)
        task.last_stream_update = past_time
        
        # Manually trigger background processing
        await self.itc._process_background_updates()
        
        # Check if background update was sent
        queue = self.itc._stream_queues[coordinator_id]
        update = await asyncio.wait_for(queue.get(), timeout=1.0)
        
        assert update["type"] == "real_time_update"
        assert update["data"]["update_type"] == "background_status"
        assert update["data"]["background"] is True
    
    @pytest.mark.asyncio
    async def test_stream_with_filtering(self):
        """Test stream filtering by task and agent."""
        coordinator_id = "filter_coordinator"
        task_id_1 = "task_1"
        task_id_2 = "task_2"
        agent_id = "test_agent"
        
        # Connect coordinator
        await self.itc.connect_coordinator(coordinator_id, "agent")
        
        # Create subscription for specific task
        subscription_id = self.itc.create_stream_subscription(
            coordinator_id=coordinator_id,
            task_id=task_id_1,  # Only subscribe to task_1
            event_types={ITCEventType.REAL_TIME_UPDATE}
        )
        
        # Send update for task_1 (should be received)
        await self.itc.send_real_time_update(
            update_data={"message": "task_1_update"},
            task_id=task_id_1,
            agent_id=agent_id
        )
        
        # Send update for task_2 (should be filtered out)
        await self.itc.send_real_time_update(
            update_data={"message": "task_2_update"},
            task_id=task_id_2,
            agent_id=agent_id
        )
        
        # Should only receive task_1 update
        queue = self.itc._stream_queues[coordinator_id]
        update = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert update["task_id"] == task_id_1
        assert update["data"]["message"] == "task_1_update"
        
        # Queue should be empty (task_2 update filtered)
        assert queue.empty()


class TestAgentStreamingIntegration:
    """Test Agent integration with ITC streaming."""
    
    def setup_method(self):
        """Setup for each test."""
        import agenticflow.core.itc as itc_module
        itc_module._itc_manager = None
        
        # Initialize ITC with streaming
        config = ITCConfig(enable_streaming=True, stream_interval=0.1)
        initialize_itc(config)
    
    @pytest.mark.asyncio
    async def test_agent_auto_connection(self):
        """Test that agents automatically connect to ITC when streaming is enabled."""
        agent_config = AgentConfig(
            name="StreamingAgent",
            instructions="Test agent for streaming",
            llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
        )
        
        # Mock LLM provider initialization
        with patch('agenticflow.llm_providers.get_llm_manager') as mock_llm_manager:
            mock_manager = MagicMock()
            mock_manager.initialize_provider = AsyncMock()
            mock_manager.get_provider = MagicMock()
            mock_llm_manager.return_value = mock_manager
            
            agent = Agent(agent_config)
            await agent.start()
            
            itc = get_itc_manager()
            
            # Check agent is registered and connected
            assert agent.id in itc._agents
            assert agent.id in itc._connected_coordinators
            
            # Check capabilities
            coordinator = itc._connected_coordinators[agent.id]
            assert coordinator.capabilities.get("streaming") is True
            assert coordinator.capabilities.get("background_monitoring") is True
            
            await agent.stop()
    
    @pytest.mark.asyncio 
    async def test_agent_task_streaming(self):
        """Test that agent tasks automatically stream progress."""
        agent_config = AgentConfig(
            name="TaskAgent",
            instructions="Test agent",
            llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
        )
        
        with patch('agenticflow.llm_providers.get_llm_manager') as mock_llm_manager:
            # Mock LLM responses
            mock_provider = MagicMock()
            mock_provider.agenerate = AsyncMock(return_value="Test response")
            mock_manager = MagicMock()
            mock_manager.initialize_provider = AsyncMock()
            mock_manager.get_provider = MagicMock(return_value=mock_provider)
            mock_llm_manager.return_value = mock_manager
            
            agent = Agent(agent_config)
            await agent.start()
            
            itc = get_itc_manager()
            
            # Create another coordinator to watch the agent's tasks
            watcher_id = "watcher"
            await itc.connect_coordinator(watcher_id, "watcher")
            subscription_id = itc.create_stream_subscription(
                coordinator_id=watcher_id,
                agent_id=agent.id,
                event_types={ITCEventType.TASK_STARTED, ITCEventType.TASK_COMPLETED}
            )
            
            # Execute a task (this should create streaming updates)
            task_result = await agent.execute_task("Test task")
            
            # Check that task events were streamed
            queue = itc._stream_queues[watcher_id]
            
            # Should have received task started event
            start_event = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert "task_started" in start_event.get("type", "").lower() or start_event.get("data", {}).get("description") == "Test task"
            
            await agent.stop()


class TestStreamingPerformance:
    """Performance tests for streaming functionality."""
    
    def setup_method(self):
        """Setup for performance tests."""
        import agenticflow.core.itc as itc_module
        itc_module._itc_manager = None
        
        config = ITCConfig(enable_streaming=True, stream_interval=0.01)  # Very fast
        self.itc = initialize_itc(config)
    
    @pytest.mark.asyncio
    async def test_multiple_coordinators_streaming(self):
        """Test streaming with multiple coordinators."""
        num_coordinators = 10
        coordinators = []
        
        # Connect multiple coordinators
        for i in range(num_coordinators):
            coord_id = f"coordinator_{i}"
            await self.itc.connect_coordinator(coord_id, "agent")
            self.itc.create_stream_subscription(
                coordinator_id=coord_id,
                event_types={ITCEventType.REAL_TIME_UPDATE}
            )
            coordinators.append(coord_id)
        
        # Send multiple updates
        num_updates = 50
        start_time = time.time()
        
        for i in range(num_updates):
            await self.itc.send_real_time_update(
                update_data={"update_id": i, "update_type": "performance_test"},
                task_id="perf_task",
                agent_id="perf_agent"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Sent {num_updates} updates to {num_coordinators} coordinators in {duration:.3f}s")
        print(f"Rate: {(num_updates * num_coordinators) / duration:.1f} updates/second")
        
        # Verify all coordinators received all updates
        for coord_id in coordinators:
            queue = self.itc._stream_queues[coord_id]
            assert queue.qsize() == num_updates
    
    @pytest.mark.asyncio
    async def test_background_monitoring_performance(self):
        """Test background monitoring performance with many tasks."""
        num_tasks = 100
        
        # Connect a coordinator
        await self.itc.connect_coordinator("perf_coordinator", "agent")
        
        # Start many tasks
        tasks = []
        for i in range(num_tasks):
            task = await self.itc.start_task(f"task_{i}", f"Performance task {i}", f"agent_{i}")
            tasks.append(task)
        
        # Time background processing
        start_time = time.time()
        await self.itc._process_background_updates()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"Processed {num_tasks} tasks in background monitoring in {duration:.3f}s")
        print(f"Rate: {num_tasks / duration:.1f} tasks/second")
        
        assert duration < 1.0  # Should process 100 tasks in under 1 second


if __name__ == "__main__":
    # Run tests manually if not using pytest
    import sys
    if "--manual" in sys.argv:
        async def run_manual_tests():
            test_suite = TestITCStreaming()
            test_suite.setup_method()
            
            print("🧪 Testing coordinator connection...")
            await test_suite.test_coordinator_connection()
            print("✅ Coordinator connection test passed")
            
            test_suite.setup_method()
            print("🧪 Testing stream subscription...")
            await test_suite.test_stream_subscription()
            print("✅ Stream subscription test passed")
            
            test_suite.setup_method()
            print("🧪 Testing real-time updates...")
            await test_suite.test_real_time_updates()
            print("✅ Real-time updates test passed")
            
            test_suite.setup_method()
            print("🧪 Testing background monitoring...")
            await test_suite.test_background_monitoring()
            print("✅ Background monitoring test passed")
            
            print("\n🎉 All manual tests passed!")
        
        asyncio.run(run_manual_tests())
    else:
        print("Run with pytest or use --manual flag for manual testing")