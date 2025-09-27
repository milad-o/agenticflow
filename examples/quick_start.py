#!/usr/bin/env python3
"""
AgenticFlow Quick Start Example
==============================

Simple example showing how to get started with AgenticFlow
for hierarchical multi-agent coordination.

Usage:
    uv run python examples/quick_start.py
"""

import os
from pathlib import Path
from agenticflow import Flow
from agenticflow.agents import FileSystemWorker, AnalysisWorker, ReportingWorker


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

# Load environment variables
load_env()


def main():
    print("🚀 AgenticFlow Quick Start")
    print("=" * 40)

    # Create hierarchical team
    flow = Flow()
    flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
    flow.add_worker("analysis", AnalysisWorker())
    flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))

    print(f"Team: {flow.list_workers()}")

    # Execute complex task
    task = "Find CSV files, analyze their patterns, and generate a report"
    print(f"\nTask: {task}")

    result = flow.run(task)

    print(f"\n✅ Success: {result['success']}")
    print(f"🔧 Workers used: {result['workers_used']}")

    # Show generated reports
    import glob
    reports = glob.glob("examples/artifact/*.md")
    if reports:
        latest_report = max(reports, key=lambda x: x.split('_')[-1])
        print(f"📄 Latest report: {latest_report}")


if __name__ == "__main__":
    main()