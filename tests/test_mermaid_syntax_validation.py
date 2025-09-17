#!/usr/bin/env python3
"""
Comprehensive test script to validate Mermaid syntax compliance.
Tests all node shapes, edge types, and diagram structures against official Mermaid documentation.
"""

import sys
import os
import pytest

# Add src to path to import agenticflow
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agenticflow.visualization.mermaid_generator import (
    MermaidGenerator, DiagramType, FlowDirection, NodeShape, EdgeType
)

class TestMermaidSyntax:
    """Test class for Mermaid syntax validation."""

    def test_node_shapes_syntax(self):
        """Test all node shapes for correct Mermaid syntax."""
        generator = MermaidGenerator()
        
        # Test cases based on Mermaid documentation
        test_cases = [
            # (shape, label, expected_pattern)
            (NodeShape.RECTANGLE, "Process", 'TEST["Process"]'),
            (NodeShape.ROUNDED, "Rounded", 'TEST("Rounded")'),
            (NodeShape.CIRCLE, "Circle", 'TEST(("Circle"))'),
            (NodeShape.DIAMOND, "Decision", 'TEST{"Decision"}'),
            (NodeShape.HEXAGON, "Hexagon", 'TEST{{"Hexagon"}}'),  # Double braces
            (NodeShape.PARALLELOGRAM, "Input", 'TEST[/"Input"/]'),
            (NodeShape.TRAPEZOID, "Manual", 'TEST[\\"Manual"\\]'),
            (NodeShape.CYLINDER, "Database", 'TEST[("Database")]'),
        ]
        
        for shape, label, expected_contains in test_cases:
            generator.clear()
            generator.add_node("TEST", label, shape)
            
            diagram = generator.generate()
            
            # Extract the node line
            node_line = None
            for line in diagram.split('\n'):
                if 'TEST' in line and any(char in line for char in ['[', '(', '{']):
                    node_line = line.strip()
                    break
            
            assert node_line is not None, f"Node line not found for {shape.name}"
            
            # Specific syntax validation based on shape
            if shape == NodeShape.HEXAGON:
                assert '{{' in node_line and '}}' in node_line, \
                    f"Hexagon should use double braces: {node_line}"
            elif shape == NodeShape.CIRCLE:
                assert '((' in node_line and '))' in node_line, \
                    f"Circle should use double parentheses: {node_line}"
            elif shape == NodeShape.DIAMOND:
                assert '{' in node_line and '}' in node_line, \
                    f"Diamond should use braces: {node_line}"
            elif shape == NodeShape.RECTANGLE:
                assert '[' in node_line and ']' in node_line, \
                    f"Rectangle should use brackets: {node_line}"

    def test_edge_types_syntax(self):
        """Test all edge types for correct Mermaid syntax."""
        generator = MermaidGenerator()
        generator.add_node("A", "Start")
        generator.add_node("B", "End")
        
        edge_tests = [
            (EdgeType.SOLID, "-->"),
            (EdgeType.DOTTED, "-.->"),
            (EdgeType.THICK, "==>"),
            (EdgeType.INVISIBLE, "~~~"),
        ]
        
        for edge_type, expected_syntax in edge_tests:
            generator.edges.clear()
            generator.add_edge("A", "B", "Test Edge", edge_type)
            
            diagram = generator.generate()
            
            # Find edge line
            edge_line = None
            for line in diagram.split('\n'):
                if 'A ' in line and ' B' in line:
                    edge_line = line.strip()
                    break
            
            assert edge_line is not None, f"Edge line not found for {edge_type.name}"
            assert expected_syntax in edge_line, \
                f"Expected '{expected_syntax}' in edge line: {edge_line}"

    def test_diagram_directions(self):
        """Test all diagram direction options."""
        directions = [
            (FlowDirection.TOP_DOWN, "TD"),
            (FlowDirection.LEFT_RIGHT, "LR"), 
            (FlowDirection.RIGHT_LEFT, "RL"),
            (FlowDirection.BOTTOM_UP, "BU"),
        ]
        
        for direction, expected_code in directions:
            generator = MermaidGenerator()
            generator.set_direction(direction)
            generator.add_node("A", "Node A")
            
            diagram = generator.generate()
            first_line = diagram.split('\n')[0]
            
            expected_header = f"flowchart {expected_code}"
            assert expected_header == first_line, \
                f"Expected '{expected_header}', got '{first_line}'"

    def test_special_characters_escaping(self):
        """Test handling of special characters in labels."""
        generator = MermaidGenerator()
        
        test_cases = [
            ('Simple Label', 'Simple Label'),
            ('With "Quotes"', 'With \\"Quotes\\"'),  # Should escape quotes
            ('With & Ampersand', 'With & Ampersand'),  # Ampersand should be fine
            ('With <Tags>', 'With <Tags>'),  # Angle brackets should be fine
        ]
        
        for input_label, expected_escaped in test_cases:
            generator.clear()
            generator.add_node("A", input_label)
            
            diagram = generator.generate()
            
            # Find node line
            node_line = None
            for line in diagram.split('\n'):
                if 'A[' in line:
                    node_line = line.strip()
                    break
            
            assert node_line is not None, f"Node line not found for label: {input_label}"
            
            if '"' in input_label:
                # Should have escaped quotes
                assert '\\"' in node_line, \
                    f"Quotes should be escaped in: {node_line}"

    def test_subgraph_syntax(self):
        """Test subgraph syntax compliance."""
        generator = MermaidGenerator()
        generator.add_node("A", "Node A")
        generator.add_node("B", "Node B")
        generator.add_subgraph("sub1", "My Subgraph", ["A", "B"])
        
        diagram = generator.generate()
        lines = diagram.split('\n')
        
        # Check for subgraph start
        subgraph_start = None
        subgraph_end = None
        
        for i, line in enumerate(lines):
            if 'subgraph sub1' in line:
                subgraph_start = i
            elif line.strip() == 'end' and subgraph_start is not None:
                subgraph_end = i
                break
        
        assert subgraph_start is not None, "Subgraph start not found"
        assert subgraph_end is not None, "Subgraph end not found"
        assert subgraph_end > subgraph_start, "Subgraph end should come after start"

    def test_hexagon_node_fix(self):
        """Specifically test the hexagon node syntax that was previously broken."""
        generator = MermaidGenerator()
        generator.add_node("hex1", "Hexagon Label", NodeShape.HEXAGON)
        
        diagram = generator.generate()
        
        # Find the hexagon node line
        hex_line = None
        for line in diagram.split('\n'):
            if 'hex1' in line and '{' in line:
                hex_line = line.strip()
                break
        
        assert hex_line is not None, "Hexagon node line not found"
        
        # Should use double braces: {{}}
        assert '{{' in hex_line, f"Hexagon should start with double braces: {hex_line}"
        assert '}}' in hex_line, f"Hexagon should end with double braces: {hex_line}"
        
        # Should not have four braces like {{{{}}}}
        assert '{{{{' not in hex_line, f"Hexagon should not have quadruple braces: {hex_line}"

    def test_complete_workflow_syntax(self):
        """Test a complete workflow with multiple elements."""
        generator = MermaidGenerator()
        generator.set_direction(FlowDirection.TOP_DOWN)
        
        # Add various node shapes
        generator.add_node("start", "Start", NodeShape.CIRCLE)
        generator.add_node("process1", "Process Data", NodeShape.RECTANGLE) 
        generator.add_node("decision", "Valid?", NodeShape.DIAMOND)
        generator.add_node("success", "Success", NodeShape.HEXAGON)
        generator.add_node("error", "Error Handler", NodeShape.RECTANGLE)
        
        # Add different edge types
        generator.add_edge("start", "process1", "Begin", EdgeType.SOLID)
        generator.add_edge("process1", "decision", "Check", EdgeType.SOLID)
        generator.add_edge("decision", "success", "Yes", EdgeType.SOLID)
        generator.add_edge("decision", "error", "No", EdgeType.DOTTED)
        
        # Add styling
        generator.add_css_class("success-style", {"fill": "#e8f5e8", "stroke": "#4caf50"})
        generator.add_style("error", {"fill": "#ffebee", "stroke": "#f44336"})
        
        diagram = generator.generate()
        
        # Validate key components
        assert "flowchart TD" in diagram, "Should have correct flowchart header"
        assert "start((" in diagram, "Circle syntax should be correct"  
        assert "decision{" in diagram, "Diamond syntax should be correct"
        assert "success{{" in diagram, "Hexagon syntax should be correct"
        assert "-->" in diagram, "Solid arrows should be present"
        assert "-.->", "Dotted arrows should be present"
        assert "style error" in diagram, "Node styling should be present"
        assert "classDef success-style" in diagram, "CSS class should be defined"

    def test_mermaid_reserved_words(self):
        """Test handling of Mermaid reserved words like 'end'."""
        generator = MermaidGenerator()
        
        # Test with 'end' which should be avoided or handled
        generator.add_node("endnode", "End Process", NodeShape.RECTANGLE)
        generator.add_node("start", "Start", NodeShape.RECTANGLE)
        generator.add_edge("start", "endnode")
        
        diagram = generator.generate()
        
        # Should not break the diagram
        assert "flowchart" in diagram
        assert "endnode[" in diagram
        
        # If we use 'end' as a label, it should be handled properly
        generator.clear()
        generator.add_node("problematic", "END", NodeShape.RECTANGLE)
        
        diagram = generator.generate()
        assert "problematic[" in diagram


def test_run_comprehensive_validation():
    """Run all tests and provide a summary."""
    print("🧪 Running comprehensive Mermaid syntax validation...")
    
    # This will be run by pytest, but we can also run it standalone
    test_instance = TestMermaidSyntax()
    
    tests = [
        ("Node Shapes", test_instance.test_node_shapes_syntax),
        ("Edge Types", test_instance.test_edge_types_syntax), 
        ("Diagram Directions", test_instance.test_diagram_directions),
        ("Special Characters", test_instance.test_special_characters_escaping),
        ("Subgraph Syntax", test_instance.test_subgraph_syntax),
        ("Hexagon Fix", test_instance.test_hexagon_node_fix),
        ("Complete Workflow", test_instance.test_complete_workflow_syntax),
        ("Reserved Words", test_instance.test_mermaid_reserved_words),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Mermaid syntax tests passed!")
    else:
        print("⚠️  Some syntax issues found - check the implementation")


if __name__ == "__main__":
    test_run_comprehensive_validation()