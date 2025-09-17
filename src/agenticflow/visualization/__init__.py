"""
AgenticFlow Visualization Module

Provides simple, zero-setup visualization for AgenticFlow objects.

## Quick Start

For workflows:
    visualize_workflow(tasks)  # Auto-opens diagram
    
For agents:
    visualize_agents(agents, topology="star")  # Shows agent network
    
For custom diagrams:
    quick_diagram(nodes, connections)  # Generic diagrams

## Object Methods

All AgenticFlow objects now have built-in visualization:
    agent.visualize()        # Shows agent with tools
    orchestrator.show()      # Shows workflow state  
    system.visualize()       # Shows multi-agent topology

## Jupyter Notebooks

Objects display automatically:
    agent                    # Shows inline visualization
    orchestrator             # Shows workflow diagram
    system                   # Shows topology

Or use explicit functions:
    show_workflow(tasks)     # For inline display
    show_agents(agents)      # For inline display
"""

# === Main API - Simple Functions (Zero Setup Required) ===
from .simple import (
    # Main visualization functions
    visualize_workflow,
    visualize_agents, 
    quick_diagram,
    
    # Jupyter notebook functions
    show_workflow,
    show_agents,
    
    # Simple data classes
    SimpleTask,
    SimpleAgent
)

# === Advanced API - For Power Users ===
from .mermaid_generator import MermaidGenerator
from .workflow_visualizer import WorkflowVisualizer, TaskNode, TaskState, WorkflowInfo
from .topology_visualizer import TopologyVisualizer

# === Export and Utilities ===
from .export_utils import (
    export_to_svg, 
    export_to_png, 
    export_to_pdf,
    check_export_capabilities,
    print_installation_guide
)

# === Mixins (Automatically Applied to Core Objects) ===
from .mixins import (
    AgentVisualizationMixin,
    WorkflowVisualizationMixin, 
    MultiAgentSystemVisualizationMixin,
    JupyterVisualizationMixin,
    FullVisualizationMixin
)

__all__ = [
    # === Primary API (Most Users) ===
    "visualize_workflow",
    "visualize_agents", 
    "quick_diagram",
    "show_workflow",
    "show_agents",
    "SimpleTask",
    "SimpleAgent",
    
    # === Advanced API (Power Users) ===
    "MermaidGenerator",
    "WorkflowVisualizer",
    "TopologyVisualizer",
    "TaskNode",
    "TaskState", 
    "WorkflowInfo",
    
    # === Export Utilities ===
    "export_to_svg",
    "export_to_png",
    "export_to_pdf",
    "check_export_capabilities",
    "print_installation_guide",
    
    # === Mixins (For Framework Developers) ===
    "AgentVisualizationMixin",
    "WorkflowVisualizationMixin", 
    "MultiAgentSystemVisualizationMixin",
    "JupyterVisualizationMixin",
    "FullVisualizationMixin",
]
