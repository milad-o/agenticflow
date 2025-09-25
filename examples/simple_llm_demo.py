#!/usr/bin/env python3
"""
Simple LLM Integration Demo

Demonstrates how easy it is to plug in any LangChain LLM object into the framework.
Just pass any LangChain LLM instance to the `llm` parameter - that's it!
"""

import asyncio
import os
from pathlib import Path

# Import any LangChain LLM you want to use
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

# Import AgenticFlow - clean and simple
from agenticflow import (
    Flow, FlowConfig,
    FileSystemAgent, ReportingAgent,
    Planner
)


async def main():
    """Demo showing how easy it is to use any LangChain LLM."""

    print("🚀 AgenticFlow - Simple LLM Integration Demo")
    print("=" * 50)

    workspace = Path(__file__).parent

    # 1. Pick ANY LangChain LLM - super easy!
    print("\n🤖 LLM Options:")

    # Option 1: Groq (fast and free)
    if os.getenv("GROQ_API_KEY"):
        llm = ChatGroq(
            model="llama-3.2-90b-text-preview",
            temperature=0.1,
            api_key=os.environ.get("GROQ_API_KEY")
        )
        print("  ✅ Using Groq LLM")

    # Option 2: OpenAI (fallback)
    elif os.getenv("OPENAI_API_KEY"):
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        print("  ✅ Using OpenAI LLM")

    # Option 3: Ollama (local)
    else:
        try:
            llm = ChatOllama(
                model="llama3.2:latest",
                temperature=0.1
            )
            print("  ✅ Using Ollama LLM (local)")
        except:
            print("  ❌ No LLM available. Set GROQ_API_KEY or OPENAI_API_KEY")
            return 1

    print(f"  📋 Model: {getattr(llm, 'model_name', getattr(llm, 'model', 'Unknown'))}")

    # 2. Create agents - just pass the llm object!
    print("\n🛠️ Creating Agents:")

    # Super simple - just pass llm object to any agent
    filesystem_agent = FileSystemAgent(
        llm=llm,  # ← This is all you need!
        name="file_explorer",
        file_pattern="*.py",
        search_root="examples"
    )
    print(f"  ✅ {filesystem_agent.__class__.__name__} created")

    reporting_agent = ReportingAgent(
        llm=llm,  # ← Same here!
        name="reporter",
        report_filename="simple_demo_report.md"
    )
    print(f"  ✅ {reporting_agent.__class__.__name__} created")

    # 3. Setup flow
    print("\n⚙️ Setting up Flow:")

    flow = Flow(FlowConfig(
        flow_name="SimpleLLMDemo",
        workspace_path=str(workspace),
        max_parallel_tasks=2
    ))

    # Install tools
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast",
        "write_text_atomic",
        "file_stat"
    ])

    # Add agents
    flow.add_agent("filesystem", filesystem_agent)
    flow.add_agent("reporter", reporting_agent)

    # Tool adoption
    filesystem_agent.adopt_flow_tools(flow, ["find_files", "read_text_fast", "file_stat"])
    reporting_agent.adopt_flow_tools(flow, ["write_text_atomic"])

    # Set planner and start
    flow.set_planner(Planner())
    flow.start()

    print(f"  ✅ Flow ready with {len(flow.agents)} agents")

    # 4. Execute task
    print("\n🎯 Executing Task:")

    request = """
    Find Python files in the examples directory, read a couple of them to understand
    what the framework does, and create a simple summary report as 'simple_demo_report.md'.
    """

    print(f"  📋 Task: {request[:60]}...")

    try:
        result = await flow.arun(request)

        print(f"  ✅ Task completed successfully!")

        # Check for report
        report_path = workspace / "simple_demo_report.md"
        if report_path.exists():
            print(f"  📄 Report created: {report_path}")

            # Show preview
            content = report_path.read_text()
            lines = content.split('\n')[:8]
            print(f"\n📖 Report Preview:")
            print("-" * 30)
            for line in lines:
                print(f"  {line}")
            if len(content.split('\n')) > 8:
                print("  ...")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return 1

    # 5. Summary
    print(f"\n🎉 Success! Key Points:")
    print(f"  • Just pass any LangChain LLM to the `llm` parameter")
    print(f"  • Works with Groq, OpenAI, Ollama, or any other LangChain LLM")
    print(f"  • No configuration needed - plug and play!")
    print(f"  • Same interface across all agents")

    print("\n" + "=" * 50)
    print("✨ AgenticFlow makes LLM integration super easy!")

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