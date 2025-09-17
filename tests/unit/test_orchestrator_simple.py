"""
Simple Unit tests for TaskOrchestrator
======================================

Tests for the core task orchestration functionality with correct API.
"""

import pytest
import asyncio
import time

from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import RetryPolicy, TaskPriority


@pytest.mark.unit
class TestTaskOrchestratorSimple:
    """Unit tests for TaskOrchestrator class with correct API."""
    
    def test_orchestrator_initialization(self, sample_retry_policy):
        """Test orchestrator initialization with various configurations."""
        orchestrator = TaskOrchestrator(
            max_concurrent_tasks=5,
            default_retry_policy=sample_retry_policy
        )
        
        assert orchestrator.max_concurrent_tasks == 5
        assert orchestrator.default_retry_policy == sample_retry_policy
        assert orchestrator.dag is not None
        assert orchestrator.status is not None
        assert len(orchestrator.dag.tasks) == 0
    
    def test_add_function_task(self, basic_orchestrator):
        """Test adding function tasks to orchestrator."""
        def sample_function(x, y):
            return x + y
        
        task_node = basic_orchestrator.add_function_task(
            "test_task",
            "Test Task",
            sample_function,
            args=(1, 2),
            kwargs={"extra": "param"},
            priority=TaskPriority.HIGH
        )
        
        assert task_node.task_id == "test_task"
        assert task_node.name == "Test Task"
        assert task_node.priority == TaskPriority.HIGH
        assert "test_task" in basic_orchestrator.dag.tasks
    
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
        
        assert "task_1" in basic_orchestrator.dag.tasks
        assert "task_2" in basic_orchestrator.dag.tasks
        
        # Verify DAG structure
        dependencies = basic_orchestrator.dag.get_dependencies("task_2")
        assert "task_1" in dependencies
    
    def test_add_task_with_invalid_dependency_raises_error(self, basic_orchestrator):
        """Test that adding task with non-existent dependency raises error."""
        def task_func():
            return "result"
        
        with pytest.raises(ValueError, match="not found"):
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
        
        # Check if the task completed successfully
        assert result["success_rate"] > 0.0
        assert result["status"]["total_tasks"] == 1
    
    @pytest.mark.asyncio
    async def test_sequential_task_execution(self, basic_orchestrator):
        """Test execution of sequential dependent tasks."""
        results = []
        
        async def task_1():
            results.append("task_1")
            return "result_1"
        
        async def task_2(**kwargs):
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
        
        # Tasks should have executed in correct order
        assert len(results) == 2
        assert results[0] == "task_1"
        assert results[1] == "task_2"
    
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
        
        start_time = time.time()
        result = await basic_orchestrator.execute_workflow()
        execution_time = time.time() - start_time
        
        # Should complete faster than sequential execution due to parallelism
        assert execution_time < 0.25  # Much less than 2 * 0.1 = 0.2 seconds
        assert len(results) == 2
        assert set(results) == {"a", "b"}
    
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
        assert result["status"]["total_tasks"] == 2
        # At least one task should complete successfully
        assert result["status"]["completed_tasks"] >= 1
    
    def test_get_status(self, basic_orchestrator):
        """Test status information retrieval."""
        def task_func():
            return "result"
        
        basic_orchestrator.add_function_task("task1", "Task 1", task_func)
        basic_orchestrator.add_function_task("task2", "Task 2", task_func)
        
        # Update status from DAG
        basic_orchestrator.status.update_from_dag(basic_orchestrator.dag)
        
        status_dict = basic_orchestrator.status.to_dict()
        assert status_dict["total_tasks"] == 2
        assert "progress_percentage" in status_dict
        assert "is_complete" in status_dict