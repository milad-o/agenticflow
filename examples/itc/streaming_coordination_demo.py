#!/usr/bin/env python3
"""
ITC Streaming and Real-time Coordination Demo
============================================

Demonstrates the enhanced Interactive Task Control (ITC) system with:
- Real-time task streaming between coordinators and agents
- Agent-to-agent coordination with live updates
- Long-running task monitoring and status queries
- Dynamic plan modification during execution

This shows how connected agents can communicate in real-time with streaming,
or for long tasks, check back later for status updates.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json

from agenticflow import Agent, AgentConfig, LLMProviderConfig, LLMProvider
from agenticflow.core.itc import (
    get_itc_manager, initialize_itc, ITCEventType, ITCConfig
)


class StreamingCoordinatorAgent(Agent):
    """A coordinator agent that uses streaming for real-time communication."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.itc = get_itc_manager()
        self.subscription_id: Optional[str] = None
        self.connected = False
    
    async def connect_to_itc(self):
        """Connect to ITC for real-time coordination."""
        await self.itc.connect_coordinator(
            coordinator_id=self.id,
            coordinator_type="coordinator_agent",
            capabilities={
                "streaming": True,
                "interruption": True,
                "task_coordination": True
            }
        )
        self.connected = True
        print(f"🔗 {self.name} connected to ITC system")
    
    async def subscribe_to_streams(self, task_id: Optional[str] = None, agent_id: Optional[str] = None):
        """Subscribe to task streams for real-time updates."""
        self.subscription_id = self.itc.create_stream_subscription(
            coordinator_id=self.id,
            task_id=task_id,
            agent_id=agent_id,
            event_types={ITCEventType.TASK_PROGRESS, ITCEventType.REAL_TIME_UPDATE, ITCEventType.TASK_COMPLETED}
        )
        print(f"📡 {self.name} subscribed to streams (subscription: {self.subscription_id})")
    
    async def monitor_streams(self, duration: float = 30.0):
        """Monitor streams for real-time updates."""
        print(f"👁️  {self.name} monitoring streams for {duration} seconds...")
        
        start_time = time.time()
        async for update in self.itc.stream_task_updates(self.id):
            elapsed = time.time() - start_time
            
            if elapsed > duration:
                break
                
            if update.get("type") == "heartbeat":
                print(f"💓 {self.name} heartbeat: {update['timestamp']}")
            else:
                print(f"📨 {self.name} received update: {json.dumps(update, indent=2)}")
                
                # React to specific update types
                if update.get("type") == "real_time_update":
                    await self.handle_real_time_update(update)
        
        print(f"🛑 {self.name} stopped monitoring streams")
    
    async def handle_real_time_update(self, update: Dict[str, Any]):
        """Handle real-time updates from other agents."""
        data = update.get("data", {})
        update_type = data.get("update_type")
        
        if update_type == "progress":
            progress = data.get("progress", 0)
            task_id = update.get("task_id")
            print(f"📊 {self.name} sees task {task_id} at {progress:.1%} progress")
            
            # Coordinate if progress is slow
            if progress < 0.5 and time.time() % 10 < 1:  # Every ~10 seconds
                await self.coordinate_slow_task(task_id)
    
    async def coordinate_slow_task(self, task_id: str):
        """Coordinate with a slow-running task."""
        result = await self.itc.coordinate_task(
            task_id=task_id,
            coordinator_id=self.id,
            coordination_data={
                "action": "boost_priority",
                "suggestion": "Consider parallel processing",
                "coordinator": self.name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        if result.get("success"):
            print(f"🎯 {self.name} coordinated task {task_id}: boosted priority")
    
    async def interrupt_task_if_needed(self, task_id: str, max_duration: float = 45.0):
        """Interrupt a task if it runs too long."""
        await asyncio.sleep(max_duration)
        
        # Check if task is still running
        status = self.itc.get_status()
        active_task_ids = [task["task_id"] for task in status["task_details"]]
        
        if task_id in active_task_ids:
            print(f"⏰ {self.name} interrupting long-running task {task_id}")
            await self.itc.interrupt_task(task_id, f"Interrupted by {self.name} after {max_duration}s")
    
    async def query_status_later(self, delay: float = 20.0):
        """Query task status after some delay - for long tasks."""
        await asyncio.sleep(delay)
        
        status = self.itc.get_status()
        print(f"\n📋 {self.name} status check after {delay}s delay:")
        print(f"   Active tasks: {status['active_tasks']}")
        
        for task_detail in status["task_details"]:
            task_id = task_detail["task_id"]
            progress = task_detail["progress"]
            duration = task_detail["duration"]
            print(f"   Task {task_id}: {progress:.1%} complete, running {duration:.1f}s")
        
        # Get connected coordinators
        coordinators = self.itc.get_connected_coordinators()
        print(f"   Connected coordinators: {len(coordinators)}")
        for coord_id, coord_info in coordinators.items():
            print(f"     {coord_id}: {coord_info['coordinator_type']} - {coord_info['subscriptions']} subscriptions")
    
    async def disconnect_from_itc(self):
        """Disconnect from ITC system."""
        if self.subscription_id:
            self.itc.cancel_stream_subscription(self.subscription_id)
        
        if self.connected:
            await self.itc.disconnect_coordinator(self.id)
            self.connected = False
            print(f"❌ {self.name} disconnected from ITC")


class LongRunningWorkerAgent(Agent):
    """A worker agent that performs long-running tasks with progress updates."""
    
    async def execute_long_task(self, task_description: str, duration: float = 30.0):
        """Execute a long-running task with regular progress updates."""
        print(f"🚀 {self.name} starting long task: {task_description}")
        
        itc = get_itc_manager()
        
        # Start ITC task tracking  
        task_id = f"long_task_{int(time.time())}"
        await itc.start_task(task_id, task_description, self.id)
        
        start_time = time.time()
        steps = 10
        
        try:
            for step in range(steps + 1):
                # Check for interruption
                if itc.is_interrupted(task_id):
                    print(f"🛑 {self.name} task {task_id} was interrupted at step {step}")
                    break
                
                # Calculate progress
                progress = step / steps
                elapsed = time.time() - start_time
                
                # Update progress with streaming
                await itc.update_task_progress(
                    task_id=task_id,
                    progress=progress,
                    status_info=f"Step {step}/{steps} - {elapsed:.1f}s elapsed"
                )
                
                # Send custom real-time update
                await itc.send_real_time_update(
                    update_data={
                        "step": step,
                        "total_steps": steps,
                        "elapsed_time": elapsed,
                        "estimated_remaining": (duration - elapsed) if elapsed < duration else 0,
                        "worker_status": "processing",
                        "update_type": "step_progress"
                    },
                    task_id=task_id,
                    agent_id=self.id
                )
                
                # Simulate work
                step_duration = duration / steps
                await asyncio.sleep(step_duration)
                
                print(f"⚙️  {self.name} completed step {step}/{steps} ({progress:.1%})")
            
            # Complete the task
            result = {
                "status": "completed",
                "duration": time.time() - start_time,
                "steps_completed": min(step + 1, steps)
            }
            
            await itc.complete_task(task_id, result)
            print(f"✅ {self.name} completed long task {task_id}")
            
            return result
            
        except Exception as e:
            print(f"❌ {self.name} task {task_id} failed: {e}")
            await itc.complete_task(task_id, {"error": str(e)})
            raise


async def demo_streaming_coordination():
    """Demonstrate streaming and real-time coordination."""
    print("🎬 Starting ITC Streaming and Coordination Demo\n")
    
    # Initialize ITC with streaming enabled
    itc_config = ITCConfig(
        enable_streaming=True,
        stream_interval=0.5,
        enable_agent_coordination=True,
        coordination_timeout=60
    )
    initialize_itc(itc_config)
    
    # Create coordinator agent
    coordinator_config = AgentConfig(
        name="StreamingCoordinator",
        instructions="You are a streaming coordinator that monitors and coordinates tasks in real-time.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    coordinator = StreamingCoordinatorAgent(coordinator_config)
    await coordinator.start()
    
    # Create worker agents
    worker1_config = AgentConfig(
        name="LongTaskWorker1",
        instructions="You perform long-running data processing tasks.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    worker1 = LongRunningWorkerAgent(worker1_config)
    await worker1.start()
    
    worker2_config = AgentConfig(
        name="LongTaskWorker2", 
        instructions="You perform long-running analysis tasks.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    worker2 = LongRunningWorkerAgent(worker2_config)
    await worker2.start()
    
    try:
        # Connect coordinator to ITC system
        await coordinator.connect_to_itc()
        await coordinator.subscribe_to_streams()
        
        print("\n🎯 Starting coordinated long-running tasks...\n")
        
        # Start tasks concurrently
        tasks = [
            coordinator.monitor_streams(duration=40.0),  # Monitor for 40 seconds
            coordinator.query_status_later(delay=15.0),  # Query status after 15 seconds
            coordinator.query_status_later(delay=25.0),  # Query status after 25 seconds
            coordinator.interrupt_task_if_needed("long_task_worker2", max_duration=35.0),  # Interrupt if needed
            worker1.execute_long_task("Process large dataset", duration=20.0),
            worker2.execute_long_task("Analyze complex patterns", duration=30.0)
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print("\n📊 Final Results:")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  Task {i}: Exception - {result}")
            else:
                print(f"  Task {i}: {result}")
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await coordinator.disconnect_from_itc()
        await coordinator.stop()
        await worker1.stop()
        await worker2.stop()
        
        # Final ITC status
        final_status = get_itc_manager().get_status()
        print(f"\n📈 Final ITC Status:")
        print(f"   Total tasks started: {final_status['stats']['tasks_started']}")
        print(f"   Total tasks completed: {final_status['stats']['tasks_completed']}")
        print(f"   Total tasks interrupted: {final_status['stats']['tasks_interrupted']}")
        print(f"   Active tasks: {final_status['active_tasks']}")


async def demo_long_task_polling():
    """Demonstrate polling-style interaction for very long tasks."""
    print("\n🔄 Starting Long Task Polling Demo\n")
    
    # Create a worker for very long tasks
    worker_config = AgentConfig(
        name="VeryLongTaskWorker",
        instructions="You perform very long-running tasks that may take hours.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    worker = LongRunningWorkerAgent(worker_config)
    await worker.start()
    
    # Create a polling coordinator
    coordinator_config = AgentConfig(
        name="PollingCoordinator",
        instructions="You check on long tasks periodically.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    coordinator = StreamingCoordinatorAgent(coordinator_config)
    await coordinator.start()
    await coordinator.connect_to_itc()
    
    try:
        print("🎯 Starting very long task with periodic status checks...\n")
        
        # Start a long task
        long_task = asyncio.create_task(
            worker.execute_long_task("Simulate multi-hour data processing", duration=25.0)
        )
        
        # Poll status every few seconds
        for check_num in range(6):  # 6 checks over ~25 seconds
            await asyncio.sleep(4.0)  # Wait 4 seconds between checks
            
            print(f"\n🔍 Status Check #{check_num + 1}:")
            await coordinator.query_status_later(delay=0.1)  # Immediate status
            
            # Simulate coordinator going away and coming back
            if check_num == 2:
                print("📴 Coordinator disconnecting (simulating network issue)...")
                await coordinator.disconnect_from_itc()
                await asyncio.sleep(2.0)
                print("🔌 Coordinator reconnecting...")
                await coordinator.connect_to_itc()
        
        # Wait for task completion
        result = await long_task
        print(f"\n✅ Long task completed: {result}")
    
    finally:
        await coordinator.disconnect_from_itc()
        await coordinator.stop()
        await worker.stop()


if __name__ == "__main__":
    print("🎭 ITC Streaming and Real-time Coordination Demo")
    print("=" * 60)
    
    async def run_demos():
        # Run streaming coordination demo
        await demo_streaming_coordination()
        
        print("\n" + "=" * 60)
        
        # Run long task polling demo
        await demo_long_task_polling()
        
        print("\n🎉 All demos completed!")
    
    asyncio.run(run_demos())