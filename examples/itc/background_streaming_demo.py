#!/usr/bin/env python3
"""
Background Streaming Demo
========================

Demonstrates how ITC background streaming works automatically in multi-agent systems.
Shows realistic scenarios where agents coordinate in the background while performing tasks.

Key features demonstrated:
- Automatic background streaming (no manual streaming setup needed)
- Agents automatically coordinate without explicit coordination calls
- Real-time monitoring of other agents' work
- Dynamic task modification based on agent observations
"""

import asyncio
import time
import random
from typing import List, Dict, Any

from agenticflow import Agent, AgentConfig, LLMProviderConfig, LLMProvider
from agenticflow.core.itc import get_itc_manager, initialize_itc, ITCConfig, ITCEventType


class BackgroundWorkerAgent(Agent):
    """Worker agent that performs tasks with automatic streaming."""
    
    async def perform_data_analysis(self, dataset_name: str, complexity: int = 5):
        """Simulate data analysis work with progress updates."""
        print(f"🔬 {self.name} starting analysis of {dataset_name}")
        
        # This will automatically create ITC task tracking and streaming
        task_result = await self.execute_task(
            f"Analyze dataset '{dataset_name}' with complexity level {complexity}"
        )
        
        # Simulate additional work with manual progress updates
        itc = get_itc_manager()
        
        # Find our task ID from recent activities
        status = itc.get_status()
        our_tasks = [task for task in status["task_details"] 
                    if task["agent_id"] == self.id and "running" in task["status"]]
        
        if our_tasks:
            task_id = our_tasks[0]["task_id"]
            
            # Simulate multi-stage analysis
            stages = ["Data cleaning", "Feature extraction", "Statistical analysis", "Report generation"]
            for i, stage in enumerate(stages):
                progress = (i + 1) / len(stages)
                
                # This automatically streams to other connected agents
                await itc.update_task_progress(
                    task_id=task_id,
                    progress=progress,
                    status_info=f"Stage {i+1}/4: {stage}"
                )
                
                # Send custom update with analysis insights
                await itc.send_real_time_update({
                    "stage": stage,
                    "findings": f"Found {random.randint(1, 10)} insights in {stage.lower()}",
                    "complexity_handled": complexity,
                    "update_type": "analysis_progress"
                }, task_id, self.id)
                
                # Simulate work time
                await asyncio.sleep(2.0)
        
        print(f"✅ {self.name} completed analysis of {dataset_name}")
        return task_result


