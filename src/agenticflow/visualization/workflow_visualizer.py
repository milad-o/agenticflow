"""
Workflow and task orchestration visualizer.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from ..orchestration.task_orchestrator import TaskOrchestrator, TaskStatus
    from ..orchestration.task_dag import TaskDAG
    from ..orchestration.task_management import Task, TaskPriority
except ImportError:
    # Fallback for when orchestration modules are not available
    TaskOrchestrator = None
    TaskDAG = None
    Task = None
    TaskStatus = None
    TaskPriority = None

from .mermaid_generator import (
    MermaidGenerator,
    DiagramType,
    FlowDirection,
    NodeShape,
    EdgeType,
    ColorSchemes,
    create_agent_visualization_styles
)


class TaskState(Enum):
    """Task execution states for visualization."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class TaskNode:
    """Represents a task node for visualization."""
    id: str
    name: str
    description: str
    state: TaskState
    priority: str
    dependencies: List[str]
    estimated_duration: Optional[float] = None
    actual_duration: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class WorkflowInfo:
    """Information about a workflow for visualization."""
    name: str
    description: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    execution_time: Optional[float] = None


class WorkflowVisualizer:
    """
    Visualizes task orchestration workflows and DAGs using Mermaid diagrams.
    
    Supports task dependencies, execution status, and performance metrics.
    """
    
    def __init__(self):
        self.generator = MermaidGenerator(DiagramType.FLOWCHART)
        self._setup_default_styles()
        
    def _setup_default_styles(self):
        """Setup default CSS classes for workflow visualization."""
        styles = create_agent_visualization_styles()
        for class_name, style_dict in styles.items():
            self.generator.add_css_class(class_name, style_dict)
            
        # Add workflow-specific styles
        self.generator.add_css_class("workflow-info", {
            "fill": "#e1f5fe",
            "stroke": "#0288d1", 
            "color": "#000"
        })
        
    def visualize_dag(
        self,
        tasks: List[TaskNode],
        workflow_info: Optional[WorkflowInfo] = None,
        layout_direction: FlowDirection = FlowDirection.TOP_DOWN,
        group_by_priority: bool = True
    ) -> str:
        """
        Visualize a task DAG with dependencies and states.
        
        Args:
            tasks: List of task nodes to visualize
            workflow_info: Optional workflow metadata
            layout_direction: Layout direction for the diagram
            group_by_priority: Whether to group tasks by priority level
            
        Returns:
            Mermaid diagram as string
        """
        self.generator.clear().set_direction(layout_direction)
        
        # Add workflow info if provided
        if workflow_info:
            self._add_workflow_info(workflow_info)
            
        # Group tasks by priority if requested
        if group_by_priority:
            return self._visualize_dag_with_priority_groups(tasks)
        else:
            return self._visualize_dag_simple(tasks)
            
    def visualize_execution_timeline(
        self,
        tasks: List[TaskNode],
        include_durations: bool = True
    ) -> str:
        """
        Visualize task execution as a timeline.
        
        Args:
            tasks: List of task nodes with execution information
            include_durations: Whether to show task durations
            
        Returns:
            Mermaid diagram as timeline
        """
        self.generator = MermaidGenerator(DiagramType.TIMELINE)
        
        lines = ["timeline"]
        lines.append("    title Task Execution Timeline")
        lines.append("")
        
        # Group tasks by state for timeline sections
        states_order = [TaskState.COMPLETED, TaskState.RUNNING, TaskState.FAILED, TaskState.PENDING]
        
        for state in states_order:
            state_tasks = [t for t in tasks if t.state == state]
            if not state_tasks:
                continue
                
            lines.append(f"    section {state.value.title()}")
            
            for task in state_tasks:
                duration_info = ""
                if include_durations and task.actual_duration:
                    duration_info = f" ({task.actual_duration:.1f}s)"
                    
                lines.append(f"        {task.name}{duration_info} : {task.description[:50]}...")
                
        return "\n".join(lines)
        
    def visualize_orchestrator_state(
        self,
        orchestrator: Any,  # TaskOrchestrator if available
        include_metrics: bool = True
    ) -> str:
        """
        Visualize the current state of a task orchestrator.
        
        Args:
            orchestrator: TaskOrchestrator instance
            include_metrics: Whether to include performance metrics
            
        Returns:
            Mermaid diagram as string
        """
        if not orchestrator:
            return self._create_placeholder_diagram("Task Orchestrator not available")
            
        self.generator.clear().set_direction(FlowDirection.LEFT_RIGHT)
        
        # Extract current state
        tasks = self._extract_tasks_from_orchestrator(orchestrator)
        
        # Create orchestrator overview
        self.generator.add_subgraph("orchestrator", "Task Orchestrator")
        
        # Add orchestrator node
        status_text = f"Active Tasks: {len([t for t in tasks if t.state == TaskState.RUNNING])}"
        self.generator.add_node(
            "orchestrator_node",
            f"Orchestrator<br/>{status_text}",
            NodeShape.HEXAGON,
            css_class="agent-coordinator"
        )
        self.generator.subgraphs["orchestrator"].nodes.append("orchestrator_node")
        
        # Add task visualization
        if tasks:
            return self._visualize_dag_simple(tasks)
        else:
            return self.generator.generate()
            
    def create_workflow_comparison(
        self,
        workflows: Dict[str, List[TaskNode]]
    ) -> str:
        """
        Create a comparison of multiple workflows.
        
        Args:
            workflows: Dictionary mapping workflow names to task lists
            
        Returns:
            Mermaid diagram comparing workflows
        """
        self.generator.clear().set_direction(FlowDirection.LEFT_RIGHT)
        
        for workflow_name, tasks in workflows.items():
            # Create subgraph for each workflow
            subgraph_id = f"workflow_{workflow_name.replace(' ', '_').lower()}"
            self.generator.add_subgraph(subgraph_id, f"Workflow: {workflow_name}")
            
            # Add workflow summary node
            completed = len([t for t in tasks if t.state == TaskState.COMPLETED])
            total = len(tasks)
            summary_node = f"{subgraph_id}_summary"
            
            self.generator.add_node(
                summary_node,
                f"{workflow_name}<br/>{completed}/{total} completed",
                NodeShape.ROUNDED,
                css_class="workflow-info"
            )
            self.generator.subgraphs[subgraph_id].nodes.append(summary_node)
            
            # Add representative task nodes
            for i, task in enumerate(tasks[:5]):  # Show first 5 tasks
                task_node_id = f"{subgraph_id}_task_{i}"
                self.generator.add_node(
                    task_node_id,
                    task.name,
                    NodeShape.RECTANGLE,
                    css_class=f"task-{task.state.value}"
                )
                self.generator.subgraphs[subgraph_id].nodes.append(task_node_id)
                
                # Connect to summary
                self.generator.add_edge(
                    summary_node,
                    task_node_id,
                    edge_type=EdgeType.DOTTED
                )
                
        return self.generator.generate()
        
    def create_performance_dashboard(
        self,
        tasks: List[TaskNode],
        workflow_info: Optional[WorkflowInfo] = None
    ) -> str:
        """
        Create a performance-focused dashboard visualization.
        
        Args:
            tasks: List of task nodes with performance data
            workflow_info: Optional workflow metadata
            
        Returns:
            Mermaid diagram as performance dashboard
        """
        self.generator.clear().set_direction(FlowDirection.TOP_DOWN)
        
        # Performance metrics subgraph
        self.generator.add_subgraph("metrics", "Performance Metrics")
        
        # Calculate metrics
        total_tasks = len(tasks)
        completed = len([t for t in tasks if t.state == TaskState.COMPLETED])
        failed = len([t for t in tasks if t.state == TaskState.FAILED])
        running = len([t for t in tasks if t.state == TaskState.RUNNING])
        
        success_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        # Add metrics nodes
        self.generator.add_node(
            "total_tasks",
            f"Total Tasks<br/>{total_tasks}",
            NodeShape.RECTANGLE,
            css_class="workflow-info"
        )
        
        self.generator.add_node(
            "completed_tasks",
            f"Completed<br/>{completed} ({success_rate:.1f}%)",
            NodeShape.RECTANGLE,
            css_class="task-completed"
        )
        
        self.generator.add_node(
            "failed_tasks",
            f"Failed<br/>{failed}",
            NodeShape.RECTANGLE,
            css_class="task-failed"
        )
        
        self.generator.add_node(
            "running_tasks",
            f"Running<br/>{running}",
            NodeShape.RECTANGLE,
            css_class="task-running"
        )
        
        # Add to subgraph
        for node_id in ["total_tasks", "completed_tasks", "failed_tasks", "running_tasks"]:
            self.generator.subgraphs["metrics"].nodes.append(node_id)
            
        # Connect metrics
        for target in ["completed_tasks", "failed_tasks", "running_tasks"]:
            self.generator.add_edge("total_tasks", target, edge_type=EdgeType.DOTTED)
            
        # Add critical path if there are dependencies
        critical_tasks = self._find_critical_path(tasks)
        if critical_tasks:
            self.generator.add_subgraph("critical_path", "Critical Path")
            
            for i, task in enumerate(critical_tasks):
                node_id = f"critical_{i}"
                self.generator.add_node(
                    node_id,
                    f"{task.name}<br/>{task.actual_duration or task.estimated_duration or 0:.1f}s",
                    NodeShape.DIAMOND,
                    css_class=f"task-{task.state.value}"
                )
                self.generator.subgraphs["critical_path"].nodes.append(node_id)
                
                if i > 0:
                    self.generator.add_edge(
                        f"critical_{i-1}",
                        node_id,
                        edge_type=EdgeType.THICK
                    )
                    
        return self.generator.generate()
        
    def _add_workflow_info(self, workflow_info: WorkflowInfo):
        """Add workflow information subgraph."""
        self.generator.add_subgraph("workflow_info", f"Workflow: {workflow_info.name}")
        
        progress = f"{workflow_info.completed_tasks}/{workflow_info.total_tasks}"
        execution_time = f" | {workflow_info.execution_time:.1f}s" if workflow_info.execution_time else ""
        
        self.generator.add_node(
            "workflow_summary",
            f"{workflow_info.description}<br/>Progress: {progress}{execution_time}",
            NodeShape.ROUNDED,
            css_class="workflow-info"
        )
        self.generator.subgraphs["workflow_info"].nodes.append("workflow_summary")
        
    def _visualize_dag_with_priority_groups(self, tasks: List[TaskNode]) -> str:
        """Visualize DAG with tasks grouped by priority."""
        
        # Group by priority
        priority_groups = {}
        for task in tasks:
            priority = task.priority.upper() if task.priority else "NORMAL"
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(task)
            
        # Create subgraphs for each priority
        priority_order = ["CRITICAL", "HIGH", "NORMAL", "LOW"]
        
        for priority in priority_order:
            if priority not in priority_groups:
                continue
                
            subgraph_id = f"priority_{priority.lower()}"
            self.generator.add_subgraph(subgraph_id, f"{priority} Priority")
            
            for task in priority_groups[priority]:
                self._add_task_node(task)
                self.generator.subgraphs[subgraph_id].nodes.append(task.id)
                
        # Add dependencies
        self._add_task_dependencies(tasks)
        
        return self.generator.generate()
        
    def _visualize_dag_simple(self, tasks: List[TaskNode]) -> str:
        """Simple DAG visualization without grouping."""
        
        # Add all task nodes
        for task in tasks:
            self._add_task_node(task)
            
        # Add dependencies
        self._add_task_dependencies(tasks)
        
        return self.generator.generate()
        
    def _add_task_node(self, task: TaskNode):
        """Add a single task node to the diagram."""
        duration_text = ""
        if task.actual_duration:
            duration_text = f"<br/>{task.actual_duration:.1f}s"
        elif task.estimated_duration:
            duration_text = f"<br/>~{task.estimated_duration:.1f}s"
            
        node_shape = NodeShape.DIAMOND if task.priority == "CRITICAL" else NodeShape.RECTANGLE
        
        self.generator.add_node(
            task.id,
            f"{task.name}{duration_text}",
            node_shape,
            css_class=f"task-{task.state.value}"
        )
        
    def _add_task_dependencies(self, tasks: List[TaskNode]):
        """Add dependency edges between tasks."""
        task_ids = {task.id for task in tasks}
        
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in task_ids:
                    edge_type = EdgeType.THICK if task.priority == "CRITICAL" else EdgeType.SOLID
                    self.generator.add_edge(
                        dep_id,
                        task.id,
                        "depends on",
                        edge_type
                    )
                    
    def _extract_tasks_from_orchestrator(self, orchestrator: Any) -> List[TaskNode]:
        """Extract task information from orchestrator."""
        tasks = []
        
        # This is a placeholder - actual implementation would depend on orchestrator API
        if hasattr(orchestrator, 'dag') and orchestrator.dag:
            for task_id, task_info in getattr(orchestrator.dag, 'tasks', {}).items():
                state = self._map_task_status(getattr(task_info, 'status', None))
                
                tasks.append(TaskNode(
                    id=task_id,
                    name=getattr(task_info, 'name', task_id),
                    description=getattr(task_info, 'description', ''),
                    state=state,
                    priority=getattr(task_info, 'priority', 'NORMAL'),
                    dependencies=getattr(task_info, 'dependencies', [])
                ))
                
        return tasks
        
    def _map_task_status(self, status: Any) -> TaskState:
        """Map orchestrator task status to visualization state."""
        if not status:
            return TaskState.PENDING
            
        status_str = str(status).upper()
        
        if 'COMPLETE' in status_str or 'SUCCESS' in status_str:
            return TaskState.COMPLETED
        elif 'RUNNING' in status_str or 'EXECUTING' in status_str:
            return TaskState.RUNNING
        elif 'FAILED' in status_str or 'ERROR' in status_str:
            return TaskState.FAILED
        elif 'BLOCKED' in status_str or 'WAITING' in status_str:
            return TaskState.BLOCKED
        else:
            return TaskState.PENDING
            
    def _find_critical_path(self, tasks: List[TaskNode]) -> List[TaskNode]:
        """Find the critical path through the task DAG."""
        # Simplified critical path calculation
        # In a real implementation, this would use proper CPM algorithm
        
        # For now, return tasks with CRITICAL priority or longest estimated duration
        critical_tasks = [t for t in tasks if t.priority == "CRITICAL"]
        
        if not critical_tasks:
            # Fall back to tasks with longest duration
            tasks_with_duration = [t for t in tasks if t.estimated_duration or t.actual_duration]
            if tasks_with_duration:
                critical_tasks = sorted(
                    tasks_with_duration,
                    key=lambda x: x.actual_duration or x.estimated_duration or 0,
                    reverse=True
                )[:3]  # Top 3 longest tasks
                
        return critical_tasks
        
    def _create_placeholder_diagram(self, message: str) -> str:
        """Create a placeholder diagram with a message."""
        self.generator.clear()
        self.generator.add_node(
            "placeholder",
            message,
            NodeShape.RECTANGLE,
            css_class="workflow-info"
        )
        return self.generator.generate()
        
    def draw_dag(self, tasks: List[TaskNode], workflow_info: Optional[WorkflowInfo] = None,
                output_path: Optional[str] = None, format: str = "png",
                layout_direction: FlowDirection = FlowDirection.TOP_DOWN,
                group_by_priority: bool = True, width: int = 1200, height: int = 800) -> bool:
        """Draw a workflow DAG and save/display it.
        
        Args:
            tasks: List of task nodes to visualize
            workflow_info: Optional workflow metadata
            output_path: Path to save the image. If None, uses temporary file
            format: Output format (png, svg, pdf)
            layout_direction: Layout direction for the diagram
            group_by_priority: Whether to group tasks by priority level
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            True if successful, False otherwise
        """
        # Generate the diagram
        diagram_code = self.visualize_dag(
            tasks, workflow_info, layout_direction, group_by_priority
        )
        
        # Export using the export utils
        from .export_utils import get_exporter
        exporter = get_exporter()
        
        if not output_path:
            import tempfile
            output_path = tempfile.mktemp(suffix=f".{format}")
            
        if format.lower() == "svg":
            success = exporter.export_to_svg(diagram_code, output_path)
        elif format.lower() == "png":
            success = exporter.export_to_png(diagram_code, output_path, width=width, height=height)
        elif format.lower() == "pdf":
            success = exporter.export_to_pdf(diagram_code, output_path)
        else:
            print(f"Unsupported format: {format}")
            return False
            
        if success:
            print(f"Workflow diagram saved to: {output_path}")
            # Try to open the file on macOS
            if output_path.startswith("/tmp"):
                try:
                    import subprocess
                    subprocess.run(["open", output_path], check=False)
                except Exception:
                    pass
                    
        return success
        
    def show_dag(self, tasks: List[TaskNode], workflow_info: Optional[WorkflowInfo] = None,
                format: str = "png", layout_direction: FlowDirection = FlowDirection.TOP_DOWN,
                group_by_priority: bool = True, width: int = 1200, height: int = 800) -> bool:
        """Show a workflow DAG in a viewer.
        
        Args:
            tasks: List of task nodes to visualize
            workflow_info: Optional workflow metadata
            format: Output format (png, svg, pdf)
            layout_direction: Layout direction for the diagram
            group_by_priority: Whether to group tasks by priority level
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            True if successful, False otherwise
        """
        return self.draw_dag(tasks, workflow_info, None, format, 
                           layout_direction, group_by_priority, width, height)
                           
    def _repr_html_(self, tasks: List[TaskNode] = None, workflow_info: Optional[WorkflowInfo] = None) -> str:
        """Return HTML representation for Jupyter notebooks.
        
        Args:
            tasks: List of task nodes to visualize (optional, uses last generated if not provided)
            workflow_info: Optional workflow metadata
            
        Returns:
            HTML string for Jupyter display
        """
        try:
            if tasks is None:
                # If no tasks provided, try to use the generator's current state
                if not self.generator.nodes:
                    return """
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px; color: #856404;">
                        <h4>No Workflow to Display</h4>
                        <p>Call visualize_dag() first or provide tasks parameter</p>
                    </div>
                    """
                # Use current generator state
                return self.generator._repr_html_()
            else:
                # Generate diagram with provided tasks
                diagram_code = self.visualize_dag(tasks, workflow_info)
                
                # Try to render as SVG
                from .mermaid_generator import MermaidGenerator
                temp_gen = MermaidGenerator()
                temp_gen.nodes = self.generator.nodes.copy()
                temp_gen.edges = self.generator.edges.copy()
                temp_gen.subgraphs = self.generator.subgraphs.copy()
                temp_gen.styles = self.generator.styles.copy()
                temp_gen.css_classes = self.generator.css_classes.copy()
                
                return temp_gen._repr_html_()
                
        except Exception as e:
            return f"""
            <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 10px; color: #c62828;">
                <h4>Workflow Visualization Error</h4>
                <p>Failed to render workflow diagram: {str(e)}</p>
            </div>
            """


