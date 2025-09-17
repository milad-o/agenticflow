#!/usr/bin/env python3
"""
Showcase modern Mermaid features including v11.3.0+ syntax and frontmatter.
"""

import sys
import os

# Add src to path to import agenticflow
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from agenticflow.visualization.mermaid_generator import (
    MermaidGenerator, DiagramType, FlowDirection, NodeShape, EdgeType,
    MermaidTheme, ThemeVariables, MermaidConfig
)

def test_modern_node_shapes():
    """Test the new v11.3.0+ node shapes with modern syntax."""
    print("=== Testing Modern Node Shapes (v11.3.0+) ===")
    
    generator = MermaidGenerator(use_modern_syntax=True)
    generator.set_title("Modern Node Shapes Demo")
    generator.set_theme(MermaidTheme.BASE, ThemeVariables(primary_color="#00ff00"))
    
    # Add various modern shapes
    generator.add_node("start", "Start Process", NodeShape.START)
    generator.add_node("process", "Main Process", NodeShape.PROCESS)
    generator.add_node("decision", "Decision Point", NodeShape.DECISION)
    generator.add_node("database", "Database Query", NodeShape.DATABASE)
    generator.add_node("manual", "Manual Step", NodeShape.MANUAL_OPERATION)
    generator.add_node("document", "Generate Document", NodeShape.DOCUMENT)
    generator.add_node("cloud", "Cloud Service", NodeShape.CLOUD)
    generator.add_node("terminal", "Terminal Point", NodeShape.TERMINAL)
    generator.add_node("subprocess", "Subprocess", NodeShape.SUBPROCESS)
    generator.add_node("stop", "End Process", NodeShape.STOP)
    
    # Add connections
    generator.add_edge("start", "process", "Begin")
    generator.add_edge("process", "decision", "Evaluate")
    generator.add_edge("decision", "database", "Query Data")
    generator.add_edge("decision", "manual", "Manual Review")
    generator.add_edge("database", "document", "Generate Report")
    generator.add_edge("manual", "cloud", "Upload")
    generator.add_edge("document", "subprocess", "Post Process")
    generator.add_edge("subprocess", "terminal", "Complete")
    generator.add_edge("cloud", "stop", "Finish")
    generator.add_edge("terminal", "stop", "End")
    
    diagram = generator.generate()
    print("Generated diagram:")
    print(diagram)
    print("\n" + "="*80 + "\n")

def test_frontmatter_theming():
    """Test frontmatter with custom theming."""
    print("=== Testing Frontmatter with Custom Theming ===")
    
    generator = MermaidGenerator()
    
    # Set up comprehensive theming
    theme_vars = ThemeVariables(
        primary_color="#ff6b6b",
        primary_text_color="#ffffff", 
        primary_border_color="#c92a2a",
        line_color="#495057",
        secondary_color="#4ecdc4",
        background="#f8f9fa",
        main_bkg="#ffffff",
        cluster_bkg="#e9ecef",
        node_border="#dee2e6"
    )
    
    config = MermaidConfig(
        theme=MermaidTheme.BASE,
        theme_variables=theme_vars,
        flow_chart={"htmlLabels": True, "curve": "basis"}
    )
    
    generator.set_title("Custom Themed Workflow")
    generator.set_config(config)
    
    # Create a simple workflow
    generator.add_node("A", "Input Data", NodeShape.RECTANGLE)
    generator.add_node("B", "Process", NodeShape.PROCESS) 
    generator.add_node("C", "Validate", NodeShape.DIAMOND)
    generator.add_node("D", "Output", NodeShape.DOCUMENT)
    
    generator.add_edge("A", "B")
    generator.add_edge("B", "C")  
    generator.add_edge("C", "D", "Success")
    
    diagram = generator.generate()
    print("Generated diagram with frontmatter:")
    print(diagram)
    print("\n" + "="*80 + "\n")

def test_mixed_syntax_compatibility():
    """Test mixing legacy and modern syntax."""
    print("=== Testing Mixed Syntax Compatibility ===")
    
    generator = MermaidGenerator(use_modern_syntax=True)
    generator.set_title("Mixed Syntax Demo")
    
    # Mix legacy shapes (will use legacy syntax) with modern shapes
    generator.add_node("legacy1", "Legacy Rectangle", NodeShape.RECTANGLE)
    generator.add_node("legacy2", "Legacy Circle", NodeShape.CIRCLE)
    generator.add_node("modern1", "Modern Manual File", NodeShape.MANUAL_FILE)
    generator.add_node("modern2", "Modern Cloud", NodeShape.CLOUD)
    generator.add_node("modern3", "Modern Process", NodeShape.PROCESS)
    
    # Connect them
    generator.add_edge("legacy1", "modern1")
    generator.add_edge("legacy2", "modern2") 
    generator.add_edge("modern1", "modern3")
    generator.add_edge("modern2", "modern3")
    
    diagram = generator.generate()
    print("Mixed syntax diagram:")
    print(diagram)
    print("\n" + "="*80 + "\n")

