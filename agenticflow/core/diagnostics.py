"""
Diagnostics and task lifecycle tracking for AgenticFlow.

Provides comprehensive tracking of:
- Task DAG structure and dependencies
- Task state transitions and timing
- Agent assignments and performance
- Flow execution patterns
"""

import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

from .logging import get_component_logger


class TaskState(Enum):
    """Task execution states."""
    CREATED = "created"
    PENDING = "pending"
    READY = "ready"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskTransition:
    """Record of a task state transition."""
    from_state: Optional[str]
    to_state: str
    timestamp: float
    agent: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDiagnostics:
    """Comprehensive diagnostics for a single task."""
    task_id: str
    description: str
    agent_assigned: Optional[str] = None

    # Lifecycle tracking
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    current_state: TaskState = TaskState.CREATED

    # Dependencies and relationships
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)

    # Execution metrics
    transitions: List[TaskTransition] = field(default_factory=list)
    execution_time: Optional[float] = None
    retry_count: int = 0

    # Results and errors
    result: Optional[Any] = None
    error: Optional[str] = None

    def add_transition(self, to_state: TaskState, agent: str = None, reason: str = None, **metadata):
        """Record a state transition."""
        transition = TaskTransition(
            from_state=self.current_state.value if self.current_state else None,
            to_state=to_state.value,
            timestamp=time.time(),
            agent=agent,
            reason=reason,
            metadata=metadata
        )
        self.transitions.append(transition)
        self.current_state = to_state

        # Update lifecycle timestamps
        if to_state == TaskState.RUNNING and not self.started_at:
            self.started_at = transition.timestamp
        elif to_state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
            if not self.completed_at:
                self.completed_at = transition.timestamp
            if self.started_at:
                self.execution_time = self.completed_at - self.started_at

    @property
    def total_time(self) -> Optional[float]:
        """Total time from creation to completion."""
        if self.completed_at:
            return self.completed_at - self.created_at
        return None

    @property
    def wait_time(self) -> Optional[float]:
        """Time spent waiting before execution started."""
        if self.started_at:
            return self.started_at - self.created_at
        return None


