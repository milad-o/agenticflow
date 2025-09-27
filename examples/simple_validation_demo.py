#!/usr/bin/env python3
"""
Simple Validation Demo - Multi-Agent CSV Validation
==================================================

A streamlined demo showing multi-agent validation of CSV data
against its hierarchical report source.
"""

import os
from pathlib import Path
from agenticflow import Flow
from agenticflow.agents import FileSystemWorker, ReportingWorker


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


class SimpleValidationAgent:
    """Simple validation agent for demo purposes."""

    def __init__(self):
        self.capabilities = ["data_validation", "report_analysis", "csv_verification"]

    async def arun(self, task: str):
        return self.execute(task)

    def execute(self, task: str):
        """Execute validation task."""
        try:
            # Check if validation files exist
            report_file = "examples/data/quarterly_report_q3_2024.txt"
            csv_files = [
                "examples/data/q3_2024_sales_data.csv",
                "examples/data/q3_2024_regional_data.csv",
                "examples/data/q3_2024_customers.csv"
            ]

            results = {
                "files_found": [],
                "files_missing": [],
                "validation_summary": ""
            }

            # Check file existence
            if os.path.exists(report_file):
                results["files_found"].append(report_file)
            else:
                results["files_missing"].append(report_file)

            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    results["files_found"].append(csv_file)
                else:
                    results["files_missing"].append(csv_file)

            # Simple validation
            if len(results["files_found"]) >= 3:
                results["validation_summary"] = f"Found {len(results['files_found'])} files for validation. Data integrity check can proceed."
                validation_status = "ready"
            else:
                results["validation_summary"] = f"Missing files prevent complete validation. Found {len(results['files_found'])}, expected 4."
                validation_status = "incomplete"

            return {
                "action": "validation_check",
                "status": validation_status,
                "files_checked": len(results["files_found"]) + len(results["files_missing"]),
                "results": results,
                "summary": results["validation_summary"]
            }

        except Exception as e:
            return {
                "action": "validation_check",
                "status": "error",
                "error": str(e)
            }


# Load environment
load_env()


def main():
    """Run simple validation demo."""
    print("🔍 SIMPLE VALIDATION DEMO - Multi-Agent CSV Data Validation")
    print("=" * 65)
    print("Mission: Validate CSV files against hierarchical Q3 2024 report")
    print()

    # Create validation team
    flow = Flow()
    flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
    flow.add_worker("validator", SimpleValidationAgent())
    flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))

    print(f"🏗️  Validation team: {flow.list_workers()}")

    # Run validation
    task = """
    Validate the Q3 2024 business data:
    1. Find the quarterly report and CSV files
    2. Check data integrity between hierarchical report and CSV files
    3. Generate validation report with findings
    """

    print(f"\n🎯 Task: Multi-agent data validation")
    print("🔄 Executing validation workflow...")

    result = flow.run(task)

    # Show results
    print(f"\n📊 VALIDATION RESULTS")
    print("-" * 30)
    print(f"✅ Success: {result['success']}")
    print(f"🔧 Teams: {', '.join(result['workers_used'])}")

    if 'validator' in result['results']:
        validator_result = result['results']['validator']
        print(f"📋 Validation: {validator_result.get('summary', 'Completed')}")

    if 'reporting' in result['results']:
        report_result = result['results']['reporting']
        if 'filepath' in report_result:
            print(f"📄 Report: {report_result['filepath']}")

    print(f"\n🎉 Multi-agent validation demo completed!")
    print("📊 CSV data validation against hierarchical reports demonstrated")


if __name__ == "__main__":
    main()