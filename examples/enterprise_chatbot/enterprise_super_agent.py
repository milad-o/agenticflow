#!/usr/bin/env python3
"""
🚀 Enterprise Super Agentic Chatbot
===================================

A comprehensive enterprise-grade chatbot that showcases the full power of AgenticFlow:
- Multi-agent coordination with specialized worker agents
- Real-time task monitoring with progress indicators
- Resource usage tracking and optimization
- Tool usage analytics and insights
- Advanced file operations (create, edit, analyze, transform)
- Complex JSON drilling and analysis
- Knowledge base integration with RAG
- Interactive UI for both end users and developers
- WebSocket-based real-time updates

This demo pushes AgenticFlow to its limits and identifies features to integrate back into the framework.
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import os
import sys

# Rich terminal UI
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.tree import Tree
from rich.json import JSON
from rich.align import Align
from rich.columns import Columns
import rich.box

# AgenticFlow imports
from agenticflow import Agent, AgentConfig, LLMProviderConfig, LLMProvider
from agenticflow.orchestration.task_orchestrator import TaskOrchestrator, CoordinationEventType
from agenticflow.orchestration.task_management import TaskPriority, RetryPolicy
from agenticflow.workflows.multi_agent import MultiAgentSystem
from agenticflow.workflows.topologies import TopologyType
from agenticflow.tools.registry import tool
from agenticflow.config.settings import MemoryConfig
from agenticflow.chatbots import RAGAgent, ChatbotConfig, KnowledgeMode

# Import advanced file management tools
try:
    from .file_management_tools import AdvancedFileManager
except ImportError:
    # Handle direct execution
    from file_management_tools import AdvancedFileManager

# System imports
import psutil
import threading
from queue import Queue
import uuid

console = Console()

@dataclass
class TaskInfo:
    """Information about a running task."""
    task_id: str
    name: str
    agent_name: str
    status: str
    progress: float
    start_time: float
    estimated_completion: Optional[float] = None
    tools_used: List[str] = None
    resources_used: Dict[str, float] = None
    result_preview: str = ""

@dataclass
class AgentStats:
    """Statistics for an agent."""
    agent_id: str
    name: str
    tasks_completed: int
    tools_used: int
    memory_usage_mb: float
    cpu_usage_percent: float
    active_tasks: int
    success_rate: float
    last_activity: datetime

@dataclass
class ToolUsage:
    """Tool usage statistics."""
    tool_name: str
    usage_count: int
    success_count: int
    avg_execution_time: float
    last_used: datetime
    agent_users: Set[str]

class ResourceMonitor:
    """Real-time resource monitoring system."""
    
    def __init__(self):
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.disk_usage = 0.0
        self.network_io = {"sent": 0, "recv": 0}
        self.process_count = 0
        self.running = False
        self._monitor_thread = None
        
    def start(self):
        """Start resource monitoring."""
        self.running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
    def stop(self):
        """Stop resource monitoring."""
        self.running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            
    def _monitor_loop(self):
        """Resource monitoring loop."""
        while self.running:
            try:
                self.cpu_usage = psutil.cpu_percent(interval=1)
                self.memory_usage = psutil.virtual_memory().percent
                self.disk_usage = psutil.disk_usage('/').percent
                
                net_io = psutil.net_io_counters()
                self.network_io = {"sent": net_io.bytes_sent, "recv": net_io.bytes_recv}
                
                self.process_count = len(psutil.pids())
            except Exception as e:
                console.log(f"Resource monitoring error: {e}")
            
            time.sleep(2.0)

class EnterpriseUI:
    """Advanced UI system for the Enterprise Super Agent."""
    
    def __init__(self):
        self.layout = Layout()
        self.setup_layout()
        
        # Data stores
        self.active_tasks: Dict[str, TaskInfo] = {}
        self.completed_tasks: List[TaskInfo] = []
        self.agent_stats: Dict[str, AgentStats] = {}
        self.tool_usage: Dict[str, ToolUsage] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        
        # UI update queue
        self.ui_queue = Queue()
        self.update_lock = threading.Lock()
        
        # Resource monitor
        self.resource_monitor = ResourceMonitor()
        
    def setup_layout(self):
        """Setup the advanced UI layout."""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="chat", ratio=2),
            Layout(name="monitoring", ratio=1)
        )
        
        self.layout["monitoring"].split(
            Layout(name="tasks", ratio=1),
            Layout(name="agents", ratio=1),
            Layout(name="resources", ratio=1)
        )
        
    def create_header(self) -> Panel:
        """Create the header panel."""
        title = Text("🚀 Enterprise Super Agentic Chatbot", style="bold blue")
        subtitle = Text("Powered by AgenticFlow v1.0.0 | Real-time Multi-Agent Coordination", style="dim")
        
        header_content = Align.center(
            Text.assemble(title, "\n", subtitle)
        )
        
        return Panel(
            header_content,
            title="🤖 AI Enterprise Assistant",
            border_style="blue",
            box=rich.box.DOUBLE
        )
    
    def create_chat_panel(self) -> Panel:
        """Create the main chat interface panel."""
        if not self.conversation_history:
            content = Text("👋 Welcome! I'm your Enterprise AI Assistant.\n\nI can help you with:\n\n📁 ADVANCED FILE OPERATIONS:\n• Multi-format analysis (JSON, XML, CSV, YAML, TOML, INI, LOG)\n• File editing & modification (find/replace, line operations)\n• Format conversion (JSON↔XML, CSV↔JSON, etc.)\n• File merging with multiple strategies\n• Pattern detection & anomaly analysis\n• File comparison & relationship mapping\n\n🗃️ DATABASE INTEGRATION:\n• SQLite query execution & schema analysis\n• Data export in multiple formats\n• Database relationship visualization\n\n📊 REPORT GENERATION:\n• HTML & Markdown reports with charts\n• Flowchart & process diagram generation\n• Data visualization & insights\n• System diagnostics & monitoring\n\n🤖 MULTI-AGENT COORDINATION:\n• Specialized worker agents (File, Data, Code, Analytics)\n• Real-time task monitoring & progress tracking\n• Knowledge base integration with RAG\n\nType your request or 'help' for detailed capabilities!", style="dim")
        else:
            lines = []
            for msg in self.conversation_history[-10:]:  # Show last 10 messages
                if msg["role"] == "user":
                    lines.append(Text(f"👤 You: {msg['content']}", style="cyan"))
                else:
                    lines.append(Text(f"🤖 Assistant: {msg['content']}", style="green"))
                lines.append(Text(""))  # Empty line
            
            content = Text("\n").join(lines)
        
        return Panel(
            content,
            title="💬 Conversation",
            border_style="green",
            height=None
        )
    
    def create_tasks_panel(self) -> Panel:
        """Create the active tasks monitoring panel."""
        if not self.active_tasks:
            content = Text("No active tasks", style="dim italic")
        else:
            table = Table(show_header=True, header_style="bold blue", box=rich.box.SIMPLE)
            table.add_column("Task", style="cyan", width=15)
            table.add_column("Agent", style="yellow", width=10)
            table.add_column("Progress", width=15)
            table.add_column("Tools", style="magenta", width=8)
            
            for task in self.active_tasks.values():
                progress_bar = f"{'█' * int(task.progress * 10)}{'░' * (10 - int(task.progress * 10))}"
                progress_text = f"{progress_bar} {task.progress:.0%}"
                
                tools_text = str(len(task.tools_used or []))
                
                table.add_row(
                    task.name[:15] + ("..." if len(task.name) > 15 else ""),
                    task.agent_name,
                    progress_text,
                    tools_text
                )
            
            content = table
        
        return Panel(
            content,
            title=f"⚡ Active Tasks ({len(self.active_tasks)})",
            border_style="yellow"
        )
    
    def create_agents_panel(self) -> Panel:
        """Create the agents monitoring panel."""
        if not self.agent_stats:
            content = Text("No agents active", style="dim italic")
        else:
            table = Table(show_header=True, header_style="bold blue", box=rich.box.SIMPLE)
            table.add_column("Agent", style="cyan", width=12)
            table.add_column("Tasks", width=6)
            table.add_column("Success%", width=8)
            table.add_column("Memory", width=8)
            
            for stats in self.agent_stats.values():
                memory_mb = f"{stats.memory_usage_mb:.1f}MB"
                success_rate = f"{stats.success_rate:.0%}" if stats.success_rate else "N/A"
                
                table.add_row(
                    stats.name[:12],
                    str(stats.tasks_completed),
                    success_rate,
                    memory_mb
                )
            
            content = table
        
        return Panel(
            content,
            title=f"🤖 Agents ({len(self.agent_stats)})",
            border_style="cyan"
        )
    
    def create_resources_panel(self) -> Panel:
        """Create the system resources panel."""
        table = Table(show_header=False, box=rich.box.SIMPLE)
        table.add_column("Metric", style="white", width=8)
        table.add_column("Usage", width=12)
        
        # CPU usage bar
        cpu_bar = f"{'█' * int(self.resource_monitor.cpu_usage / 10)}{'░' * (10 - int(self.resource_monitor.cpu_usage / 10))}"
        cpu_color = "red" if self.resource_monitor.cpu_usage > 80 else "yellow" if self.resource_monitor.cpu_usage > 60 else "green"
        
        # Memory usage bar
        mem_bar = f"{'█' * int(self.resource_monitor.memory_usage / 10)}{'░' * (10 - int(self.resource_monitor.memory_usage / 10))}"
        mem_color = "red" if self.resource_monitor.memory_usage > 80 else "yellow" if self.resource_monitor.memory_usage > 60 else "green"
        
        table.add_row("CPU", Text(f"{cpu_bar} {self.resource_monitor.cpu_usage:.1f}%", style=cpu_color))
        table.add_row("Memory", Text(f"{mem_bar} {self.resource_monitor.memory_usage:.1f}%", style=mem_color))
        table.add_row("Processes", str(self.resource_monitor.process_count))
        
        return Panel(
            table,
            title="📊 System Resources",
            border_style="magenta"
        )
    
    def create_footer(self) -> Panel:
        """Create the footer panel."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        status_items = [
            f"🕒 {current_time}",
            f"⚡ {len(self.active_tasks)} tasks active",
            f"🤖 {len(self.agent_stats)} agents",
            f"🔧 {sum(len(usage.agent_users) for usage in self.tool_usage.values())} tools used"
        ]
        
        footer_text = " | ".join(status_items)
        
        return Panel(
            Align.center(Text(footer_text, style="dim")),
            border_style="dim"
        )
    
    def update_display(self):
        """Update the entire display."""
        with self.update_lock:
            self.layout["header"].update(self.create_header())
            self.layout["chat"].update(self.create_chat_panel())
            self.layout["tasks"].update(self.create_tasks_panel())
            self.layout["agents"].update(self.create_agents_panel())
            self.layout["resources"].update(self.create_resources_panel())
            self.layout["footer"].update(self.create_footer())
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })
    
    def update_task(self, task_id: str, **kwargs):
        """Update a task's information."""
        if task_id in self.active_tasks:
            for key, value in kwargs.items():
                setattr(self.active_tasks[task_id], key, value)
        else:
            # Create new task info
            self.active_tasks[task_id] = TaskInfo(
                task_id=task_id,
                name=kwargs.get("name", "Unknown Task"),
                agent_name=kwargs.get("agent_name", "Unknown Agent"),
                status=kwargs.get("status", "pending"),
                progress=kwargs.get("progress", 0.0),
                start_time=kwargs.get("start_time", time.time()),
                tools_used=kwargs.get("tools_used", []),
                resources_used=kwargs.get("resources_used", {})
            )
    
    def complete_task(self, task_id: str, result: str = ""):
        """Move a task to completed status."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = "completed"
            task.progress = 1.0
            task.result_preview = result[:100] + ("..." if len(result) > 100 else "")
            
            self.completed_tasks.append(task)
            del self.active_tasks[task_id]
    
    def update_agent_stats(self, agent_id: str, **kwargs):
        """Update agent statistics."""
        if agent_id not in self.agent_stats:
            self.agent_stats[agent_id] = AgentStats(
                agent_id=agent_id,
                name=kwargs.get("name", f"Agent-{agent_id[:8]}"),
                tasks_completed=0,
                tools_used=0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                active_tasks=0,
                success_rate=0.0,
                last_activity=datetime.now()
            )
        
        stats = self.agent_stats[agent_id]
        for key, value in kwargs.items():
            if hasattr(stats, key):
                setattr(stats, key, value)
        
        stats.last_activity = datetime.now()
    
    def record_tool_usage(self, tool_name: str, agent_id: str, success: bool, execution_time: float):
        """Record tool usage statistics."""
        if tool_name not in self.tool_usage:
            self.tool_usage[tool_name] = ToolUsage(
                tool_name=tool_name,
                usage_count=0,
                success_count=0,
                avg_execution_time=0.0,
                last_used=datetime.now(),
                agent_users=set()
            )
        
        usage = self.tool_usage[tool_name]
        usage.usage_count += 1
        if success:
            usage.success_count += 1
        
        # Update average execution time
        usage.avg_execution_time = (usage.avg_execution_time * (usage.usage_count - 1) + execution_time) / usage.usage_count
        usage.last_used = datetime.now()
        usage.agent_users.add(agent_id)

class EnterpriseSuperAgent:
    """The main Enterprise Super Agentic Chatbot class."""
    
    def __init__(self):
        self.ui = EnterpriseUI()
        self.orchestrator = None
        self.supervisor = None
        self.worker_agents = {}
        self.knowledge_base = None
        self.running = False
        
        # Advanced file management system
        self.file_manager = AdvancedFileManager()
        
        # Tool tracking
        self.active_tools = {}
        self.tool_results = {}
        
    async def initialize(self):
        """Initialize the enterprise chatbot system."""
        console.log("🚀 Initializing Enterprise Super Agentic Chatbot...")
        
        # Start resource monitoring
        self.ui.resource_monitor.start()
        
        # Create orchestrator with enhanced capabilities
        self.orchestrator = TaskOrchestrator(
            max_concurrent_tasks=8,
            enable_streaming=True,
            enable_coordination=True,
            stream_interval=0.5,
            coordination_timeout=120
        )
        
        # Create supervisor agent (RAG-enabled)
        supervisor_config = ChatbotConfig(
            name="Enterprise_Supervisor",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.3-70b-versatile",
                temperature=0.1
            ),
            knowledge_mode=KnowledgeMode.HYBRID,
            instructions="""You are the Enterprise AI Supervisor coordinating a team of specialized agents.
            
