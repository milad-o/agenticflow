#!/usr/bin/env python3
"""
Simple AgenticFlow Visualization Demo

This example demonstrates the visualization capabilities without complex dependencies.
"""

from pathlib import Path
from agenticflow.visualization import (
    MermaidGenerator,
    TopologyVisualizer,
    WorkflowVisualizer,
    export_to_svg,
    export_to_png,
    check_export_capabilities
)
from agenticflow.visualization.mermaid_generator import (
    FlowDirection,
    NodeShape,
    EdgeType,
    create_agent_visualization_styles
)
from agenticflow.visualization.workflow_visualizer import (
    TaskNode,
    TaskState,
    WorkflowInfo,
    visualize_simple_workflow,
    create_task_progress_diagram
)


def create_star_topology():
    """Create a star topology visualization."""
    generator = MermaidGenerator()
    generator.set_direction(FlowDirection.TOP_DOWN)
    
    # Add default styles
    styles = create_agent_visualization_styles()
    for class_name, style in styles.items():
        generator.add_css_class(class_name, style)
    
    # Supervisor at center
    generator.add_node(
        "supervisor",
        "Supervisor Agent<br/>(Coordinator)",
        NodeShape.HEXAGON,
        css_class="agent-supervisor"
    )
    
    # Worker agents around supervisor
    workers = [
        ("researcher", "Research Agent\\n(Data Gathering)"),
        ("writer", "Writing Agent\\n(Content Creation)"),
        ("analyst", "Analysis Agent\\n(Data Analysis)"),
        ("reviewer", "Review Agent\\n(Quality Check)")
    ]
    
    for worker_id, worker_name in workers:
        generator.add_node(
            worker_id,
            worker_name,
            NodeShape.ROUNDED,
            css_class="agent-worker"
        )
        
        # Connect to supervisor
        generator.add_edge(
            "supervisor",
            worker_id,
            "manages",
            EdgeType.SOLID
        )
        generator.add_edge(
            worker_id,
            "supervisor", 
            "reports",
            EdgeType.DOTTED
        )
    
    # Add tools subgraph
    generator.add_subgraph("tools", "Available Tools")
    
    tools = [
        ("search_tool", "Web Search", "tool-external"),
        ("db_tool", "Database", "tool-database"),
        ("llm_tool", "LLM API", "tool-llm"),
        ("file_tool", "File System", "tool-default")
    ]
    
    for tool_id, tool_name, tool_class in tools:
        generator.add_node(
            tool_id,
            tool_name,
            NodeShape.CYLINDER,
            css_class=tool_class
        )
        generator.subgraphs["tools"].nodes.append(tool_id)
    
    # Connect some agents to tools
    generator.add_edge("researcher", "search_tool", "uses", EdgeType.DOTTED)
    generator.add_edge("analyst", "db_tool", "queries", EdgeType.DOTTED)
    generator.add_edge("writer", "llm_tool", "uses", EdgeType.DOTTED)
    
    return generator.generate()


def create_peer_to_peer_topology():
    """Create a peer-to-peer topology visualization."""
    generator = MermaidGenerator()
    generator.set_direction(FlowDirection.LEFT_RIGHT)
    
    # Add styles
    styles = create_agent_visualization_styles()
    for class_name, style in styles.items():
        generator.add_css_class(class_name, style)
    
    # All agents are equal peers
    agents = [
        ("agent_a", "Agent A\\n(Specialist)", "agent-specialist"),
        ("agent_b", "Agent B\\n(Coordinator)", "agent-coordinator"),
        ("agent_c", "Agent C\\n(Worker)", "agent-worker"),
        ("agent_d", "Agent D\\n(Specialist)", "agent-specialist")
    ]
    
    # Add all agent nodes
    for agent_id, agent_name, agent_class in agents:
        generator.add_node(
            agent_id,
            agent_name,
            NodeShape.ROUNDED,
            css_class=agent_class
        )
    
    # Connect all agents to each other (fully connected)
    for i, (agent1_id, _, _) in enumerate(agents):
        for j, (agent2_id, _, _) in enumerate(agents):
            if i < j:  # Avoid duplicate connections
                generator.add_edge(
                    agent1_id,
                    agent2_id,
                    "communicates",
                    EdgeType.DOTTED
                )
    
    return generator.generate()


