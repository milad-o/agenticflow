"""
Simple, fully-abstracted visualization interface for AgenticFlow.

This module provides the simplest possible interface for creating visualizations.
No graph setup required - just call functions with your data and get results!
"""

import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass

from .mermaid_generator import MermaidGenerator, NodeShape, EdgeType, FlowDirection
from .workflow_visualizer import WorkflowVisualizer, TaskNode, TaskState, WorkflowInfo


@dataclass
class SimpleTask:
    """Simple task representation for easy visualization."""
    name: str
    status: str = "pending"  # pending, running, completed, failed
    duration: Optional[float] = None
    depends_on: List[str] = None
    description: str = ""
    priority: str = "normal"  # low, normal, high, critical
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass 
class SimpleAgent:
    """Simple agent representation for easy visualization."""
    name: str
    role: str = "worker"  # worker, supervisor, specialist, coordinator
    tools: List[str] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []


def visualize_workflow(
    tasks: Union[List[SimpleTask], List[Dict], List[TaskNode]], 
    workflow_name: str = "Workflow",
    description: str = "Task execution workflow",
    show: bool = True,
    save_path: Optional[str] = None,
    format: str = "svg"
) -> Optional[str]:
    """
    Create a workflow visualization with zero setup required.
    
    Args:
        tasks: List of tasks (can be SimpleTask objects, dicts, or TaskNode objects)
        workflow_name: Name of the workflow
        description: Brief description
        show: Whether to open the visualization automatically
        save_path: Where to save (if None, uses temp file when show=True)
        format: Output format (svg, png, pdf)
        
    Returns:
        Path to the generated file, or None if failed
        
    Examples:
        # Super simple - just task names and dependencies
        visualize_workflow([
            {"name": "Load Data", "depends_on": []},
            {"name": "Process Data", "depends_on": ["Load Data"]},
            {"name": "Save Results", "depends_on": ["Process Data"]}
        ])
        
        # With status and timing
        visualize_workflow([
            SimpleTask("Setup", "completed", duration=15.0),
            SimpleTask("Training", "running", depends_on=["Setup"]),
            SimpleTask("Deploy", "pending", depends_on=["Training"])
        ])
    """
    # Convert input to TaskNode objects
    task_nodes = _convert_to_task_nodes(tasks)
    
    # Create workflow info
    completed = len([t for t in task_nodes if t.state == TaskState.COMPLETED])
    total = len(task_nodes)
    
    workflow_info = WorkflowInfo(
        name=workflow_name,
        description=description,
        total_tasks=total,
        completed_tasks=completed,
        failed_tasks=len([t for t in task_nodes if t.state == TaskState.FAILED]),
        execution_time=sum(t.actual_duration for t in task_nodes if t.actual_duration) or None
    )
    
    # Generate visualization
    viz = WorkflowVisualizer()
    
    # Determine output path
    if save_path:
        output_path = save_path
    elif show:
        output_path = tempfile.mktemp(suffix=f".{format}")
    else:
        return None
        
    # Create the visualization
    success = viz.draw_dag(
        task_nodes, 
        workflow_info, 
        output_path,
        format=format,
        group_by_priority=True
    )
    
    if success:
        if show and not save_path:
            # Open automatically
            try:
                import subprocess
                subprocess.run(["open", output_path], check=False)
            except Exception:
                pass
                
        return output_path
    else:
        print("❌ Failed to generate workflow visualization")
        return None


def visualize_agents(
    agents: Union[List[SimpleAgent], List[Dict]],
    topology: str = "star",  # star, hierarchy, pipeline, mesh
    title: str = "Multi-Agent System",
    show: bool = True,
    save_path: Optional[str] = None,
    format: str = "svg"
) -> Optional[str]:
    """
    Create an agent topology visualization with zero setup required.
    
    Args:
        agents: List of agents (can be SimpleAgent objects or dicts)
        topology: Type of topology (star, hierarchy, pipeline, mesh)
        title: Title for the diagram
        show: Whether to open the visualization automatically
        save_path: Where to save (if None, uses temp file when show=True)
        format: Output format (svg, png, pdf)
        
    Returns:
        Path to the generated file, or None if failed
        
    Examples:
        # Simple agent list
        visualize_agents([
            {"name": "Supervisor", "role": "supervisor"},
            {"name": "Worker 1", "role": "worker", "tools": ["search", "calculator"]},
            {"name": "Worker 2", "role": "worker", "tools": ["database"]}
        ])
        
        # Using SimpleAgent objects
        visualize_agents([
            SimpleAgent("Manager", "supervisor"),
            SimpleAgent("Researcher", "specialist", ["web_search", "pdf_reader"]),
            SimpleAgent("Analyst", "worker", ["calculator", "database"])
        ])
    """
    # Convert input to simple format we can work with
    agent_list = []
    for agent in agents:
        if isinstance(agent, dict):
            agent_list.append(SimpleAgent(
                name=agent.get("name", "Agent"),
                role=agent.get("role", "worker"),
                tools=agent.get("tools", [])
            ))
        elif isinstance(agent, SimpleAgent):
            agent_list.append(agent)
        else:
            # Try to extract from object
            agent_list.append(SimpleAgent(
                name=getattr(agent, 'name', str(agent)),
                role=getattr(agent, 'role', 'worker'),
                tools=getattr(agent, 'tools', [])
            ))
    
    # Create the visualization
    gen = MermaidGenerator()
    gen.set_direction(FlowDirection.TOP_DOWN)
    
    # Add title
    if title:
        gen.add_node("title", title, NodeShape.RECTANGLE, css_class="workflow-info")
    
    # Build topology based on type
    if topology.lower() == "star":
        _build_star_topology(gen, agent_list)
    elif topology.lower() in ["hierarchy", "hierarchical"]:
        _build_hierarchical_topology(gen, agent_list)
    elif topology.lower() == "pipeline":
        _build_pipeline_topology(gen, agent_list)
    elif topology.lower() in ["mesh", "peer-to-peer", "p2p"]:
        _build_mesh_topology(gen, agent_list)
    else:
        # Default to star
        _build_star_topology(gen, agent_list)
    
    # Add tools if any agents have them
    _add_tools_to_topology(gen, agent_list)
    
    # Determine output path
    if save_path:
        output_path = save_path
    elif show:
        output_path = tempfile.mktemp(suffix=f".{format}")
    else:
        return None
        
    # Generate the diagram
    success = gen.draw(output_path, format=format)
    
    if success:
        if show and not save_path:
            # Open automatically
            try:
                import subprocess
                subprocess.run(["open", output_path], check=False)
            except Exception:
                pass
                
        return output_path
    else:
        print("❌ Failed to generate agent topology visualization")
        return None


def quick_diagram(
    nodes: List[Union[str, Dict]],
    connections: List[tuple] = None,
    title: str = "Diagram", 
    show: bool = True,
    save_path: Optional[str] = None,
    format: str = "svg"
) -> Optional[str]:
    """
    Create any kind of diagram with minimal setup.
    
    Args:
        nodes: List of node names or dicts with node info
        connections: List of (from, to) or (from, to, label) tuples
        title: Diagram title
        show: Whether to open automatically
        save_path: Where to save
        format: Output format
        
    Returns:
        Path to generated file
        
    Examples:
        # Super simple
        quick_diagram(
            nodes=["Start", "Process", "End"],
            connections=[("Start", "Process"), ("Process", "End")]
        )
        
        # With labels and styling
        quick_diagram(
            nodes=[
                {"name": "API", "shape": "hexagon", "style": "external"},
                {"name": "Database", "shape": "cylinder", "style": "database"}
            ],
            connections=[("API", "Database", "queries")]
        )
    """
    gen = MermaidGenerator()
    gen.set_direction(FlowDirection.TOP_DOWN)
    
    # Add title
    if title:
        gen.add_node("title", title, NodeShape.RECTANGLE, css_class="workflow-info")
    
    # Process nodes
    for node in nodes:
        if isinstance(node, str):
            gen.add_node(node.lower().replace(" ", "_"), node)
        elif isinstance(node, dict):
            node_id = node.get("name", "node").lower().replace(" ", "_")
            name = node.get("name", "Node")
            shape = _get_node_shape(node.get("shape", "rectangle"))
            style = node.get("style", None)
            css_class = f"tool-{style}" if style else None
            
            gen.add_node(node_id, name, shape, css_class=css_class)
    
    # Process connections
    if connections:
        for conn in connections:
            if len(conn) == 2:
                from_name, to_name = conn
                label = ""
            elif len(conn) == 3:
                from_name, to_name, label = conn
            else:
                continue
                
            from_id = from_name.lower().replace(" ", "_")
            to_id = to_name.lower().replace(" ", "_")
            
            gen.add_edge(from_id, to_id, label)
    
    # Generate output
    if save_path:
        output_path = save_path
    elif show:
        output_path = tempfile.mktemp(suffix=f".{format}")
    else:
        return None
        
    success = gen.draw(output_path, format=format)
    
    if success:
        if show and not save_path:
            try:
                import subprocess
                subprocess.run(["open", output_path], check=False)
            except Exception:
                pass
                
        return output_path
    else:
        print("❌ Failed to generate diagram")
        return None


# === Jupyter notebook integration ===

def show_workflow(tasks, **kwargs):
    """Show workflow inline in Jupyter notebooks."""
    task_nodes = _convert_to_task_nodes(tasks)
    viz = WorkflowVisualizer()
    viz.visualize_dag(task_nodes, **kwargs)
    return viz  # Will display via _repr_html_


def show_agents(agents, topology="star", **kwargs):
    """Show agent topology inline in Jupyter notebooks.""" 
    # Convert and create the visualization
    gen = MermaidGenerator()
    
    # Set up CSS classes like the full system does
    from .mermaid_generator import create_agent_visualization_styles
    styles = create_agent_visualization_styles()
    for class_name, style_dict in styles.items():
        gen.add_css_class(class_name, style_dict)
    
    agent_list = []
    for agent in agents:
        if isinstance(agent, dict):
            agent_list.append(SimpleAgent(**agent))
        else:
            agent_list.append(agent)
    
    # Build based on topology
    if topology.lower() == "star":
        _build_star_topology(gen, agent_list)
    elif topology.lower() == "hierarchy":
        _build_hierarchical_topology(gen, agent_list) 
    else:
        _build_star_topology(gen, agent_list)
        
    return gen  # Will display via _repr_html_


# === Helper functions ===

def _convert_to_task_nodes(tasks: List[Union[SimpleTask, Dict, TaskNode]]) -> List[TaskNode]:
    """Convert various task formats to TaskNode objects."""
    task_nodes = []
    
    for task in tasks:
        if isinstance(task, TaskNode):
            task_nodes.append(task)
        elif isinstance(task, SimpleTask):
            state = _convert_status_to_state(task.status)
            task_nodes.append(TaskNode(
                id=task.name.lower().replace(" ", "_"),
                name=task.name,
                description=task.description,
                state=state,
                priority=task.priority.upper(),
                dependencies=[dep.lower().replace(" ", "_") for dep in task.depends_on],
                actual_duration=task.duration
            ))
        elif isinstance(task, dict):
            state = _convert_status_to_state(task.get("status", "pending"))
            task_nodes.append(TaskNode(
                id=task.get("name", "task").lower().replace(" ", "_"),
                name=task.get("name", "Task"),
                description=task.get("description", ""),
                state=state,
                priority=task.get("priority", "normal").upper(),
                dependencies=[dep.lower().replace(" ", "_") for dep in task.get("depends_on", [])],
                actual_duration=task.get("duration")
            ))
    
    return task_nodes


def _convert_status_to_state(status: str) -> TaskState:
    """Convert string status to TaskState enum."""
    status_lower = status.lower()
    if status_lower in ["completed", "done", "finished", "complete"]:
        return TaskState.COMPLETED
    elif status_lower in ["running", "active", "executing", "in_progress"]:
        return TaskState.RUNNING
    elif status_lower in ["failed", "error", "cancelled"]:
        return TaskState.FAILED
    elif status_lower in ["blocked", "waiting"]:
        return TaskState.BLOCKED
    else:
        return TaskState.PENDING


def _get_node_shape(shape_name: str) -> NodeShape:
    """Convert string shape name to NodeShape enum."""
    shape_lower = shape_name.lower()
    if shape_lower in ["circle", "round"]:
        return NodeShape.CIRCLE
    elif shape_lower in ["diamond", "decision"]:
        return NodeShape.DIAMOND
    elif shape_lower in ["hexagon", "hex"]:
        return NodeShape.HEXAGON
    elif shape_lower in ["cylinder", "database", "db"]:
        return NodeShape.CYLINDER
    elif shape_lower in ["rounded", "pill"]:
        return NodeShape.ROUNDED
    else:
        return NodeShape.RECTANGLE


