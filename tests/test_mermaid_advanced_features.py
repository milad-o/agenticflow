#!/usr/bin/env python3
"""
Test advanced Mermaid features and newer syntax (v11.3.0+).
"""

import sys
import os

# Add src to path to import agenticflow
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agenticflow.visualization.mermaid_generator import (
    MermaidGenerator, DiagramType, FlowDirection, NodeShape, EdgeType
)

def test_cloud_shape_fix():
    """Test and potentially fix cloud shape syntax."""
    print("=== Testing Cloud Shape ===")
    
    generator = MermaidGenerator()
    generator.add_node("cloud1", "Cloud Service", NodeShape.CLOUD)
    
    diagram = generator.generate()
    print("Generated diagram:")
    print(diagram)
    
    # Find cloud node line
    cloud_line = None
    for line in diagram.split('\n'):
        if 'cloud1' in line and ('>' in line or '<' in line):
            cloud_line = line.strip()
            break
    
    print(f"Cloud node line: {cloud_line}")
    
    # According to Mermaid docs, cloud should be cloud1>\"Label\"] but that doesn't look right
    # Let's check what the actual correct syntax should be
    
def test_new_mermaid_shapes():
    """Test some of the new Mermaid v11.3.0+ shapes using the new syntax."""
    print("=== Testing New Mermaid v11.3.0+ Syntax ===")
    
    generator = MermaidGenerator()
    
    # Test new syntax format: A@{ shape: rect }
    # We'll need to add support for this
    print("Current shapes are limited to the legacy syntax")
    print("New syntax like A@{ shape: rect } is not yet supported")
    
def test_problematic_shapes():
    """Test shapes that might have syntax issues."""
    print("=== Testing Potentially Problematic Shapes ===")
    
    generator = MermaidGenerator()
    
    test_shapes = [
        (NodeShape.CLOUD, "Cloud"),
        (NodeShape.TRAPEZOID, "Trapezoid"), 
        (NodeShape.PARALLELOGRAM, "Parallelogram"),
        (NodeShape.CYLINDER, "Database"),
    ]
    
    for shape, label in test_shapes:
        generator.clear()
        generator.add_node("test", label, shape)
        diagram = generator.generate()
        
        print(f"\n{shape.name}:")
        for line in diagram.split('\n'):
            if 'test' in line and any(char in line for char in ['[', '(', '{', '>', '<']):
                print(f"  {line.strip()}")
                
def test_edge_labels_with_special_chars():
    """Test edge labels with special characters."""
    print("=== Testing Edge Labels with Special Characters ===")
    
    generator = MermaidGenerator()
    generator.add_node("A", "Start")
    generator.add_node("B", "End")
    
    test_labels = [
        "Simple",
        "With \"Quotes\"",
        "With & Ampersand", 
        "With | Pipe",
        "With < > Brackets",
    ]
    
    for label in test_labels:
        generator.edges.clear()
        generator.add_edge("A", "B", label)
        
        diagram = generator.generate()
        edge_line = None
        for line in diagram.split('\n'):
            if 'A ' in line and ' B' in line:
                edge_line = line.strip()
                break
                
        print(f"Label: '{label}' -> {edge_line}")

def test_subgraph_with_special_titles():
    """Test subgraphs with special characters in titles."""
    print("=== Testing Subgraph Titles ===")
    
    generator = MermaidGenerator()
    generator.add_node("A", "Node A")
    generator.add_node("B", "Node B")
    
    test_titles = [
        "Simple Title",
        "Title with \"Quotes\"",
        "Title with & Special Chars",
    ]
    
    for title in test_titles:
        generator.subgraphs.clear()
        generator.add_subgraph("sub1", title, ["A", "B"])
        
        diagram = generator.generate()
        
        print(f"\nTitle: '{title}'")
        for line in diagram.split('\n'):
            if 'subgraph sub1' in line:
                print(f"  {line.strip()}")
                break

def identify_syntax_issues():
    """Run comprehensive tests to identify any remaining syntax issues."""
    print("🔍 Identifying Potential Syntax Issues")
    print("=" * 50)
    
    test_cloud_shape_fix()
    test_new_mermaid_shapes()
    test_problematic_shapes()
    test_edge_labels_with_special_chars()
    test_subgraph_with_special_titles()
    
    print("\n" + "=" * 50)
    print("Analysis complete. Check output above for any issues.")

if __name__ == "__main__":
    identify_syntax_issues()