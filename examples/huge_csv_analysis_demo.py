#!/usr/bin/env python3
"""
Huge CSV Analysis Demo

Goal: Compute average size per category from examples/data/huge/products-1000000.csv
using a three-agent workflow:
- Filesystem agent (validate path, optional streaming read preview)
- Analysis agent (chunked CSV aggregation)
- Reporting agent (write an executive report with a summary table)
"""
import asyncio
import time
import os
import logging
from pathlib import Path

from agenticflow import (
    Flow, FlowConfig, Planner,
    FileSystemAgent, AnalysisAgent, ReportingAgent,
    get_easy_llm
)


async def main() -> int:
    base = Path(__file__).resolve().parent.parent
    workspace = base / "examples"

    # Quiet console; full transcript goes to logs/
    try:
        logging.getLogger().setLevel(logging.WARNING)
    except Exception:
        pass
    os.environ.setdefault("AGENTICFLOW_LLM_PROVIDER", "groq")

    flow = Flow(
        FlowConfig(
            flow_name="HugeCSVAnalysis",
            workspace_path=str(workspace),
            max_parallel_tasks=3,
            recursion_limit=10,
        )
    )

    # Install tools: filesystem, streaming, csv analysis, reporting
    flow.install_tools_from_repo([
        "find_files",
        "file_stat",
        "streaming_file_reader",
        "read_text_fast",
        "pandas_chunk_aggregate",
        "write_text_atomic",
    ])

    # Get LLM instance for agents (auto-detect best available)
    llm = get_easy_llm("auto", temperature=0.1)
    print(f"🤖 Using LLM: {type(llm).__name__}")

    # Agents
    csv_path = "examples/data/huge/products-1000000.csv"

    # Ensure dataset exists; generate a small synthetic CSV if missing
    abs_csv = (base / csv_path).resolve()
    if not abs_csv.parent.exists():
        abs_csv.parent.mkdir(parents=True, exist_ok=True)
    if not abs_csv.exists():
        try:
            import random
            import csv as _csv
            cats = ["A", "B", "C", "D", "E"]
            with open(abs_csv, "w", newline="", encoding="utf-8") as f:
                w = _csv.writer(f)
                w.writerow(["category", "size"])  # minimal columns needed
                for i in range(10000):  # ~10k rows for quick demo
                    w.writerow([random.choice(cats), random.randint(1, 1000)])
            print(f"Generated synthetic dataset at {abs_csv}")
        except Exception as e:
            print(f"Failed to generate synthetic dataset: {e}")

    fs = FileSystemAgent(
        llm=llm,
        name="hybrid_filesystem",
        file_pattern="*.csv",
        search_root="data/huge",
        max_attempts=2,
        use_llm_reflection=False,
    )
    fs.static_resources.update({
        "stream_threshold_kb": 1024,  # 1MB threshold for streaming
        "chunk_size_kb": 512,
        "max_stream_chunks": 2,  # just preview a couple of chunks
        "csv_path": csv_path,
    })
    analysis = AnalysisAgent(
        llm=llm,
        name="hybrid_analysis",
        csv_path=csv_path,
        group_by="category",
        value_column="size",
    )

    report_name = "huge_csv_analysis_report.md"
    reporter = ReportingAgent(
        llm=llm,
        name="hybrid_reporting",
        report_filename=report_name,
        max_attempts=2,
        use_llm_reflection=False,
    )
    # Always prefer intelligent (LLM) reporting
    reporter.static_resources["use_llm_for_report"] = True

    # Register agents with flow
    flow.add_agent("hybrid_filesystem", fs)
    flow.add_agent("hybrid_analysis", analysis)
    flow.add_agent("hybrid_reporting", reporter)

    # Adopt tools
    fs.adopt_flow_tools(flow, ["find_files", "file_stat", "streaming_file_reader", "read_text_fast"])
    analysis.adopt_flow_tools(flow, ["pandas_chunk_aggregate"])
    reporter.adopt_flow_tools(flow, ["write_text_atomic"])

    # Planner & start
    flow.set_planner(Planner())
    flow.start()

    request = (
        "Validate the large CSV exists and is accessible, then compute the average size per category from "
        f"{csv_path}. Use chunked processing suitable for large files. Finally, write an executive-ready report "
        "with a small summary table of the top categories by count."
    )

    print("\n===== HUGE CSV ANALYSIS DEMO =====")
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

    candidates = [workspace / report_name, base / report_name]
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