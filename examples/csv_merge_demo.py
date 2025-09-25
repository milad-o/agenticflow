#!/usr/bin/env python3
"""
CSV Merge Demo

Discovers CSV files under examples/data/csv, reads them, and generates a merge plan
report using the hybrid RPAVH system with LLM synthesis enabled when available.

Outputs:
- Report path
- Transcript path (full, human-readable flow trace)
"""
import asyncio
import time
import logging
from pathlib import Path

from agenticflow import (
    Flow, FlowConfig, Planner,
    FileSystemAgent, ReportingAgent,
    get_easy_llm  # Easy LLM setup!
)


async def main() -> int:
    base = Path(__file__).resolve().parent.parent
    workspace = base / "examples"
    artifact_dir = workspace / "artifact"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Keep console quiet; full trace in logs
    try:
        logging.getLogger().setLevel(logging.WARNING)
    except Exception:
        pass

    flow = Flow(
        FlowConfig(
            flow_name="CSVMergeDemo",
            workspace_path=str(workspace),
            max_parallel_tasks=2,
            recursion_limit=10,
        )
    )

    # Tools
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast",
        "write_text_atomic",
        "file_stat",
        "streaming_file_reader",
    ])

    # Super easy LLM setup - auto-detects best available!
    try:
        llm = get_easy_llm("auto", temperature=0.1)
        print(f"🤖 Using LLM: {type(llm).__name__}")
    except Exception as e:
        print(f"❌ LLM setup failed: {e}")
        return 1

    # Filesystem agent configured for CSV discovery
    fs_agent = FileSystemAgent(
        llm=llm,
        name="hybrid_filesystem",
        file_pattern="*.csv",
        search_root="examples/data/csv",
        max_attempts=2,
        use_llm_reflection=False,
    )
    fs_agent.static_resources.update({
        "stream_threshold_kb": 32,
        "chunk_size_kb": 64,
        "max_stream_chunks": 3,
    })

    report_name = "csv_merge_report.md"
    reporter = ReportingAgent(
        llm=llm,
        name="hybrid_reporting",
        report_filename=str(artifact_dir / report_name),
        max_attempts=2,
        use_llm_reflection=False,
    )
    reporter.static_resources["use_llm_for_report"] = True

    # Register
    flow.add_agent("hybrid_filesystem", fs_agent)
    flow.add_agent("hybrid_reporting", reporter)

    # Adopt only necessary tools
    fs_agent.adopt_flow_tools(flow, ["find_files", "read_text_fast", "file_stat", "streaming_file_reader"])
    reporter.adopt_flow_tools(flow, ["write_text_atomic"])

    flow.set_planner(Planner())
    flow.start()

    request = (
        "Find CSV files under examples/data/csv (*.csv), inspect their headers and sample rows, and propose a clear merge plan "
        "(keys, join type, column mappings, data cleaning). Then write a concise, executive-ready report as 'csv_merge_report.md'."
    )

    print("\n===== CSV MERGE DEMO =====")
    print("Workspace:", workspace)
    print("Request:", request)

    start = time.time()
    result = await flow.arun(request)
    elapsed = time.time() - start

    # Summary
    final_response = result.get("final_response", "")
    tasks = result.get("tasks", [])
    task_results = result.get("task_results", {})

    print("\n--- DEMO SUMMARY ---")
    print(f"Completed in {elapsed:.2f}s")
    print(f"Tasks: {len(task_results)}/{len(tasks)} completed")

    candidates = [artifact_dir / report_name]
    report_path = next((p for p in candidates if p.exists()), None)
    if report_path:
        print("Report:", report_path)
        preview_lines = (report_path.read_text(encoding="utf-8", errors="ignore").splitlines())[:40]
        print("\nReport Preview:")
        print("-" * 40)
        for line in preview_lines:
            print(line)
        if len(preview_lines) == 40:
            print("...")
    else:
        print("Report not found (expected:", candidates, ")")

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