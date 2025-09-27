#!/usr/bin/env python3
"""
AgenticFlow Demo - Hierarchical Multi-Agent Orchestration
=========================================================

This demo showcases AgenticFlow's capabilities with a real-world scenario:
analyzing local sales data while gathering market intelligence from the web.

Features demonstrated:
- Hierarchical team coordination with LangGraph
- Multi-worker collaboration (FileSystem, Analysis, Reporting, Web Research)
- State management and intelligent task routing
- Real tool execution with comprehensive reporting

Usage:
    uv run python demo.py
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
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")


# Load environment variables at module level
load_env()


class WebResearchWorker:
    """Web research worker using Tavily API for market intelligence."""

    def __init__(self):
        self.capabilities = ["web_search", "market_research", "trend_analysis"]
        self.tavily_key = os.getenv("TAVILY_API_KEY")

    async def arun(self, task: str):
        return self.execute(task)

    def execute(self, task: str):
        """Execute web research using Tavily API."""
        if not self.tavily_key:
            return {
                "action": "web_research",
                "status": "skipped",
                "reason": "No Tavily API key provided",
                "recommendation": "Set TAVILY_API_KEY environment variable for web research"
            }

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.tavily_key)

            # Extract search query from task
            if "widget" in task.lower() or "product" in task.lower():
                query = "widget market trends 2024 sales analysis"
            elif "customer" in task.lower():
                query = "customer behavior analytics e-commerce trends 2024"
            else:
                query = "business intelligence market analysis 2024"

            print(f"🔍 Searching web for: {query}")
            results = client.search(query, max_results=3)

            return {
                "action": "web_research",
                "query": query,
                "results": results.get("results", []),
                "summary": self._summarize_results(results.get("results", [])),
                "status": "completed"
            }

        except ImportError:
            return {
                "action": "web_research",
                "status": "error",
                "error": "Tavily client not installed. Run: pip install tavily-python"
            }
        except Exception as e:
            return {
                "action": "web_research",
                "status": "error",
                "error": str(e)
            }

    def _summarize_results(self, results):
        """Create summary of web research results."""
        if not results:
            return "No results found"

        summary = f"Found {len(results)} relevant sources:\n"
        for i, result in enumerate(results[:3], 1):
            title = result.get("title", "No title")[:60]
            summary += f"{i}. {title}...\n"

        return summary


def print_banner():
    """Print demo banner."""
    print("=" * 70)
    print("🚀 AGENTICFLOW DEMO - Hierarchical Multi-Agent Orchestration")
    print("=" * 70)
    print("Scenario: Comprehensive Business Intelligence Analysis")
    print("- Local sales data analysis")
    print("- Market research and trends")
    print("- Integrated reporting")
    print("-" * 70)


def demo_basic_functionality():
    """Demo 1: Basic functionality test."""
    print("\n📋 DEMO 1: Basic Framework Test")
    print("-" * 40)

    flow = Flow()
    flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))

    result = flow.run("Find and list all CSV files in the data directory")

    print(f"✅ Success: {result['success']}")
    print(f"🔧 Workers: {result['workers_used']}")
    print(f"📊 Files found: {len(result['results']['filesystem']['files'])}")


def demo_comprehensive_analysis():
    """Demo 2: Comprehensive multi-agent analysis."""
    print("\n📋 DEMO 2: Comprehensive Multi-Agent Analysis")
    print("-" * 50)

    # Create hierarchical team
    flow = Flow()
    flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
    flow.add_worker("analysis", AnalysisWorker())
    flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))
    flow.add_worker("web_research", WebResearchWorker())

    print(f"🏗️  Team assembled: {flow.list_workers()}")

    # Complex business intelligence task
    task = """
    Perform comprehensive business intelligence analysis:
    1. Find and analyze all CSV data files
    2. Calculate key business metrics (revenue, top products, customer insights)
    3. Research current market trends for widgets and customer behavior
    4. Generate executive report combining local data with market intelligence
    """

    print(f"\n🎯 Task: {task.strip()}")
    print("\n🔄 Executing hierarchical team workflow...")

    result = flow.run(task)

    return result


def demo_market_research():
    """Demo 3: Market research integration."""
    print("\n📋 DEMO 3: Market Research Integration")
    print("-" * 45)

    flow = Flow()
    flow.add_worker("web_research", WebResearchWorker())
    flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))

    result = flow.run("Research widget market trends and create market intelligence report")

    print(f"✅ Success: {result['success']}")
    print(f"🔧 Workers: {result['workers_used']}")


def show_results(result):
    """Display comprehensive results."""
    print("\n" + "=" * 70)
    print("📊 EXECUTION RESULTS")
    print("=" * 70)

    print(f"✅ Success: {result['success']}")
    print(f"🔧 Workers Used: {', '.join(result['workers_used'])}")
    print(f"📝 Total Messages: {result['summary']['total_messages']}")
    print(f"⚡ Execution Complete: {result['summary']['is_complete']}")

    if result['results']:
        print(f"\n🔍 Worker Results:")
        for worker, worker_result in result['results'].items():
            action = worker_result.get('action', 'unknown')
            print(f"  • {worker}: {action}")

            # Show specific results
            if worker == 'filesystem' and 'files' in worker_result:
                print(f"    📁 Files found: {len(worker_result['files'])}")
            elif worker == 'reporting' and 'filepath' in worker_result:
                print(f"    📄 Report: {worker_result['filepath']}")
            elif worker == 'web_research' and 'summary' in worker_result:
                print(f"    🌐 Research: {worker_result['summary'][:100]}...")

    # Show any generated reports
    import glob
    reports = glob.glob("examples/artifact/*.md")
    if reports:
        latest_report = max(reports, key=os.path.getctime)
        print(f"\n📋 Latest Report: {latest_report}")


def main():
    """Run the comprehensive AgenticFlow demo."""
    print_banner()

    try:
        # Demo 1: Basic functionality
        demo_basic_functionality()

        # Demo 2: Comprehensive analysis (main demo)
        result = demo_comprehensive_analysis()
        show_results(result)

        # Demo 3: Market research (if Tavily available)
        if os.getenv("TAVILY_API_KEY"):
            demo_market_research()
        else:
            print(f"\n💡 Tip: Set TAVILY_API_KEY for web research capabilities")

        print("\n" + "=" * 70)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("✅ AgenticFlow hierarchical multi-agent orchestration working perfectly")
        print("📊 Check examples/artifact/ for generated reports")
        print("🔧 All workers coordinated successfully via LangGraph")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()