# Utility functions for common visualizations
def visualize_simple_workflow(
    task_names: List[str],
    dependencies: Dict[str, List[str]] = None,
    task_states: Dict[str, TaskState] = None
) -> str:
    """
    Create a simple workflow visualization from task names and dependencies.
    
    Args:
        task_names: List of task names
        dependencies: Dict mapping task names to their dependencies
        task_states: Dict mapping task names to their states
        
    Returns:
        Mermaid diagram as string
    """
    dependencies = dependencies or {}
    task_states = task_states or {}
    
    # Convert to TaskNode objects
    tasks = []
    for name in task_names:
        tasks.append(TaskNode(
            id=name.replace(" ", "_").lower(),
            name=name,
            description=f"Task: {name}",
            state=task_states.get(name, TaskState.PENDING),
            priority="NORMAL",
            dependencies=[dep.replace(" ", "_").lower() for dep in dependencies.get(name, [])]
        ))
    
    visualizer = WorkflowVisualizer()
    return visualizer.visualize_dag(tasks)


def create_task_progress_diagram(
    total_tasks: int,
    completed_tasks: int,
    failed_tasks: int,
    running_tasks: int
) -> str:
    """Create a simple task progress visualization."""
    
    workflow_info = WorkflowInfo(
        name="Task Progress",
        description="Current execution status",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks
    )
    
    # Create mock tasks for visualization
    tasks = []
    
    # Add completed tasks
    for i in range(completed_tasks):
        tasks.append(TaskNode(
            id=f"completed_{i}",
            name=f"Task {i+1}",
            description="Completed task",
            state=TaskState.COMPLETED,
            priority="NORMAL",
            dependencies=[]
        ))
    
    # Add running tasks
    for i in range(running_tasks):
        tasks.append(TaskNode(
            id=f"running_{i}",
            name=f"Task {completed_tasks + i + 1}",
            description="Running task",
            state=TaskState.RUNNING,
            priority="NORMAL",
            dependencies=[]
        ))
    
    # Add failed tasks
    for i in range(failed_tasks):
        tasks.append(TaskNode(
            id=f"failed_{i}",
            name=f"Failed Task {i+1}",
            description="Failed task",
            state=TaskState.FAILED,
            priority="NORMAL",
            dependencies=[]
        ))
    
    visualizer = WorkflowVisualizer()
    return visualizer.create_performance_dashboard(tasks, workflow_info)