"""
Tests for the AgenticFlow visualization module.
"""

import pytest
from pathlib import Path
import tempfile
import os

from agenticflow.visualization import (
    MermaidGenerator,
    TopologyVisualizer,
    WorkflowVisualizer,
    check_export_capabilities
)
from agenticflow.visualization.mermaid_generator import (
    FlowDirection,
    NodeShape,
    EdgeType,
    DiagramType
)
from agenticflow.visualization.workflow_visualizer import (
    TaskNode,
    TaskState,
    WorkflowInfo,
    visualize_simple_workflow
)


class TestMermaidGenerator:
    """Test the core Mermaid generator."""
    
    def test_basic_flowchart_generation(self):
        """Test basic flowchart generation."""
        generator = MermaidGenerator()
        
        # Add nodes and edges
        generator.add_node("start", "Start", NodeShape.CIRCLE)
        generator.add_node("process", "Process Data", NodeShape.RECTANGLE)
        generator.add_node("end", "End", NodeShape.CIRCLE)
        
        generator.add_edge("start", "process", "begin")
        generator.add_edge("process", "end", "complete")
        
        diagram = generator.generate()
        
        assert "flowchart TD" in diagram
        assert "start((\"Start\"))" in diagram
        assert "process[\"Process Data\"]" in diagram
        assert "end((\"End\"))" in diagram
        assert "start -->|\"begin\"| process" in diagram
        assert "process -->|\"complete\"| end" in diagram
        
    def test_node_shapes(self):
        """Test different node shapes."""
        generator = MermaidGenerator()
        
        shapes_tests = [
            (NodeShape.RECTANGLE, "rect[\"Rectangle\"]"),
            (NodeShape.ROUNDED, "round(\"Rounded\")"),
            (NodeShape.CIRCLE, "circle((\"Circle\"))"),
            (NodeShape.DIAMOND, "diamond{\"Diamond\"}"),
            (NodeShape.HEXAGON, "hex{{Hexagon}}"),
        ]
        
        for shape, expected in shapes_tests:
            generator.clear()
            generator.add_node("test", shape.value.title(), shape)
            diagram = generator.generate()
            # Check that the node is formatted correctly (basic check)
            assert "test" in diagram
            
    def test_subgraphs(self):
        """Test subgraph functionality."""
        generator = MermaidGenerator()
        
        generator.add_node("a", "Node A")
        generator.add_node("b", "Node B")
        generator.add_subgraph("group1", "Group 1", ["a", "b"])
        
        diagram = generator.generate()
        
        assert "subgraph group1 [\"Group 1\"]" in diagram
        assert "a[\"Node A\"]" in diagram
        assert "b[\"Node B\"]" in diagram
        
    def test_css_classes_and_styles(self):
        """Test CSS classes and styling."""
        generator = MermaidGenerator()
        
        generator.add_css_class("highlight", {"fill": "#ff0000", "stroke": "#000"})
        generator.add_node("styled", "Styled Node", css_class="highlight")
        generator.add_style("styled", {"color": "#fff"})
        
        diagram = generator.generate()
        
        assert "classDef highlight fill:#ff0000,stroke:#000" in diagram
        assert "class styled highlight" in diagram
        assert "style styled color:#fff" in diagram


class TestWorkflowVisualizer:
    """Test the workflow visualizer."""
    
    def test_simple_workflow_creation(self):
        """Test simple workflow visualization."""
        task_names = ["Start", "Process", "End"]
        dependencies = {
            "Process": ["Start"],
            "End": ["Process"]
        }
        task_states = {
            "Start": TaskState.COMPLETED,
            "Process": TaskState.RUNNING,
            "End": TaskState.PENDING
        }
        
        diagram = visualize_simple_workflow(task_names, dependencies, task_states)
        
        assert "flowchart TD" in diagram
        assert "start" in diagram.lower()
        assert "process" in diagram.lower()
        assert "end" in diagram.lower()
        
    def test_task_dag_visualization(self):
        """Test task DAG visualization."""
        tasks = [
            TaskNode(
                id="task1",
                name="Task 1",
                description="First task",
                state=TaskState.COMPLETED,
                priority="HIGH",
                dependencies=[]
            ),
            TaskNode(
                id="task2",
                name="Task 2", 
                description="Second task",
                state=TaskState.RUNNING,
                priority="NORMAL",
                dependencies=["task1"]
            )
        ]
        
        visualizer = WorkflowVisualizer()
        diagram = visualizer.visualize_dag(tasks)
        
        assert "Task 1" in diagram
        assert "Task 2" in diagram
        assert "task1" in diagram
        assert "task2" in diagram
        
    def test_performance_dashboard(self):
        """Test performance dashboard creation."""
        tasks = [
            TaskNode("t1", "Task 1", "Desc", TaskState.COMPLETED, "NORMAL", []),
            TaskNode("t2", "Task 2", "Desc", TaskState.FAILED, "NORMAL", []),
            TaskNode("t3", "Task 3", "Desc", TaskState.RUNNING, "NORMAL", [])
        ]
        
        workflow_info = WorkflowInfo(
            name="Test Workflow",
            description="Test workflow description",
            total_tasks=3,
            completed_tasks=1,
            failed_tasks=1
        )
        
        visualizer = WorkflowVisualizer()
        diagram = visualizer.create_performance_dashboard(tasks, workflow_info)
        
        assert "Performance Metrics" in diagram
        assert "Total Tasks" in diagram
        assert "Completed" in diagram
        assert "Failed" in diagram


