# Example 05: Local Docs Summary (Self-contained)

This example scans local text files and writes a naive summary with top terms and citations:
- ScanAgent(scanner) finds files under data/ with ignore globs
- SummarizeAgent(summarizer) computes a frequency sketch and writes summary.md with citations
- VisualizationRenderer writes workflow/system diagrams

## Structure
- data/ — inputs (text files to scan)
- artifacts/ — outputs (summary.md, diagrams)
- demo.py — OOP runner with parameters set in the script

## Run
```bash
uv run python examples/05_local_docs/demo.py
```

## Customize
- Add/modify files in `examples/05_local_docs/data/`.
- Edit `ignore`, `max_files`, and `top_k` in the `Config` at the top of `demo.py`.

## Outputs
- summary.md — list of top terms and file citations
- workflow.mmd — Mermaid workflow diagram
- system.mmd — Mermaid system diagram
- system.dot — Graphviz DOT of the system diagram
- system.svg — SVG if Graphviz `dot` is available
