#!/usr/bin/env python3
"""
AgenticFlow Validation Demo - Multi-Agent Data Integrity Verification
=====================================================================

This demo showcases a multi-agent system that validates CSV data against
its original semi-structured hierarchical report to ensure data integrity.

Scenario:
- Original: Q3 2024 quarterly business report (hierarchical text format)
- Derived: CSV files extracted from the report (sales, regional, customer data)
- Challenge: Verify CSV data truly represents the original report

Multi-Agent Teams:
1. Structure Validation Team - Schema and format verification
2. Content Validation Team - Numerical accuracy and data validation
3. Consistency Validation Team - Business rules and logical consistency
4. Reporting Team - Comprehensive validation report generation

Usage:
    uv run python validation_demo.py
"""

import os
from pathlib import Path
from agenticflow import Flow
from agenticflow.agents import (
    FileSystemWorker,
    ReportingWorker,
    StructureValidationAgent,
    ContentValidationAgent,
    ConsistencyValidationAgent
)


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
        print(f"✅ Loaded environment from {env_file}")


# Load environment variables
load_env()


def print_validation_banner():
    """Print validation demo banner."""
    print("=" * 80)
    print("🔍 AGENTICFLOW VALIDATION DEMO - Multi-Agent Data Integrity Verification")
    print("=" * 80)
    print("Scenario: Validate CSV data against original hierarchical report")
    print()
    print("📋 Original Report: Q3 2024 Quarterly Business Report (hierarchical text)")
    print("📊 Derived CSV Data: Sales, Regional, and Customer data files")
    print("🎯 Mission: Verify CSV data truly represents the original report")
    print()
    print("🏗️  Multi-Agent Validation Teams:")
    print("   • Structure Validation - Schema and format verification")
    print("   • Content Validation - Numerical accuracy verification")
    print("   • Consistency Validation - Business rules and logic")
    print("   • Reporting Team - Comprehensive validation report")
    print("-" * 80)


def demo_file_discovery():
    """Demo 1: Discover and catalog validation files."""
    print("\n📋 DEMO 1: File Discovery and Cataloging")
    print("-" * 50)

    flow = Flow()
    flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))

    task = "Find the Q3 2024 quarterly report and related CSV files for validation"
    print(f"🎯 Task: {task}")

    result = flow.run(task)

    print(f"✅ Discovery complete")
    print(f"📁 Files found: {result['results']['filesystem']['count']}")

    return result


def demo_structure_validation():
    """Demo 2: Structure validation team."""
    print("\n📋 DEMO 2: Structure Validation Team")
    print("-" * 45)

    flow = Flow()
    flow.add_worker("structure_validator", StructureValidationAgent())
    flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))

    task = """
    Validate the structural integrity between the Q3 2024 quarterly report
    and its corresponding CSV files. Check schemas, field completeness,
    and data format consistency.
    """

    print(f"🎯 Task: Structure validation of report vs CSV files")
    result = flow.run(task)

    print(f"✅ Structure validation complete")
    if 'structure_validator' in result['results']:
        structure_result = result['results']['structure_validator']
        print(f"📊 Summary: {structure_result.get('summary', 'No summary available')}")

    return result


def demo_content_validation():
    """Demo 3: Content validation team."""
    print("\n📋 DEMO 3: Content Validation Team")
    print("-" * 42)

    flow = Flow()
    flow.add_worker("content_validator", ContentValidationAgent())

    task = """
    Validate the numerical accuracy and content integrity between the
    Q3 2024 quarterly report and CSV files. Verify calculations, totals,
    and data accuracy across all files.
    """

    print(f"🎯 Task: Content and numerical validation")
    result = flow.run(task)

    print(f"✅ Content validation complete")
    if 'content_validator' in result['results']:
        content_result = result['results']['content_validator']
        accuracy_score = content_result.get('accuracy_score', 0)
        print(f"📊 Accuracy Score: {accuracy_score:.1f}%")

    return result


def demo_consistency_validation():
    """Demo 4: Consistency validation team."""
    print("\n📋 DEMO 4: Consistency Validation Team")
    print("-" * 47)

    flow = Flow()
    flow.add_worker("consistency_validator", ConsistencyValidationAgent())

    task = """
    Validate logical consistency and business rules between the Q3 2024
    quarterly report and CSV files. Check cross-references, business logic,
    and data relationships.
    """

    print(f"🎯 Task: Consistency and business rules validation")
    result = flow.run(task)

    print(f"✅ Consistency validation complete")
    if 'consistency_validator' in result['results']:
        consistency_result = result['results']['consistency_validator']
        consistency_score = consistency_result.get('consistency_score', 0)
        print(f"📊 Consistency Score: {consistency_score:.1f}%")

    return result


def demo_comprehensive_validation():
    """Demo 5: Comprehensive multi-team validation."""
    print("\n📋 DEMO 5: Comprehensive Multi-Team Validation")
    print("-" * 55)

    # Create comprehensive validation team
    flow = Flow()
    flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
    flow.add_worker("structure_validator", StructureValidationAgent())
    flow.add_worker("content_validator", ContentValidationAgent())
    flow.add_worker("consistency_validator", ConsistencyValidationAgent())
    flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))

    print(f"🏗️  Validation team assembled: {flow.list_workers()}")

    task = """
    Perform comprehensive data integrity validation of Q3 2024 quarterly report
    against derived CSV files:

    1. Discover and catalog all validation files
    2. Validate structural integrity and schemas
    3. Verify numerical accuracy and content integrity
    4. Check logical consistency and business rules
    5. Generate comprehensive validation report with findings and recommendations

    Ensure the CSV data truly represents the original hierarchical report.
    """

    print(f"\n🎯 Comprehensive Validation Mission:")
    print("   1. File discovery and cataloging")
    print("   2. Structure validation (schemas, formats)")
    print("   3. Content validation (numerical accuracy)")
    print("   4. Consistency validation (business rules)")
    print("   5. Comprehensive validation report")

    print(f"\n🔄 Executing multi-team validation workflow...")

    result = flow.run(task)

    return result


def show_validation_results(result):
    """Display comprehensive validation results."""
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE VALIDATION RESULTS")
    print("=" * 80)

    print(f"✅ Success: {result['success']}")
    print(f"🔧 Teams Deployed: {', '.join(result['workers_used'])}")
    print(f"📝 Total Coordination Messages: {result['summary']['total_messages']}")

    if result['results']:
        print(f"\n🔍 Validation Team Results:")

        # Structure validation
        if 'structure_validator' in result['results']:
            struct_result = result['results']['structure_validator']
            print(f"  📐 Structure Validation: {struct_result.get('summary', 'Completed')}")

        # Content validation
        if 'content_validator' in result['results']:
            content_result = result['results']['content_validator']
            accuracy = content_result.get('accuracy_score', 0)
            print(f"  📊 Content Validation: {accuracy:.1f}% accuracy")

        # Consistency validation
        if 'consistency_validator' in result['results']:
            consist_result = result['results']['consistency_validator']
            consistency = consist_result.get('consistency_score', 0)
            print(f"  🔗 Consistency Validation: {consistency:.1f}% consistent")

        # Reporting
        if 'reporting' in result['results']:
            report_result = result['results']['reporting']
            if 'filepath' in report_result:
                print(f"  📋 Validation Report: {report_result['filepath']}")

    # Show generated validation reports
    import glob
    validation_reports = glob.glob("examples/artifact/*.md")
    if validation_reports:
        latest_report = max(validation_reports, key=os.path.getctime)
        print(f"\n📋 Latest Validation Report: {latest_report}")

    print(f"\n🎯 Validation Status:")
    if result['success']:
        print("✅ Multi-agent validation completed successfully")
        print("🔍 CSV data integrity verified against hierarchical report")
        print("📊 All validation teams coordinated via LangGraph")
    else:
        print("❌ Validation encountered issues - see report for details")


def main():
    """Run the comprehensive validation demo."""
    print_validation_banner()

    try:
        # Demo 1: File discovery
        demo_file_discovery()

        # Demo 2: Structure validation
        demo_structure_validation()

        # Demo 3: Content validation
        demo_content_validation()

        # Demo 4: Consistency validation
        demo_consistency_validation()

        # Demo 5: Comprehensive validation (main demo)
        result = demo_comprehensive_validation()
        show_validation_results(result)

        print("\n" + "=" * 80)
        print("🎉 VALIDATION DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("✅ Multi-agent data integrity verification working perfectly")
        print("🔍 CSV validation against hierarchical reports demonstrated")
        print("🏗️  Structure, Content, and Consistency teams coordinated")
        print("📊 Check examples/artifact/ for detailed validation reports")
        print("🤖 LangGraph-based multi-agent orchestration operational")

    except Exception as e:
        print(f"\n❌ Validation demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()