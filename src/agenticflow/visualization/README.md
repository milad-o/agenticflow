# 🗺️ AgenticFlow Visualization

> **Modern Mermaid diagram generation with v11.3.0+ support, frontmatter, and advanced theming**

Generate professional workflow diagrams, agent topologies, and task orchestration visualizations directly from your AgenticFlow components.

## ✨ Features

### 🆕 Modern Mermaid v11.3.0+ Support
- **30+ new node shapes**: `process`, `database`, `cloud`, `manual-file`, etc.
- **Modern syntax**: `A@{ shape: shape-name, label: "Label" }`
- **Backward compatibility**: Legacy syntax still fully supported

### 🎨 Rich Theming & Frontmatter
- **YAML frontmatter** with custom titles and themes
- **Comprehensive theme variables** (colors, backgrounds, borders)
- **Professional styling** for enterprise-grade diagrams

### 🔧 Easy Integration
- **Visualization mixins** - Add `.visualize()` and `.show()` methods to core objects
- **Simple interface** - Generate diagrams in one line of code
- **Export utilities** - Save as SVG, PNG, PDF with multiple backends

## 🚀 Quick Start

### Basic Agent Visualization
```python
from agenticflow import Agent
from agenticflow.config.settings import AgentConfig, LLMProviderConfig, LLMProvider

# Create an agent
config = AgentConfig(
    name="data_analyst",
    instructions="Analyze data and generate insights",
    llm=LLMProviderConfig(provider=LLMProvider.GROQ, model="llama-3.1-8b-instant")
)
agent = Agent(config)

# Visualize it directly
agent.visualize()  # Opens diagram in browser
agent.show()       # Shows in Jupyter notebook
```

### Task Orchestration Visualization
```python
from agenticflow.orchestration.task_orchestrator import TaskOrchestrator

# Create workflow
orchestrator = TaskOrchestrator()
orchestrator.add_function_task("data_collection", "Collect Data", collect_data)
orchestrator.add_function_task("data_analysis", "Analyze Data", analyze_data, dependencies=["data_collection"])
orchestrator.add_function_task("report_generation", "Generate Report", generate_report, dependencies=["data_analysis"])

# Visualize workflow
orchestrator.visualize(title="Data Processing Pipeline")
```

### Modern Mermaid Features
```python
from agenticflow.visualization.mermaid_generator import (
    MermaidGenerator, NodeShape, MermaidTheme, ThemeVariables
)

# Create generator with modern syntax
generator = MermaidGenerator(use_modern_syntax=True)

# Set title and theme
generator.set_title("AI Agent Process")
generator.set_theme(MermaidTheme.BASE, ThemeVariables(primary_color="#2563eb"))

# Add modern node shapes
generator.add_node("start", "Start Process", NodeShape.START)
generator.add_node("llm", "LLM Analysis", NodeShape.MANUAL_OPERATION)
generator.add_node("db", "Database Query", NodeShape.DATABASE)
generator.add_node("cloud", "Cloud Service", NodeShape.CLOUD)
generator.add_node("end", "Complete", NodeShape.TERMINAL)

# Connect with styled edges
generator.add_edge("start", "llm", "Begin")
generator.add_edge("llm", "db", "Query Context")
generator.add_edge("db", "cloud", "Upload Results")
generator.add_edge("cloud", "end", "Finish")

# Generate diagram with frontmatter
diagram = generator.generate()
print(diagram)
```

**Output:**
```mermaid
---
title: AI Agent Process
config:
  theme: base
  themeVariables:
    primaryColor: "#2563eb"
---

flowchart TD

    start@{ shape: start, label: "Start Process" }
    llm@{ shape: manual, label: "LLM Analysis" }
    db@{ shape: database, label: "Database Query" }
    cloud@{ shape: cloud, label: "Cloud Service" }
    end@{ shape: terminal, label: "Complete" }

    start -->|"Begin"| llm
    llm -->|"Query Context"| db
    db -->|"Upload Results"| cloud
    cloud -->|"Finish"| end
```

## 📊 Available Node Shapes

### Legacy Shapes (Traditional Syntax)
- `RECTANGLE` - Standard process boxes
- `CIRCLE` - Start/end points  
- `DIAMOND` - Decision points
- `HEXAGON` - Preparation steps
- `PARALLELOGRAM` - Input/output
- `TRAPEZOID` - Manual operations
- `CYLINDER` - Database storage

### Modern Shapes (v11.3.0+ Syntax)
- `PROCESS` - Standard processing
- `DATABASE` - Data storage
- `CLOUD` - Cloud services
- `MANUAL_FILE` - File operations
- `MANUAL_INPUT` - User input
- `MANUAL_OPERATION` - Manual tasks
- `DOCUMENT` - Document generation
- `EVENT` - Event triggers
- `START` / `STOP` - Process boundaries
- `TERMINAL` - Terminal points
- `SUBPROCESS` - Nested processes
- And 20+ more specialized shapes!

