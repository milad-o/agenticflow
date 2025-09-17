#!/usr/bin/env python3
"""
AgenticFlow Interactive Visualization Demo

This demo shows how to use AgenticFlow's visualization capabilities
with .draw() and .show() methods for immediate diagram rendering.
"""

from pathlib import Path
from agenticflow.visualization import (
    MermaidGenerator,
    WorkflowVisualizer,
    TopologyVisualizer
)
from agenticflow.visualization.workflow_visualizer import (
    TaskNode,
    TaskState,
    WorkflowInfo
)
from agenticflow.visualization.mermaid_generator import (
    FlowDirection,
    NodeShape,
    EdgeType
)


def demo_quick_workflow():
    """Demo: Quickly create and render a workflow diagram."""
    print("🚀 Quick Workflow Visualization")
    print("=" * 50)
    
    # Create tasks
    tasks = [
        TaskNode("setup", "Environment Setup", "Initialize environment", 
                TaskState.COMPLETED, "HIGH", [], actual_duration=15.0),
        TaskNode("data_load", "Data Loading", "Load training data", 
                TaskState.COMPLETED, "CRITICAL", ["setup"], actual_duration=45.0),
        TaskNode("preprocessing", "Data Preprocessing", "Clean and prepare data", 
                TaskState.RUNNING, "HIGH", ["data_load"], estimated_duration=30.0),
        TaskNode("training", "Model Training", "Train ML model", 
                TaskState.PENDING, "CRITICAL", ["preprocessing"], estimated_duration=120.0),
        TaskNode("evaluation", "Model Evaluation", "Evaluate performance", 
                TaskState.PENDING, "HIGH", ["training"], estimated_duration=20.0),
        TaskNode("deployment", "Model Deployment", "Deploy to production", 
                TaskState.PENDING, "NORMAL", ["evaluation"], estimated_duration=25.0)
    ]
    
    workflow_info = WorkflowInfo(
        name="ML Training Pipeline",
        description="End-to-end ML model training",
        total_tasks=6,
        completed_tasks=2,
        failed_tasks=0,
        execution_time=60.0
    )
    
    # Create visualizer
    visualizer = WorkflowVisualizer()
    
    print("✨ Generating and displaying workflow diagram...")
    
    # Save to visible output directory using SVG (works with mermaid-py)
    output_path = Path(__file__).parent / "output" / "ml_workflow.svg"
    output_path.parent.mkdir(exist_ok=True)
    
    success = visualizer.draw_dag(
        tasks, 
        workflow_info, 
        str(output_path),
        format="svg",  # Use SVG format which works reliably with mermaid-py
        group_by_priority=True
    )
    
    if success:
        print(f"✅ Workflow diagram saved to: {output_path}")
        print(f"   You can open it with: open {output_path}")
    else:
        print("❌ Failed to render diagram")
    
    return tasks, workflow_info


def demo_quick_topology():
    """Demo: Quickly create and render a topology diagram.""" 
    print("\n🏗️ Quick Topology Visualization")
    print("=" * 40)
    
    # Create a simple topology using the generator directly
    generator = MermaidGenerator()
    generator.set_direction(FlowDirection.TOP_DOWN)
    
    # Add nodes
    generator.add_node("api", "API Gateway", NodeShape.HEXAGON, css_class="tool-external")
    generator.add_node("supervisor", "Supervisor Agent", NodeShape.DIAMOND, css_class="agent-supervisor") 
    generator.add_node("worker1", "Research Worker", NodeShape.ROUNDED, css_class="agent-worker")
    generator.add_node("worker2", "Analysis Worker", NodeShape.ROUNDED, css_class="agent-specialist")
    generator.add_node("db", "Database", NodeShape.CYLINDER, css_class="tool-database")
    
    # Add connections
    generator.add_edge("api", "supervisor", "request", EdgeType.SOLID)
    generator.add_edge("supervisor", "worker1", "assign", EdgeType.THICK)
    generator.add_edge("supervisor", "worker2", "assign", EdgeType.THICK)
    generator.add_edge("worker1", "db", "query", EdgeType.DOTTED)
    generator.add_edge("worker2", "db", "query", EdgeType.DOTTED)
    
    # Add subgraph
    generator.add_subgraph("workers", "Worker Agents", ["worker1", "worker2"])
    
    print("✨ Generating and displaying topology diagram...")
    
    # Save to visible output directory using SVG 
    output_path = Path(__file__).parent / "output" / "topology.svg"
    output_path.parent.mkdir(exist_ok=True)
    
    success = generator.draw(str(output_path), format="svg")
    
    if success:
        print(f"✅ Topology diagram saved to: {output_path}")
        print(f"   You can open it with: open {output_path}")
    else:
        print("❌ Failed to render diagram")


