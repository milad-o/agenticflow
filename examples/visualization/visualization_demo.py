#!/usr/bin/env python3
"""
AgenticFlow Visualization Demo

This example demonstrates how to visualize multi-agent systems, workflows,
and task orchestration using the AgenticFlow visualization module.
"""

import asyncio
import tempfile
import os
from pathlib import Path

from agenticflow import Agent
from agenticflow.config.settings import AgentConfig, LLMProviderConfig, LLMProvider
from agenticflow.workflows.multi_agent import MultiAgentSystem
from agenticflow.workflows.topologies import TopologyType
from agenticflow.visualization import (
    TopologyVisualizer,
    WorkflowVisualizer,
    MermaidGenerator,
    export_to_svg,
    export_to_png,
    check_export_capabilities,
    print_installation_guide
)
from agenticflow.visualization.workflow_visualizer import (
    TaskNode,
    TaskState,
    WorkflowInfo,
    visualize_simple_workflow,
    create_task_progress_diagram
)
from agenticflow.visualization.mermaid_generator import (
    FlowDirection,
    NodeShape,
    EdgeType
)


def create_sample_agents():
    """Create sample agents for demonstration."""
    
    # Supervisor agent
    supervisor_config = AgentConfig(
        name="Supervisor",
        instructions="You coordinate and manage other agents",
        llm=LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-8b-instant"
        )
    )
    supervisor = Agent(supervisor_config)
    
    # Worker agents
    researcher_config = AgentConfig(
        name="Researcher",
        instructions="You research and gather information",
        llm=LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-8b-instant"
        )
    )
    researcher = Agent(researcher_config)
    
    writer_config = AgentConfig(
        name="Writer",
        instructions="You write and edit content",
        llm=LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-8b-instant"
        )
    )
    writer = Agent(writer_config)
    
    analyst_config = AgentConfig(
        name="Data Analyst",
        instructions="You analyze data and create insights",
        llm=LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-8b-instant"
        )
    )
    analyst = Agent(analyst_config)
    
    return supervisor, [researcher, writer, analyst]


def demo_topology_visualizations():
    """Demonstrate topology visualizations."""
    print("🏗️ Multi-Agent Topology Visualizations")
    print("=" * 50)
    
    supervisor, workers = create_sample_agents()
    
    # Create multi-agent systems with different topologies
    topologies = {
        "Star": TopologyType.STAR,
        "Peer-to-Peer": TopologyType.PEER_TO_PEER,
        "Hierarchical": TopologyType.HIERARCHICAL,
        "Pipeline": TopologyType.PIPELINE
    }
    
    visualizer = TopologyVisualizer()
    
    for name, topology_type in topologies.items():
        print(f"\n📊 {name} Topology:")
        print("-" * 30)
        
        # Create system
        system = MultiAgentSystem(
            supervisor=supervisor if topology_type != TopologyType.PEER_TO_PEER else None,
            agents=workers,
            topology=topology_type
        )
        
        # Generate visualization
        diagram = visualizer.visualize_system(
            system,
            include_tools=True,
            include_tool_relationships=True,
            layout_direction=FlowDirection.LEFT_RIGHT if name == "Pipeline" else FlowDirection.TOP_DOWN
        )
        
        print("Mermaid Code:")
        print(diagram)
        
        # Save to file
        output_dir = Path("visualization_output")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{name.lower().replace('-', '_')}_topology"
        
        # Save Mermaid source
        with open(output_dir / f"{filename}.mmd", "w") as f:
            f.write(diagram)
            
        # Try to export to SVG
        svg_path = output_dir / f"{filename}.svg"
        if export_to_svg(diagram, svg_path):
            print(f"✅ Exported to: {svg_path}")
        else:
            print("ℹ️  SVG export not available (install mermaid-cli for export support)")
            
        print()


