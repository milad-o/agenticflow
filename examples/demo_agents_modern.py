#!/usr/bin/env python3
"""
Modern Agent Demo

This demo showcases basic multi-agent orchestration with report generation.
Creates a simple filesystem agent and reporting agent that work together
to analyze data and generate an LLM-only report.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agenticflow import Flow, FlowConfig
from agenticflow.agent import Agent
from agenticflow.core.config import AgentConfig
from agenticflow.agent.roles import AgentRole
from langchain_ollama import ChatOllama


def _pick_ollama_models():
    """Pick the best available Ollama model."""
    import subprocess
    prefer = ('qwen2.5:7b', 'granite3.2:8b', 'llama3.2:3b')
    names = []
    try:
        p = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=False)
        for line in p.stdout.splitlines()[1:]:
            parts = line.split()
            if parts:
                names.append(parts[0])
    except Exception:
        names = []
    chat = next((m for m in prefer if any(n.startswith(m) for n in names)), names[0] if names else None)
    if not chat:
        raise RuntimeError('No Ollama model found')
    return chat, None


async def demo_agents_modern():
    """Demo modern agent orchestration with report generation."""
    print("=" * 60)
    print("🤖 MODERN AGENTS DEMO")
    print("=" * 60)

    workspace = Path(__file__).parent
    print(f"Workspace: {workspace}")

    # Ensure artifact directory exists
    artifact_dir = workspace / "artifact"
    artifact_dir.mkdir(exist_ok=True)

    # Suppress noisy logs
    try:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("ollama").setLevel(logging.WARNING)
        logging.getLogger().setLevel(logging.WARNING)
    except Exception:
        pass

    # Create flow
    flow = Flow(
        FlowConfig(
            flow_name="ModernAgentsDemo",
            workspace_path=str(workspace),
            max_parallel_tasks=2,
            recursion_limit=10,
        )
    )

    # Install tools
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast", 
        "write_text_atomic",
        "file_stat"
    ])

    # Get LLM
    chat_model, _ = _pick_ollama_models()
    llm = ChatOllama(model=chat_model, temperature=0.1)
    print(f"🤖 Using LLM: {chat_model}")

    # Create filesystem agent (specialized, no sharing)
    filesystem_agent = Agent(
        config=AgentConfig(
            name="filesystem_agent",
            model=chat_model,
            temperature=0.1,
            role=AgentRole.FILESYSTEM
        ),
        model=llm,
        tools=flow.tool_registry.tools
    )

    # Create reporting agent (specialized, no sharing)
    reporting_agent = Agent(
        config=AgentConfig(
            name="reporting_agent", 
            model=chat_model,
            temperature=0.1,
            role=AgentRole.REPORTER
        ),
        model=llm,
        tools=flow.tool_registry.tools,
        static_resources={
            "report_filename": "examples/artifact/demo_agents_modern_report.md",
            "search_root": "examples/data",
            "file_pattern": "*.csv",
            "use_llm_for_report": True  # Enforce LLM-only reports
        }
    )

    print(f"✅ Created filesystem agent and reporting agent")

    # Task 1: Filesystem agent finds data files
    filesystem_request = "Find CSV files in examples/data directory and read their content to understand the structure"
    print(f"\n📋 Filesystem Task: {filesystem_request}")

    try:
        filesystem_result = await filesystem_agent.arun(filesystem_request)
        print(f"✅ Filesystem agent completed: {filesystem_result['success']}")
        if filesystem_result['success']:
            print(f"📊 Found data: {filesystem_result['message'][:100]}...")
    except Exception as e:
        print(f"❌ Filesystem agent failed: {e}")
        filesystem_result = {"success": False, "data": {}}

    # Task 2: Reporting agent generates comprehensive report
    reporting_request = """Generate a comprehensive analysis report based on the CSV data found in examples/data. 
    Write the report to examples/artifact/demo_agents_modern_report.md with sections for data overview, 
    key findings, and recommendations."""
    
    print(f"\n📋 Reporting Task: {reporting_request}")

    try:
        reporting_result = await reporting_agent.arun(reporting_request)
        print(f"✅ Reporting agent completed: {reporting_result['success']}")
        if reporting_result['success']:
            print(f"📝 Report generated: {reporting_result['message']}")
    except Exception as e:
        print(f"❌ Reporting agent failed: {e}")
        reporting_result = {"success": False}

    # Check final results
    print("\n" + "=" * 60)
    print("📊 DEMO RESULTS")
    print("=" * 60)

    report_path = workspace / "artifact" / "demo_agents_modern_report.md"
    if report_path.exists():
        print(f"✅ Report created: {report_path}")
        with open(report_path, 'r') as f:
            content = f.read()
            preview = content[:300] + "..." if len(content) > 300 else content
            print(f"\n📖 Report Preview:")
            print("-" * 40)
            print(preview)
            print("-" * 40)
    else:
        print(f"❌ Report not found at: {report_path}")

    print(f"\n🔄 Filesystem Success: {filesystem_result['success']}")
    print(f"📝 Reporting Success: {reporting_result['success']}")
    
    print("\n" + "=" * 60)
    print("🎯 MODERN AGENTS DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo_agents_modern())