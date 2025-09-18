#!/usr/bin/env python3
"""
Simple ITC Streaming Example
============================

Demonstrates basic streaming communication between connected agents:
- Agent A starts a task and streams progress updates
- Agent B subscribes to Agent A's updates and reacts in real-time
- Coordinator C polls status periodically for long-running tasks
"""

import asyncio
import time
from agenticflow import Agent, AgentConfig, LLMProviderConfig, LLMProvider
from agenticflow.core.itc import get_itc_manager, initialize_itc, ITCEventType, ITCConfig


class StreamingAgent(Agent):
    """An agent that can stream updates and coordinate with others."""
    
    async def connect_for_streaming(self):
        """Connect to ITC system for real-time communication."""
        itc = get_itc_manager()
        await itc.connect_coordinator(self.id, "agent", {"streaming": True})
        print(f"🔗 {self.name} connected for streaming")
    
    async def stream_task_progress(self, task_name: str, duration: float = 10.0):
        """Perform a task while streaming progress updates."""
        itc = get_itc_manager()
        task_id = f"{self.name.lower().replace(' ', '_')}_task"
        
        print(f"🚀 {self.name} starting: {task_name}")
        await itc.start_task(task_id, task_name, self.id)
        
        start_time = time.time()
        steps = 5
        
        for step in range(steps + 1):
            if itc.is_interrupted(task_id):
                print(f"🛑 {self.name} task interrupted!")
                break
            
            progress = step / steps
            elapsed = time.time() - start_time
            
            # Stream progress update
            await itc.update_task_progress(
                task_id, progress, f"Step {step}/{steps} - {elapsed:.1f}s"
            )
            
            # Send detailed update
            await itc.send_real_time_update({
                "worker": self.name,
                "step": step,
                "message": f"Completed step {step} of {task_name}",
                "update_type": "progress"
            }, task_id, self.id)
            
            print(f"⚙️  {self.name} step {step}/{steps} ({progress:.0%})")
            await asyncio.sleep(duration / steps)
        
        await itc.complete_task(task_id, {"completed_steps": step + 1})
        print(f"✅ {self.name} finished: {task_name}")
        return task_id
    
    async def subscribe_and_watch(self, duration: float = 15.0):
        """Subscribe to updates and watch other agents' progress."""
        itc = get_itc_manager()
        
        # Subscribe to all real-time updates
        subscription_id = itc.create_stream_subscription(
            self.id, 
            event_types={ITCEventType.REAL_TIME_UPDATE, ITCEventType.TASK_PROGRESS}
        )
        
        print(f"👁️  {self.name} watching for updates...")
        
        start_time = time.time()
        async for update in itc.stream_task_updates(self.id):
            elapsed = time.time() - start_time
            if elapsed > duration:
                break
            
            if update.get("type") == "real_time_update":
                data = update.get("data", {})
                if data.get("worker") != self.name:  # Don't watch own updates
                    worker = data.get("worker", "Unknown")
                    message = data.get("message", "Update")
                    print(f"👀 {self.name} sees: {worker} - {message}")
            elif update.get("type") == "heartbeat":
                print(f"💓 {self.name} heartbeat")
        
        print(f"👁️  {self.name} stopped watching")
        return subscription_id
    
    async def poll_status(self, check_interval: float = 3.0, max_checks: int = 5):
        """Poll system status periodically (for long tasks)."""
        itc = get_itc_manager()
        
        for check in range(max_checks):
            await asyncio.sleep(check_interval)
            
            status = itc.get_status()
            active_tasks = len(status["task_details"])
            
            print(f"📊 {self.name} status check #{check + 1}: {active_tasks} active tasks")
            
            for task in status["task_details"]:
                task_id = task["task_id"]
                progress = task["progress"]
                duration = task["duration"]
                print(f"   📋 {task_id}: {progress:.0%} complete, {duration:.1f}s running")
        
        print(f"📊 {self.name} finished status polling")


async def simple_streaming_demo():
    """Run a simple streaming demo."""
    print("🎬 Simple ITC Streaming Demo")
    print("=" * 40)
    
    # Initialize ITC
    initialize_itc(ITCConfig(enable_streaming=True, stream_interval=0.5))
    
    # Create agents
    worker_config = AgentConfig(
        name="Worker Agent",
        instructions="You perform tasks and stream progress updates.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    worker = StreamingAgent(worker_config)
    
    watcher_config = AgentConfig(
        name="Watcher Agent", 
        instructions="You watch other agents' progress in real-time.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    watcher = StreamingAgent(watcher_config)
    
    coordinator_config = AgentConfig(
        name="Coordinator Agent",
        instructions="You poll system status periodically.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    coordinator = StreamingAgent(coordinator_config)
    
    try:
        # Start agents
        await worker.start()
        await watcher.start() 
        await coordinator.start()
        
        # Connect to ITC
        await worker.connect_for_streaming()
        await watcher.connect_for_streaming()
        await coordinator.connect_for_streaming()
        
        print("\n🎯 Starting coordinated tasks...\n")
        
        # Run tasks concurrently
        tasks = [
            worker.stream_task_progress("Data Processing Task", duration=12.0),
            watcher.subscribe_and_watch(duration=15.0),
            coordinator.poll_status(check_interval=4.0, max_checks=4)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print("\n📊 Results:")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  Task {i}: Error - {result}")
            else:
                print(f"  Task {i}: {result}")
    
    finally:
        # Cleanup
        print("\n🧹 Cleanup...")
        await worker.stop()
        await watcher.stop()
        await coordinator.stop()
        
        final_status = get_itc_manager().get_status()
        print(f"\n📈 Final Stats: {final_status['stats']['tasks_completed']} tasks completed")


if __name__ == "__main__":
    asyncio.run(simple_streaming_demo())