#!/usr/bin/env python3
"""
Simple Streaming Example with Embedded Interactive Control
==========================================================

Demonstrates basic streaming communication using TaskOrchestrator's embedded 
interactive control capabilities:
- TaskOrchestrator executes tasks with real-time streaming
- Coordinators can connect and subscribe to updates
- Interactive task control is fully integrated into the orchestration engine
"""

import asyncio
import time
from agenticflow import TaskOrchestrator, FunctionTaskExecutor
from agenticflow.orchestration.task_management import TaskPriority
from agenticflow.orchestration.task_orchestrator import CoordinationEventType


# Simulated work functions for demonstration
class WorkerFunctions:
    """Functions that simulate work with progress tracking."""
    
    @staticmethod
    def data_processing_task():
        """Simulate a data processing task."""
        import time
        time.sleep(2)  # Simulate work
        return "Data processing completed successfully"
    
    @staticmethod
    def analysis_task():
        """Simulate an analysis task."""
        import time
        time.sleep(1.5)  # Simulate work
        return "Analysis completed successfully"
    
    @staticmethod
    def cleanup_task():
        """Simulate a cleanup task."""
        import time
        time.sleep(1)  # Simulate work
        return "Cleanup completed successfully"


async def simple_streaming_demo():
    """Run a simple streaming demo using embedded interactive control."""
    print("🍬 Simple Streaming Demo with Embedded Interactive Control")
    print("=" * 60)
    
    # Create TaskOrchestrator with embedded interactive control
    orchestrator = TaskOrchestrator(
        max_concurrent_tasks=3,
        enable_streaming=True,
        enable_coordination=True,
        stream_interval=0.5  # Stream updates every 500ms
    )
    
    print("🚀 TaskOrchestrator created with embedded interactive control")
    
    # Connect coordinator for streaming
    coordinator_id = "demo_coordinator"
    await orchestrator.connect_coordinator(coordinator_id, "human")
    print(f"🔗 Coordinator {coordinator_id} connected for streaming")
    
    # Create stream subscription
    subscription_id = orchestrator.create_stream_subscription(
        coordinator_id,
        event_types={CoordinationEventType.TASK_STARTED, CoordinationEventType.TASK_COMPLETED, CoordinationEventType.TASK_PROGRESS}
    )
    print(f"📺 Stream subscription created: {subscription_id}")
    
    try:
        # Add interactive tasks with streaming enabled
        print("\n🏗️ Adding interactive tasks...")
        
        # Task 1: Data processing with interruption capability
        task1 = orchestrator.add_interactive_task(
            task_id="data_processing",
            name="Data Processing Task",
            executor=FunctionTaskExecutor(WorkerFunctions.data_processing_task),
            streaming_enabled=True,
            interruptible=True,
            priority=TaskPriority.HIGH
        )
        
        # Task 2: Analysis task
        task2 = orchestrator.add_interactive_task(
            task_id="analysis",
            name="Analysis Task",
            executor=FunctionTaskExecutor(WorkerFunctions.analysis_task),
            dependencies=["data_processing"],
            streaming_enabled=True,
            interruptible=True
        )
        
        # Task 3: Cleanup task
        task3 = orchestrator.add_interactive_task(
            task_id="cleanup",
            name="Cleanup Task",
            executor=FunctionTaskExecutor(WorkerFunctions.cleanup_task),
            dependencies=["analysis"],
            streaming_enabled=True,
            interruptible=False  # Cleanup should not be interrupted
        )
        
        print(f"✅ Added {len(orchestrator.dag.tasks)} interactive tasks")
        
        # Start execution with real-time streaming
        print("\n🎯 Starting workflow execution with streaming...\n")
        
        # Create monitoring task
        async def monitor_updates():
            """Monitor and display real-time updates."""
            update_count = 0
            async for update in orchestrator.stream_updates(coordinator_id):
                update_count += 1
                update_type = update.get("type", "unknown")
                
                if update_type == "task_started":
                    task_id = update.get("task_id")
                    print(f"⚡ Task started: {task_id}")
                elif update_type == "task_completed":
                    task_id = update.get("task_id")
                    print(f"✅ Task completed: {task_id}")
                elif update_type == "task_progress":
                    task_id = update.get("task_id")
                    data = update.get("data", {})
                    print(f"📈 Progress update for {task_id}: {data}")
                elif update_type == "workflow_completed":
                    print(f"🎉 Workflow completed! Total updates received: {update_count}")
                    break
                elif update_type == "heartbeat":
                    print("💓 Heartbeat received")
                else:
                    print(f"📬 Update: {update_type} - {update}")
        
        # Run workflow and monitoring concurrently
        monitoring_task = asyncio.create_task(monitor_updates())
        
        # Execute workflow with streaming and collect results
        workflow_results = []
        async for update in orchestrator.execute_workflow_with_streaming():
            workflow_results.append(update)
            if update.get("type") == "workflow_completed":
                break
        
        # Cancel monitoring after workflow completes
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
        
        # Show final results
        print("\n📈 Final Results:")
        status = orchestrator.get_comprehensive_status()
        workflow_status = status["workflow_status"]
        
        print(f"  Total Tasks: {workflow_status['total_tasks']}")
        print(f"  Completed: {workflow_status['completed_tasks']}")
        print(f"  Failed: {workflow_status['failed_tasks']}")
        print(f"  Progress: {workflow_status['progress_percentage']:.1f}%")
        print(f"  Coordination Actions: {workflow_status['coordination_actions']}")
        
        return workflow_results
    
    except Exception as e:
        print(f"⚠️ Error during execution: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(simple_streaming_demo())