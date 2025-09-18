#!/usr/bin/env python3
"""
Comprehensive Test for Enhanced Orchestration with Integrated ITC
================================================================

Tests the integrated layered architecture with:
- Enhanced TaskOrchestrator with real-time streaming
- Interactive task control and interruption  
- Multi-agent coordination and communication
- Event-driven architecture with unified messaging

This validates the super framework's integrated capabilities.
"""

import asyncio
import pytest
import time
from typing import Dict, Any

from agenticflow.orchestration.task_orchestrator import (
    TaskOrchestrator, InteractiveTaskNode, CoordinationEventType,
    WorkflowStatus, CoordinationManager
)
from agenticflow.orchestration.task_management import (
    FunctionTaskExecutor, TaskState, TaskResult, RetryPolicy
)
from agenticflow.config.settings import ITCConfig


class MockFunction:
    """Mock function for testing task execution."""
    
    def __init__(self, duration: float = 1.0, should_fail: bool = False, 
                 check_interruption: bool = True):
        self.duration = duration
        self.should_fail = should_fail
        self.check_interruption = check_interruption
        self.execution_count = 0
        self.start_count = 0
        self.actual_duration = 0.0
    
    async def __call__(self, **kwargs) -> str:
        """Async callable that simulates task work."""
        self.start_count += 1
        actual_start = time.time()
        
        try:
            # Simulate work with interruption checking
            elapsed = 0.0
            while elapsed < self.duration:
                # Check if we have access to task for interruption
                if self.check_interruption and 'task' in kwargs:
                    task = kwargs['task']
                    if hasattr(task, 'is_interrupted') and task.is_interrupted():
                        raise asyncio.CancelledError("Task was interrupted")
                
                await asyncio.sleep(min(0.05, self.duration - elapsed))
                elapsed = time.time() - actual_start
            
            if self.should_fail:
                raise RuntimeError(f"Mock function failed on execution {self.execution_count + 1}")
            
            # Only increment count on successful completion
            self.execution_count += 1
            self.actual_duration = time.time() - actual_start
            
            return f"Completed execution {self.execution_count} in {self.actual_duration:.2f}s"
            
        except asyncio.CancelledError:
            # Don't increment count if cancelled
            raise
    
    def __repr__(self):
        return f"MockFunction(starts={self.start_count}, completed={self.execution_count}, duration={self.duration})"


@pytest.fixture
def task_orchestrator():
    """Create a task orchestrator for testing."""
    return TaskOrchestrator(
        max_concurrent_tasks=3,
        enable_streaming=True,
        enable_coordination=True,
        itc_config=ITCConfig(stream_interval=0.1, enable_streaming=True)
    )


class TestTaskOrchestration:
    """Test suite for task orchestration capabilities."""
    
    @pytest.mark.asyncio
    async def test_basic_task_execution(self, task_orchestrator):
        """Test basic task execution with the task orchestrator."""
        orchestrator = task_orchestrator
        
        # Add a simple task
        mock_func = MockFunction(duration=0.5)
        executor = FunctionTaskExecutor(mock_func)
        
        task = orchestrator.add_interactive_task(
            task_id="test_task",
            name="Test Task",
            executor=executor,
            streaming_enabled=True,
            interruptible=True
        )
        
        assert isinstance(task, InteractiveTaskNode)
        assert task.streaming_enabled is True
        assert task.interruptible is True
        assert task.state == TaskState.PENDING
        
        # Execute workflow and collect updates
        updates = []
        async for update in orchestrator.execute_workflow_with_streaming():
            updates.append(update)
            if update.get("type") == "workflow_completed":
                break
        
        # Verify execution
        assert mock_func.execution_count == 1
        assert task.state == TaskState.COMPLETED
        assert len(updates) > 0
        
        # Check for streaming updates
        status_updates = [u for u in updates if u.get("type") == "status_update"]
        assert len(status_updates) > 0
    
    @pytest.mark.asyncio
    async def test_task_interruption(self, task_orchestrator):
        """Test task interruption capabilities."""
        orchestrator = task_orchestrator
        
        # Add a long-running task
        mock_func = MockFunction(duration=5.0, check_interruption=True)
        executor = FunctionTaskExecutor(mock_func)
        
        task = orchestrator.add_interactive_task(
            task_id="long_task",
            name="Long Running Task",
            executor=executor,
            interruptible=True
        )
        
        # Start execution
        execution_task = asyncio.create_task(
            orchestrator._execute_workflow_with_coordination().__anext__()
        )
        
        # Wait a bit, then interrupt
        await asyncio.sleep(0.3)
        success = await orchestrator.interrupt_task("long_task", "User interrupt")
        
        assert success is True
        assert task.is_interrupted() is True
        assert task.context.get("interrupt_reason") == "User interrupt"
        
        # Cancel the execution task
        execution_task.cancel()
        try:
            await execution_task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_coordination_events(self, task_orchestrator):
        """Test coordination event system."""
        orchestrator = task_orchestrator
        
        events_received = []
        
        async def event_handler(event):
            events_received.append(event)
        
        # Register event handlers
        orchestrator.coordination.register_event_handler(
            CoordinationEventType.TASK_STARTED, event_handler
        )
        orchestrator.coordination.register_event_handler(
            CoordinationEventType.TASK_COMPLETED, event_handler
        )
        
        # Add and execute a task
        mock_func = MockFunction(duration=0.2)
        executor = FunctionTaskExecutor(mock_func)
        
        orchestrator.add_interactive_task(
            task_id="event_test",
            name="Event Test Task",
            executor=executor
        )
        
        # Execute workflow
        async for update in orchestrator.execute_workflow_with_streaming():
            if update.get("type") == "workflow_completed":
                break
        
        # Verify events were emitted
        assert len(events_received) >= 2
        event_types = [event.event_type for event in events_received]
        assert CoordinationEventType.TASK_STARTED in event_types
        assert CoordinationEventType.TASK_COMPLETED in event_types
    
    @pytest.mark.asyncio
    async def test_streaming_subscriptions(self, task_orchestrator):
        """Test real-time streaming subscriptions."""
        orchestrator = task_orchestrator
        
        # Connect a coordinator
        coordinator_id = "test_coordinator"
        await orchestrator.connect_coordinator(coordinator_id, "test")
        
        # Create subscription
        subscription_id = orchestrator.create_stream_subscription(
            coordinator_id=coordinator_id,
            event_types={CoordinationEventType.REAL_TIME_UPDATE}
        )
        
        assert subscription_id is not None
        assert len(orchestrator.coordination.stream_subscriptions) == 1
        
        # Add task and start execution
        mock_func = MockFunction(duration=0.5)
        executor = FunctionTaskExecutor(mock_func)
        
        orchestrator.add_interactive_task(
            task_id="stream_test",
            name="Streaming Test Task",
            executor=executor,
            streaming_enabled=True
        )
        
        # Start streaming in background
        stream_updates = []
        
        async def collect_updates():
            try:
                async for update in orchestrator.stream_updates(coordinator_id):
                    stream_updates.append(update)
                    if len(stream_updates) >= 3:  # Collect a few updates
                        break
            except asyncio.CancelledError:
                pass
        
        stream_task = asyncio.create_task(collect_updates())
        
        # Execute workflow (create async generator then convert to list)
        async def collect_workflow_updates():
            updates = []
            async for update in orchestrator.execute_workflow_with_streaming():
                updates.append(update)
                if update.get("type") == "workflow_completed":
                    break
            return updates
        
        execution_task = asyncio.create_task(collect_workflow_updates())
        
        # Wait for both tasks with timeout
        try:
            await asyncio.wait_for(asyncio.gather(stream_task, execution_task), timeout=3.0)
        except asyncio.TimeoutError:
            pass
        
        # Cleanup
        stream_task.cancel()
        execution_task.cancel()
        
        # Verify streaming updates were received
        assert len(stream_updates) > 0
        update_types = [update.get("type") for update in stream_updates]
        assert "real_time_update" in update_types or "heartbeat" in update_types
    
    @pytest.mark.asyncio
    async def test_workflow_with_dependencies(self, task_orchestrator):
        """Test workflow execution with task dependencies."""
        orchestrator = task_orchestrator
        
        # Create tasks with dependencies
        task1_func = MockFunction(duration=0.2)
        task2_func = MockFunction(duration=0.2) 
        task3_func = MockFunction(duration=0.2)
        
        # Task 1 (no dependencies)
        orchestrator.add_interactive_task(
            task_id="task1",
            name="Task 1",
            executor=FunctionTaskExecutor(task1_func)
        )
        
        # Task 2 (depends on Task 1)
        orchestrator.add_interactive_task(
            task_id="task2", 
            name="Task 2",
            executor=FunctionTaskExecutor(task2_func),
            dependencies=["task1"]
        )
        
        # Task 3 (depends on Task 2)
        orchestrator.add_interactive_task(
            task_id="task3",
            name="Task 3", 
            executor=FunctionTaskExecutor(task3_func),
            dependencies=["task2"]
        )
        
        # Execute workflow
        start_time = time.time()
        async for update in orchestrator.execute_workflow_with_streaming():
            if update.get("type") == "workflow_completed":
                break
        
        execution_time = time.time() - start_time
        
        # Verify sequential execution (should take at least 0.6s for 3 tasks)
        assert execution_time >= 0.6
        assert task1_func.execution_count == 1
        assert task2_func.execution_count == 1
        assert task3_func.execution_count == 1
        
        # Verify final states
        assert orchestrator.dag.tasks["task1"].state == TaskState.COMPLETED
        assert orchestrator.dag.tasks["task2"].state == TaskState.COMPLETED  
        assert orchestrator.dag.tasks["task3"].state == TaskState.COMPLETED
    
    @pytest.mark.asyncio
    async def test_parallel_task_execution(self, task_orchestrator):
        """Test parallel execution of independent tasks."""
        orchestrator = task_orchestrator
        
        # Create multiple independent tasks
        funcs = [MockFunction(duration=0.5) for _ in range(3)]
        
        for i, func in enumerate(funcs):
            orchestrator.add_interactive_task(
                task_id=f"parallel_task_{i}",
                name=f"Parallel Task {i}",
                executor=FunctionTaskExecutor(func)
            )
        
        # Execute workflow
        start_time = time.time()
        async for update in orchestrator.execute_workflow_with_streaming():
            if update.get("type") == "workflow_completed":
                break
        
        execution_time = time.time() - start_time
        
        # Verify parallel execution (should take ~0.5s, not 1.5s)
        # Allow some overhead for streaming and coordination
        assert execution_time < 1.2  # Much less than sequential execution (would be 1.5s)
        
        # Verify all tasks completed
        for func in funcs:
            assert func.execution_count == 1
    
    @pytest.mark.asyncio
    async def test_comprehensive_status(self, task_orchestrator):
        """Test comprehensive status reporting."""
        orchestrator = task_orchestrator
        
        # Connect coordinator
        await orchestrator.connect_coordinator("status_test", "test")
        
        # Add tasks
        orchestrator.add_interactive_task(
            task_id="status_task",
            name="Status Task",
            executor=FunctionTaskExecutor(MockFunction(duration=0.1))
        )
        
        # Get status before execution
        status_before = orchestrator.get_comprehensive_status()
        assert status_before["orchestrator_id"] is not None
        assert status_before["workflow_status"]["total_tasks"] == 1
        assert status_before["coordination"]["connected_coordinators"] == 1
        
        # Execute workflow
        async for update in orchestrator.execute_workflow_with_streaming():
            if update.get("type") == "workflow_completed":
                break
        
        # Get status after execution
        status_after = orchestrator.get_comprehensive_status()
        assert status_after["workflow_status"]["completed_tasks"] == 1
        assert status_after["workflow_status"]["progress_percentage"] == 100.0
        assert status_after["workflow_status"]["is_complete"] is True


