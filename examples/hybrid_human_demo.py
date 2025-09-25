#!/usr/bin/env python3
"""
Hybrid RPAVH Human Demo

A realistic, minimal-noise demo of the Hybrid RPAVH system responding to a typical
human request: discover SSIS packages, read them (stream large files), and generate
an executive-ready markdown report.

Outputs:
- Report path
- Transcript path (full, human-readable flow trace)
"""
import asyncio
import time
import os
import logging
from pathlib import Path

from agenticflow.core.flow import Flow
from agenticflow.core.config import FlowConfig
from agenticflow.planner.planner import Planner
from agenticflow.agents_repo.hybrid_filesystem_agent import create_hybrid_filesystem_agent
from agenticflow.agents_repo.hybrid_reporting_agent import create_hybrid_reporting_agent


async def main() -> int:
    base = Path(__file__).resolve().parent.parent
    workspace = base / "examples"

    # Configure a clean flow (console keeps minimal noise; transcript written to /logs)
    # Reduce console log noise further by default; transcript still captures full detail
    try:
        logging.getLogger().setLevel(logging.WARNING)
    except Exception:
        pass
    # Prefer Groq as provider if not explicitly set (LLM calls are optional and fail-soft)
    os.environ.setdefault("AGENTICFLOW_LLM_PROVIDER", "groq")

    flow = Flow(
        FlowConfig(
            flow_name="HybridHumanDemo",
            workspace_path=str(workspace),
            max_parallel_tasks=2,
            recursion_limit=10,
        )
    )

    # Install essential tools (includes streaming for large-file reads)
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast",
        "write_text_atomic",
        "file_stat",
        "streaming_file_reader",
    ])

    # Create agents
    fs_agent = create_hybrid_filesystem_agent(
        name="hybrid_filesystem",
        file_pattern="*.dtsx",
        search_root="data/ssis",
        max_attempts=2,
        use_llm_reflection=False,
    )
    # Encourage streaming to demonstrate chunked reads (even for small demo files)
    fs_agent.static_resources.update({
        "stream_threshold_kb": 1,   # stream when file > 1KB
        "chunk_size_kb": 64,
        "max_stream_chunks": 3,
    })

    report_name = "hybrid_demo_report.md"
    reporter = create_hybrid_reporting_agent(
        name="hybrid_reporting",
        report_filename=report_name,
        max_attempts=2,
        use_llm_reflection=False,
    )
    # Enable LLM report synthesis by default for this demo (fails soft to heuristic if provider/key not set)
    try:
        reporter.static_resources["use_llm_for_report"] = True
    except Exception:
        pass

    # Register agents with the flow
    flow.add_agent("hybrid_filesystem", fs_agent)
    flow.add_agent("hybrid_reporting", reporter)

    # Adopt only the tools each agent needs
    fs_agent.adopt_flow_tools(
        flow, ["find_files", "read_text_fast", "file_stat", "streaming_file_reader"]
    )
    reporter.adopt_flow_tools(flow, ["write_text_atomic"])

    # Planner for DAG
    flow.set_planner(Planner())

    # Start flow
    flow.start()

    # Human-style request
    request = (
        "Please scan the SSIS packages under examples/data/ssis (*.dtsx), read their contents "
        "(use chunked streaming for larger files), and produce a concise executive-ready report "
        "with Executive Summary, Data Overview, and Key Findings. Save the report as 'hybrid_demo_report.md'."
    )

    print("\n===== HYBRID HUMAN DEMO =====")
    print("Workspace:", workspace)
    print("Request:", request)

    start = time.time()
    result = await flow.arun(request)
    elapsed = time.time() - start

    # Summarize outcome
    final_response = result.get("final_response", "")
    tasks = result.get("tasks", [])
    task_results = result.get("task_results", {})

    print("\n--- DEMO SUMMARY ---")
    print(f"Completed in {elapsed:.2f}s")
    print(f"Tasks: {len(task_results)}/{len(tasks)} completed")

    # Resolve report path
    candidates = [workspace / report_name, base / report_name]
    report_path = next((p for p in candidates if p.exists()), None)
    if report_path:
        print("Report:", report_path)
        preview_lines = (report_path.read_text(encoding="utf-8", errors="ignore").splitlines())[:12]
        print("\nReport Preview:")
        print("-" * 40)
        for line in preview_lines:
            print(line)
        if len(preview_lines) == 12:
            print("...")
    else:
        print("Report not found (expected:", candidates, ")")

    # Transcript path (minimal console logs; full transcript written to file)
    transcript_path = base / "logs" / f"flow_transcript-{flow.run_id}.log"
    if transcript_path.exists():
        print("\nTranscript:", transcript_path)
    else:
        print("\nTranscript not found at:", transcript_path)

    print("\nFinal Response (preview):", (final_response or "").split("\n")[0][:160])
    print("===== DEMO COMPLETE =====\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(130)