def _build_star_topology(gen: MermaidGenerator, agents: List[SimpleAgent]):
    """Build star topology with supervisor at center."""
    supervisor = next((a for a in agents if a.role.lower() in ["supervisor", "manager"]), agents[0])
    workers = [a for a in agents if a != supervisor]
    
    # Add supervisor
    gen.add_node(
        supervisor.name.lower().replace(" ", "_"),
        f"{supervisor.name}<br/>({supervisor.role})",
        NodeShape.HEXAGON,
        css_class="agent-supervisor"
    )
    
    # Add workers
    for worker in workers:
        worker_id = worker.name.lower().replace(" ", "_")
        gen.add_node(
            worker_id,
            f"{worker.name}<br/>({worker.role})",
            NodeShape.ROUNDED,
            css_class=f"agent-{worker.role.lower()}"
        )
        
        # Connect to supervisor
        gen.add_edge(
            supervisor.name.lower().replace(" ", "_"),
            worker_id,
            "manages",
            EdgeType.SOLID
        )


def _build_hierarchical_topology(gen: MermaidGenerator, agents: List[SimpleAgent]):
    """Build hierarchical topology with layers."""
    supervisors = [a for a in agents if a.role.lower() in ["supervisor", "manager"]]
    coordinators = [a for a in agents if a.role.lower() in ["coordinator", "lead"]]
    workers = [a for a in agents if a.role.lower() in ["worker", "specialist"]]
    
    # Add all agents
    for agent_list, css_class in [
        (supervisors, "agent-supervisor"),
        (coordinators, "agent-coordinator"), 
        (workers, "agent-worker")
    ]:
        for agent in agent_list:
            agent_id = agent.name.lower().replace(" ", "_")
            shape = NodeShape.HEXAGON if "supervisor" in css_class else NodeShape.ROUNDED
            gen.add_node(
                agent_id,
                f"{agent.name}<br/>({agent.role})",
                shape,
                css_class=css_class
            )
    
    # Add connections
    for supervisor in supervisors:
        sup_id = supervisor.name.lower().replace(" ", "_")
        for coordinator in coordinators:
            coord_id = coordinator.name.lower().replace(" ", "_")
            gen.add_edge(sup_id, coord_id, "delegates", EdgeType.SOLID)
        for worker in workers:
            worker_id = worker.name.lower().replace(" ", "_") 
            gen.add_edge(sup_id, worker_id, "oversees", EdgeType.DOTTED)


def _build_pipeline_topology(gen: MermaidGenerator, agents: List[SimpleAgent]):
    """Build pipeline topology with sequential flow."""
    for i, agent in enumerate(agents):
        agent_id = agent.name.lower().replace(" ", "_")
        gen.add_node(
            agent_id,
            f"{agent.name}<br/>({agent.role})",
            NodeShape.ROUNDED,
            css_class=f"agent-{agent.role.lower()}"
        )
        
        if i > 0:
            prev_id = agents[i-1].name.lower().replace(" ", "_")
            gen.add_edge(prev_id, agent_id, f"step {i}", EdgeType.THICK)


def _build_mesh_topology(gen: MermaidGenerator, agents: List[SimpleAgent]):
    """Build mesh topology with all agents connected."""
    # Add agents
    for agent in agents:
        agent_id = agent.name.lower().replace(" ", "_")
        gen.add_node(
            agent_id,
            f"{agent.name}<br/>({agent.role})",
            NodeShape.ROUNDED,
            css_class=f"agent-{agent.role.lower()}"
        )
    
    # Connect all to all
    for i, agent1 in enumerate(agents):
        for j, agent2 in enumerate(agents):
            if i < j:
                id1 = agent1.name.lower().replace(" ", "_")
                id2 = agent2.name.lower().replace(" ", "_")
                gen.add_edge(id1, id2, "communicates", EdgeType.DOTTED)


def _add_tools_to_topology(gen: MermaidGenerator, agents: List[SimpleAgent]):
    """Add tool nodes and connections to the topology."""
    all_tools = set()
    for agent in agents:
        all_tools.update(agent.tools)
    
    if not all_tools:
        return
        
    # Add tool nodes
    for tool in all_tools:
        tool_id = f"tool_{tool.lower().replace(' ', '_')}"
        gen.add_node(
            tool_id,
            tool,
            NodeShape.CYLINDER,
            css_class="tool-default"
        )
    
    # Connect agents to their tools
    for agent in agents:
        agent_id = agent.name.lower().replace(" ", "_")
        for tool in agent.tools:
            tool_id = f"tool_{tool.lower().replace(' ', '_')}"
            gen.add_edge(agent_id, tool_id, "uses", EdgeType.DOTTED)