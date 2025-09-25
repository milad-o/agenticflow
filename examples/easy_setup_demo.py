#!/usr/bin/env python3
"""
Easy LLM and Embedding Setup Demo

Shows how incredibly easy it is to setup any LLM and embedding model with AgenticFlow.
Just plug in any LangChain LLM or embedding - no configuration needed!
"""

import asyncio
import os
from pathlib import Path

# Import any LangChain providers you want
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import ChatOllama

# AgenticFlow - super easy setup
from agenticflow import (
    # Core framework
    Flow, FlowConfig,
    # Agents that accept llm parameter
    FileSystemAgent, ReportingAgent,
    # Easy helper functions
    get_easy_llm, get_embeddings,
    Planner
)


async def main():
    """Demonstrate super easy LLM and embedding setup."""

    print("🚀 AgenticFlow - Easy LLM & Embedding Setup")
    print("=" * 55)

    workspace = Path(__file__).parent
    artifact_dir = workspace / "artifact"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Method 1: Use any LangChain LLM directly
    print("\n🎯 Method 1: Direct LangChain Integration")
    print("Just pass any LangChain LLM to the 'llm' parameter!")

    if os.getenv("GROQ_API_KEY"):
        # Use Groq directly
        llm1 = ChatGroq(
            model="llama-3.2-90b-text-preview",
            temperature=0.1
        )
        print(f"  ✅ Direct: {type(llm1).__name__}")
    elif os.getenv("OPENAI_API_KEY"):
        # Use OpenAI directly
        llm1 = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1
        )
        print(f"  ✅ Direct: {type(llm1).__name__}")
    else:
        # Use Ollama directly
        llm1 = ChatOllama(
            model="llama3.2:latest",
            temperature=0.1
        )
        print(f"  ✅ Direct: {type(llm1).__name__}")

    # Method 2: Use helper functions for even easier setup
    print("\n🛠️ Method 2: Helper Functions (Even Easier!)")
    print("Use get_easy_llm() and get_embeddings() for auto-detection:")

    try:
        # Auto-detect best available LLM
        llm2 = get_easy_llm("auto")
        print(f"  ✅ Auto LLM: {type(llm2).__name__}")

        # Auto-detect best available embeddings
        embeddings = get_embeddings("auto")
        print(f"  ✅ Auto Embeddings: {type(embeddings).__name__}")

    except Exception as e:
        print(f"  ⚠️ Auto-detection: {e}")
        # Fallback to Method 1
        llm2 = llm1
        embeddings = None

    # Method 3: Manual provider selection
    print("\n⚙️ Method 3: Specific Provider Selection")

    examples = []

    if os.getenv("GROQ_API_KEY"):
        groq_llm = get_easy_llm("groq", model="llama-3.2-90b-text-preview")
        examples.append(f"  ✅ Groq: {type(groq_llm).__name__}")

    if os.getenv("OPENAI_API_KEY"):
        openai_llm = get_easy_llm("openai", model="gpt-4o-mini")
        openai_embeddings = get_embeddings("openai")
        examples.extend([
            f"  ✅ OpenAI LLM: {type(openai_llm).__name__}",
            f"  ✅ OpenAI Embeddings: {type(openai_embeddings).__name__}"
        ])

    try:
        hf_embeddings = get_embeddings("huggingface", model_name="all-MiniLM-L6-v2")
        examples.append(f"  ✅ HuggingFace: {type(hf_embeddings).__name__}")
    except:
        examples.append("  ⚠️ HuggingFace: Not available (pip install langchain-huggingface)")

    for example in examples:
        print(example)

    # Demo: Create agents with easy LLM setup
    print("\n🤖 Creating Agents (Super Simple!):")

    # Create agents - just pass any LLM!
    filesystem_agent = FileSystemAgent(
        llm=llm2,  # ← Any LangChain LLM works here!
        name="easy_filesystem",
        file_pattern="*.py",
        search_root="examples"
    )
    print(f"  ✅ {filesystem_agent.__class__.__name__} with {type(llm2).__name__}")

    reporting_agent = ReportingAgent(
        llm=llm2,  # ← Same LLM or different one!
        name="easy_reporter",
        report_filename=str(artifact_dir / "easy_setup_report.md")
    )
    print(f"  ✅ {reporting_agent.__class__.__name__} with {type(llm2).__name__}")

    # Setup and run flow
    print("\n⚡ Running Demo Workflow:")

    flow = Flow(FlowConfig(
        flow_name="EasySetupDemo",
        workspace_path=str(workspace)
    ))

    # Install tools
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast",
        "write_text_atomic"
    ])

    # Add agents and tools
    flow.add_agent("filesystem", filesystem_agent)
    flow.add_agent("reporter", reporting_agent)

    filesystem_agent.adopt_flow_tools(flow, ["find_files", "read_text_fast"])
    reporting_agent.adopt_flow_tools(flow, ["write_text_atomic"])

    # Start flow
    flow.set_planner(Planner())
    flow.start()

    # Execute task
    request = """
    Find Python demo files in the examples directory, read a couple to understand
    the easy setup approach, and create a summary report as 'easy_setup_report.md'.
    """

    print(f"  📋 Task: {request[:50]}...")

    try:
        result = await flow.arun(request)
        print(f"  ✅ Completed successfully!")

        # Check report
        report_path = artifact_dir / "easy_setup_report.md"
        if report_path.exists():
            print(f"  📄 Report: {report_path}")

            # Preview
            content = report_path.read_text()[:300]
            print(f"\n📖 Report Preview:")
            print("-" * 40)
            print(content + "..." if len(content) == 300 else content)

    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Summary of the easy approach
    print(f"\n🎉 Easy Setup Summary:")
    print(f"  ✅ Any LangChain LLM → Just pass to 'llm' parameter")
    print(f"  ✅ Any LangChain Embeddings → Works the same way")
    print(f"  ✅ Helper functions → get_easy_llm(), get_embeddings()")
    print(f"  ✅ Auto-detection → Tries best available providers")
    print(f"  ✅ No configuration files → Pure code approach")

    print(f"\n🔧 Supported Providers:")
    providers = [
        ("LLMs", "Groq, OpenAI, Anthropic, Ollama, any LangChain LLM"),
        ("Embeddings", "OpenAI, HuggingFace, Ollama, Cohere, any LangChain Embeddings")
    ]
    for category, items in providers:
        print(f"  • {category}: {items}")

    print("\n" + "=" * 55)
    print("✨ AgenticFlow: Plug any LLM/Embedding and go!")

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        raise SystemExit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted.")
        raise SystemExit(130)
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        raise SystemExit(1)