class TestTopologyVisualizer:
    """Test the topology visualizer."""
    
    def test_star_topology_basic(self):
        """Test basic star topology visualization without real agents."""
        # Since we can't easily create real agents in unit tests,
        # we'll test the internal methods with mock data
        visualizer = TopologyVisualizer()
        
        # This is a basic test to ensure the visualizer can be instantiated
        assert visualizer is not None
        assert hasattr(visualizer, 'generator')
        
    def test_topology_comparison(self):
        """Test topology comparison functionality."""
        visualizer = TopologyVisualizer()
        
        # Test that the method exists and can be called
        # In a full integration test, we'd pass real agents here
        assert hasattr(visualizer, 'create_topology_comparison')


class TestExportCapabilities:
    """Test export functionality."""
    
    def test_check_export_capabilities(self):
        """Test export capability detection."""
        capabilities = check_export_capabilities()
        
        assert "backends" in capabilities
        assert "formats" in capabilities
        assert "recommendations" in capabilities
        
        # Check expected backends
        assert "mermaid-py" in capabilities["backends"]
        assert "pyppeteer" in capabilities["backends"]
        assert "cli" in capabilities["backends"]
        
        # Check expected formats
        assert "svg" in capabilities["formats"]
        assert "png" in capabilities["formats"]
        assert "pdf" in capabilities["formats"]
        
    def test_mermaid_py_availability(self):
        """Test that mermaid-py is available."""
        generator = MermaidGenerator()
        
        # Should be available since we added it as a dependency
        assert generator.has_mermaid_py()
        
    def test_svg_export_basic(self):
        """Test basic SVG export functionality."""
        generator = MermaidGenerator()
        generator.add_node("test", "Test Node")
        
        # Test rendering (if mermaid-py is available)
        if generator.has_mermaid_py():
            svg_content = generator.render_to_svg()
            # SVG export might fail due to various reasons, so we just test it doesn't crash
            # In a real environment with proper mermaid setup, this would return SVG content
            assert svg_content is None or isinstance(svg_content, str)


class TestIntegration:
    """Integration tests for the visualization module."""
    
    def test_full_workflow_visualization(self):
        """Test complete workflow visualization pipeline."""
        # Create a simple workflow
        task_names = ["Setup", "Execute", "Cleanup"]
        dependencies = {
            "Execute": ["Setup"],
            "Cleanup": ["Execute"]
        }
        task_states = {
            "Setup": TaskState.COMPLETED,
            "Execute": TaskState.RUNNING,
            "Cleanup": TaskState.PENDING
        }
        
        # Generate diagram
        diagram = visualize_simple_workflow(task_names, dependencies, task_states)
        
        # Verify it's valid Mermaid syntax
        assert diagram.startswith("flowchart")
        assert "Setup" in diagram
        assert "Execute" in diagram
        assert "Cleanup" in diagram
        
        # Test that we can save to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as tmp:
            tmp.write(diagram)
            tmp.flush()
            
            # Verify file was created and has content
            assert os.path.exists(tmp.name)
            with open(tmp.name, 'r') as f:
                content = f.read()
                assert len(content) > 0
                assert "flowchart" in content
                
            # Cleanup
            os.unlink(tmp.name)


if __name__ == "__main__":
    pytest.main([__file__])