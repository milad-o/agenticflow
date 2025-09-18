#!/usr/bin/env python3
"""
Simple Human-in-the-Loop Demo
=============================

Demonstrates core HITL concepts:
1. Query agent status while it's working
2. Interrupt ongoing tasks
3. Modify instructions dynamically
4. Resume or change course

This shows how to build HITL systems with AgenticFlow's existing components.
"""

import asyncio
import os
import threading
from typing import Optional, Dict, Any

from agenticflow import RAGAgent, Agent
from agenticflow.chatbots import ChatbotConfig
from agenticflow.config.settings import LLMProviderConfig, LLMProvider, AgentConfig


class SimpleHITL:
    """Simple Human-in-the-Loop demonstration."""
    
    def __init__(self):
        self.supervisor: Optional[RAGAgent] = None
        self.worker: Optional[Agent] = None
        self.current_task: Optional[str] = None
        self.task_progress: int = 0
        self.is_running: bool = False
        self.interrupt_flag: bool = False
        self.status_lock = threading.Lock()
        
    async def initialize(self):
        """Initialize agents."""
        print("🚀 Initializing Simple HITL System...")
        
        llm_config = LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY", "sk-dummy")
        )
        
        # Create a worker agent
        self.worker = Agent(AgentConfig(
            name="Research Worker",
            llm=llm_config,
            instructions="You research topics thoroughly and provide detailed insights."
        ))
        
        # Create HITL supervisor
        self.supervisor = RAGAgent(ChatbotConfig(
            name="HITL Supervisor",
            llm=llm_config,
            knowledge_sources=[],
            instructions="""You coordinate work with humans in the loop.
            
            You can:
            1. Break down tasks and track progress
            2. Answer questions about current work status
            3. Adapt to human feedback and interruptions
            4. Resume or modify work based on human input
            
            Always be responsive to human queries and ready to adjust the plan."""
        ))
        
        # Start agents
        await self.worker.start()
        await self.supervisor.start()
        
        # Register worker as tool for delegation
        worker_tool = self.worker.as_tool(
            name="research_task",
            description="Delegate research tasks to the worker"
        )
        self.supervisor.register_async_tool(worker_tool)
        
        print("✅ Simple HITL system ready!")
        print("   - Supervisor can delegate to worker")
        print("   - Human can interrupt and query at any time")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status - can be called anytime."""
        with self.status_lock:
            return {
                "is_running": self.is_running,
                "current_task": self.current_task,
                "progress": self.task_progress,
                "interrupted": self.interrupt_flag,
                "can_modify": self.is_running or self.current_task is not None
            }
    
    def interrupt(self, reason: str = "Human interrupt"):
        """Interrupt current work."""
        print(f"\n🛑 INTERRUPT: {reason}")
        self.interrupt_flag = True
    
    async def work_on_task(self, task_description: str):
        """Simulate interruptible work."""
        print(f"\n🔄 Starting work on: {task_description[:60]}...")
        
        with self.status_lock:
            self.current_task = task_description
            self.is_running = True
            self.task_progress = 0
            self.interrupt_flag = False
        
        try:
            # Simulate work in phases (each can be interrupted)
            phases = [
                "Planning approach...",
                "Gathering information...", 
                "Analyzing findings...",
                "Preparing results...",
                "Finalizing output..."
            ]
            
            for i, phase in enumerate(phases):
                if self.interrupt_flag:
                    print(f"⏸️ Work interrupted during: {phase}")
                    return {"status": "interrupted", "phase": phase}
                
                print(f"  📊 {phase} ({i+1}/{len(phases)})")
                
                with self.status_lock:
                    self.task_progress = int(((i+1) / len(phases)) * 100)
                
                # Simulate work time with interrupt checking
                for _ in range(3):  # Check for interrupts frequently
                    if self.interrupt_flag:
                        print(f"⏸️ Work interrupted during: {phase}")
                        return {"status": "interrupted", "phase": phase}
                    await asyncio.sleep(1)
            
            print("✅ Work completed successfully!")
            return {"status": "completed", "result": f"Completed: {task_description}"}
            
        finally:
            with self.status_lock:
                self.is_running = False
                if not self.interrupt_flag:
                    self.current_task = None
                    self.task_progress = 100
    
    async def interactive_demo(self):
        """Run interactive demo."""
        print("\n" + "="*50)
        print("🤖 SIMPLE HITL DEMONSTRATION")
        print("="*50)
        print("Try these commands while work is running:")
        print("  status    - Check current status")
        print("  interrupt - Stop current work")
        print("  ask <q>   - Ask supervisor a question")
        print("  quit      - Exit")
        print("="*50)
        
        # Get work request
        task = input("\n👤 What should I work on? ") or "Research the future of AI technology"
        
        # Start work in background
        work_task = asyncio.create_task(self.work_on_task(task))
        print("🚀 Work started in background. You can interrupt or query anytime!")
        
        # Interactive loop
        while not work_task.done():
            try:
                # Non-blocking input with timeout
                cmd = await asyncio.wait_for(
                    asyncio.to_thread(input, "\n👤 Command: "), 
                    timeout=2.0
                )
                cmd = cmd.strip().lower()
                
                if cmd == "status":
                    status = self.get_status()
                    print(f"\n📊 Status:")
                    print(f"  Running: {status['is_running']}")
                    print(f"  Task: {status['current_task']}")
                    print(f"  Progress: {status['progress']}%")
                    print(f"  Interrupted: {status['interrupted']}")
                
                elif cmd == "interrupt":
                    self.interrupt("User requested stop")
                    await work_task  # Wait for task to handle interrupt
                    break
                
                elif cmd.startswith("ask "):
                    question = cmd[4:].strip()
                    print("🤖 Let me check on that...")
                    
                    status = self.get_status()
                    response = await self.supervisor.execute_task(f"""
                    Human asked: "{question}"
                    
                    Current work status:
                    - Task: {status['current_task'] or 'None'}
                    - Progress: {status['progress']}%
                    - Running: {status['is_running']}
                    
                    Please provide a helpful response about the current work.
                    """)
                    
                    response_text = response.get('response', '') if isinstance(response, dict) else str(response)
                    print(f"🤖 {response_text}")
                
                elif cmd == "quit":
                    self.interrupt("User quit")
                    await work_task
                    break
                
                else:
                    print("❓ Try: status, interrupt, ask <question>, or quit")
            
            except asyncio.TimeoutError:
                # No input, continue working
                continue
            except KeyboardInterrupt:
                print("\n🛑 Ctrl+C - interrupting work...")
                self.interrupt("Keyboard interrupt")
                await work_task
                break
        
        # Check final result
        if work_task.done():
            try:
                result = await work_task
                print(f"\n📋 Final Result: {result}")
            except Exception as e:
                print(f"\n❌ Work ended with error: {e}")
        
        # Cleanup
        print("\n🧹 Shutting down...")
        if self.worker:
            await self.worker.stop()
        if self.supervisor:
            await self.supervisor.stop()
        
        print("👋 HITL demo completed!")


async def main():
    """Run the simple HITL demo."""
    hitl = SimpleHITL()
    
    try:
        await hitl.initialize()
        await hitl.interactive_demo()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🤖 Simple Human-in-the-Loop Demo")
    print("Shows how to build HITL systems with AgenticFlow")
    print("You can interrupt, query status, and modify work in real-time")
    print()
    
    asyncio.run(main())