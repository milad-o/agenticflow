"""
Simple validation test for enhanced orchestrator
"""

import asyncio
import pytest
from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import FunctionTaskExecutor, TaskState


class SimpleFunction:
    """Test function that tracks its execution."""
    def __init__(self):
        self.called = False
        
    async def __call__(self):
        self.called = True
        await asyncio.sleep(0.1)
        return "Function completed"


@pytest.mark.asyncio
async def test_simple_orchestrator_validation():
    """Test basic functionality of enhanced orchestrator."""
    # Create orchestrator
    orchestrator = TaskOrchestrator()
    
    # Create simple function
    func = SimpleFunction()
    executor = FunctionTaskExecutor(func)
    
    # Add task
    task = orchestrator.add_interactive_task(
        task_id="simple_test",
        name="Simple Test",
        executor=executor
    )
    
    # Verify task creation
    assert task.task_id == "simple_test"
    assert task.state == TaskState.PENDING
    assert not func.called, "Function should not be called before execution"
    
    # Execute workflow
    updates = []
    async for update in orchestrator.execute_workflow_with_streaming():
        updates.append(update)
        if update.get("type") == "workflow_completed":
            break
    
    # Verify execution
    assert func.called, "Function should be called after execution"
    assert task.state == TaskState.COMPLETED
    assert task.result is not None
    assert task.result.success
    assert task.result.result == "Function completed"
    assert len(updates) > 0, "Should receive streaming updates"
    
    # Verify update types
    update_types = [u.get("type") for u in updates]
    assert "status_update" in update_types, "Should receive status updates"
    assert "workflow_completed" in update_types, "Should receive completion update"