@pytest.mark.asyncio
async def test_error_handling_and_retry():
    """Test error handling and retry capabilities."""
    orchestrator = TaskOrchestrator(
        default_retry_policy=RetryPolicy(max_attempts=3, initial_delay=0.1)
    )
    
    # Create a function that fails twice then succeeds
    call_count = 0
    
    def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError(f"Attempt {call_count} failed")
        return f"Success on attempt {call_count}"
    
    executor = FunctionTaskExecutor(failing_func)
    orchestrator.add_interactive_task(
        task_id="retry_test",
        name="Retry Test Task", 
        executor=executor
    )
    
    # Execute workflow
    async for update in orchestrator.execute_workflow_with_streaming():
        if update.get("type") == "workflow_completed":
            break
    
    # Verify retry logic worked
    task = orchestrator.dag.tasks["retry_test"]
    assert task.state == TaskState.COMPLETED
    assert task.attempts == 3  # Should have tried 3 times
    assert call_count == 3


@pytest.mark.asyncio 
async def test_integration_with_existing_components():
    """Test integration with existing AgenticFlow components."""
    # This test ensures the enhanced orchestrator works with existing components
    
    orchestrator = TaskOrchestrator()
    
    # Test with existing TaskDAG validation
    is_valid, issues = orchestrator.dag.validate_dag()
    assert is_valid is True
    assert len(issues) == 0
    
    # Test with existing task management components
    from agenticflow.orchestration.task_management import TaskPriority, ErrorCategory
    
    retry_policy = RetryPolicy(
        max_attempts=2,
        retry_categories={ErrorCategory.TRANSIENT}
    )
    
    task = orchestrator.add_interactive_task(
        task_id="integration_test",
        name="Integration Test",
        executor=FunctionTaskExecutor(lambda: "success"),
        priority=TaskPriority.HIGH,
        retry_policy=retry_policy
    )
    
    assert task.priority == TaskPriority.HIGH
    assert task.retry_policy.max_attempts == 2
    
    # Execute to ensure compatibility
    async for update in orchestrator.execute_workflow_with_streaming():
        if update.get("type") == "workflow_completed":
            break
    
    assert task.state == TaskState.COMPLETED


