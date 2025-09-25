"""Agent State Management for tracking agent availability and task progress.

Agents maintain state through their lifecycle: AVAILABLE → BUSY → VERIFYING → AVAILABLE
This enables proper coordination and prevents infinite loops.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from enum import Enum
from datetime import datetime
import uuid


class AgentStatus(Enum):
    """Agent availability status."""
    AVAILABLE = "available"
    BUSY = "busy"
    VERIFYING = "verifying"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStage(Enum):
    """Stages of task execution."""
    RECEIVED = "received"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskProgress:
    """Progress tracking for a specific task."""
    task_id: str
    stage: TaskStage = TaskStage.RECEIVED
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Progress tracking
    steps_completed: List[str] = field(default_factory=list)
    current_step: str = ""
    total_steps: Optional[int] = None
    
    # Results tracking
    files_discovered: Set[str] = field(default_factory=set)
    files_processed: Set[str] = field(default_factory=set)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    # Completion criteria
    completion_checks: Dict[str, bool] = field(default_factory=dict)
    
    def update_stage(self, stage: TaskStage, step: str = ""):
        """Update task stage and progress."""
        self.stage = stage
        self.last_updated = datetime.utcnow()
        if step:
            self.current_step = step
            if step not in self.steps_completed:
                self.steps_completed.append(step)
    
    def add_tool_call(self, tool_name: str, input_data: Dict[str, Any], output_data: Any):
        """Record a tool call for progress tracking."""
        self.tool_calls.append({
            "tool": tool_name,
            "timestamp": datetime.utcnow().isoformat(),
            "input": input_data,
            "output_preview": str(output_data)[:200] if output_data else ""
        })
    
    def add_discovered_file(self, file_path: str):
        """Add a discovered file."""
        self.files_discovered.add(file_path)
    
    def add_processed_file(self, file_path: str):
        """Add a processed file."""
        self.files_processed.add(file_path)
    
    def check_completion_criteria(self) -> bool:
        """Check if task meets completion criteria."""
        # For file discovery tasks
        if "file_discovery" in self.completion_checks:
            # Must have discovered and processed files
            if not self.files_discovered or not self.files_processed:
                return False
            
            # Must have read all discovered files
            if len(self.files_processed) < len(self.files_discovered):
                return False
        
        # For reporting tasks
        if "report_generation" in self.completion_checks:
            # Must have made write calls
            write_calls = [tc for tc in self.tool_calls if tc["tool"] == "write_text_atomic"]
            if not write_calls:
                return False
        
        return True
    
    def is_complete(self) -> bool:
        """Check if task is complete based on criteria and progress."""
        return (self.stage == TaskStage.COMPLETED and 
                self.check_completion_criteria())


@dataclass
class AgentState:
    """Complete state tracking for an agent."""
    
    agent_name: str
    status: AgentStatus = AgentStatus.AVAILABLE
    
    # Current task tracking
    current_task_id: Optional[str] = None
    current_progress: Optional[TaskProgress] = None
    
    # Historical tracking
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    
    # Performance metrics
    total_tasks: int = 0
    success_rate: float = 0.0
    average_task_duration: float = 0.0
    
    # State timestamps
    status_changed_at: datetime = field(default_factory=datetime.utcnow)
    last_activity_at: datetime = field(default_factory=datetime.utcnow)
    
    # Agent capabilities and constraints
    specialized_tools: Set[str] = field(default_factory=set)
    max_concurrent_tasks: int = 1
    
    def start_task(self, task_id: str, task_type: str = "") -> TaskProgress:
        """Start a new task and update agent state."""
        if self.status != AgentStatus.AVAILABLE:
            raise ValueError(f"Agent {self.agent_name} is not available (status: {self.status})")
        
        self.status = AgentStatus.BUSY
        self.current_task_id = task_id
        self.current_progress = TaskProgress(task_id=task_id)
        
        # Set completion criteria based on task type
        if "file" in task_type.lower() or "discovery" in task_type.lower():
            self.current_progress.completion_checks["file_discovery"] = True
        elif "report" in task_type.lower() or "analysis" in task_type.lower():
            self.current_progress.completion_checks["report_generation"] = True
        
        self.status_changed_at = datetime.utcnow()
        self.last_activity_at = datetime.utcnow()
        
        return self.current_progress
    
    def update_task_progress(self, stage: TaskStage, step: str = "", 
                           tool_call: Optional[Dict[str, Any]] = None):
        """Update current task progress."""
        if not self.current_progress:
            return
        
        self.current_progress.update_stage(stage, step)
        self.last_activity_at = datetime.utcnow()
        
        if tool_call:
            self.current_progress.add_tool_call(
                tool_call.get("tool", ""),
                tool_call.get("input", {}),
                tool_call.get("output", "")
            )
        
        # Update agent status based on task stage
        if stage == TaskStage.VERIFYING:
            self.status = AgentStatus.VERIFYING
        elif stage in [TaskStage.COMPLETED, TaskStage.FAILED]:
            self.status = AgentStatus.AVAILABLE
    
    def complete_task(self, success: bool = True) -> bool:
        """Complete current task and check if actually done."""
        if not self.current_progress:
            return False
        
        # Check completion criteria
        task_actually_complete = self.current_progress.check_completion_criteria()
        
        if success and task_actually_complete:
            self.current_progress.stage = TaskStage.COMPLETED
            self.completed_tasks.append(self.current_task_id)
            self.total_tasks += 1
        elif not task_actually_complete:
            # Task not actually complete - continue working
            self.current_progress.update_stage(TaskStage.EXECUTING, "continuing_work")
            return False
        else:
            self.current_progress.stage = TaskStage.FAILED
            self.failed_tasks.append(self.current_task_id)
            self.total_tasks += 1
        
        # Update success rate
        if self.total_tasks > 0:
            self.success_rate = len(self.completed_tasks) / self.total_tasks
        
        # Reset for next task
        self.status = AgentStatus.AVAILABLE
        self.current_task_id = None
        self.current_progress = None
        self.status_changed_at = datetime.utcnow()
        
        return task_actually_complete
    
    def record_file_discovery(self, file_path: str):
        """Record that a file was discovered."""
        if self.current_progress:
            self.current_progress.add_discovered_file(file_path)
    
    def record_file_processing(self, file_path: str):
        """Record that a file was processed."""
        if self.current_progress:
            self.current_progress.add_processed_file(file_path)
    
    def is_task_complete(self) -> bool:
        """Check if current task is actually complete."""
        if not self.current_progress:
            return True
        return self.current_progress.is_complete()
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        if not self.current_progress:
            return {"status": "no_active_task"}
        
        return {
            "task_id": self.current_task_id,
            "stage": self.current_progress.stage.value,
            "current_step": self.current_progress.current_step,
            "steps_completed": len(self.current_progress.steps_completed),
            "files_discovered": len(self.current_progress.files_discovered),
            "files_processed": len(self.current_progress.files_processed),
            "tool_calls": len(self.current_progress.tool_calls),
            "completion_criteria_met": self.current_progress.check_completion_criteria()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent state to dictionary."""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "current_task_id": self.current_task_id,
            "total_tasks": self.total_tasks,
            "success_rate": self.success_rate,
            "completed_tasks_count": len(self.completed_tasks),
            "failed_tasks_count": len(self.failed_tasks),
            "specialized_tools": list(self.specialized_tools),
            "progress": self.get_progress_summary()
        }


class AgentStateManager:
    """Manages state for all agents in the system."""
    
    def __init__(self):
        self.agent_states: Dict[str, AgentState] = {}
    
    def register_agent(self, agent_name: str, specialized_tools: List[str] = None) -> AgentState:
        """Register a new agent."""
        state = AgentState(
            agent_name=agent_name,
            specialized_tools=set(specialized_tools or [])
        )
        self.agent_states[agent_name] = state
        return state
    
    def get_agent_state(self, agent_name: str) -> Optional[AgentState]:
        """Get state for a specific agent."""
        return self.agent_states.get(agent_name)
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return [name for name, state in self.agent_states.items() 
                if state.status == AgentStatus.AVAILABLE]
    
    def get_busy_agents(self) -> List[str]:
        """Get list of busy agent names."""
        return [name for name, state in self.agent_states.items() 
                if state.status == AgentStatus.BUSY]
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get summary of entire agent system."""
        return {
            "total_agents": len(self.agent_states),
            "available": len(self.get_available_agents()),
            "busy": len(self.get_busy_agents()),
            "agents": {name: state.to_dict() for name, state in self.agent_states.items()}
        }