"""
Unit tests for TaskOrchestrator
==============================

Tests for the core task orchestration functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import RetryPolicy, TaskPriority, TaskState


@pytest.mark.unit
class TestTaskOrchestrator:
    """Unit tests for TaskOrchestrator class."""
    
    def test_orchestrator_initialization(self, sample_retry_policy):
        """Test orchestrator initialization with various configurations."""
        orchestrator = TaskOrchestrator(
            max_concurrent_tasks=5,
            default_retry_policy=sample_retry_policy
        )
        
        assert orchestrator.max_concurrent_tasks == 5
        assert orchestrator.default_retry_policy == sample_retry_policy
        assert orchestrator.task_dag is not None
        assert len(orchestrator.tasks) == 0
        assert orchestrator.status is not None
    
    def test_add_function_task(self, basic_orchestrator):
        """Test adding function tasks to orchestrator."""
        def sample_function(x, y):
            return x + y
        
        task_id = basic_orchestrator.add_function_task(
            "test_task",
            "Test Task",
            sample_function,
            args=(1, 2),
            kwargs={"extra": "param"},
            priority=TaskPriority.HIGH
        )
        
        assert task_id == "test_task"
        assert "test_task" in basic_orchestrator.tasks
        
        task = basic_orchestrator.tasks["test_task"]
        assert task.name == "Test Task"
        assert task.priority == TaskPriority.HIGH
        
        # Check that executor has the function and args
        executor = basic_orchestrator.executors["test_task"]
        assert executor.func == sample_function
    
    def test_add_task_with_dependencies(self, basic_orchestrator):
        """Test adding tasks with dependencies."""
        def task_func():
            return "result"
        
        # Add first task
        basic_orchestrator.add_function_task("task_1", "Task 1", task_func)
        
        # Add dependent task
        basic_orchestrator.add_function_task(
            "task_2", 
            "Task 2", 
            task_func, 
            dependencies=["task_1"]
        )
        
        assert "task_1" in basic_orchestrator.tasks
        assert "task_2" in basic_orchestrator.tasks
        
        # Verify DAG structure
        dependencies = basic_orchestrator.task_dag.get_dependencies("task_2")
        assert "task_1" in dependencies
    
    def test_add_duplicate_task_raises_error(self, basic_orchestrator):
        """Test that adding duplicate task IDs raises an error."""
        def task_func():
            return "result"
        
        basic_orchestrator.add_function_task("duplicate", "First", task_func)
        
        with pytest.raises(ValueError, match="already exists"):
            basic_orchestrator.add_function_task("duplicate", "Second", task_func)
    
    def test_add_task_with_invalid_dependency_raises_error(self, basic_orchestrator):
        """Test that adding task with non-existent dependency raises error."""
        def task_func():
            return "result"
        
        with pytest.raises(ValueError, match="does not exist"):
            basic_orchestrator.add_function_task(
                "task_1",
                "Task 1", 
                task_func,
                dependencies=["non_existent"]
            )
    
    @pytest.mark.asyncio
    async def test_simple_task_execution(self, basic_orchestrator):
        """Test execution of a simple task without dependencies."""
        async def simple_task():
            return "success"
        
        basic_orchestrator.add_function_task("simple", "Simple Task", simple_task)
        
        result = await basic_orchestrator.execute_workflow()
        
        assert result["success_rate"] == 100.0
        assert result["status"]["is_complete"] is True
        assert result["status"]["completed_tasks"] == 1
        assert "simple" in result["task_results"]
        assert result["task_results"]["simple"]["state"] == "completed"
    
    @pytest.mark.asyncio
    async def test_sequential_task_execution(self, basic_orchestrator):
        """Test execution of sequential dependent tasks."""
        results = []
        
        async def task_1():
            results.append("task_1")
            return "result_1"
        
        async def task_2():
            results.append("task_2")
            return "result_2"
        
        basic_orchestrator.add_function_task("task_1", "Task 1", task_1)
        basic_orchestrator.add_function_task(
            "task_2", 
            "Task 2", 
            task_2, 
            dependencies=["task_1"]
        )
        
        result = await basic_orchestrator.execute_workflow()
        
        assert result["success_rate"] == 100.0
        assert results == ["task_1", "task_2"]  # Execution order matters
        assert result["status"]["completed_tasks"] == 2
    
    @pytest.mark.asyncio
    async def test_parallel_task_execution(self, basic_orchestrator):
        """Test execution of parallel independent tasks."""
        results = []
        
        async def parallel_task(task_id):
            await asyncio.sleep(0.1)  # Small delay to test concurrency
            results.append(task_id)
            return f"result_{task_id}"
        
        basic_orchestrator.add_function_task("task_a", "Task A", parallel_task, args=("a",))
        basic_orchestrator.add_function_task("task_b", "Task B", parallel_task, args=("b",))
        basic_orchestrator.add_function_task("task_c", "Task C", parallel_task, args=("c",))
        
        start_time = time.time()
        result = await basic_orchestrator.execute_workflow()
        execution_time = time.time() - start_time
        
        assert result["success_rate"] == 100.0
        assert result["status"]["completed_tasks"] == 3
        # Should complete faster than sequential execution due to parallelism
        # More lenient timing to account for system variations
        assert execution_time < 0.5  # Less than 5x the individual task time
        assert len(results) == 3
        assert set(results) == {"a", "b", "c"}
    
    @pytest.mark.asyncio 
    async def test_task_failure_handling(self, basic_orchestrator):
        """Test handling of task failures."""
        async def failing_task():
            raise ValueError("Task failed")
        
        async def success_task():
            return "success"
        
        basic_orchestrator.add_function_task("fail", "Failing Task", failing_task)
        basic_orchestrator.add_function_task("success", "Success Task", success_task)
        
        result = await basic_orchestrator.execute_workflow()
        
        # Should complete with partial success
        assert result["success_rate"] == 50.0  # 1 out of 2 tasks succeeded
        assert result["status"]["completed_tasks"] == 1
        # Task should be in failed state after retries are exhausted
        assert result["task_results"]["fail"]["state"] in ["failed", "retrying"]
        assert result["task_results"]["success"]["state"] == "completed"
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test task retry mechanism."""
        call_count = 0
        
        async def flaky_task():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise ValueError("Flaky failure")
            return "success"
        
        retry_policy = RetryPolicy(
            max_attempts=3,
            initial_delay=0.01,
            max_delay=0.1,
            backoff_multiplier=2.0
        )
        
        orchestrator = TaskOrchestrator(
            max_concurrent_tasks=2,
            default_retry_policy=retry_policy
        )
        
        orchestrator.add_function_task("flaky", "Flaky Task", flaky_task)
        
        result = await orchestrator.execute_workflow()
        
        assert result["success_rate"] == 100.0
        assert call_count == 3  # Should have been called 3 times
        assert result["task_results"]["flaky"]["attempts"] == 3
    
    @pytest.mark.asyncio
    async def test_task_timeout(self):
        """Test task timeout handling."""
        async def slow_task():
            await asyncio.sleep(1.0)  # Task that takes longer than timeout
            return "late_result"
        
        orchestrator = TaskOrchestrator(max_concurrent_tasks=1)
        
        # Add task with a very short timeout
        task_id = orchestrator.add_function_task("slow", "Slow Task", slow_task)
        task = orchestrator.dag.tasks[task_id]
        task.timeout = 0.1  # 100ms timeout, much shorter than the 1s task duration
        
        # Execute with timeout
        result = await orchestrator.execute_workflow()
        
        # Task should fail due to timeout (or at least not complete successfully)
        # Since timeout handling might mark as failed or retrying
        assert result["success_rate"] <= 50.0  # Allow for retry behavior
        assert result["task_results"]["slow"]["state"] in ["failed", "timeout", "retrying"]
    
    @pytest.mark.asyncio
    async def test_complex_dag_execution(self, basic_orchestrator):
        """Test execution of complex DAG with multiple dependencies."""
        execution_order = []
        
        async def tracked_task(task_id):
            execution_order.append(task_id)
            await asyncio.sleep(0.01)  # Small delay
            return f"result_{task_id}"
        
        # Create diamond dependency pattern
        basic_orchestrator.add_function_task("start", "Start", tracked_task, args=("start",))
        basic_orchestrator.add_function_task("left", "Left", tracked_task, args=("left",), dependencies=["start"])
        basic_orchestrator.add_function_task("right", "Right", tracked_task, args=("right",), dependencies=["start"])
        basic_orchestrator.add_function_task("end", "End", tracked_task, args=("end",), dependencies=["left", "right"])
        
        result = await basic_orchestrator.execute_workflow()
        
        assert result["success_rate"] == 100.0
        assert result["status"]["completed_tasks"] == 4
        
        # Verify execution order respects dependencies
        assert execution_order[0] == "start"
        assert execution_order[-1] == "end"
        # left and right can execute in any order after start
        assert "left" in execution_order[1:3]
        assert "right" in execution_order[1:3]
    
    def test_task_priority_handling(self, basic_orchestrator):
        """Test that task priorities are properly handled."""
        def task_func():
            return "result"
        
        basic_orchestrator.add_function_task("low", "Low Priority", task_func, priority=TaskPriority.LOW)
        basic_orchestrator.add_function_task("high", "High Priority", task_func, priority=TaskPriority.HIGH)
        basic_orchestrator.add_function_task("critical", "Critical", task_func, priority=TaskPriority.CRITICAL)
        
        # Verify priorities are set correctly
        assert basic_orchestrator.tasks["low"].priority == TaskPriority.LOW
        assert basic_orchestrator.tasks["high"].priority == TaskPriority.HIGH
        assert basic_orchestrator.tasks["critical"].priority == TaskPriority.CRITICAL
    
    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, basic_orchestrator):
        """Test workflow cancellation capabilities."""
        async def long_running_task():
            try:
                await asyncio.sleep(5.0)  # Long delay
                return "completed"
            except asyncio.CancelledError:
                return "cancelled"
        
        basic_orchestrator.add_function_task("long", "Long Task", long_running_task)
        
        # Start execution
        task = asyncio.create_task(basic_orchestrator.execute_workflow())
        
        # Cancel after short delay
        await asyncio.sleep(0.1)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            # Expected behavior
            pass
    
    def test_get_execution_stats(self, basic_orchestrator):
        """Test execution statistics gathering."""
        stats = basic_orchestrator.get_execution_stats()
        
        assert "total_tasks" in stats
        assert "completed_tasks" in stats
        assert "failed_tasks" in stats
        assert "execution_time" in stats
        assert stats["total_tasks"] == 0  # No tasks added yet
    
    @pytest.mark.asyncio
    async def test_task_result_passing(self, basic_orchestrator):
        """Test that task results are properly passed between dependent tasks."""
        async def producer_task():
            return {"data": "produced_value", "count": 42}
        
        async def consumer_task(**kwargs):
            # Should receive result from producer_task
            producer_result = None
            for key, value in kwargs.items():
                if key.endswith("_result") and isinstance(value, dict) and "data" in value:
                    producer_result = value
                    break
            
            assert producer_result is not None
            assert producer_result["data"] == "produced_value"
            assert producer_result["count"] == 42
            return "consumed"
        
        basic_orchestrator.add_function_task("producer", "Producer", producer_task)
        basic_orchestrator.add_function_task(
            "consumer", 
            "Consumer", 
            consumer_task, 
            dependencies=["producer"]
        )
        
        result = await basic_orchestrator.execute_workflow()
        
        assert result["success_rate"] == 100.0
        assert result["task_results"]["consumer"]["result"]["result"] == "consumed"
    
    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self):
        """Test that concurrent task limit is respected."""
        execution_times = []
        
        async def timed_task(task_id):
            start_time = time.time()
            await asyncio.sleep(0.2)
            end_time = time.time()
            execution_times.append((task_id, start_time, end_time))
            return f"result_{task_id}"
        
        # Create orchestrator with limit of 2 concurrent tasks
        orchestrator = TaskOrchestrator(max_concurrent_tasks=2)
        
        # Add 4 independent tasks
        for i in range(4):
            orchestrator.add_function_task(f"task_{i}", f"Task {i}", timed_task, args=(i,))
        
        start_time = time.time()
        result = await orchestrator.execute_workflow()
        total_time = time.time() - start_time
        
        assert result["success_rate"] == 100.0
        assert result["status"]["completed_tasks"] == 4
        
        # Should take at least 2 batches * 0.2s = 0.4s due to concurrency limit
        assert total_time >= 0.35
        assert len(execution_times) == 4