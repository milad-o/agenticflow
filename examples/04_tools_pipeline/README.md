# Example 04: Tools Pipeline (Self-contained)

This example runs a simple pipeline using built-in utility agents and a ToolAgent:
- ToolAgent(reader) with FSReadTool reads a local file from data/
- StatsAgent(processor) computes basic stats and writes stats.json
- ReportAgent(writer) renders report.md from stats.json
- VisualizationRenderer writes workflow/system diagrams

## Structure
- data/ — inputs (e.g., `input.txt`)
- artifacts/ — outputs (stats.json, report.md, diagrams)
- demo.py — OOP runner with parameters set in the script

## Run
```bash
uv run python examples/04_tools_pipeline/demo.py
```

## Customize
- Edit `examples/04_tools_pipeline/data/input.txt` to change the input.
- Or edit `file_path` in the `Config` at the top of `demo.py`.

## Outputs
- workflow.mmd — Mermaid workflow diagram
- system.mmd — Mermaid system diagram (agents, tools, task types)
- system.dot — Graphviz DOT of the system diagram
- system.svg — SVG system diagram if Graphviz `dot` is available