def create_hierarchical_topology():
    """Create a hierarchical topology visualization."""
    generator = MermaidGenerator()
    generator.set_direction(FlowDirection.TOP_DOWN)
    
    # Add styles
    styles = create_agent_visualization_styles()
    for class_name, style in styles.items():
        generator.add_css_class(class_name, style)
    
    # Management layer
    generator.add_subgraph("management", "Management Layer")
    generator.add_node(
        "ceo_agent",
        "CEO Agent\\n(Strategic)",
        NodeShape.HEXAGON,
        css_class="agent-supervisor"
    )
    generator.subgraphs["management"].nodes.append("ceo_agent")
    
    # Coordination layer
    generator.add_subgraph("coordination", "Coordination Layer")
    coordinators = [
        ("ops_coordinator", "Operations\\nCoordinator"),
        ("tech_coordinator", "Technical\\nCoordinator")
    ]
    
    for coord_id, coord_name in coordinators:
        generator.add_node(
            coord_id,
            coord_name,
            NodeShape.DIAMOND,
            css_class="agent-coordinator"
        )
        generator.subgraphs["coordination"].nodes.append(coord_id)
        
        # Connect to management
        generator.add_edge("ceo_agent", coord_id, "delegates", EdgeType.SOLID)
    
    # Execution layer
    generator.add_subgraph("execution", "Execution Layer")
    workers = [
        ("data_worker", "Data Worker", "ops_coordinator"),
        ("api_worker", "API Worker", "ops_coordinator"),
        ("ml_worker", "ML Worker", "tech_coordinator"),
        ("dev_worker", "Dev Worker", "tech_coordinator")
    ]
    
    for worker_id, worker_name, manager in workers:
        generator.add_node(
            worker_id,
            worker_name,
            NodeShape.ROUNDED,
            css_class="agent-worker"
        )
        generator.subgraphs["execution"].nodes.append(worker_id)
        
        # Connect to coordinator
        generator.add_edge(manager, worker_id, "manages", EdgeType.SOLID)
    
    return generator.generate()


def create_pipeline_topology():
    """Create a pipeline topology visualization."""
    generator = MermaidGenerator()
    generator.set_direction(FlowDirection.LEFT_RIGHT)
    
    # Add styles
    styles = create_agent_visualization_styles()
    for class_name, style in styles.items():
        generator.add_css_class(class_name, style)
    
    # Pipeline stages
    stages = [
        ("input_agent", "Input Agent\\n(Data Ingestion)", "agent-coordinator"),
        ("process_agent", "Process Agent\\n(Data Cleaning)", "agent-worker"),
        ("transform_agent", "Transform Agent\\n(Feature Engineering)", "agent-specialist"),
        ("analyze_agent", "Analyze Agent\\n(ML Analysis)", "agent-specialist"),
        ("output_agent", "Output Agent\\n(Results)", "agent-coordinator")
    ]
    
    # Add pipeline nodes
    for i, (agent_id, agent_name, agent_class) in enumerate(stages):
        generator.add_node(
            agent_id,
            agent_name,
            NodeShape.ROUNDED,
            css_class=agent_class
        )
        
        # Connect in sequence
        if i > 0:
            prev_agent_id = stages[i-1][0]
            generator.add_edge(
                prev_agent_id,
                agent_id,
                f"step {i}",
                EdgeType.THICK
            )
    
    # Add feedback loop
    generator.add_edge(
        "analyze_agent",
        "process_agent",
        "feedback",
        EdgeType.DOTTED
    )
    
    return generator.generate()


