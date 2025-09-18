#!/usr/bin/env python3
"""
HITL System Demonstration
=========================

Shows how Human-in-the-Loop works in AgenticFlow without requiring interactive input.
This demo simulates the key HITL patterns you'd use in real applications.
"""

import asyncio
import os
from typing import Optional, Dict, Any
import threading
import time

from agenticflow import RAGAgent, Agent
from agenticflow.chatbots import ChatbotConfig
from agenticflow.config.settings import LLMProviderConfig, LLMProvider, AgentConfig


class HITLDemo:
    """Demonstration of HITL patterns."""
    
    def __init__(self):
        self.supervisor: Optional[RAGAgent] = None
        self.worker: Optional[Agent] = None
        self.current_task: Optional[str] = None
        self.task_progress: int = 0
        self.is_running: bool = False
        self.interrupt_flag: bool = False
        self.status_lock = threading.Lock()
        
    async def initialize(self):
        """Initialize the HITL system."""
        print("🚀 Initializing HITL Demo System...")
        
        llm_config = LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY", "sk-dummy")
        )
        
        # Create worker agent
        self.worker = Agent(AgentConfig(
            name="Research Worker",
            llm=llm_config,
            instructions="You research topics thoroughly. You work in phases and can be interrupted."
        ))
        
        # Create HITL supervisor
        self.supervisor = RAGAgent(ChatbotConfig(
            name="HITL Supervisor",
            llm=llm_config,
            knowledge_sources=[],
            instructions="""You are a Human-in-the-Loop supervisor.
            
            You coordinate work with humans and can:
            1. Plan and break down complex tasks
            2. Delegate work to specialists
            3. Provide status updates on current progress
            4. Handle interruptions gracefully
            5. Adapt plans based on human feedback
            
            Always be responsive to human queries and ready to modify plans."""
        ))
        
        # Start agents
        await self.worker.start()
        await self.supervisor.start()
        
        # Register worker as tool
        worker_tool = self.worker.as_tool(
            name="delegate_research",
            description="Delegate research tasks to the specialist worker"
        )
        self.supervisor.register_async_tool(worker_tool)
        
        print("✅ HITL system initialized")
        print(f"   - Supervisor: {self.supervisor.name}")
        print(f"   - Worker: {self.worker.name}")
        print(f"   - Available tools: {self.supervisor.get_available_tools()}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        with self.status_lock:
            return {
                "running": self.is_running,
                "current_task": self.current_task,
                "progress": self.task_progress,
                "interrupted": self.interrupt_flag,
                "timestamp": time.time()
            }
    
    def interrupt(self, reason: str = "Demo interrupt"):
        """Interrupt current work."""
        print(f"\n🛑 INTERRUPT: {reason}")
        self.interrupt_flag = True
    
    async def simulate_work_phases(self, task_description: str):
        """Simulate interruptible work with progress tracking."""
        print(f"\n🔄 Starting work: {task_description}")
        
        with self.status_lock:
            self.current_task = task_description
            self.is_running = True
            self.task_progress = 0
            self.interrupt_flag = False
        
        # Simulate work phases
        phases = [
            "📋 Planning research approach",
            "🔍 Gathering initial information", 
            "📚 Deep research and analysis",
            "📊 Processing and organizing findings",
            "📝 Preparing final results"
        ]
        
        try:
            for i, phase in enumerate(phases):
                print(f"  {phase}... ({i+1}/{len(phases)})")
                
                # Update progress
                with self.status_lock:
                    self.task_progress = int(((i+1) / len(phases)) * 100)
                
                # Simulate work time with interrupt checking
                for step in range(3):
                    if self.interrupt_flag:
                        print(f"  ⏸️ Work interrupted during: {phase}")
                        return {"status": "interrupted", "phase": phase, "step": step+1}
                    
                    await asyncio.sleep(0.8)  # Simulate work
                    print(f"    Step {step+1}/3 complete")
            
            print("  ✅ All work phases completed!")
            return {"status": "completed", "result": f"Successfully completed: {task_description}"}
            
        finally:
            with self.status_lock:
                self.is_running = False
                if not self.interrupt_flag:
                    self.current_task = None
                    self.task_progress = 100
    
    async def demonstrate_status_queries(self):
        """Show how status queries work during execution."""
        print("\n" + "="*60)
        print("🤖 DEMONSTRATION: Real-time Status Queries")
        print("="*60)
        
        # Start work in background
        task = "Research the impact of AI on future job markets"
        work_task = asyncio.create_task(self.simulate_work_phases(task))
        
        # Simulate human querying status during work
        for i in range(6):
            await asyncio.sleep(2)  # Wait a bit
            
            if work_task.done():
                break
            
            # Query status
            status = self.get_status()
            print(f"\n👤 Status Query {i+1}:")
            print(f"   Running: {status['running']}")
            print(f"   Current Task: {status['current_task'][:50]}..." if status['current_task'] else 'None')
            print(f"   Progress: {status['progress']}%")
            
            # Ask supervisor about current work
            if status['running']:
                try:
                    response = await self.supervisor.execute_task(f"""
                    A human is asking about current work progress.
                    
                    Current status:
                    - Task: {status['current_task']}
                    - Progress: {status['progress']}%
                    - Running: {status['running']}
                    
                    Provide a brief, helpful update about what's being worked on right now.
                    """)
                    
                    response_text = response.get('response', '') if isinstance(response, dict) else str(response)
                    print(f"🤖 Supervisor: {response_text[:100]}...")
                except Exception as e:
                    print(f"🤖 Supervisor: Working on the research task, {status['progress']}% complete")
        
        # Wait for work to finish
        result = await work_task
        print(f"\n📋 Work completed: {result}")
    
    async def demonstrate_interruption(self):
        """Show how interruption works."""
        print("\n" + "="*60)
        print("🛑 DEMONSTRATION: Work Interruption")
        print("="*60)
        
        # Start new work
        task = "Analyze trends in renewable energy technology"
        work_task = asyncio.create_task(self.simulate_work_phases(task))
        
        # Let it work for a bit
        await asyncio.sleep(3)
        
        # Check status before interrupt
        status = self.get_status()
        print(f"\n👤 Before interrupt - Progress: {status['progress']}%")
        
        # Interrupt the work
        self.interrupt("Human decided to change direction")
        
        # Wait for interruption to take effect
        result = await work_task
        print(f"📋 Work result after interrupt: {result}")
        
        # Show status after interrupt
        status = self.get_status()
        print(f"👤 After interrupt - Running: {status['running']}, Interrupted: {status['interrupted']}")
    
    async def demonstrate_plan_modification(self):
        """Show how plans can be modified."""
        print("\n" + "="*60)
        print("📝 DEMONSTRATION: Dynamic Plan Modification")
        print("="*60)
        
        # Simulate getting new instructions from human
        original_request = "Research artificial intelligence applications"
        modified_request = "Focus specifically on AI applications in healthcare and medicine"
        
        print(f"👤 Original request: {original_request}")
        print("🤖 Creating initial plan...")
        
        # Get plan from supervisor
        planning_response = await self.supervisor.execute_task(f"""
        Human request: {original_request}
        
        Please create a brief research plan with 3-4 main areas to investigate.
        """)
        
        plan_text = planning_response.get('response', '') if isinstance(planning_response, dict) else str(planning_response)
        print(f"📋 Initial plan: {plan_text[:200]}...")
        
        # Human modifies the request
        print(f"\n👤 Modified request: {modified_request}")
        print("🤖 Adapting plan...")
        
        adaptation_response = await self.supervisor.execute_task(f"""
        Original plan was: {plan_text}
        
        Human now wants to focus on: {modified_request}
        
        Please adapt the research plan to focus specifically on healthcare and medical AI applications.
        """)
        
        adapted_text = adaptation_response.get('response', '') if isinstance(adaptation_response, dict) else str(adaptation_response)
        print(f"📋 Adapted plan: {adapted_text[:200]}...")
        
        print("✅ Plan successfully modified based on human feedback!")
    
    async def demonstrate_conversational_queries(self):
        """Show conversational interaction with supervisor."""
        print("\n" + "="*60)
        print("💬 DEMONSTRATION: Conversational Queries")
        print("="*60)
        
        queries = [
            "What types of research tasks can you handle?",
            "How do you coordinate with your worker agents?",
            "What happens if I need to change priorities mid-task?",
            "Can you explain your workflow process?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n👤 Question {i}: {query}")
            
            response = await self.supervisor.execute_task(f"""
            Human asked: "{query}"
            
            As a Human-in-the-Loop supervisor, please provide a helpful explanation 
            about your capabilities and how you work with humans.
            """)
            
            response_text = response.get('response', '') if isinstance(response, dict) else str(response)
            print(f"🤖 Response: {response_text}")
            
            await asyncio.sleep(1)  # Pause between questions
    
    async def run_complete_demo(self):
        """Run all demonstrations."""
        print("🤖 Human-in-the-Loop System Demonstration")
        print("=" * 60)
        print("This shows how HITL works in AgenticFlow:")
        print("1. Real-time status queries during work")
        print("2. Interrupting work mid-execution") 
        print("3. Modifying plans dynamically")
        print("4. Conversational interaction")
        print("=" * 60)
        
        try:
            # Run demonstrations
            await self.demonstrate_status_queries()
            await asyncio.sleep(1)
            
            await self.demonstrate_interruption()
            await asyncio.sleep(1)
            
            await self.demonstrate_plan_modification()
            await asyncio.sleep(1)
            
            await self.demonstrate_conversational_queries()
            
            print("\n" + "="*60)
            print("🎉 HITL DEMONSTRATION COMPLETE!")
            print("="*60)
            print("✅ Status queries - Ask about progress anytime")
            print("✅ Interruption - Stop work instantly when needed")
            print("✅ Plan modification - Change direction mid-stream")
            print("✅ Conversational - Natural interaction with supervisor")
            print("\n💡 Key Insight: This works just like your interaction with me!")
            print("   You can interrupt, ask questions, and modify the approach")
            print("   at any point during execution.")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            print("\n🧹 Cleaning up...")
            if self.worker:
                await self.worker.stop()
            if self.supervisor:
                await self.supervisor.stop()
            print("👋 Demo completed!")


async def main():
    """Run the HITL demonstration."""
    demo = HITLDemo()
    
    try:
        await demo.initialize()
        await demo.run_complete_demo()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())