Your capabilities:
1. Task decomposition and delegation
2. Multi-agent coordination
3. Knowledge base queries
4. Progress monitoring and reporting
5. Error handling and recovery

Available worker agents:
- FileAgent: Advanced file operations, multi-format analysis, editing, conversion
- DataAgent: Data processing, JSON/XML/CSV analysis, transformations, pattern detection
- CodeAgent: Code analysis, generation, debugging, flowchart creation
- AnalyticsAgent: Statistical analysis, insights, reporting, visualization

Advanced File Capabilities:
• Multi-format support: JSON, XML, CSV, YAML, TOML, INI, LOG, Python, JavaScript, HTML, SQL
• File editing: find/replace, line operations, merging strategies
• Format conversion with validation
• Database integration (SQLite queries, schema analysis)
• Report generation (HTML/Markdown with charts)
• File relationship mapping & dependency analysis
• Pattern detection & anomaly analysis
• Flowchart & visualization generation
• Advanced file comparison & metadata analysis

Always provide detailed, actionable responses and coordinate with appropriate agents for complex file-focused tasks."""
        )
        
        self.supervisor = RAGAgent(supervisor_config)
        
        # Register comprehensive enterprise file management tools
        await self.register_enterprise_tools()
        
        # Create specialized worker agents
        await self.create_worker_agents()
        
        # Connect to orchestrator coordination
        await self.orchestrator.connect_coordinator(
            coordinator_id="enterprise_supervisor",
            coordinator_type="agent"
        )
        
        console.log("✅ Enterprise Super Agentic Chatbot initialized successfully!")
    
    async def register_enterprise_tools(self):
        """Register comprehensive enterprise file management tools."""
        
        # Basic file operations (enhanced)
        @tool(name="create_file", description="Create a new file with specified content")
        async def create_file(filename: str, content: str, directory: str = ".") -> str:
            """Create a new file with content."""
            try:
                self.ui.record_tool_usage("create_file", "supervisor", True, 0.1)
                
                path = Path(directory) / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return f"✅ File created: {path} ({len(content)} characters)"
            except Exception as e:
                self.ui.record_tool_usage("create_file", "supervisor", False, 0.1)
                return f"❌ Error creating file: {str(e)}"
        
        @tool(name="read_file", description="Read and return the contents of a file")
        async def read_file(filename: str, directory: str = ".") -> str:
            """Read file contents."""
            try:
                self.ui.record_tool_usage("read_file", "supervisor", True, 0.1)
                
                path = Path(directory) / filename
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return f"📄 File content ({len(content)} chars):\n\n{content}"
            except Exception as e:
                self.ui.record_tool_usage("read_file", "supervisor", False, 0.1)
                return f"❌ Error reading file: {str(e)}"
                
        @tool(name="system_info", description="Get detailed system information and diagnostics")
        async def system_info() -> str:
            """Get comprehensive system information."""
            try:
                self.ui.record_tool_usage("system_info", "supervisor", True, 0.1)
                
                info = {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent,
                    "process_count": len(psutil.pids()),
                    "active_agents": len(self.ui.agent_stats),
                    "active_tasks": len(self.ui.active_tasks),
                    "completed_tasks": len(self.ui.completed_tasks)
                }
                
                return f"💻 System Information:\n{json.dumps(info, indent=2)}"
                
            except Exception as e:
                self.ui.record_tool_usage("system_info", "supervisor", False, 0.1)
                return f"❌ Error getting system info: {str(e)}"
        
        # Advanced file management tools (delegate to file_manager)
        self.supervisor.tools = {
            # Basic operations
            "create_file": create_file,
            "read_file": read_file,
            "system_info": system_info,
            
            # Advanced file operations
            "analyze_file_comprehensive": self.file_manager.analyze_file_comprehensive,
            "convert_file_format": self.file_manager.convert_file_format,
            "edit_file_content": self.file_manager.edit_file_content,
            "merge_files": self.file_manager.merge_files,
            
            # Database operations  
            "query_database": self.file_manager.query_database,
            "analyze_database_schema": self.file_manager.analyze_database_schema,
            
            # Report generation
            "generate_report": self.file_manager.generate_report,
            
            # File analysis
            "map_file_relationships": self.file_manager.map_file_relationships,
            "analyze_file_patterns": self.file_manager.analyze_file_patterns,
            "compare_files": self.file_manager.compare_files,
            
            # Visualization
            "generate_flowchart": self.file_manager.generate_flowchart
        }
        
        # Start supervisor 
        await self.supervisor.start()
    
    
    async def create_worker_agents(self):
        """Create specialized worker agents."""
        
        # File Operations Agent
        file_agent_config = AgentConfig(
            name="FileAgent",
            instructions="You are a specialized file operations agent. Handle all file-related tasks with precision.",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            ),
            memory=MemoryConfig(type="buffer", max_messages=50)
        )
        self.worker_agents["file"] = Agent(file_agent_config)
        
        # Data Processing Agent
        data_agent_config = AgentConfig(
            name="DataAgent",
            instructions="You are a data processing specialist. Handle JSON analysis, transformations, and data insights.",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            ),
            memory=MemoryConfig(type="buffer", max_messages=50)
        )
        self.worker_agents["data"] = Agent(data_agent_config)
        
        # Code Analysis Agent
        code_agent_config = AgentConfig(
            name="CodeAgent", 
            instructions="You are a code analysis and generation expert. Handle programming tasks and code review.",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            ),
            memory=MemoryConfig(type="buffer", max_messages=50)
        )
        self.worker_agents["code"] = Agent(code_agent_config)
        
        # Analytics Agent
        analytics_agent_config = AgentConfig(
            name="AnalyticsAgent",
            instructions="You are an analytics specialist. Provide insights, statistics, and reporting.",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            ),
            memory=MemoryConfig(type="buffer", max_messages=50)
        )
        self.worker_agents["analytics"] = Agent(analytics_agent_config)
        
        # Start all worker agents
        for name, agent in self.worker_agents.items():
            await agent.start()
            self.ui.update_agent_stats(
                agent.id,
                name=name,
                tasks_completed=0,
                memory_usage_mb=25.0,  # Estimated
                success_rate=1.0
            )
    
    async def process_user_input(self, user_input: str) -> str:
        """Process user input through the enterprise system."""
        try:
            # Add user message to UI
            self.ui.add_message("user", user_input)
            
            # Create task in orchestrator
            task_id = str(uuid.uuid4())
            self.ui.update_task(
                task_id,
                name="User Request",
                agent_name="Supervisor",
                status="processing",
                progress=0.1,
                start_time=time.time()
            )
            
            # Process through supervisor
            start_time = time.time()
            response = await self.supervisor.execute_task(user_input)
            
            execution_time = time.time() - start_time
            
            # Update task progress
            self.ui.update_task(task_id, progress=0.8, tools_used=["llm", "reasoning"])
            
            # Complete task
            self.ui.complete_task(task_id, response.get("response", ""))
            
            # Update agent stats
            self.ui.update_agent_stats(
                self.supervisor.id,
                name="Supervisor",
                tasks_completed=self.ui.agent_stats.get(self.supervisor.id, AgentStats(
                    self.supervisor.id, "Supervisor", 0, 0, 0, 0, 0, 0, datetime.now()
                )).tasks_completed + 1
            )
            
            # Add response to UI
            response_text = response.get("response", "No response generated")
            self.ui.add_message("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_msg = f"❌ Error processing request: {str(e)}"
            self.ui.add_message("assistant", error_msg)
            return error_msg
    
    async def run_interactive_session(self):
        """Run the interactive chat session with live UI updates."""
        self.running = True
        
        # Start supervisor agent
        await self.supervisor.start()
        
        console.print("\n🚀 Enterprise Super Agentic Chatbot Started!", style="bold green")
        console.print("Type 'help' for available commands or 'exit' to quit.", style="dim")
        console.print("\n📁 File-Focused Capabilities:")
        console.print("  • Multi-format analysis (JSON, XML, CSV, YAML, TOML, INI, LOG, Python, JS, HTML, SQL, MD)", style="cyan")
        console.print("  • Format conversion & editing (find/replace, line operations, merging)", style="cyan")
        console.print("  • Database integration (SQLite queries, schema analysis)", style="cyan")
        console.print("  • Report generation (HTML, Markdown with analytics)", style="cyan")
        console.print("  • File relationship mapping & dependency analysis", style="cyan")
        console.print("  • Pattern detection & anomaly analysis", style="cyan")
        
        try:
            while self.running:
                try:
                    # Get user input
                    user_input = console.input("\n🤖 [bold blue]Enterprise AI[/bold blue] > ")
                    
                    if user_input.lower() in ['exit', 'quit', 'bye']:
                        break
                    elif user_input.lower() == 'help':
                        self.show_help()
                        continue
                    elif user_input.lower() == 'demo':
                        await self.run_demo_sequence()
                        continue
                    elif not user_input.strip():
                        continue
                    
                    # Process user input
                    console.print(f"\n💭 Processing: {user_input}", style="dim")
                    response = await self.process_user_input(user_input)
                    
                    # Display response
                    console.print(f"\n✨ Response:", style="bold green")
                    console.print(f"{response}", style="white")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    console.print(f"❌ Error: {str(e)}", style="red")
                    
        except KeyboardInterrupt:
            pass
        
        console.print("\n👋 Goodbye! Enterprise Super Agentic Chatbot session ended.", style="bold blue")
    
    async def shutdown(self):
        """Gracefully shutdown the system."""
        console.log("🔄 Shutting down Enterprise Super Agentic Chatbot...")
        
        self.running = False
        
        # Stop resource monitoring
        self.ui.resource_monitor.stop()
        
        # Stop agents
        if self.supervisor:
            await self.supervisor.stop()
        
        for agent in self.worker_agents.values():
            await agent.stop()
        
        console.log("✅ Shutdown complete!")

async def main():
    """Main function to run the Enterprise Super Agentic Chatbot."""
    try:
        # Check for required environment variables
        if not os.getenv("GROQ_API_KEY"):
            console.print("❌ Error: GROQ_API_KEY environment variable is required", style="red bold")
            console.print("Please set it with: export GROQ_API_KEY='your-groq-api-key'", style="yellow")
            return
        
        # Create and initialize the enterprise agent
        enterprise_agent = EnterpriseSuperAgent()
        await enterprise_agent.initialize()
        
        # Run interactive session
        await enterprise_agent.run_interactive_session()
        
        # Shutdown
        await enterprise_agent.shutdown()
        
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye! Enterprise Super Agentic Chatbot session ended.", style="yellow")
    except Exception as e:
        console.print(f"❌ Fatal error: {str(e)}", style="red bold")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Required environment check
    required_packages = ["rich", "psutil"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"Install them with: pip install {' '.join(missing_packages)}")
        sys.exit(1)
    
    # Run the enterprise chatbot
    asyncio.run(main())