"""
Unit tests for FunctionTaskExecutor parameter handling.

Tests the fix for task_id parameter conflicts and proper context filtering.
"""

import pytest
import asyncio
from agenticflow.orchestration.task_management import (
    FunctionTaskExecutor,
    TaskNode,
    TaskPriority
)


class TestFunctionTaskExecutor:
    """Test FunctionTaskExecutor parameter handling and conflict resolution."""

    @pytest.mark.asyncio
    async def test_function_without_task_id_parameter(self):
        """Test function that doesn't accept task_id parameter doesn't receive it from context."""
        def simple_task(message: str) -> str:
            return f"Processed: {message}"
        
        executor = FunctionTaskExecutor(simple_task, message="Hello World")
        
        task = TaskNode(
            task_id="test_task_1",
            name="Simple Task",
            priority=TaskPriority.NORMAL
        )
        
        # Context includes task_id (should be filtered out)
        context = {"task_id": "test_task_1", "extra_data": "some value"}
        
        result = await executor.execute(task, context)
        
        assert result.success is True
        assert result.result == "Processed: Hello World"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_function_with_explicit_task_id_parameter(self):
        """Test function that explicitly accepts task_id parameter receives it from context."""
        def task_with_task_id(task_id: str, message: str) -> str:
            return f"Task {task_id} processed: {message}"
        
        executor = FunctionTaskExecutor(task_with_task_id, message="Hello World")
        
        task = TaskNode(
            task_id="test_task_2",
            name="Task with ID",
            priority=TaskPriority.NORMAL
        )
        
        context = {"task_id": "test_task_2", "extra_data": "some value"}
        
        result = await executor.execute(task, context)
        
        assert result.success is True
        assert result.result == "Task test_task_2 processed: Hello World"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_context_parameters_passed_to_function(self):
        """Test that non-reserved context values are passed to function parameters."""
        def task_with_context(message: str, extra_data: str) -> str:
            return f"Message: {message}, Extra: {extra_data}"
        
        executor = FunctionTaskExecutor(task_with_context, message="Hello")
        
        task = TaskNode(
            task_id="test_task_3",
            name="Task with Context",
            priority=TaskPriority.NORMAL
        )
        
        context = {"task_id": "test_task_3", "extra_data": "context_value"}
        
        result = await executor.execute(task, context)
        
        assert result.success is True
        assert result.result == "Message: Hello, Extra: context_value"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_positional_args_take_precedence_over_context(self):
        """Test that positional arguments take precedence over context parameters."""
        def parallel_task(task_id: str) -> str:
            return f"result_{task_id}"
        
        # Pass "a" as positional argument for task_id
        executor = FunctionTaskExecutor(parallel_task, "a")
        
        task = TaskNode(
            task_id="task_a",
            name="Task A",
            priority=TaskPriority.NORMAL
        )
        
        # Context also contains task_id but should be ignored due to positional arg
        context = {"task_id": "task_a", "some_other_data": "value"}
        
        result = await executor.execute(task, context)
        
        assert result.success is True
        assert result.result == "result_a"  # Should use positional arg "a", not context "task_a"
        assert result.error is None

    @pytest.mark.asyncio 
    async def test_constructor_kwargs_take_precedence_over_context(self):
        """Test that constructor kwargs take precedence over context parameters."""
        def task_with_kwargs(message: str, priority: str) -> str:
            return f"{message} with priority {priority}"
        
        # Pass priority via constructor kwargs
        executor = FunctionTaskExecutor(task_with_kwargs, message="Hello", priority="HIGH")
        
        task = TaskNode(
            task_id="test_task_4",
            name="Task with kwargs",
            priority=TaskPriority.NORMAL
        )
        
        # Context also contains priority but constructor kwargs should take precedence
        context = {"task_id": "test_task_4", "priority": "LOW"}
        
        result = await executor.execute(task, context)
        
        assert result.success is True
        assert result.result == "Hello with priority HIGH"  # Should use constructor kwarg
        assert result.error is None

    @pytest.mark.asyncio
    async def test_reserved_keys_filtered_out_unless_accepted(self):
        """Test that reserved system keys are filtered out unless function explicitly accepts them."""
        def task_without_reserved_params(message: str) -> str:
            return f"Message: {message}"
        
        executor = FunctionTaskExecutor(task_without_reserved_params, message="Hello")
        
        task = TaskNode(
            task_id="test_task_5",
            name="Task without reserved",
            priority=TaskPriority.NORMAL
        )
        
        # Context includes reserved keys that should be filtered out
        context = {
            "task_id": "test_task_5",
            "task_name": "Test Task", 
            "task_state": "running",
            "created_at": "2023-01-01T00:00:00",
            "started_at": "2023-01-01T00:00:01",
            "completed_at": None
        }
        
        result = await executor.execute(task, context)
        
        assert result.success is True
        assert result.result == "Message: Hello"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_async_function_execution(self):
        """Test that async functions are executed properly."""
        async def async_task(message: str) -> str:
            await asyncio.sleep(0.01)  # Small delay
            return f"Async result: {message}"
        
        executor = FunctionTaskExecutor(async_task, message="Hello Async")
        
        task = TaskNode(
            task_id="test_async_task",
            name="Async Task",
            priority=TaskPriority.NORMAL
        )
        
        context = {"task_id": "test_async_task"}
        
        result = await executor.execute(task, context)
        
        assert result.success is True
        assert result.result == "Async result: Hello Async"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_function_exception_handling(self):
        """Test that function exceptions are properly handled and categorized."""
        def failing_task() -> str:
            raise ValueError("This task always fails")
        
        executor = FunctionTaskExecutor(failing_task)
        
        task = TaskNode(
            task_id="failing_task",
            name="Failing Task", 
            priority=TaskPriority.NORMAL
        )
        
        context = {"task_id": "failing_task"}
        
        result = await executor.execute(task, context)
        
        assert result.success is False
        assert result.result is None
        assert result.error is not None
        assert result.error.error_type == "ValueError"
        assert result.error.message == "This task always fails"