def create_workflow_dag():
    """Create a workflow DAG visualization."""
    tasks = [
        TaskNode(
            id="data_ingestion",
            name="Data Ingestion",
            description="Collect data from sources",
            state=TaskState.COMPLETED,
            priority="CRITICAL",
            dependencies=[],
            actual_duration=45.2
        ),
        TaskNode(
            id="data_validation",
            name="Data Validation",
            description="Validate data quality",
            state=TaskState.COMPLETED,
            priority="HIGH",
            dependencies=["data_ingestion"],
            actual_duration=23.7
        ),
        TaskNode(
            id="data_processing",
            name="Data Processing",
            description="Clean and process data",
            state=TaskState.RUNNING,
            priority="HIGH",
            dependencies=["data_validation"],
            estimated_duration=60.0
        ),
        TaskNode(
            id="feature_engineering",
            name="Feature Engineering",
            description="Create ML features",
            state=TaskState.PENDING,
            priority="NORMAL",
            dependencies=["data_processing"],
            estimated_duration=35.0
        ),
        TaskNode(
            id="model_training",
            name="Model Training",
            description="Train ML model",
            state=TaskState.PENDING,
            priority="CRITICAL",
            dependencies=["feature_engineering"],
            estimated_duration=120.0
        ),
        TaskNode(
            id="model_evaluation",
            name="Model Evaluation",
            description="Evaluate model performance",
            state=TaskState.PENDING,
            priority="HIGH",
            dependencies=["model_training"],
            estimated_duration=25.0
        ),
        TaskNode(
            id="deployment",
            name="Model Deployment",
            description="Deploy model to production",
            state=TaskState.PENDING,
            priority="CRITICAL",
            dependencies=["model_evaluation"],
            estimated_duration=40.0
        )
    ]
    
    workflow_info = WorkflowInfo(
        name="ML Pipeline Workflow",
        description="Complete machine learning pipeline",
        total_tasks=len(tasks),
        completed_tasks=2,
        failed_tasks=0,
        execution_time=68.9
    )
    
    visualizer = WorkflowVisualizer()
    return visualizer.visualize_dag(tasks, workflow_info, group_by_priority=True)


def create_performance_dashboard():
    """Create a performance dashboard."""
    tasks = [
        TaskNode(f"task_{i}", f"Task {i+1}", f"Description {i+1}", 
                state, priority, [])
        for i, (state, priority) in enumerate([
            (TaskState.COMPLETED, "NORMAL"),
            (TaskState.COMPLETED, "HIGH"),
            (TaskState.COMPLETED, "NORMAL"),
            (TaskState.RUNNING, "CRITICAL"),
            (TaskState.RUNNING, "HIGH"),
            (TaskState.FAILED, "NORMAL"),
            (TaskState.PENDING, "LOW"),
            (TaskState.PENDING, "NORMAL"),
            (TaskState.PENDING, "HIGH")
        ])
    ]
    
    workflow_info = WorkflowInfo(
        name="Production Workflow",
        description="Production system performance",
        total_tasks=9,
        completed_tasks=3,
        failed_tasks=1,
        execution_time=245.8
    )
    
    visualizer = WorkflowVisualizer()
    return visualizer.create_performance_dashboard(tasks, workflow_info)


