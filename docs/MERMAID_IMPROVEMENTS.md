# Mermaid Syntax Improvements and Modern Features

## Overview

The AgenticFlow visualization module has been significantly enhanced to support the latest Mermaid features, including v11.3.0+ syntax, frontmatter configuration, and comprehensive theming options.

## Key Improvements

### 1. Modern Mermaid v11.3.0+ Syntax Support

**New Node Shape Syntax**: `A@{ shape: shape-name, label: "Label" }`

- Added 30+ new node shapes from Mermaid v11.3.0+
- Support for both legacy and modern syntax
- Automatic fallback to legacy syntax when needed

**New Shapes Available**:
```python
NodeShape.BANG, NodeShape.CARD, NodeShape.CLOUD, NodeShape.COLLATE,
NodeShape.COM_LINK, NodeShape.COMMENT, NodeShape.DATABASE, NodeShape.DECISION,
NodeShape.DELAY, NodeShape.DISPLAY, NodeShape.DOCUMENT, NodeShape.EVENT,
NodeShape.EXTRACT, NodeShape.FORK, NodeShape.JUNCTION, NodeShape.MANUAL_FILE,
NodeShape.MANUAL_INPUT, NodeShape.MANUAL_OPERATION, NodeShape.MULTI_DOCUMENT,
NodeShape.MULTI_PROCESS, NodeShape.PAPER_TAPE, NodeShape.PREPARE, NodeShape.PRIORITY,
NodeShape.PROCESS, NodeShape.START, NodeShape.STOP, NodeShape.STORED_DATA,
NodeShape.SUBPROCESS, NodeShape.SUMMARY, NodeShape.TERMINAL, NodeShape.TEXT_BLOCK
```

### 2. Frontmatter Support

**YAML Frontmatter** for diagram configuration:
```yaml
---
title: My Diagram Title
config:
  theme: base
  themeVariables:
    primaryColor: "#ff6b6b"
    primaryTextColor: "#ffffff"
---
```

**Features**:
- Custom titles
- Theme selection (default, neutral, dark, forest, base)
- Comprehensive theme variables
- Flowchart-specific configuration
- Sequence diagram settings
- Gantt chart options

### 3. Enhanced Theming System

**Theme Variables Available**:
- `primaryColor`, `primaryTextColor`, `primaryBorderColor`
- `lineColor`, `secondaryColor`, `tertiaryColor`
- `background`, `mainBkg`, `secondBkg`
- `nodeBorder`, `clusterBkg`, `clusterBorder`
- `defaultLinkColor`, `titleColor`, `edgeLabelBackground`

**Usage Examples**:
```python
# Set theme with variables
theme_vars = ThemeVariables(
    primary_color="#2563eb",
    primary_text_color="#ffffff",
    background="#f8f9fa"
)
generator.set_theme(MermaidTheme.BASE, theme_vars)

# Add individual theme variables
generator.add_theme_variable("primaryColor", "#ff6b6b")
```

### 4. Syntax Compliance Fixes

**Issues Fixed**:
- ✅ Hexagon node syntax: `A{{\"Label\"}}` (double braces)
- ✅ Subgraph title escaping for special characters
- ✅ Edge label formatting with special characters
- ✅ Proper quote escaping throughout

**Validation**:
- Comprehensive test suite with 8 test categories
- Validates all node shapes, edge types, directions
- Tests special character handling
- Verifies subgraph and styling syntax

## Usage Examples

### Basic Modern Syntax
```python
from agenticflow.visualization.mermaid_generator import (
    MermaidGenerator, NodeShape, MermaidTheme
)

generator = MermaidGenerator(use_modern_syntax=True)
generator.set_title("Modern Workflow")
generator.set_theme(MermaidTheme.BASE)

# Modern node shapes
generator.add_node("start", "Start Process", NodeShape.START)
generator.add_node("process", "Main Task", NodeShape.PROCESS) 
generator.add_node("db", "Database", NodeShape.DATABASE)
generator.add_node("end", "Complete", NodeShape.TERMINAL)

# Connect with different edge types
generator.add_edge("start", "process", "Begin")
generator.add_edge("process", "db", "Query")
generator.add_edge("db", "end", "Finish")

print(generator.generate())
```

### Advanced Theming
```python
# Custom theme configuration
theme_vars = ThemeVariables(
    primary_color="#2563eb",
    primary_text_color="#ffffff",
    line_color="#6b7280",
    secondary_color="#10b981"
)

config = MermaidConfig(
    theme=MermaidTheme.BASE,
    theme_variables=theme_vars,
    flow_chart={"htmlLabels": True, "curve": "basis"}
)

generator.set_config(config)
generator.set_title("Custom Themed Diagram")
```

### Mixed Syntax Compatibility
```python
# Automatically handles mixing legacy and modern shapes
generator = MermaidGenerator(use_modern_syntax=True)

# Legacy shapes use traditional syntax
generator.add_node("rect", "Rectangle", NodeShape.RECTANGLE)  # A["Rectangle"]
generator.add_node("circle", "Circle", NodeShape.CIRCLE)     # B(("Circle"))

# Modern shapes use new syntax  
generator.add_node("cloud", "Cloud", NodeShape.CLOUD)       # C@{ shape: cloud, label: "Cloud" }
generator.add_node("manual", "Manual", NodeShape.MANUAL_FILE) # D@{ shape: manual-file, label: "Manual" }
```

## Testing

### Validation Tests
Run comprehensive syntax validation:
```bash
uv run python tests/test_mermaid_syntax_validation.py
uv run pytest tests/test_mermaid_syntax_validation.py -v
```

### Feature Showcase
See all modern features in action:
```bash
uv run python examples/visualization/test_modern_mermaid_features.py
```

## Backward Compatibility

- **Legacy syntax fully supported**: Set `use_modern_syntax=False` 
- **Automatic fallback**: Modern generator gracefully handles legacy shapes
- **No breaking changes**: Existing code continues to work unchanged
- **Gradual migration**: Can mix legacy and modern syntax in same diagram

## Benefits

1. **Future-proof**: Supports latest Mermaid v11.3.0+ features
2. **Professional styling**: Rich theming and customization options
3. **Better semantics**: Shape names match their intended use cases
4. **Enhanced readability**: Frontmatter makes diagrams self-documenting
5. **Flexibility**: Choose between legacy and modern syntax as needed

## References

- [Official Mermaid Flowchart Documentation](https://mermaid.js.org/syntax/flowchart.html)
- [Mermaid v11.3.0+ New Shapes](https://mermaid.js.org/syntax/flowchart.html#expanded-node-shapes-in-mermaid-flowcharts-v1130)
- [Mermaid Frontmatter Configuration](https://mermaid.js.org/config/configuration.html)

---

*These improvements bring AgenticFlow's Mermaid support up to the latest standards while maintaining full backward compatibility.*