#!/usr/bin/env python3
"""
Human-in-the-Loop Supervisor System
====================================

Demonstrates a practical HITL system where:
1. RAGAgent supervisor can be interrupted and queried during task execution
2. Task plans can be modified in real-time
3. Status updates are available at any time
4. Human can add instructions, stop tasks, or change priorities

This works much like Claude's system where you can interrupt ongoing work
and modify the plan dynamically.
"""

import asyncio
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import threading

from agenticflow import RAGAgent, Agent
from agenticflow.chatbots import ChatbotConfig
from agenticflow.config.settings import LLMProviderConfig, LLMProvider, AgentConfig


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1  # 1=high, 2=medium, 3=low


class HITLSupervisor:
    """Human-in-the-Loop Supervisor with real-time task management."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.agents: Dict[str, Agent] = {}
        self.supervisor: Optional[RAGAgent] = None
        self.is_running = False
        self.current_task_id: Optional[str] = None
        self.interrupt_flag = False
        self.status_lock = threading.Lock()
        
    async def initialize(self):
        """Initialize the supervisor and specialist agents."""
        print("🚀 Initializing Human-in-the-Loop Supervisor System")
        
        # Create LLM config
        llm_config = LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY", "sk-dummy")
        )
        
        # Create specialist agents
        self.agents = {
            "researcher": Agent(AgentConfig(
                name="Research Specialist",
                llm=llm_config,
                instructions="You conduct research and gather information on topics."
            )),
            
            "analyst": Agent(AgentConfig(
                name="Data Analyst", 
                llm=llm_config,
                instructions="You analyze data and provide insights."
            )),
            
            "writer": Agent(AgentConfig(
                name="Content Writer",
                llm=llm_config,
                instructions="You create written content and reports."
            ))
        }
        
        # Create HITL supervisor
        self.supervisor = RAGAgent(ChatbotConfig(
            name="HITL Supervisor",
            llm=llm_config,
            knowledge_sources=[],
            instructions="""You are a Human-in-the-Loop supervisor managing a team of specialists.
            
            Your capabilities:
            1. Break down complex requests into manageable tasks
            2. Assign tasks to appropriate specialists
            3. Monitor task progress and provide status updates
            4. Handle human interruptions and plan modifications
            5. Coordinate between agents and synthesize results
            
            Always be responsive to human queries about:
            - Current task status
            - Task plan modifications
            - Adding new requirements
            - Stopping or changing priorities
            
            Work collaboratively with the human to achieve the best results."""
        ))
        
        # Start all agents
        for agent in self.agents.values():
            await agent.start()
        
        await self.supervisor.start()
        
        # Convert agents to tools for delegation
        for name, agent in self.agents.items():
            tool = agent.as_tool(
                name=f"{name}_tasks",
                description=f"Delegate tasks to {name}"
            )
            self.supervisor.register_async_tool(tool)
        
        print("✅ HITL Supervisor System initialized")
        print(f"📋 Available specialists: {list(self.agents.keys())}")
        
    async def create_task_plan(self, request: str) -> List[Task]:
        """Create a task plan from a human request."""
        print(f"\n🎯 Creating task plan for: '{request[:100]}...'")
        
        planning_prompt = f"""
        Human Request: {request}
        
        Create a detailed task plan. Break this down into specific, actionable tasks that can be assigned to specialists:
        - Research Specialist: For information gathering and research
        - Data Analyst: For data analysis and insights
        - Content Writer: For creating written content
        
        For each task, specify:
        1. Task description (clear and actionable)
        2. Which specialist should handle it
        3. Dependencies (which tasks must complete first)
        4. Priority (1=high, 2=medium, 3=low)
        
        Respond in JSON format:
        {{
            "tasks": [
                {{
                    "description": "Research current trends in...",
                    "agent": "researcher", 
                    "dependencies": [],
                    "priority": 1
                }},
                ...
            ]
        }}
        """
        
        try:
            response = await self.supervisor.execute_task(planning_prompt)
            response_text = response.get('response', '') if isinstance(response, dict) else str(response)
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
                tasks = []
                
                for i, task_data in enumerate(plan_data.get('tasks', [])):
                    task = Task(
                        id=f"task_{i+1}",
                        description=task_data['description'],
                        assigned_agent=task_data.get('agent'),
                        dependencies=task_data.get('dependencies', []),
                        priority=task_data.get('priority', 2)
                    )
                    tasks.append(task)
                    self.tasks[task.id] = task
                
                print(f"📋 Created {len(tasks)} tasks:")
                for task in tasks:
                    deps_str = f" (deps: {task.dependencies})" if task.dependencies else ""
                    print(f"  {task.id}: {task.description[:60]}... → {task.assigned_agent}{deps_str}")
                
                return tasks
        except Exception as e:
            print(f"❌ Error creating task plan: {e}")
            
        # Fallback: create simple task
        task = Task(
            id="task_1",
            description=request,
            assigned_agent="researcher"
        )
        self.tasks[task.id] = task
        return [task]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        with self.status_lock:
            status = {
                "is_running": self.is_running,
                "current_task": self.current_task_id,
                "interrupt_flag": self.interrupt_flag,
                "task_summary": {
                    "total": len(self.tasks),
                    "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
                    "in_progress": sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS),
                    "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                    "cancelled": sum(1 for t in self.tasks.values() if t.status == TaskStatus.CANCELLED),
                },
                "tasks": [
                    {
                        "id": t.id,
                        "description": t.description[:60] + "..." if len(t.description) > 60 else t.description,
                        "status": t.status.value,
                        "agent": t.assigned_agent,
                        "started_at": t.started_at.isoformat() if t.started_at else None
                    }
                    for t in self.tasks.values()
                ]
            }
        return status
    
    def interrupt(self, reason: str = "User interrupt"):
        """Interrupt current execution."""
        print(f"\n🛑 INTERRUPT: {reason}")
        self.interrupt_flag = True
        
    def modify_task(self, task_id: str, new_description: str = None, new_priority: int = None):
        """Modify an existing task."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                if new_description:
                    task.description = new_description
                if new_priority:
                    task.priority = new_priority
                print(f"📝 Modified {task_id}: {task.description[:60]}... (priority: {task.priority})")
            else:
                print(f"⚠️ Cannot modify {task_id} - status: {task.status.value}")
        else:
            print(f"❌ Task {task_id} not found")
    
    def add_task(self, description: str, agent: str = "researcher", priority: int = 2):
        """Add a new task to the plan."""
        task_id = f"task_{len(self.tasks) + 1}"
        task = Task(
            id=task_id,
            description=description,
            assigned_agent=agent,
            priority=priority
        )
        self.tasks[task_id] = task
        print(f"➕ Added {task_id}: {description[:60]}... → {agent}")
        return task_id
    
    def cancel_task(self, task_id: str):
        """Cancel a task."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.CANCELLED
                print(f"🚫 Cancelled {task_id}")
            else:
                print(f"⚠️ Cannot cancel {task_id} - already completed")
        else:
            print(f"❌ Task {task_id} not found")
    
    async def execute_task(self, task: Task) -> bool:
        """Execute a single task with interrupt checking."""
        if self.interrupt_flag:
            print(f"⏸️ Execution interrupted before {task.id}")
            return False
            
        print(f"\n🔄 Executing {task.id}: {task.description[:60]}...")
        
        with self.status_lock:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            self.current_task_id = task.id
        
        try:
            # Check for interrupts during execution
            if self.interrupt_flag:
                task.status = TaskStatus.CANCELLED
                print(f"🛑 Task {task.id} interrupted")
                return False
            
            # Get the assigned agent tool
            agent_tool_name = f"{task.assigned_agent}_tasks"
            
            # Execute via the agent tool with interrupt checking
            result = await self._execute_with_interrupt_check(agent_tool_name, task.description)
            
            if self.interrupt_flag:
                task.status = TaskStatus.CANCELLED
                print(f"🛑 Task {task.id} interrupted during execution")
                return False
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            duration = (task.completed_at - task.started_at).total_seconds()
            print(f"✅ Completed {task.id} in {duration:.1f}s")
            return True
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.result = f"Error: {e}"
            print(f"❌ Task {task.id} failed: {e}")
            return False
        finally:
            with self.status_lock:
                self.current_task_id = None
    
    async def _execute_with_interrupt_check(self, agent_tool_name: str, task_description: str) -> str:
        """Execute agent task with periodic interrupt checking."""
        # Get the tool from supervisor
        available_tools = self.supervisor.get_available_tools()
        if agent_tool_name not in available_tools:
            raise ValueError(f"Agent tool {agent_tool_name} not available")
        
        # Execute the task (this would be the actual agent execution)
        # For demo, we simulate with shorter intervals to check interrupts
        for i in range(3):  # Simulate 3 steps of work
            if self.interrupt_flag:
                raise InterruptedError("Task interrupted by user")
            
            # Simulate work
            await asyncio.sleep(1)
            print(f"  📊 Progress: {((i+1)/3)*100:.0f}%")
        
        # Simulate successful result
        return f"Completed task: {task_description[:100]}"
    
    async def execute_all_tasks(self):
        """Execute all pending tasks with human oversight."""
        print("\n🚀 Starting task execution (interruptible)")
        self.is_running = True
        self.interrupt_flag = False
        
        try:
            # Sort tasks by priority and dependencies
            pending_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
            pending_tasks.sort(key=lambda x: x.priority)
            
            for task in pending_tasks:
                if self.interrupt_flag:
                    print("🛑 Execution stopped by user")
                    break
                
                # Check dependencies
                deps_completed = all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED 
                    for dep_id in task.dependencies 
                    if dep_id in self.tasks
                )
                
                if not deps_completed:
                    print(f"⏳ Skipping {task.id} - dependencies not met")
                    continue
                
                await self.execute_task(task)
                
                # Brief pause to allow for interrupts
                await asyncio.sleep(0.5)
                
        finally:
            self.is_running = False
    
    async def interactive_session(self):
        """Run interactive HITL session."""
        print("\n" + "="*60)
        print("🤖 HUMAN-IN-THE-LOOP SUPERVISOR SESSION")
        print("="*60)
        print("Commands:")
        print("  status        - Show current status")
        print("  interrupt     - Interrupt current execution")
        print("  modify <id>   - Modify task description")
        print("  add <desc>    - Add new task")
        print("  cancel <id>   - Cancel a task")
        print("  execute       - Start/resume execution")
        print("  quit          - Exit session")
        print("="*60)
        
        # Get initial request
        request = input("\n👤 What would you like me to work on? ")
        if not request.strip():
            request = "Research the latest trends in artificial intelligence and create a summary report"
        
        # Create task plan
        await self.create_task_plan(request)
        
        # Start execution in background
        execution_task = None
        
        while True:
            try:
                command = input(f"\n👤 Command (or ask me anything): ").strip().lower()
                
                if command == "quit":
                    if execution_task:
                        self.interrupt()
                        await execution_task
                    break
                
                elif command == "status":
                    status = self.get_status()
                    print(f"\n📊 System Status:")
                    print(f"  Running: {status['is_running']}")
                    print(f"  Current Task: {status['current_task'] or 'None'}")
                    print(f"  Task Summary: {status['task_summary']}")
                    print(f"\n📋 Tasks:")
                    for task_info in status['tasks']:
                        print(f"    {task_info['id']}: {task_info['description']} "
                             f"[{task_info['status']}] → {task_info['agent']}")
                
                elif command == "interrupt":
                    self.interrupt("User requested interrupt")
                    if execution_task:
                        await execution_task
                        execution_task = None
                
                elif command.startswith("modify "):
                    task_id = command.split(" ", 1)[1] if len(command.split()) > 1 else ""
                    if task_id:
                        new_desc = input(f"New description for {task_id}: ")
                        self.modify_task(task_id, new_description=new_desc)
                
                elif command.startswith("add "):
                    desc = command[4:].strip()
                    if desc:
                        agent = input("Assign to (researcher/analyst/writer): ").strip() or "researcher"
                        self.add_task(desc, agent)
                
                elif command.startswith("cancel "):
                    task_id = command.split(" ", 1)[1] if len(command.split()) > 1 else ""
                    if task_id:
                        self.cancel_task(task_id)
                
                elif command == "execute":
                    if not self.is_running:
                        self.interrupt_flag = False
                        execution_task = asyncio.create_task(self.execute_all_tasks())
                        print("🚀 Started execution in background")
                    else:
                        print("⚠️ Already executing")
                
                else:
                    # Treat as a question to the supervisor
                    print("🤖 Let me help with that...")
                    response = await self.supervisor.execute_task(f"""
                    The user asked: "{command}"
                    
                    Current system status:
                    - Tasks: {len(self.tasks)} total
                    - Running: {self.is_running}
                    - Current task: {self.current_task_id or 'None'}
                    
                    Please provide a helpful response about the current work or status.
                    """)
                    
                    response_text = response.get('response', '') if isinstance(response, dict) else str(response)
                    print(f"🤖 {response_text}")
            
            except KeyboardInterrupt:
                print("\n🛑 Ctrl+C detected - interrupting...")
                self.interrupt("Keyboard interrupt")
                if execution_task:
                    await execution_task
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Cleanup
        print("\n🧹 Shutting down...")
        for agent in self.agents.values():
            await agent.stop()
        if self.supervisor:
            await self.supervisor.stop()
        
        print("👋 HITL Supervisor session ended")


async def main():
    """Demo the Human-in-the-Loop supervisor system."""
    supervisor = HITLSupervisor()
    
    try:
        await supervisor.initialize()
        await supervisor.interactive_session()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🤖 Human-in-the-Loop Supervisor System")
    print("This demonstrates practical HITL with real-time task management")
    print("You can interrupt, modify plans, and query status at any time")
    print()
    
    asyncio.run(main())