def demo_workflow_visualizations():
    """Demonstrate workflow and task orchestration visualizations."""
    print("\n🔄 Workflow & Task Orchestration Visualizations")
    print("=" * 50)
    
    # Create sample workflow tasks
    tasks = [
        TaskNode(
            id="data_collection",
            name="Data Collection",
            description="Gather required data from sources",
            state=TaskState.COMPLETED,
            priority="HIGH",
            dependencies=[],
            actual_duration=15.2
        ),
        TaskNode(
            id="data_processing",
            name="Data Processing",
            description="Clean and process collected data",
            state=TaskState.COMPLETED,
            priority="HIGH", 
            dependencies=["data_collection"],
            actual_duration=23.8
        ),
        TaskNode(
            id="analysis",
            name="Analysis",
            description="Analyze processed data",
            state=TaskState.RUNNING,
            priority="CRITICAL",
            dependencies=["data_processing"],
            estimated_duration=30.0
        ),
        TaskNode(
            id="report_generation",
            name="Report Generation", 
            description="Generate final report",
            state=TaskState.PENDING,
            priority="NORMAL",
            dependencies=["analysis"],
            estimated_duration=12.0
        ),
        TaskNode(
            id="review",
            name="Review",
            description="Review and validate report",
            state=TaskState.PENDING,
            priority="NORMAL",
            dependencies=["report_generation"],
            estimated_duration=8.0
        )
    ]
    
    workflow_info = WorkflowInfo(
        name="Data Analysis Pipeline",
        description="Complete data analysis workflow",
        total_tasks=len(tasks),
        completed_tasks=2,
        failed_tasks=0,
        execution_time=89.5
    )
    
    visualizer = WorkflowVisualizer()
    
    # DAG Visualization
    print("\n📊 Task DAG with Priority Groups:")
    print("-" * 40)
    dag_diagram = visualizer.visualize_dag(
        tasks,
        workflow_info=workflow_info,
        layout_direction=FlowDirection.TOP_DOWN,
        group_by_priority=True
    )
    print(dag_diagram)
    
    # Save DAG diagram
    output_dir = Path("visualization_output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "workflow_dag.mmd", "w") as f:
        f.write(dag_diagram)
        
    # Performance Dashboard
    print("\n📈 Performance Dashboard:")
    print("-" * 30)
    dashboard_diagram = visualizer.create_performance_dashboard(tasks, workflow_info)
    print(dashboard_diagram)
    
    with open(output_dir / "performance_dashboard.mmd", "w") as f:
        f.write(dashboard_diagram)
        
    # Timeline Visualization
    print("\n⏱️  Execution Timeline:")
    print("-" * 25)
    timeline_diagram = visualizer.visualize_execution_timeline(tasks)
    print(timeline_diagram)
    
    with open(output_dir / "execution_timeline.mmd", "w") as f:
        f.write(timeline_diagram)


def demo_simple_workflow():
    """Demonstrate simple workflow creation."""
    print("\n🚀 Simple Workflow Visualization")
    print("=" * 40)
    
    # Create a simple workflow with dependencies
    task_names = ["Setup", "Data Collection", "Processing", "Analysis", "Reporting"]
    dependencies = {
        "Data Collection": ["Setup"],
        "Processing": ["Data Collection"],
        "Analysis": ["Processing"],
        "Reporting": ["Analysis"]
    }
    task_states = {
        "Setup": TaskState.COMPLETED,
        "Data Collection": TaskState.COMPLETED,
        "Processing": TaskState.RUNNING,
        "Analysis": TaskState.PENDING,
        "Reporting": TaskState.PENDING
    }
    
    diagram = visualize_simple_workflow(task_names, dependencies, task_states)
    print(diagram)
    
    # Save simple workflow
    output_dir = Path("visualization_output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "simple_workflow.mmd", "w") as f:
        f.write(diagram)


def demo_progress_visualization():
    """Demonstrate task progress visualization."""
    print("\n📊 Task Progress Visualization")
    print("=" * 35)
    
    diagram = create_task_progress_diagram(
        total_tasks=20,
        completed_tasks=12,
        failed_tasks=2, 
        running_tasks=3
    )
    print(diagram)
    
    # Save progress diagram
    output_dir = Path("visualization_output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "task_progress.mmd", "w") as f:
        f.write(diagram)


def demo_custom_mermaid():
    """Demonstrate custom Mermaid diagram creation."""
    print("\n🎨 Custom Mermaid Diagram")
    print("=" * 30)
    
    generator = MermaidGenerator()
    
    # Create a custom system architecture diagram
    generator.set_direction(FlowDirection.LEFT_RIGHT)
    
    # Add nodes
    generator.add_node("user", "User", NodeShape.CIRCLE, css_class="agent-coordinator")
    generator.add_node("api", "API Gateway", NodeShape.HEXAGON, css_class="tool-external")
    generator.add_node("supervisor", "Supervisor Agent", NodeShape.DIAMOND, css_class="agent-supervisor")
    generator.add_node("worker1", "Research Agent", NodeShape.ROUNDED, css_class="agent-worker")
    generator.add_node("worker2", "Analysis Agent", NodeShape.ROUNDED, css_class="agent-specialist")
    generator.add_node("db", "Database", NodeShape.CYLINDER, css_class="tool-database")
    
    # Add edges
    generator.add_edge("user", "api", "request", EdgeType.SOLID)
    generator.add_edge("api", "supervisor", "delegate", EdgeType.SOLID)
    generator.add_edge("supervisor", "worker1", "assign task", EdgeType.THICK)
    generator.add_edge("supervisor", "worker2", "assign task", EdgeType.THICK)
    generator.add_edge("worker1", "db", "query", EdgeType.DOTTED)
    generator.add_edge("worker2", "db", "query", EdgeType.DOTTED)
    generator.add_edge("worker1", "supervisor", "report", EdgeType.SOLID)
    generator.add_edge("worker2", "supervisor", "report", EdgeType.SOLID)
    generator.add_edge("supervisor", "api", "response", EdgeType.SOLID)
    generator.add_edge("api", "user", "result", EdgeType.SOLID)
    
    # Add subgraph
    generator.add_subgraph("agents", "AI Agents", ["supervisor", "worker1", "worker2"])
    
    diagram = generator.generate()
    print(diagram)
    
    # Save custom diagram
    output_dir = Path("visualization_output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "custom_architecture.mmd", "w") as f:
        f.write(diagram)
        
    # Try direct SVG export using mermaid-py
    if generator.has_mermaid_py():
        svg_path = output_dir / "custom_architecture.svg"
        if generator.export_svg(str(svg_path)):
            print(f"✅ Direct SVG export successful: {svg_path}")
        else:
            print("❌ Direct SVG export failed")


def demo_export_capabilities():
    """Demonstrate export capabilities and show installation guide."""
    print("\n🔧 Export Capabilities")
    print("=" * 25)
    
    capabilities = check_export_capabilities()
    
    print("Current Export Capabilities:")
    for backend, available in capabilities["backends"].items():
        status = "✅" if available else "❌"
        print(f"  {status} {backend}")
        
    print("\nSupported Formats:")
    for format, supported in capabilities["formats"].items():
        status = "✅" if supported else "❌"
        print(f"  {status} {format.upper()}")
        
    if capabilities["recommendations"]:
        print("\nRecommendations:")
        for rec in capabilities["recommendations"]:
            print(f"  💡 {rec}")
            
    print("\n" + "="*50)
    print_installation_guide()


def main():
    """Run the visualization demo."""
    print("🎨 AgenticFlow Visualization Demo")
    print("="*50)
    print()
    
    # Create output directory
    output_dir = Path("visualization_output")
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output will be saved to: {output_dir.absolute()}")
    print()
    
    try:
        # Run all demos
        demo_export_capabilities()
        demo_topology_visualizations()
        demo_workflow_visualizations()
        demo_simple_workflow()
        demo_progress_visualization()
        demo_custom_mermaid()
        
        print("\n🎉 Demo completed successfully!")
        print("\n📋 Generated Files:")
        for file in sorted(output_dir.glob("*")):
            print(f"  • {file.name}")
            
        print(f"\n💡 To view the diagrams:")
        print(f"   1. Copy the .mmd file contents to https://mermaid.live")
        print(f"   2. Or install mermaid-cli: npm install -g @mermaid-js/mermaid-cli")
        print(f"   3. Then export: mmdc -i diagram.mmd -o diagram.svg")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()