def generate_readme(output_dir: Path, visualizations: dict):
    """Generate README.md with embedded Mermaid diagrams."""
    
    # Read all generated .mmd files
    diagrams = {}
    for mmd_file in output_dir.glob("*.mmd"):
        filename = mmd_file.stem  # Get filename without extension
        with open(mmd_file, 'r') as f:
            diagrams[filename] = f.read()
    
    readme_content = '''# 🎨 AgenticFlow Visualization Examples

This directory contains examples demonstrating the **AgenticFlow Visualization Module** capabilities.

## 🚀 Quick Start

```bash
# Run the visualization demo
uv run python simple_visualization_demo.py

# View outputs in the output/ directory
ls output/
```

## 📊 Generated Visualizations

'''  # noqa: E501
    
    # Add each visualization with embedded Mermaid
    diagram_descriptions = {
        "star_topology": ("⭐ Star Topology", "Central supervisor coordinating multiple worker agents with shared tools"),
        "peer_to_peer": ("🔗 Peer-to-Peer Topology", "Fully connected network where all agents communicate directly"),
        "hierarchical": ("🏢 Hierarchical Topology", "Multi-layer organizational structure with clear command chains"),
        "pipeline": ("⚡ Pipeline Topology", "Sequential data processing with feedback loops"),
        "workflow_dag": ("📊 Workflow DAG", "Task orchestration with priority levels and dependencies"),
        "performance_dashboard": ("📈 Performance Dashboard", "Real-time system performance metrics and critical path analysis"),
        "simple_workflow": ("🚀 Simple Workflow", "Basic sequential workflow for documentation"),
        "task_progress": ("📊 Task Progress Overview", "High-level project status dashboard")
    }
    
    for filename, (title, description) in diagram_descriptions.items():
        if filename in diagrams:
            readme_content += f'''### {title}
**{description}**

```mermaid
{diagrams[filename]}
```

'''
    
    readme_content += '''## 🎯 Features Demonstrated

### 🎨 **Visual Elements**
- **Node Shapes**: Hexagons (supervisors), Diamonds (coordinators), Rectangles (tasks), Cylinders (tools)
- **Edge Types**: Solid arrows (management), Dotted (communication), Thick (critical path)
- **Color Coding**: Role-based colors for agents, status-based colors for tasks
- **Subgraphs**: Logical grouping of related elements

### 🏗️ **Topology Types**
- **Star**: Central coordination with worker agents
- **Peer-to-Peer**: Fully connected agent network
- **Hierarchical**: Multi-layer organizational structure
- **Pipeline**: Sequential processing with feedback

### 📊 **Workflow Features**
- **DAG Visualization**: Task dependencies and execution flow
- **Priority Grouping**: CRITICAL, HIGH, NORMAL task priorities
- **Status Tracking**: Completed, Running, Pending, Failed states
- **Performance Metrics**: Success rates, timing, critical path

## 🔧 Usage in Your Code

```python
from agenticflow.visualization import TopologyVisualizer, WorkflowVisualizer

# Visualize multi-agent system
topology_viz = TopologyVisualizer()
diagram = topology_viz.visualize_system(your_system, include_tools=True)

# Visualize workflow
workflow_viz = WorkflowVisualizer()
dag_diagram = workflow_viz.visualize_dag(your_tasks, group_by_priority=True)

# Export to files
from agenticflow.visualization import export_to_svg, export_to_png
export_to_svg(diagram, "topology.svg")
export_to_png(diagram, "topology.png")
```

## 📁 Files

- `simple_visualization_demo.py` - Main demo script (generates this README)
- `output/` - Generated Mermaid (.mmd) files
- `README.md` - This file with embedded diagrams (auto-generated)

## 💡 Next Steps

1. **View Source**: Check the `.mmd` files in `output/` directory
2. **Export**: Use mermaid-cli to export PNG/SVG: `mmdc -i diagram.mmd -o diagram.png`
3. **Integrate**: Use these patterns in your own AgenticFlow applications
4. **Customize**: Modify colors, shapes, and layouts for your specific needs

---

*This README was automatically generated by `simple_visualization_demo.py`*
'''
    
    # Write README.md
    readme_path = output_dir.parent / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
        
    return readme_path


