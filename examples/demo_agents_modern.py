#!/usr/bin/env python3
"""
Modern Agents Demo

Demonstrates the new OOP-based agent API with LangChain LLM integration.
Shows how to easily switch between different LLM providers and configure agents.

Key features:
- Clean OOP agent instantiation
- LangChain LLM integration for easy provider switching
- Standardized agent interface
- No factory functions needed
"""
import asyncio
import time
import os
import logging
from pathlib import Path
from langchain_ollama import ChatOllama, OllamaEmbeddings


def _pick_ollama_models():
    import subprocess
    prefer = ("qwen2.5:7b", "granite3.2:8b")
    prefer_embed = ("nomic-embed-text:latest", "nomic-embed-text")
    names = []
    try:
        p = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
        for line in p.stdout.splitlines()[1:]:
            parts = line.split()
            if parts:
                names.append(parts[0])
    except Exception:
        names = []
    chat = next((m for m in prefer if any(n.startswith(m) for n in names)), names[0] if names else None)
    embed = next((m for m in prefer_embed if any(n.startswith(m) for n in names)), None)
    if not chat:
        raise RuntimeError("No Ollama chat model found. Please `ollama pull qwen2.5:7b` or `granite3.2:8b`.")
    return chat, embed

from agenticflow import (
    Flow, FlowConfig,
    FileSystemAgent, ReportingAgent, AnalysisAgent,
    Planner
)


# Explicit Ollama only for this demo


async def main() -> int:
    base = Path(__file__).resolve().parent.parent
    workspace = base / "examples"
    artifact_dir = workspace / "artifact"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.getLogger().setLevel(logging.WARNING)

    # Explicit Ollama setup
    chat_model, embed_model = _pick_ollama_models()
    llm = ChatOllama(model=chat_model, temperature=0.1)
    embeddings = OllamaEmbeddings(model=embed_model) if embed_model else None
    llm_provider = "ollama"

    # Initialize flow
    flow = Flow(
        FlowConfig(
            flow_name="ModernAgentsDemo",
            workspace_path=str(workspace),
            max_parallel_tasks=2,
            recursion_limit=10,
        )
    )

    # Install required tools
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast",
        "write_text_atomic",
        "file_stat",
        "streaming_file_reader",
    ])

    # Create agents using modern OOP approach
    filesystem_agent = FileSystemAgent(
        llm=llm,
        name="filesystem_agent",
        file_pattern="*.dtsx",
        search_root="examples/data/ssis",
        max_attempts=2,
        use_llm_reflection=True,  # Enable smart reflection with LLM
        temperature=0.0  # Deterministic for filesystem operations
    )

    report_name = f"{Path(__file__).stem}_report.md"
    reporting_agent = ReportingAgent(
        llm=llm,
        name="reporting_agent",
        report_filename=str(artifact_dir / report_name),
        report_format="markdown",
        max_attempts=2,
        use_llm_reflection=False,  # Keep report generation fast
        temperature=0.1  # Slight creativity for report writing
    )

    # Configure agents
    filesystem_agent.static_resources.update({
        "stream_threshold_kb": 1,  # Stream files > 1KB for demo
        "chunk_size_kb": 64,
        "max_stream_chunks": 3,
    })

    # Enable intelligent report synthesis
    reporting_agent.static_resources["use_llm_for_report"] = True

    # Register agents with flow
    flow.add_agent("filesystem", filesystem_agent)
    flow.add_agent("reporting", reporting_agent)

    # Adopt tools
    filesystem_agent.adopt_flow_tools(
        flow, ["find_files", "read_text_fast", "file_stat", "streaming_file_reader"]
    )
    reporting_agent.adopt_flow_tools(flow, ["write_text_atomic"])

    # Set planner and start flow
    flow.set_planner(Planner())
    flow.start()

    # Human-style request
    request = (
        "Please discover SSIS packages under examples/data/ssis (*.dtsx), "
        "analyze their structure and content using streaming for larger files, "
        "then generate a comprehensive executive report as 'modern_demo_report.md' "
        "with insights about the data integration patterns found."
    )

    print(f"\n===== MODERN AGENTS DEMO (LLM: {llm_provider.upper()}) =====")
    print("Workspace:", workspace)
    print("Request:", request)
    print("Agents: FileSystemAgent, ReportingAgent")
    print("LLM Integration: LangChain with", type(llm).__name__)

    start = time.time()
    result = await flow.arun(request)
    elapsed = time.time() - start

    # Display results
    final_response = result.get("final_response", "")
    tasks = result.get("tasks", [])
    task_results = result.get("task_results", {})

    print("\n--- DEMO RESULTS ---")
    print(f"Completed in {elapsed:.2f}s")
    print(f"Tasks: {len(task_results)}/{len(tasks)} completed")
    print(f"LLM Provider: {llm_provider}")
    print(f"LLM Model: {getattr(llm, 'model_name', getattr(llm, 'model', 'Unknown'))}")

    # Check for report
    report_path = artifact_dir / report_name
    if report_path.exists():
        print("Report:", report_path)
        preview_lines = report_path.read_text(encoding="utf-8", errors="ignore").splitlines()[:10]
        print("\nReport Preview:")
        print("-" * 50)
        for line in preview_lines:
            print(line)
        if len(preview_lines) >= 10:
            print("...")
    else:
        print("Report not found at:", report_path)

    print(f"\nFinal Response: {(final_response or '')[:150]}...")
    print("===== DEMO COMPLETE =====\n")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        raise SystemExit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(130)