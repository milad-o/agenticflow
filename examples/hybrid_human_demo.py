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

from agenticflow import (
    Flow, FlowConfig, Planner,
    FileSystemAgent, ReportingAgent,
    get_easy_llm
)


async def main() -> int:
    base = Path(__file__).resolve().parent.parent
    workspace = base / "examples"
    artifact_dir = workspace / "artifact"
    artifact_dir.mkdir(parents=True, exist_ok=True)

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

    # Get LLM instance for agents (auto-detect best available)
    llm = get_easy_llm("auto", temperature=0.1)
    print(f"🤖 Using LLM: {type(llm).__name__}")

    # Ensure demo SSIS directory exists with a couple of sample packages
    ssis_dir = (base / "examples" / "data" / "ssis").resolve()
    try:
        if not ssis_dir.exists():
            ssis_dir.mkdir(parents=True, exist_ok=True)
            # Create minimal .dtsx-like XML stubs
            for i in range(1, 3):
                (ssis_dir / f"Package{i}.dtsx").write_text(
                    f"""<?xml version=\"1.0\"?><DTS:Executable><DTS:Property DTS:Name=\"ObjectName\">Package{i}</DTS:Property><DTS:Executable/></DTS:Executable>""",
                    encoding="utf-8"
                )
            print(f"Generated synthetic SSIS packages under {ssis_dir}")
    except Exception as e:
        print(f"Failed to prepare SSIS demo data: {e}")

    # Create agents using new OOP approach
    fs_agent = FileSystemAgent(
        llm=llm,
        name="hybrid_filesystem",
        file_pattern="*.dtsx",
        search_root="examples/data/ssis",
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
    reporter = ReportingAgent(
        llm=llm,
        name="hybrid_reporting",
        report_filename=str(artifact_dir / report_name),
        max_attempts=2,
        use_llm_reflection=False,
    )
    # Enable LLM report synthesis by default for this demo
    reporter.static_resources["use_llm_for_report"] = True

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
    candidates = [artifact_dir / report_name]
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