def demo_custom_diagram():
    """Demo: Create a custom business process diagram."""
    print("\n📊 Custom Business Process Diagram")
    print("=" * 40)
    
    generator = MermaidGenerator()
    generator.set_direction(FlowDirection.LEFT_RIGHT)
    
    # Business process flow
    generator.add_node("start", "Customer Request", NodeShape.CIRCLE, css_class="task-pending")
    generator.add_node("intake", "Request Intake", NodeShape.RECTANGLE, css_class="task-completed")
    generator.add_node("analysis", "Requirements Analysis", NodeShape.RECTANGLE, css_class="task-running")
    generator.add_node("approval", "Manager Approval", NodeShape.DIAMOND, css_class="task-pending")
    generator.add_node("implementation", "Implementation", NodeShape.RECTANGLE, css_class="task-pending")
    generator.add_node("testing", "Quality Testing", NodeShape.RECTANGLE, css_class="task-pending")
    generator.add_node("delivery", "Delivery", NodeShape.CIRCLE, css_class="task-pending")
    
    # Process flow
    generator.add_edge("start", "intake", "submit", EdgeType.SOLID)
    generator.add_edge("intake", "analysis", "process", EdgeType.SOLID)
    generator.add_edge("analysis", "approval", "review", EdgeType.SOLID)
    generator.add_edge("approval", "implementation", "approved", EdgeType.SOLID)
    generator.add_edge("approval", "analysis", "needs revision", EdgeType.DOTTED)
    generator.add_edge("implementation", "testing", "complete", EdgeType.SOLID)
    generator.add_edge("testing", "delivery", "pass", EdgeType.SOLID)
    generator.add_edge("testing", "implementation", "fail", EdgeType.DOTTED)
    
    # Add process stages
    generator.add_subgraph("initiation", "Initiation", ["start", "intake"])
    generator.add_subgraph("planning", "Planning", ["analysis", "approval"])
    generator.add_subgraph("execution", "Execution", ["implementation", "testing", "delivery"])
    
    print("✨ Generating custom business process diagram...")
    
    # Save to visible output directory using SVG
    output_path = Path(__file__).parent / "output" / "business_process.svg"
    output_path.parent.mkdir(exist_ok=True)
    
    success = generator.draw(str(output_path), format="svg")
    
    if success:
        print(f"✅ Business process diagram saved to: {output_path}")
        print(f"   You can open it with: open {output_path}")
    else:
        print("❌ Failed to render diagram")


def main():
    """Run the interactive visualization demos."""
    print("🎨 AgenticFlow Interactive Visualization Demo")
    print("=" * 55)
    print("This demo shows how to quickly generate and display diagrams")
    print("using .draw() and .show() methods for quick visualization")
    print()
    
    # Check export capabilities
    from agenticflow.visualization import check_export_capabilities
    capabilities = check_export_capabilities()
    
    print("📊 Export Capabilities:")
    for backend, available in capabilities["backends"].items():
        status = "✅" if available else "❌"
        print(f"  {status} {backend}")
    
    if not any(capabilities["backends"].values()):
        print("\n⚠️  No export backends available!")
        print("💡 Install mermaid-cli: npm install -g @mermaid-js/mermaid-cli")
        print("💡 Or pyppeteer is already installed for browser-based rendering")
        return
        
    print("\n" + "="*55)
    
    try:
        # Demo 1: Quick workflow
        demo_quick_workflow()
        
        # Demo 2: Quick topology  
        demo_quick_topology()
        
        # Demo 3: Custom diagram
        demo_custom_diagram()
        
        print(f"\n🎉 Demo completed!")
        print(f"\n💡 Key takeaways:")
        print(f"  • Use .show() for immediate viewing")
        print(f"  • Use .draw(path) to save to specific location")
        print(f"  • Interactive visualization at your fingertips!")
        print(f"  • Supports PNG, SVG, PDF formats")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\n🔧 Troubleshooting:")
        print(f"  1. Install mermaid-cli: npm install -g @mermaid-js/mermaid-cli")
        print(f"  2. Or check that pyppeteer is working")
        print(f"  3. Run: uv run python -c 'from agenticflow.visualization import check_export_capabilities; print(check_export_capabilities())'")


if __name__ == "__main__":
    main()