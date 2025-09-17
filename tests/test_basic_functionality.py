"""
Basic functionality test
========================

Minimal tests to verify the testing framework is working.
"""

import pytest
from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import RetryPolicy, TaskPriority


def test_basic_imports():
    """Test that basic imports work."""
    # If we can import these, the basic structure is working
    assert TaskOrchestrator is not None
    assert RetryPolicy is not None
    assert TaskPriority is not None


def test_orchestrator_creation():
    """Test that we can create an orchestrator."""
    orchestrator = TaskOrchestrator()
    assert orchestrator is not None
    assert orchestrator.max_concurrent_tasks == 10  # Default value


def test_retry_policy_creation():
    """Test retry policy creation."""
    policy = RetryPolicy(max_attempts=3, initial_delay=0.1)
    assert policy.max_attempts == 3
    assert policy.initial_delay == 0.1


def test_task_priority_enum():
    """Test task priority enum values."""
    assert TaskPriority.LOW.value < TaskPriority.NORMAL.value
    assert TaskPriority.NORMAL.value < TaskPriority.HIGH.value
    assert TaskPriority.HIGH.value < TaskPriority.CRITICAL.value


def test_add_simple_task():
    """Test adding a simple task without execution."""
    orchestrator = TaskOrchestrator()
    
    def simple_func():
        return "test"
    
    # This should not raise an exception
    task_node = orchestrator.add_function_task("test", "Test Task", simple_func)
    assert task_node is not None
    assert task_node.task_id == "test"


def test_framework_components_exist():
    """Test that main framework components can be imported."""
    from agenticflow.orchestration.task_dag import TaskDAG
    from agenticflow.orchestration.task_management import TaskNode
    from agenticflow.tools.registry import ToolRegistry
    
    # If imports succeed, basic structure is there
    assert TaskDAG is not None
    assert TaskNode is not None
    assert ToolRegistry is not None