def main():
    """Generate all visualization examples."""
    print("🎨 AgenticFlow Visualization Gallery")
    print("="*50)
    
    # Create output directory relative to this script
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    # Check export capabilities
    capabilities = check_export_capabilities()
    print(f"\n📊 Export capabilities:")
    for backend, available in capabilities["backends"].items():
        status = "✅" if available else "❌"
        print(f"  {status} {backend}")
    
    print(f"\n🎯 Generating visualizations...")
    
    # Generate all topology types
    visualizations = {
        "star_topology": ("⭐ Star Topology", create_star_topology),
        "peer_to_peer": ("🔗 Peer-to-Peer Topology", create_peer_to_peer_topology),
        "hierarchical": ("🏢 Hierarchical Topology", create_hierarchical_topology),
        "pipeline": ("⚡ Pipeline Topology", create_pipeline_topology),
        "workflow_dag": ("📊 Workflow DAG", create_workflow_dag),
        "performance_dashboard": ("📈 Performance Dashboard", create_performance_dashboard)
    }
    
    for filename, (title, generator_func) in visualizations.items():
        print(f"\n{title}")
        print("-" * len(title))
        
        # Generate diagram
        diagram = generator_func()
        
        # Save Mermaid source
        mmd_path = output_dir / f"{filename}.mmd"
        with open(mmd_path, "w") as f:
            f.write(diagram)
        print(f"📄 Saved: {mmd_path}")
        
        # Try to export to SVG
        svg_path = output_dir / f"{filename}.svg"
        if export_to_svg(diagram, svg_path):
            print(f"🖼️  SVG exported: {svg_path}")
        else:
            print("ℹ️  SVG export not available")
        
        # Show a preview of the Mermaid code (first few lines)
        lines = diagram.split('\n')
        preview = '\n'.join(lines[:8]) + ('\n...' if len(lines) > 8 else '')
        print(f"👀 Preview:\n{preview}")
    
    # Create a simple workflow example
    print(f"\n🚀 Simple Workflow Example")
    print("-" * 30)
    
    simple_diagram = visualize_simple_workflow(
        task_names=["Setup", "Process", "Validate", "Deploy"],
        dependencies={
            "Process": ["Setup"],
            "Validate": ["Process"],
            "Deploy": ["Validate"]
        },
        task_states={
            "Setup": TaskState.COMPLETED,
            "Process": TaskState.COMPLETED,
            "Validate": TaskState.RUNNING,
            "Deploy": TaskState.PENDING
        }
    )
    
    simple_path = output_dir / "simple_workflow.mmd"
    with open(simple_path, "w") as f:
        f.write(simple_diagram)
    print(f"📄 Saved: {simple_path}")
    
    # Task progress example
    print(f"\n📊 Task Progress Example")
    print("-" * 28)
    
    progress_diagram = create_task_progress_diagram(
        total_tasks=25,
        completed_tasks=15,
        failed_tasks=3,
        running_tasks=4
    )
    
    progress_path = output_dir / "task_progress.mmd"
    with open(progress_path, "w") as f:
        f.write(progress_diagram)
    print(f"📄 Saved: {progress_path}")
    
    print(f"\n🎉 All visualizations generated!")
    
    # Generate README.md with embedded diagrams
    print(f"\n📝 Generating README.md...")
    readme_path = generate_readme(output_dir, visualizations)
    print(f"📄 Generated: {readme_path}")
    
    print(f"\n📋 Generated Files:")
    for file in sorted(output_dir.glob("*.mmd")):
        print(f"  • {file.name}")
    print(f"  • README.md (with embedded diagrams)")
    
    print(f"\n💡 Next steps:")
    print(f"  1. View diagrams: Open README.md in GitHub/GitLab or markdown viewer")
    print(f"  2. View online: Copy .mmd contents to https://mermaid.live")
    print(f"  3. Install CLI: npm install -g @mermaid-js/mermaid-cli")
    print(f"  4. Export: mmdc -i diagram.mmd -o diagram.png")
    print(f"  5. Use in docs: Include .mmd files in your documentation")


if __name__ == "__main__":
    main()