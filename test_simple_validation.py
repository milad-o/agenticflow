#!/usr/bin/env python3
"""
Simple validation test for enhanced orchestrator
"""

import asyncio
import time

from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import FunctionTaskExecutor


class SimpleFunction:
    def __init__(self):
        self.called = False
        
    async def __call__(self):
        print(f"SimpleFunction called")
        self.called = True
        await asyncio.sleep(0.1)
        return "Function completed"


async def main():
    print("🧪 Simple Enhanced Orchestrator Validation")
    print("=" * 50)
    
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
    
    print(f"Task created: {task.task_id}")
    print(f"Task state: {task.state}")
    print(f"Function called before: {func.called}")
    
    # Execute workflow
    print("\nExecuting workflow...")
    updates = []
    async for update in orchestrator.execute_workflow_with_streaming():
        updates.append(update)
        print(f"Update: {update.get('type', 'unknown')}")
        if update.get("type") == "workflow_completed":
            break
    
    print(f"\nExecution complete!")
    print(f"Function called after: {func.called}")
    print(f"Task state: {task.state}")
    print(f"Task result: {task.result}")
    print(f"Updates received: {len(updates)}")
    
    # Check task result
    if task.result:
        print(f"Task result success: {task.result.success}")
        print(f"Task result data: {task.result.result}")
    
    return func.called


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n✅ Validation {'PASSED' if result else 'FAILED'}!")