class BackgroundCoordinatorAgent(Agent):
    """Coordinator agent that monitors and coordinates other agents automatically."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.monitored_agents: List[str] = []
        self.coordination_actions_taken = 0
        
    async def start_background_monitoring(self, agents_to_monitor: List[Agent]):
        """Start monitoring other agents in the background."""
        self.monitored_agents = [agent.id for agent in agents_to_monitor]
        
        itc = get_itc_manager()
        
        # Subscribe to all updates from monitored agents
        for agent in agents_to_monitor:
            itc.create_stream_subscription(
                coordinator_id=self.id,
                agent_id=agent.id,
                event_types={
                    ITCEventType.TASK_PROGRESS,
                    ITCEventType.REAL_TIME_UPDATE,
                    ITCEventType.TASK_STARTED,
                    ITCEventType.TASK_COMPLETED
                }
            )
        
        # Start background monitoring task
        asyncio.create_task(self._background_monitoring_loop())
        print(f"👁️  {self.name} started background monitoring of {len(agents_to_monitor)} agents")
    
    async def _background_monitoring_loop(self):
        """Background loop that monitors and coordinates automatically."""
        itc = get_itc_manager()
        
        try:
            # Monitor streams in the background
            async for update in itc.stream_task_updates(self.id):
                await self._handle_background_update(update)
        except asyncio.CancelledError:
            print(f"🛑 {self.name} stopped background monitoring")
        except Exception as e:
            print(f"❌ {self.name} monitoring error: {e}")
    
    async def _handle_background_update(self, update: Dict[str, Any]):
        """Handle updates from monitored agents automatically."""
        if update.get("type") == "heartbeat":
            return  # Ignore heartbeats
        
        update_data = update.get("data", {})
        task_id = update.get("task_id")
        agent_id = update.get("agent_id")
        
        # React to different types of updates
        if update_data.get("update_type") == "analysis_progress":
            await self._handle_analysis_update(update_data, task_id, agent_id)
        elif update_data.get("update_type") == "progress":
            await self._handle_progress_update(update_data, task_id, agent_id)
        elif update_data.get("update_type") == "background_status":
            await self._handle_background_status(update_data, task_id, agent_id)
    
    async def _handle_analysis_update(self, data: Dict[str, Any], task_id: str, agent_id: str):
        """Handle analysis progress updates."""
        stage = data.get("stage", "Unknown")
        findings = data.get("findings", "No findings")
        complexity = data.get("complexity_handled", 1)
        
        print(f"📊 {self.name} sees: Agent {agent_id[-8:]} - {stage}: {findings}")
        
        # Coordinate if complexity is high and findings are low
        if complexity > 3 and "1 insights" in findings:
            await self._coordinate_performance_boost(task_id, agent_id, stage)
    
    async def _handle_progress_update(self, data: Dict[str, Any], task_id: str, agent_id: str):
        """Handle task progress updates."""
        progress = data.get("progress", 0)
        
        # Intervene if progress is slow
        if progress < 0.3 and random.random() < 0.2:  # 20% chance to help
            await self._offer_assistance(task_id, agent_id, progress)
    
    async def _handle_background_status(self, data: Dict[str, Any], task_id: str, agent_id: str):
        """Handle background status updates."""
        status = data.get("status", "unknown")
        duration = data.get("duration", 0)
        
        # Intervene if task is running too long
        if duration > 10 and status == "running":
            await self._suggest_optimization(task_id, agent_id, duration)
    
    async def _coordinate_performance_boost(self, task_id: str, agent_id: str, stage: str):
        """Coordinate to boost performance for low-insight stages."""
        itc = get_itc_manager()
        
        result = await itc.coordinate_task(
            task_id=task_id,
            coordinator_id=self.id,
            coordination_data={
                "action": "performance_boost",
                "reason": f"Low insights detected in {stage}",
                "suggestion": "Try alternative analysis methods",
                "coordinator": self.name,
                "boost_level": "high"
            }
        )
        
        if result.get("success"):
            self.coordination_actions_taken += 1
            print(f"🎯 {self.name} coordinated performance boost for {agent_id[-8:]} in {stage}")
    
    async def _offer_assistance(self, task_id: str, agent_id: str, progress: float):
        """Offer assistance to slow-progressing tasks."""
        itc = get_itc_manager()
        
        await itc.coordinate_task(
            task_id=task_id,
            coordinator_id=self.id,
            coordination_data={
                "action": "offer_assistance",
                "reason": f"Progress slow at {progress:.1%}",
                "suggestion": "Consider parallel processing or resource allocation",
                "assistance_type": "resource_boost"
            }
        )
        
        self.coordination_actions_taken += 1
        print(f"🤝 {self.name} offered assistance to {agent_id[-8:]} (progress: {progress:.1%})")
    
    async def _suggest_optimization(self, task_id: str, agent_id: str, duration: float):
        """Suggest optimization for long-running tasks."""
        itc = get_itc_manager()
        
        await itc.coordinate_task(
            task_id=task_id,
            coordinator_id=self.id,
            coordination_data={
                "action": "suggest_optimization",
                "reason": f"Task running for {duration:.1f}s",
                "suggestion": "Consider breaking into smaller chunks",
                "optimization_type": "time_management"
            }
        )
        
        self.coordination_actions_taken += 1
        print(f"⚡ {self.name} suggested optimization to {agent_id[-8:]} (duration: {duration:.1f}s)")


async def demo_background_streaming():
    """Demonstrate automatic background streaming and coordination."""
    print("🎭 Background Streaming Demo")
    print("=" * 50)
    print("Agents will coordinate automatically in the background!")
    print()
    
    # Initialize ITC with background streaming enabled
    itc_config = ITCConfig(
        enable_streaming=True,
        stream_interval=1.0,  # 1 second intervals
        enable_agent_coordination=True,
        coordination_timeout=30
    )
    initialize_itc(itc_config)
    
    # Create worker agents
    worker_agents = []
    for i in range(3):
        config = AgentConfig(
            name=f"DataAnalyst_{i+1}",
            instructions=f"You are data analyst #{i+1} specializing in complex data analysis.",
            llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
        )
        agent = BackgroundWorkerAgent(config)
        worker_agents.append(agent)
    
    # Create coordinator agent
    coordinator_config = AgentConfig(
        name="AnalysisCoordinator",
        instructions="You coordinate and optimize data analysis workflows.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    coordinator = BackgroundCoordinatorAgent(coordinator_config)
    
    try:
        # Start all agents (they auto-connect to ITC)
        print("🚀 Starting agents...")
        for agent in worker_agents:
            await agent.start()
        await coordinator.start()
        
        # Start background monitoring
        await coordinator.start_background_monitoring(worker_agents)
        
        print("\n📊 Starting coordinated data analysis tasks...")
        print("(Watch for automatic coordination messages)\n")
        
        # Start multiple analysis tasks concurrently
        analysis_tasks = [
            worker_agents[0].perform_data_analysis("Customer_Dataset_A", complexity=4),
            worker_agents[1].perform_data_analysis("Sales_Dataset_B", complexity=6),
            worker_agents[2].perform_data_analysis("Product_Dataset_C", complexity=2),
        ]
        
        # Let tasks run and coordinate automatically
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        print("\n📈 Analysis Results:")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  Analyst {i+1}: Error - {result}")
            else:
                print(f"  Analyst {i+1}: Completed successfully")
        
        # Show coordination statistics
        print(f"\n🎯 Coordination Summary:")
        print(f"  Coordination actions taken: {coordinator.coordination_actions_taken}")
        
        # Show final ITC status
        final_status = get_itc_manager().get_status()
        print(f"  Total tasks completed: {final_status['stats']['tasks_completed']}")
        print(f"  Connected coordinators: {len(final_status.get('task_details', []))}")
        
        # Let background monitoring run a bit longer
        print(f"\n⏳ Letting background monitoring run for 5 more seconds...")
        await asyncio.sleep(5.0)
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        for agent in worker_agents:
            await agent.stop()
        await coordinator.stop()
        
        # Stop background monitoring
        itc = get_itc_manager()
        itc.disable_background_monitoring()


async def demo_polling_pattern():
    """Demonstrate polling pattern for very long-running tasks."""
    print("\n🔄 Long-task Polling Pattern Demo")
    print("=" * 50)
    
    # Create a long-running worker
    worker_config = AgentConfig(
        name="LongRunningAnalyst",
        instructions="You perform very long data analysis tasks.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    worker = BackgroundWorkerAgent(worker_config)
    
    # Create a polling supervisor
    supervisor_config = AgentConfig(
        name="PollingSupervisor", 
        instructions="You check on long-running tasks periodically.",
        llm=LLMProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    )
    supervisor = Agent(supervisor_config)
    
    try:
        await worker.start()
        await supervisor.start()
        
        print("🚀 Starting very long analysis task...")
        
        # Start long task
        long_task = asyncio.create_task(
            worker.perform_data_analysis("Massive_Dataset_XL", complexity=8)
        )
        
        # Polling supervisor checks periodically
        itc = get_itc_manager()
        
        for check_num in range(4):  # 4 status checks
            await asyncio.sleep(3.0)  # Wait between checks
            
            status = itc.get_status()
            print(f"\n📋 Status Check #{check_num + 1} by {supervisor.name}:")
            print(f"   Active tasks: {len(status['task_details'])}")
            
            for task_detail in status["task_details"]:
                if task_detail["agent_id"] == worker.id:
                    progress = task_detail["progress"]
                    duration = task_detail["duration"]
                    print(f"   🔬 {worker.name}: {progress:.1%} complete, {duration:.1f}s elapsed")
                    
                    # Supervisor can take action based on polling
                    if progress < 0.5 and duration > 6:
                        print(f"   🎯 {supervisor.name}: Task seems slow, considering intervention...")
                        
                        # Could coordinate here if needed
                        await itc.coordinate_task(
                            task_id=task_detail["task_id"],
                            coordinator_id=supervisor.id,
                            coordination_data={
                                "action": "status_check_intervention",
                                "note": f"Checked at {duration:.1f}s with {progress:.1%} progress"
                            }
                        )
        
        # Wait for completion
        result = await long_task
        print(f"\n✅ Long analysis completed: {result.get('response', 'Success')}")
        
    finally:
        await worker.stop()
        await supervisor.stop()


if __name__ == "__main__":
    async def main():
        # Run background streaming demo
        await demo_background_streaming()
        
        # Run polling pattern demo
        await demo_polling_pattern()
        
        print("\n🎉 Background streaming demos completed!")
        print("\nKey takeaways:")
        print("- Agents automatically connect and stream when ITC is enabled")
        print("- Background monitoring runs without explicit setup")
        print("- Coordinators can react to events automatically")
        print("- Both real-time streaming and polling patterns are supported")
    
    asyncio.run(main())