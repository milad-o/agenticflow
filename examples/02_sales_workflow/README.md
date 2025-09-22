# Example 02: Sales Workflow (Self-contained)

This example runs a two-agent workflow over a CSV: analyze totals, then generate a markdown report. It is self-contained with a single entrypoint and clear data/artifacts separation.

## Structure
- `data/` — inputs (e.g., `sales.csv`)
- `artifacts/` — outputs (analysis.json, report.md, diagrams)
- `demo.py` — OOP runner (no CLI required)

## Run
```bash
uv run python examples/02_sales_workflow/demo.py
```

Outputs:
- Workflow Mermaid: artifacts/workflow.mmd
- System Mermaid: artifacts/system.mmd
- System DOT: artifacts/system.dot
- If Graphviz is installed, also writes artifacts/system.svg
