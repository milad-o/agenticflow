#!/usr/bin/env python3
"""
Background Streaming Demo with Groq
==================================

Demonstrates how ITC background streaming works automatically in multi-agent systems.
Uses Groq for more accessible testing without OpenAI API keys.

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
            f"Analyze dataset '{dataset_name}' with complexity level {complexity}. Provide a brief summary of the analysis process."
        )
        
        # Simulate additional work with manual progress updates
        itc = get_itc_manager()
        
        # Find our task ID from recent activities
        status = itc.get_status()
        our_tasks = [task for task in status["task_details"] 
                    if task["agent_id"] == self.id and task["status"] == "running"]
        
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
                await asyncio.sleep(1.5)
        
        print(f"✅ {self.name} completed analysis of {dataset_name}")
        return task_result


class BackgroundCoordinatorAgent(Agent):
    """Coordinator agent that monitors and coordinates other agents automatically."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.monitored_agents: List[str] = []
        self.coordination_actions_taken = 0
        self._monitoring_task = None
        
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
        self._monitoring_task = asyncio.create_task(self._background_monitoring_loop())
        print(f"👁️  {self.name} started background monitoring of {len(agents_to_monitor)} agents")
    
    async def stop_background_monitoring(self):
        """Stop background monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
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
        if progress < 0.3 and random.random() < 0.3:  # 30% chance to help
            await self._offer_assistance(task_id, agent_id, progress)
    
    async def _handle_background_status(self, data: Dict[str, Any], task_id: str, agent_id: str):
        """Handle background status updates."""
        status = data.get("status", "unknown")
        duration = data.get("duration", 0)
        
        # Intervene if task is running too long
        if duration > 8 and status == "running":
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
    print("🎭 Background Streaming Demo with Groq")
    print("=" * 55)
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
    
    # Create worker agents using Groq
    worker_agents = []
    for i in range(3):
        config = AgentConfig(
            name=f"DataAnalyst_{i+1}",
            instructions=f"You are data analyst #{i+1} specializing in complex data analysis. Provide brief, concise responses focusing on key insights.",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ, 
                model="llama-3.1-8b-instant",
                temperature=0.3
            )
        )
        agent = BackgroundWorkerAgent(config)
        worker_agents.append(agent)
    
    # Create coordinator agent using Groq
    coordinator_config = AgentConfig(
        name="AnalysisCoordinator",
        instructions="You coordinate and optimize data analysis workflows. Keep responses brief and actionable.",
        llm=LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-8b-instant",
            temperature=0.1
        )
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
                response = result.get('response', 'Completed')
                # Truncate long responses for readability
                if len(response) > 100:
                    response = response[:100] + "..."
                print(f"  Analyst {i+1}: {response}")
        
        # Show coordination statistics
        print(f"\n🎯 Coordination Summary:")
        print(f"  Coordination actions taken: {coordinator.coordination_actions_taken}")
        
        # Show final ITC status
        final_status = get_itc_manager().get_status()
        print(f"  Total tasks completed: {final_status['stats']['tasks_completed']}")
        print(f"  Connected coordinators: {len(final_status.get('task_details', []))}")
        
        # Let background monitoring run a bit longer to show background updates
        print(f"\n⏳ Letting background monitoring run for 3 more seconds...")
        await asyncio.sleep(3.0)
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await coordinator.stop_background_monitoring()
        for agent in worker_agents:
            await agent.stop()
        await coordinator.stop()
        
        # Stop background monitoring
        itc = get_itc_manager()
        itc.disable_background_monitoring()


async def demo_no_llm_background():
    """Demonstrate background streaming without actual LLM calls."""
    print("\n🤖 No-LLM Background Streaming Demo")
    print("=" * 45)
    print("Pure ITC streaming without LLM dependency")
    print()
    
    # Initialize ITC 
    itc_config = ITCConfig(
        enable_streaming=True,
        stream_interval=0.5,
        enable_agent_coordination=True
    )
    initialize_itc(itc_config)
    
    itc = get_itc_manager()
    
    # Create mock agents (no LLM needed)
    agents = ["DataProcessor_1", "DataProcessor_2", "DataProcessor_3"]
    coordinator_id = "StreamingCoordinator"
    
    try:
        # Connect agents and coordinator
        for agent_id in agents:
            await itc.connect_coordinator(agent_id, "agent", {"streaming": True})
        
        await itc.connect_coordinator(coordinator_id, "coordinator", {"streaming": True})
        
        # Subscribe coordinator to agent updates
        for agent_id in agents:
            itc.create_stream_subscription(
                coordinator_id=coordinator_id,
                agent_id=agent_id,
                event_types={ITCEventType.TASK_PROGRESS, ITCEventType.REAL_TIME_UPDATE}
            )
        
        print("🔗 All agents and coordinator connected")
        
        # Start mock tasks
        tasks = []
        for i, agent_id in enumerate(agents):
            task_id = f"task_{i+1}"
            task = await itc.start_task(task_id, f"Processing dataset {i+1}", agent_id)
            tasks.append((task_id, agent_id))
        
        print("🚀 Started 3 background tasks\n")
        
        # Simulate work with streaming updates
        for step in range(5):
            print(f"📊 Step {step + 1}/5 - Background processing...")
            
            for task_id, agent_id in tasks:
                progress = (step + 1) / 5
                
                # Stream progress update
                await itc.update_task_progress(
                    task_id=task_id,
                    progress=progress,
                    status_info=f"Processing step {step + 1}"
                )
                
                # Send custom real-time update
                await itc.send_real_time_update({
                    "step": step + 1,
                    "processing_time": step * 0.5,
                    "records_processed": (step + 1) * 1000,
                    "update_type": "processing_progress"
                }, task_id, agent_id)
            
            # Coordinator processes background updates
            print("👁️  Coordinator monitoring background activities...")
            
            # Check stream queue for coordinator
            queue = itc._stream_queues.get(coordinator_id)
            if queue and not queue.empty():
                update_count = 0
                try:
                    while not queue.empty() and update_count < 3:
                        update = await asyncio.wait_for(queue.get(), timeout=0.1)
                        if update.get("type") == "real_time_update":
                            data = update.get("data", {})
                            agent_id = update.get("agent_id", "unknown")
                            print(f"   📨 Saw: {agent_id[-8:]} processed {data.get('records_processed', 0)} records")
                        update_count += 1
                except asyncio.TimeoutError:
                    pass
            
            await asyncio.sleep(1.0)
        
        # Complete tasks
        for task_id, agent_id in tasks:
            await itc.complete_task(task_id, {"status": "completed", "records": 5000})
        
        print("\n✅ All background tasks completed!")
        
        # Show final stats
        final_status = itc.get_status()
        print(f"📊 Final ITC Statistics:")
        print(f"   Tasks completed: {final_status['stats']['tasks_completed']}")
        print(f"   Connected coordinators: {len(final_status.get('task_details', []))}")
        
    finally:
        # Cleanup
        for agent_id in agents + [coordinator_id]:
            await itc.disconnect_coordinator(agent_id)


if __name__ == "__main__":
    async def main():
        try:
            # First try with Groq (requires API key)
            await demo_background_streaming()
        except Exception as e:
            if "api_key" in str(e).lower():
                print(f"\n⚠️  Groq API key not found: {e}")
                print("💡 Running no-LLM demo instead...\n")
                # Fallback to no-LLM demo
                await demo_no_llm_background()
            else:
                print(f"❌ Error: {e}")
                raise
        
        print("\n🎉 Background streaming demos completed!")
        print("\n🔑 Key Takeaways:")
        print("✅ Agents automatically connect and stream when ITC is enabled")
        print("✅ Background monitoring runs without explicit setup")  
        print("✅ Coordinators can react to events automatically")
        print("✅ Both real-time streaming and polling patterns supported")
        print("✅ Works with any LLM provider (Groq, OpenAI, Ollama) or no LLM at all")
    
    asyncio.run(main())