@dataclass
class DAGDiagnostics:
    """Diagnostics for the entire task DAG."""
    run_id: str
    flow_name: str
    created_at: float = field(default_factory=time.time)

    # DAG structure
    tasks: Dict[str, TaskDiagnostics] = field(default_factory=dict)
    dependency_graph: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    # Execution metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0

    # Agent utilization
    agent_assignments: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    agent_performance: Dict[str, Dict[str, float]] = field(default_factory=lambda: defaultdict(dict))

    def add_task(self, task_id: str, description: str, dependencies: List[str] = None) -> TaskDiagnostics:
        """Add a new task to the DAG."""
        if dependencies is None:
            dependencies = []

        task = TaskDiagnostics(
            task_id=task_id,
            description=description,
            dependencies=set(dependencies)
        )

        self.tasks[task_id] = task
        self.total_tasks += 1

        # Update dependency graph
        for dep in dependencies:
            self.dependency_graph[dep].add(task_id)
            if dep in self.tasks:
                self.tasks[dep].dependents.add(task_id)

        return task

    def update_task_state(self, task_id: str, state: TaskState, agent: str = None, **metadata):
        """Update task state and record transition."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found in DAG")

        task = self.tasks[task_id]
        old_state = task.current_state

        task.add_transition(state, agent=agent, **metadata)

        # Update counters
        if state == TaskState.COMPLETED and old_state != TaskState.COMPLETED:
            self.completed_tasks += 1
        elif state == TaskState.FAILED and old_state != TaskState.FAILED:
            self.failed_tasks += 1
        elif state == TaskState.CANCELLED and old_state != TaskState.CANCELLED:
            self.cancelled_tasks += 1

        # Track agent assignments
        if agent and state == TaskState.ASSIGNED:
            task.agent_assigned = agent
            self.agent_assignments[agent].append(task_id)

    def get_dag_summary(self) -> Dict[str, Any]:
        """Get a summary of the DAG state."""
        return {
            "run_id": self.run_id,
            "flow_name": self.flow_name,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "cancelled_tasks": self.cancelled_tasks,
            "pending_tasks": self.total_tasks - self.completed_tasks - self.failed_tasks - self.cancelled_tasks,
            "agents_involved": len(self.agent_assignments),
            "longest_chain": self._calculate_longest_chain(),
            "average_task_time": self._calculate_average_task_time(),
        }

    def _calculate_longest_chain(self) -> int:
        """Calculate the longest dependency chain in the DAG."""
        def dfs_depth(task_id: str, visited: Set[str]) -> int:
            if task_id in visited:
                return 0
            visited.add(task_id)

            max_depth = 0
            for dependent in self.dependency_graph.get(task_id, set()):
                max_depth = max(max_depth, dfs_depth(dependent, visited.copy()))

            return max_depth + 1

        max_chain = 0
        for task_id in self.tasks:
            if not self.tasks[task_id].dependencies:  # Root tasks
                max_chain = max(max_chain, dfs_depth(task_id, set()))

        return max_chain

    def _calculate_average_task_time(self) -> Optional[float]:
        """Calculate average execution time for completed tasks."""
        completed_tasks = [t for t in self.tasks.values()
                          if t.execution_time is not None]

        if not completed_tasks:
            return None

        return sum(t.execution_time for t in completed_tasks) / len(completed_tasks)

    def get_critical_path(self) -> List[str]:
        """Identify the critical path (longest execution chain)."""
        def calculate_path_time(task_id: str, visited: Set[str]) -> tuple[float, List[str]]:
            if task_id in visited or task_id not in self.tasks:
                return 0.0, []

            visited.add(task_id)
            task = self.tasks[task_id]
            task_time = task.execution_time or 0.0

            max_subsequent_time = 0.0
            max_path = []

            for dependent in task.dependents:
                subsequent_time, subsequent_path = calculate_path_time(dependent, visited.copy())
                if subsequent_time > max_subsequent_time:
                    max_subsequent_time = subsequent_time
                    max_path = subsequent_path

            return task_time + max_subsequent_time, [task_id] + max_path

        max_total_time = 0.0
        critical_path = []

        # Check all root tasks (tasks with no dependencies)
        for task_id, task in self.tasks.items():
            if not task.dependencies:
                total_time, path = calculate_path_time(task_id, set())
                if total_time > max_total_time:
                    max_total_time = total_time
                    critical_path = path

        return critical_path

    def export_dag_visualization(self) -> Dict[str, Any]:
        """Export DAG data for visualization tools."""
        nodes = []
        edges = []

        for task_id, task in self.tasks.items():
            nodes.append({
                "id": task_id,
                "label": task.description[:50] + "..." if len(task.description) > 50 else task.description,
                "state": task.current_state.value,
                "agent": task.agent_assigned,
                "execution_time": task.execution_time,
                "created_at": task.created_at,
                "completed_at": task.completed_at
            })

            for dep in task.dependencies:
                edges.append({
                    "from": dep,
                    "to": task_id,
                    "type": "dependency"
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": self.get_dag_summary(),
            "critical_path": self.get_critical_path()
        }


class DiagnosticsTracker:
    """Main diagnostics tracking system."""

    def __init__(self, run_id: str, flow_name: str):
        self.dag = DAGDiagnostics(run_id=run_id, flow_name=flow_name)
        self.logger = get_component_logger("DiagnosticsTracker", "diagnostics")

    def track_task_created(self, task_id: str, description: str, dependencies: List[str] = None):
        """Track when a task is created."""
        task = self.dag.add_task(task_id, description, dependencies)
        self.logger.user_info(f"Task created: {task_id}")
        self.logger.debug("Task details", task_id=task_id, dependencies=dependencies)

    def track_task_state_change(self, task_id: str, new_state: TaskState, agent: str = None, **metadata):
        """Track task state transitions."""
        self.dag.update_task_state(task_id, new_state, agent, **metadata)

        # User-friendly state change notifications
        if new_state == TaskState.RUNNING:
            self.logger.user_progress(f"Task started: {task_id}" + (f" (assigned to {agent})" if agent else ""))
        elif new_state == TaskState.COMPLETED:
            task = self.dag.tasks[task_id]
            exec_time = f" in {task.execution_time:.1f}s" if task.execution_time else ""
            self.logger.user_success(f"Task completed: {task_id}{exec_time}")
        elif new_state == TaskState.FAILED:
            self.logger.user_error(f"Task failed: {task_id}")

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        summary = self.dag.get_dag_summary()
        self.logger.user_info(
            f"Progress: {summary['completed_tasks']}/{summary['total_tasks']} tasks completed"
        )
        return summary

    def export_diagnostics(self, filepath: str = None) -> Dict[str, Any]:
        """Export full diagnostics data."""
        data = {
            "dag": self.dag.export_dag_visualization(),
            "detailed_tasks": {
                task_id: asdict(task) for task_id, task in self.dag.tasks.items()
            },
            "export_timestamp": datetime.now(timezone.utc).isoformat()
        }

        if filepath:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.user_success(f"Diagnostics exported to {filepath}")

        return data