## 🎨 Theming Options

### Available Themes
- `DEFAULT` - Standard Mermaid theme
- `NEUTRAL` - Neutral colors
- `DARK` - Dark mode
- `FOREST` - Green nature theme
- `BASE` - Clean base theme

### Theme Variables
```python
theme_vars = ThemeVariables(
    primary_color="#2563eb",        # Main node color
    primary_text_color="#ffffff",   # Text on primary nodes
    primary_border_color="#1d4ed8", # Primary borders
    line_color="#6b7280",           # Connection lines
    secondary_color="#10b981",      # Secondary elements
    background="#f8f9fa",           # Diagram background
    main_bkg="#ffffff",             # Main background
    cluster_bkg="#e9ecef",          # Subgraph background
    node_border="#dee2e6",          # Node borders
)
```

## 🔧 Export Options

### Supported Formats
- **SVG** - Vector graphics (best quality)
- **PNG** - Raster images (good for presentations)
- **PDF** - Print-ready documents

### Export Utilities
```python
from agenticflow.visualization.export_utils import get_exporter

exporter = get_exporter()

# Export to different formats
diagram_code = generator.generate()
exporter.export_to_svg(diagram_code, "workflow.svg")
exporter.export_to_png(diagram_code, "workflow.png", width=1200, height=800)
exporter.export_to_pdf(diagram_code, "workflow.pdf")
```

## 🎯 Integration Examples

### With MultiAgentSystem
```python
from agenticflow.workflows.multi_agent import MultiAgentSystem
from agenticflow.workflows.topologies import TopologyType

# Create multi-agent system
system = MultiAgentSystem(
    supervisor=supervisor_agent,
    agents=[researcher, writer, reviewer],
    topology=TopologyType.HIERARCHICAL
)

# Visualize the agent topology
system.visualize(title="Content Creation Pipeline")
```

### With Jupyter Notebooks
```python
# In Jupyter, objects auto-display as diagrams
agent  # Shows agent visualization
orchestrator  # Shows workflow diagram
system  # Shows agent topology
```

## 🧪 Testing & Examples

### Run Feature Showcase
```bash
# See all modern features in action
uv run python examples/visualization/test_modern_mermaid_features.py
```

### Validation Tests
```bash
# Ensure syntax compliance
uv run pytest tests/test_mermaid_syntax_validation.py -v
```

## 📈 Advanced Features

### Subgraphs & Clustering
```python
# Group related nodes
generator.add_subgraph("processing", "Data Processing", ["collect", "analyze", "validate"])
generator.add_subgraph("output", "Output Generation", ["format", "export"])
```

### Custom Styling
```python
# Define CSS classes
generator.add_css_class("critical", {"fill": "#fecaca", "stroke": "#ef4444"})
generator.add_css_class("success", {"fill": "#d1fae5", "stroke": "#10b981"})

# Apply to nodes
generator.add_node("error_handler", "Error Handler", css_class="critical")
generator.add_node("success_state", "Success", css_class="success")
```

### Click Actions
```python
# Add interactive elements
generator.add_node("details", "Click for Details", click_action="callback()")
```

## 🔄 Migration Guide

### From Legacy to Modern Syntax
```python
# Old way (still works)
generator = MermaidGenerator(use_modern_syntax=False)
generator.add_node("proc", "Process", NodeShape.RECTANGLE)  # proc["Process"]

# New way (recommended)
generator = MermaidGenerator(use_modern_syntax=True)
generator.add_node("proc", "Process", NodeShape.PROCESS)    # proc@{ shape: process, label: "Process" }
```

### Mixed Compatibility
```python
# You can mix legacy and modern shapes in the same diagram
generator = MermaidGenerator(use_modern_syntax=True)
generator.add_node("legacy", "Legacy Node", NodeShape.RECTANGLE)    # Uses legacy syntax
generator.add_node("modern", "Modern Node", NodeShape.CLOUD)        # Uses modern syntax
```

## 📚 Documentation

- [Mermaid Documentation](https://mermaid.js.org/syntax/flowchart.html)
- [v11.3.0+ New Shapes](https://mermaid.js.org/syntax/flowchart.html#expanded-node-shapes-in-mermaid-flowcharts-v1130)
- [AgenticFlow Main Documentation](../../../docs/)

## 🤝 Contributing

The visualization module is actively developed. Contributions welcome for:
- New export backends
- Additional diagram types (sequence, gantt, etc.)
- Enhanced styling options
- Performance optimizations

---

*Create beautiful, professional diagrams that make your AI workflows shine! ✨*