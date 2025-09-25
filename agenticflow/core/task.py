"""Task objects with lifecycle state tracking for agent coordination.

Tasks represent units of work that agents perform, with stateful tracking
of their progress, completion criteria, and results.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime
import uuid


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskResult:
    """Result of task execution."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    artifacts: List[str] = field(default_factory=list)  # File paths, URLs, etc.
    metrics: Dict[str, Any] = field(default_factory=dict)  # Performance metrics
    errors: List[str] = field(default_factory=list)


@dataclass
class CompletionCriteria:
    """Criteria for determining when a task is complete."""
    
    # Function to check if task is complete based on result
    check_function: Optional[Callable[[TaskResult], bool]] = None
    
    # Simple criteria
    required_artifacts: List[str] = field(default_factory=list)
    minimum_data_size: int = 0
    required_keywords: List[str] = field(default_factory=list)
    
    def is_complete(self, result: TaskResult) -> bool:
        """Check if task meets completion criteria."""
        
        # Use custom function if provided
        if self.check_function:
            return self.check_function(result)
        
        # Check required artifacts
        if self.required_artifacts:
            if not all(artifact in result.artifacts for artifact in self.required_artifacts):
                return False
        
        # Check data size
        if self.minimum_data_size > 0:
            total_size = sum(len(str(v)) for v in result.data.values())
            if total_size < self.minimum_data_size:
                return False
        
        # Check required keywords in message/data
        if self.required_keywords:
            text_content = result.message + " " + " ".join(str(v) for v in result.data.values())
            if not all(keyword.lower() in text_content.lower() for keyword in self.required_keywords):
                return False
        
        return True


@dataclass 
class Task:
    """A stateful task with lifecycle tracking."""
    
    # Core task info
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    
    # Assignment and execution
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)  # Task IDs this task depends on
    dependents: List[str] = field(default_factory=list)    # Task IDs that depend on this task
    
    # Execution tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results and completion
    result: Optional[TaskResult] = None
    completion_criteria: Optional[CompletionCriteria] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def start(self, agent_name: str) -> None:
        """Mark task as started by an agent."""
        self.status = TaskStatus.IN_PROGRESS
        self.assigned_agent = agent_name
        self.started_at = datetime.utcnow()
    
    def complete(self, result: TaskResult) -> bool:
        """Mark task as completed with result. Returns True if actually complete."""
        self.result = result
        
        # Check completion criteria if defined
        if self.completion_criteria and not self.completion_criteria.is_complete(result):
            # Task not actually complete yet
            return False
        
        # Task is complete
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        return True
    
    def fail(self, error_message: str, errors: List[str] = None) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        
        if not self.result:
            self.result = TaskResult(success=False)
        
        self.result.success = False
        self.result.message = error_message
        self.result.errors = errors or [error_message]
    
    def is_ready_to_execute(self, completed_tasks: set) -> bool:
        """Check if all dependencies are completed."""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)
    
    def duration(self) -> Optional[float]:
        """Get task duration in seconds if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "assigned_agent": self.assigned_agent,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration(),
            "metadata": self.metadata,
            "tags": self.tags,
            "result": {
                "success": self.result.success if self.result else None,
                "message": self.result.message if self.result else "",
                "data_size": len(str(self.result.data)) if self.result else 0,
                "artifacts_count": len(self.result.artifacts) if self.result else 0,
                "errors_count": len(self.result.errors) if self.result else 0
            } if self.result else None
        }


# Convenience functions for common task types
def create_file_discovery_task(title: str, file_pattern: str, search_path: str) -> Task:
    """Create a task for discovering files."""
    criteria = CompletionCriteria(
        minimum_data_size=50,  # At least some file data
        required_keywords=["file", "path"]
    )
    
    return Task(
        title=title,
        description=f"Find all {file_pattern} files in {search_path} and read their contents",
        completion_criteria=criteria,
        tags=["file_discovery", "filesystem"],
        metadata={
            "file_pattern": file_pattern,
            "search_path": search_path,
            "task_type": "file_discovery"
        }
    )


def create_report_generation_task(title: str, report_filename: str, depends_on: List[str] = None) -> Task:
    """Create a task for generating reports."""
    criteria = CompletionCriteria(
        required_artifacts=[report_filename],
        minimum_data_size=200,  # Substantial report content
        required_keywords=["report", "analysis"]
    )
    
    return Task(
        title=title,
        description=f"Generate comprehensive analysis report and save as {report_filename}",
        dependencies=depends_on or [],
        completion_criteria=criteria,
        tags=["reporting", "analysis"],
        metadata={
            "report_filename": report_filename,
            "task_type": "report_generation"
        }
    )