def test_advanced_workflow_with_styling():
    """Create an advanced workflow with comprehensive styling and modern features."""
    print("=== Testing Advanced Workflow with Full Features ===")
    
    generator = MermaidGenerator(use_modern_syntax=True)
    
    # Set up advanced theming
    generator.set_title("AgenticFlow Process Visualization")
    generator.add_theme_variable("primaryColor", "#2563eb")
    generator.add_theme_variable("primaryTextColor", "#ffffff")
    generator.add_theme_variable("primaryBorderColor", "#1d4ed8") 
    generator.add_theme_variable("lineColor", "#6b7280")
    generator.add_theme_variable("secondaryColor", "#10b981")
    generator.add_theme_variable("tertiaryColor", "#f59e0b")
    generator.set_theme(MermaidTheme.BASE)
    
    # Create a complex workflow representing an AI agent process
    generator.add_subgraph("input", "Input Processing", [])
    generator.add_node("receive", "Receive Request", NodeShape.EVENT)
    generator.add_node("parse", "Parse Input", NodeShape.PROCESS)
    generator.add_node("validate", "Validate Request", NodeShape.DECISION)
    
    generator.add_subgraph("processing", "AI Processing", [])
    generator.add_node("llm", "LLM Analysis", NodeShape.MANUAL_OPERATION)
    generator.add_node("memory", "Memory Lookup", NodeShape.DATABASE)
    generator.add_node("tools", "Tool Execution", NodeShape.SUBPROCESS)
    
    generator.add_subgraph("output", "Output Generation", [])
    generator.add_node("generate", "Generate Response", NodeShape.PROCESS)
    generator.add_node("format", "Format Output", NodeShape.DOCUMENT)
    generator.add_node("deliver", "Deliver Response", NodeShape.TERMINAL)
    
    # Connect the workflow
    generator.add_edge("receive", "parse", "Raw Input", EdgeType.SOLID)
    generator.add_edge("parse", "validate", "Parsed Data", EdgeType.SOLID)
    generator.add_edge("validate", "llm", "Valid", EdgeType.SOLID)
    generator.add_edge("validate", "receive", "Invalid", EdgeType.DOTTED)
    generator.add_edge("llm", "memory", "Context Query", EdgeType.SOLID)
    generator.add_edge("memory", "tools", "Retrieved Context", EdgeType.SOLID)
    generator.add_edge("tools", "generate", "Tool Results", EdgeType.SOLID)
    generator.add_edge("generate", "format", "Raw Response", EdgeType.SOLID)
    generator.add_edge("format", "deliver", "Formatted Output", EdgeType.THICK)
    
    # Add custom styling
    generator.add_css_class("highlight", {"fill": "#fef3c7", "stroke": "#f59e0b", "stroke-width": "3px"})
    generator.add_css_class("critical", {"fill": "#fecaca", "stroke": "#ef4444", "stroke-width": "2px"})
    
    # Apply styles to specific nodes
    generator.add_style("llm", {"fill": "#dbeafe", "stroke": "#2563eb"})
    generator.add_style("memory", {"fill": "#d1fae5", "stroke": "#10b981"})
    
    diagram = generator.generate()
    print("Advanced workflow diagram:")
    print(diagram)
    print("\n" + "="*80 + "\n")

def test_legacy_vs_modern_comparison():
    """Compare legacy vs modern syntax output."""
    print("=== Legacy vs Modern Syntax Comparison ===")
    
    # Legacy syntax
    print("--- Legacy Syntax ---")
    legacy_gen = MermaidGenerator(use_modern_syntax=False)
    legacy_gen.add_node("A", "Process", NodeShape.PROCESS)
    legacy_gen.add_node("B", "Database", NodeShape.DATABASE)
    legacy_gen.add_node("C", "Decision", NodeShape.DECISION)
    legacy_gen.add_edge("A", "B")
    legacy_gen.add_edge("B", "C")
    
    legacy_diagram = legacy_gen.generate()
    print(legacy_diagram)
    
    print("\n--- Modern Syntax ---")
    modern_gen = MermaidGenerator(use_modern_syntax=True)
    modern_gen.add_node("A", "Process", NodeShape.PROCESS)
    modern_gen.add_node("B", "Database", NodeShape.DATABASE) 
    modern_gen.add_node("C", "Decision", NodeShape.DECISION)
    modern_gen.add_edge("A", "B")
    modern_gen.add_edge("B", "C")
    
    modern_diagram = modern_gen.generate()
    print(modern_diagram)
    print("\n" + "="*80 + "\n")

def main():
    """Run all modern Mermaid feature tests."""
    print("🚀 AgenticFlow Modern Mermaid Features Showcase")
    print("=" * 80)
    
    test_modern_node_shapes()
    test_frontmatter_theming()
    test_mixed_syntax_compatibility()
    test_advanced_workflow_with_styling()
    test_legacy_vs_modern_comparison()
    
    print("🎉 All modern Mermaid features demonstrated!")
    print("\nThese diagrams now support:")
    print("• Modern v11.3.0+ node shapes (30+ new shapes)")
    print("• Frontmatter with titles and theming")
    print("• Custom theme variables and colors")
    print("• Mixed legacy/modern syntax compatibility")
    print("• Advanced styling and configuration")

if __name__ == "__main__":
    main()
