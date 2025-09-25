import asyncio
from pathlib import Path

import pytest

from agenticflow.core.flow import Flow
from agenticflow.core.config import FlowConfig
from agenticflow.planner.planner import Planner
from agenticflow.agents_repo.hybrid_filesystem_agent import create_hybrid_filesystem_agent
from agenticflow.agents_repo.hybrid_reporting_agent import create_hybrid_reporting_agent


@pytest.mark.asyncio
async def test_hybrid_minimal_e2e():
    base = Path.cwd()
    workspace = base / "examples"

    # Configure a clean flow with minimal console noise; transcript goes to file automatically
    flow = Flow(
        FlowConfig(
            flow_name="HybridMinimal",
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
        name="fs",
        file_pattern="*.dtsx",
        search_root="data/ssis",
        max_attempts=2,
        use_llm_reflection=False,
    )
    # Encourage streaming even for small demo files
    fs_agent.static_resources.update({
        "stream_threshold_kb": 1,
        "chunk_size_kb": 64,
        "max_stream_chunks": 2,
    })

    report_name = "hybrid_minimal_report.md"
    reporter = create_hybrid_reporting_agent(
        name="reporter",
        report_filename=report_name,
        max_attempts=2,
        use_llm_reflection=False,
    )

    # Register agents
    flow.add_agent("fs", fs_agent)
    flow.add_agent("reporter", reporter)

    # Adopt only the tools each agent needs
    fs_agent.adopt_flow_tools(
        flow, ["find_files", "read_text_fast", "file_stat", "streaming_file_reader"]
    )
    reporter.adopt_flow_tools(flow, ["write_text_atomic"])

    # Planner for DAG
    flow.set_planner(Planner())

    # Start flow
    flow.start()

    # Execute a concise end-to-end request
    request = (
        "Analyze SSIS packages (*.dtsx) under examples/data/ssis and generate a comprehensive report."
    )
    result = await flow.arun(request)

    # Basic result assertions
    assert result.get("final_response", "") != ""
    assert isinstance(result.get("task_results"), dict)
    assert len(result.get("task_results")) >= 1

    # Verify report file exists (workspace or project root, depending on guard)
    candidates = [workspace / report_name, base / report_name]
    report_path = next((p for p in candidates if p.exists()), None)
    assert report_path is not None, "Report file not found"

    content = report_path.read_text()
    assert "## Executive Summary" in content
    assert ("Data Overview" in content) or ("## Data Overview" in content)

    # Verify transcript exists and indicates reading actions (streaming preferred)
    transcript_path = base / "logs" / f"flow_transcript-{flow.run_id}.log"
    assert transcript_path.exists(), f"Transcript not found at {transcript_path}"
    t = transcript_path.read_text()
    assert ("tool=streaming_file_reader" in t) or ("tool=read_text_fast" in t)
