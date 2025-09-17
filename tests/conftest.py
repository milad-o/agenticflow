"""
Test Configuration and Fixtures
===============================

Global pytest configuration and shared fixtures for AgenticFlow tests.
"""

import asyncio
import pytest
import tempfile
import shutil
import os
from typing import Dict, Any
from pathlib import Path

# Add src to Python path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import RetryPolicy, TaskPriority
from agenticflow.tools.registry import ToolRegistry


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_retry_policy():
    """Create a sample retry policy for testing."""
    return RetryPolicy(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=1.0,
        backoff_multiplier=2.0
    )


@pytest.fixture
def basic_orchestrator(sample_retry_policy):
    """Create a basic task orchestrator for testing."""
    return TaskOrchestrator(
        max_concurrent_tasks=2,
        default_retry_policy=sample_retry_policy
    )


@pytest.fixture
def tool_registry():
    """Create a tool registry with basic tools for testing."""
    registry = ToolRegistry()
    
    # Register some basic tools for testing
    @registry.register_function("test_add")
    def add_numbers(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
    
    @registry.register_function("test_multiply")
    def multiply_numbers(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
    
    @registry.register_function("test_async_operation")
    async def async_operation(delay: float = 0.1) -> str:
        """Perform an async operation with delay."""
        await asyncio.sleep(delay)
        return "completed"
    
    return registry




@pytest.fixture
def sample_task_data():
    """Sample data for testing task operations."""
    return {
        "task_1": {
            "name": "Sample Task 1",
            "function": lambda: "result_1",
            "priority": TaskPriority.HIGH
        },
        "task_2": {
            "name": "Sample Task 2", 
            "function": lambda: "result_2",
            "priority": TaskPriority.NORMAL,
            "dependencies": ["task_1"]
        },
        "task_3": {
            "name": "Sample Task 3",
            "function": lambda: "result_3", 
            "priority": TaskPriority.LOW,
            "dependencies": ["task_1", "task_2"]
        }
    }


class MockLLMProvider:
    """Mock LLM provider for testing without API calls."""
    
    def __init__(self):
        self.call_count = 0
        self.responses = []
    
    def set_responses(self, responses: list):
        """Set predefined responses for testing."""
        self.responses = responses
        self.call_count = 0
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Mock generation method."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return "mock_response"
    
    async def chat(self, messages: list, **kwargs) -> str:
        """Mock chat method."""
        return await self.generate("", **kwargs)


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider for testing."""
    return MockLLMProvider()


# Test data fixtures
@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for integration testing."""
    return {
        "simple_workflow": [
            {"id": "start", "name": "Start Task", "dependencies": []},
            {"id": "process", "name": "Process Task", "dependencies": ["start"]},
            {"id": "end", "name": "End Task", "dependencies": ["process"]}
        ],
        "parallel_workflow": [
            {"id": "init", "name": "Initialize", "dependencies": []},
            {"id": "branch_1", "name": "Branch 1", "dependencies": ["init"]},
            {"id": "branch_2", "name": "Branch 2", "dependencies": ["init"]},
            {"id": "merge", "name": "Merge", "dependencies": ["branch_1", "branch_2"]}
        ]
    }


# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance testing."""
    return {
        "max_execution_time": 10.0,  # seconds
        "memory_limit": 100 * 1024 * 1024,  # 100MB
        "concurrent_task_limit": 10
    }


# Async test helper
def async_test(func):
    """Decorator to run async tests."""
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(func(*args, **kwargs))
    return wrapper


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow