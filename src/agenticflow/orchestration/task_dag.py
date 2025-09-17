"""
Task Directed Acyclic Graph (DAG) for AgenticFlow

Manages task dependencies, validates workflow structure,
and determines optimal execution order.
"""

import asyncio
from collections import defaultdict, deque
from typing import Dict, List, Set, Optional, Tuple
import structlog

from .task_management import TaskNode, TaskState, TaskPriority

logger = structlog.get_logger(__name__)


class CyclicDependencyError(Exception):
    """Raised when a cyclic dependency is detected in the task graph."""
    pass


class TaskDAG:
    """
    Directed Acyclic Graph for managing task dependencies and execution order.
    
    Features:
    - Dependency validation (cycle detection)
    - Topological sorting for execution order
    - Parallel execution planning
    - Dynamic task insertion/removal
    - Dependency resolution
    """
    
    def __init__(self):
        self.tasks: Dict[str, TaskNode] = {}
        self.adjacency_list: Dict[str, Set[str]] = defaultdict(set)  # task_id -> dependents
        self.reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)  # task_id -> dependencies
        self.logger = logger.bind(component="task_dag")
    
    def add_task(self, task: TaskNode) -> None:
        """Add a task to the DAG."""
        if task.task_id in self.tasks:
            raise ValueError(f"Task {task.task_id} already exists in DAG")
        
        self.tasks[task.task_id] = task
        
        # Initialize empty adjacency entries
        if task.task_id not in self.adjacency_list:
            self.adjacency_list[task.task_id] = set()
        if task.task_id not in self.reverse_adjacency:
            self.reverse_adjacency[task.task_id] = set()
        
        self.logger.debug(f"Added task {task.task_id} to DAG")
    
    def add_dependency(self, dependent_id: str, dependency_id: str) -> None:
        """
        Add a dependency relationship: dependent_id depends on dependency_id.
        
        Args:
            dependent_id: Task that depends on another
            dependency_id: Task that must complete first
        """
        if dependent_id not in self.tasks:
            raise ValueError(f"Dependent task {dependent_id} not found in DAG")
        if dependency_id not in self.tasks:
            raise ValueError(f"Dependency task {dependency_id} not found in DAG")
        
        # Add to graph structures
        self.adjacency_list[dependency_id].add(dependent_id)
        self.reverse_adjacency[dependent_id].add(dependency_id)
        
        # Update task objects
        self.tasks[dependent_id].add_dependency(dependency_id)
        self.tasks[dependency_id].add_dependent(dependent_id)
        
        # Validate no cycles created
        if self._has_cycle():
            # Rollback the addition
            self.adjacency_list[dependency_id].discard(dependent_id)
            self.reverse_adjacency[dependent_id].discard(dependency_id)
            self.tasks[dependent_id].remove_dependency(dependency_id)
            raise CyclicDependencyError(
                f"Adding dependency {dependency_id} -> {dependent_id} would create a cycle"
            )
        
        self.logger.debug(f"Added dependency: {dependency_id} -> {dependent_id}")
    
    def remove_task(self, task_id: str) -> Optional[TaskNode]:
        """Remove a task and all its dependencies from the DAG."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        # Remove all incoming dependencies
        for dep_id in list(self.reverse_adjacency[task_id]):
            self.remove_dependency(task_id, dep_id)
        
        # Remove all outgoing dependencies
        for dependent_id in list(self.adjacency_list[task_id]):
            self.remove_dependency(dependent_id, task_id)
        
        # Clean up adjacency lists
        del self.adjacency_list[task_id]
        del self.reverse_adjacency[task_id]
        del self.tasks[task_id]
        
        self.logger.debug(f"Removed task {task_id} from DAG")
        return task
    
    def remove_dependency(self, dependent_id: str, dependency_id: str) -> bool:
        """Remove a dependency relationship."""
        if dependent_id not in self.tasks or dependency_id not in self.tasks:
            return False
        
        # Remove from graph structures
        self.adjacency_list[dependency_id].discard(dependent_id)
        self.reverse_adjacency[dependent_id].discard(dependency_id)
        
        # Update task objects
        self.tasks[dependent_id].remove_dependency(dependency_id)
        
        self.logger.debug(f"Removed dependency: {dependency_id} -> {dependent_id}")
        return True
    
    def _has_cycle(self) -> bool:
        """Check if the graph has any cycles using DFS."""
        # Three states: 0=white (unvisited), 1=gray (visiting), 2=black (visited)
        state = {task_id: 0 for task_id in self.tasks}
        
        def dfs(task_id: str) -> bool:
            if state[task_id] == 1:  # Gray = cycle detected
                return True
            if state[task_id] == 2:  # Black = already processed
                return False
            
            state[task_id] = 1  # Mark as gray (visiting)
            
            # Check all dependents
            for dependent_id in self.adjacency_list[task_id]:
                if dfs(dependent_id):
                    return True
            
            state[task_id] = 2  # Mark as black (visited)
            return False
        
        # Check all nodes (in case of disconnected components)
        for task_id in self.tasks:
            if state[task_id] == 0 and dfs(task_id):
                return True
        
        return False
    
    def topological_sort(self) -> List[str]:
        """
        Return tasks in topological order (dependencies before dependents).
        Uses Kahn's algorithm.
        """
        # Calculate in-degrees
        in_degree = {task_id: len(self.reverse_adjacency[task_id]) for task_id in self.tasks}
        
        # Find all tasks with no dependencies
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Remove this task from all its dependents
            for dependent_id in self.adjacency_list[current]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
        
        # Check if all tasks were processed (no cycles)
        if len(result) != len(self.tasks):
            remaining = set(self.tasks.keys()) - set(result)
            raise CyclicDependencyError(f"Cycle detected involving tasks: {remaining}")
        
        return result
    
    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[TaskNode]:
        """Get all tasks that are ready to run (dependencies satisfied)."""
        ready = []
        
        for task_id, task in self.tasks.items():
            if (task.state in {TaskState.PENDING, TaskState.READY} and 
                task.is_ready(completed_tasks)):
                ready.append(task)
        
        # Sort by priority (higher priority first) - higher enum value = higher priority
        ready.sort(key=lambda t: t.priority.value, reverse=True)
        return ready
    
    def get_blocked_tasks(self, completed_tasks: Set[str]) -> List[TaskNode]:
        """Get tasks that are blocked waiting for dependencies."""
        blocked = []
        
        for task_id, task in self.tasks.items():
            if (task.state in {TaskState.PENDING, TaskState.BLOCKED} and 
                not task.is_ready(completed_tasks)):
                blocked.append(task)
        
        return blocked
    
    def get_execution_levels(self) -> List[List[str]]:
        """
        Group tasks by execution levels for optimal parallelization.
        Tasks in the same level can be run in parallel.
        """
        levels = []
        remaining_tasks = set(self.tasks.keys())
        
        while remaining_tasks:
            # Find tasks with no remaining dependencies
            current_level = []
            for task_id in list(remaining_tasks):
                dependencies = self.reverse_adjacency[task_id]
                if dependencies.issubset(set().union(*levels)):  # All dependencies in previous levels
                    current_level.append(task_id)
            
            if not current_level:
                # This should not happen if graph is acyclic
                raise CyclicDependencyError("Unable to resolve execution levels - cycle detected")
            
            levels.append(current_level)
            remaining_tasks -= set(current_level)
        
        return levels
    
    def get_critical_path(self) -> Tuple[List[str], float]:
        """
        Find the critical path (longest path) through the DAG.
        Returns (path, estimated_duration).
        """
        # Topological sort to process in dependency order
        topo_order = self.topological_sort()
        
        # Calculate longest path to each task
        longest_distance = {task_id: 0.0 for task_id in self.tasks}
        predecessors = {task_id: None for task_id in self.tasks}
        
        for task_id in topo_order:
            task = self.tasks[task_id]
            task_duration = self._estimate_task_duration(task)
            
            # Update distances for all dependents
            for dependent_id in self.adjacency_list[task_id]:
                new_distance = longest_distance[task_id] + task_duration
                if new_distance > longest_distance[dependent_id]:
                    longest_distance[dependent_id] = new_distance
                    predecessors[dependent_id] = task_id
        
        # Find the task with maximum distance (end of critical path)
        max_task = max(longest_distance.keys(), key=lambda t: longest_distance[t])
        max_duration = longest_distance[max_task]
        
        # Reconstruct path
        path = []
        current = max_task
        while current is not None:
            path.append(current)
            current = predecessors[current]
        path.reverse()
        
        return path, max_duration
    
    def _estimate_task_duration(self, task: TaskNode) -> float:
        """Estimate task duration based on historical data or defaults."""
        if task.result and task.result.execution_time:
            return task.result.execution_time
        
        # Default estimates based on priority
        duration_estimates = {
            TaskPriority.CRITICAL: 5.0,
            TaskPriority.HIGH: 10.0,
            TaskPriority.NORMAL: 15.0,
            TaskPriority.LOW: 30.0
        }
        return duration_estimates.get(task.priority, 15.0)
    
    def get_task_ancestors(self, task_id: str) -> Set[str]:
        """Get all tasks that must complete before this task can run."""
        if task_id not in self.tasks:
            return set()
        
        ancestors = set()
        to_visit = deque([task_id])
        
        while to_visit:
            current = to_visit.popleft()
            for dependency in self.reverse_adjacency[current]:
                if dependency not in ancestors:
                    ancestors.add(dependency)
                    to_visit.append(dependency)
        
        return ancestors
    
    def get_task_descendants(self, task_id: str) -> Set[str]:
        """Get all tasks that depend on this task (directly or indirectly)."""
        if task_id not in self.tasks:
            return set()
        
        descendants = set()
        to_visit = deque([task_id])
        
        while to_visit:
            current = to_visit.popleft()
            for dependent in self.adjacency_list[current]:
                if dependent not in descendants:
                    descendants.add(dependent)
                    to_visit.append(dependent)
        
        return descendants
    
    def validate_dag(self) -> Tuple[bool, List[str]]:
        """
        Validate the entire DAG structure.
        Returns (is_valid, list_of_issues).
        """
        issues = []
        
        try:
            # Check for cycles
            if self._has_cycle():
                issues.append("Cyclic dependencies detected")
            
            # Validate topological sort works
            self.topological_sort()
            
            # Independent parallel tasks are perfectly valid, so no need to check for orphans
            
            # Check for inconsistent state
            for task_id, task in self.tasks.items():
                if task.dependencies != self.reverse_adjacency[task_id]:
                    issues.append(f"Task {task_id} has inconsistent dependency state")
        
        except Exception as e:
            issues.append(f"DAG validation error: {str(e)}")
        
        return len(issues) == 0, issues
    
    def get_dag_stats(self) -> Dict[str, any]:
        """Get comprehensive statistics about the DAG."""
        if not self.tasks:
            return {"empty": True}
        
        levels = self.get_execution_levels()
        critical_path, critical_duration = self.get_critical_path()
        
        # Count tasks by state
        state_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        
        for task in self.tasks.values():
            state_counts[task.state.value] += 1
            priority_counts[task.priority.value] += 1
        
        return {
            "total_tasks": len(self.tasks),
            "execution_levels": len(levels),
            "max_parallelism": max(len(level) for level in levels) if levels else 0,
            "critical_path_length": len(critical_path),
            "critical_path_duration": critical_duration,
            "critical_path": critical_path,
            "state_distribution": dict(state_counts),
            "priority_distribution": dict(priority_counts),
            "average_dependencies": sum(len(deps) for deps in self.reverse_adjacency.values()) / len(self.tasks),
            "total_edges": sum(len(deps) for deps in self.adjacency_list.values())
        }
    
    def to_dict(self) -> Dict[str, any]:
        """Convert DAG to dictionary representation."""
        return {
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "dependencies": {
                task_id: list(deps) for task_id, deps in self.reverse_adjacency.items()
            },
            "stats": self.get_dag_stats()
        }