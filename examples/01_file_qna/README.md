# Example 01: LLM File Q&A (with citations)

This example lets you ask a question about a set of local files. It uses an LLM to read relevant files and produce a concise, cited answer.

## Prerequisites
- Set up your LLM provider environment (e.g., GROQ):
  - export GROQ_API_KEY=... (and optionally GROQ_MODEL)

## Structure
- `data/` — small corpus across nature, science, literature, business, law
- `artifacts/` — generated answers and citations (plus diagrams)
- `demo.py` — OOP runner (no CLI required)

## Run (provider-free)
```bash
AGENTICFLOW_LLM_PROVIDER=noop \
uv run python examples/01_file_qna/demo.py
```

## Run (Groq)
```bash
export AGENTICFLOW_LLM_PROVIDER=groq
export GROQ_API_KEY={{GROQ_API_KEY}}
uv run python examples/01_file_qna/demo.py
```