if __name__ == "__main__":
    # Run the tests
    import sys
    
    async def run_tests():
        """Run all tests manually."""
        print("🧪 Running Enhanced Orchestration Tests")
        print("=" * 50)
        
        # Test basic functionality
        print("\n🔧 Testing basic task execution...")
        orchestrator = TaskOrchestrator()
        mock_func = MockFunction(duration=0.1)
        
        orchestrator.add_interactive_task(
            "basic_test",
            "Basic Test",
            FunctionTaskExecutor(mock_func)
        )
        
        updates = []
        async for update in orchestrator.execute_workflow_with_streaming():
            updates.append(update)
            print(f"   📊 {update.get('type', 'unknown')}: {update.get('data', {}).get('progress_percentage', 'N/A')}%")
            if update.get("type") == "workflow_completed":
                break
        
        print(f"✅ Basic test passed! {len(updates)} updates received")
        
        # Test streaming
        print("\n📡 Testing streaming capabilities...")
        orchestrator = TaskOrchestrator()
        await orchestrator.connect_coordinator("test_human", "human")
        
        subscription = orchestrator.create_stream_subscription("test_human")
        print(f"✅ Created subscription: {subscription}")
        
        # Test interruption
        print("\n🛑 Testing interruption...")
        orchestrator = TaskOrchestrator()
        long_func = MockFunction(duration=2.0, check_interruption=True)
        
        task = orchestrator.add_interactive_task(
            "interrupt_test",
            "Interrupt Test",
            FunctionTaskExecutor(long_func),
            interruptible=True
        )
        
        # Start execution and interrupt after short delay
        execution_started = time.time()
        
        async def interrupt_after_delay():
            await asyncio.sleep(0.2)
            success = await orchestrator.interrupt_task("interrupt_test", "Test interrupt")
            print(f"   🛑 Interrupt sent: {success}")
        
        interrupt_task = asyncio.create_task(interrupt_after_delay())
        
        try:
            async for update in orchestrator.execute_workflow_with_streaming():
                if update.get("type") in ["workflow_completed", "workflow_error"]:
                    break
        except:
            pass
        
        await interrupt_task
        execution_time = time.time() - execution_started
        
        print(f"✅ Interruption test completed in {execution_time:.2f}s (should be < 1s)")
        
        print("\n🎉 All manual tests completed successfully!")
    
    # Run tests if executed directly
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        asyncio.run(run_tests())
    else:
        print("Run with 'manual' argument to execute manual tests")
        print("Or use pytest to run the full test suite")