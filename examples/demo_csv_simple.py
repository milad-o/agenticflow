#!/usr/bin/env python3
"""
Simple CSV Demo - Using Easy LLM Setup

A simplified version that directly demonstrates the easy LLM integration
without complex orchestration, just showing the core functionality.
"""

import asyncio
import os
from pathlib import Path
import pandas as pd

# Direct imports without complex orchestration
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

# Explicit Ollama LLM + Embeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings


def _pick_ollama_models():
    import subprocess
    prefer = ("qwen2.5:7b", "granite3.2:8b")
    prefer_embed = ("nomic-embed-text:latest", "nomic-embed-text")
    names = []
    try:
        p = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
        for line in p.stdout.splitlines()[1:]:
            parts = line.split()
            if parts:
                names.append(parts[0])
    except Exception:
        names = []
    chat = next((m for m in prefer if any(n.startswith(m) for n in names)), names[0] if names else None)
    embed = next((m for m in prefer_embed if any(n.startswith(m) for n in names)), None)
    if not chat:
        raise RuntimeError("No Ollama chat model found. Please `ollama pull qwen2.5:7b` or `granite3.2:8b`.")
    return chat, embed


@tool
def read_csv_sample(filepath: str, nrows: int = 5) -> str:
    """Read a sample of rows from a CSV file."""
    try:
        df = pd.read_csv(filepath, nrows=nrows)
        return f"CSV '{filepath}' sample ({len(df)} rows):\n{df.to_string()}"
    except Exception as e:
        return f"Error reading CSV: {e}"


@tool
def analyze_csv_structure(filepath: str) -> str:
    """Analyze the structure of a CSV file."""
    try:
        df = pd.read_csv(filepath)
        info = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "null_counts": df.isnull().sum().to_dict()
        }
        return f"CSV '{filepath}' structure:\n{info}"
    except Exception as e:
        return f"Error analyzing CSV: {e}"


@tool
def find_csv_files(directory: str = "examples/data/csv") -> str:
    """Find CSV files in a directory."""
    try:
        csv_dir = Path(directory)
        if not csv_dir.exists():
            return f"Directory '{directory}' does not exist"

        csv_files = list(csv_dir.glob("*.csv"))
        if not csv_files:
            return f"No CSV files found in '{directory}'"

        files_info = []
        for file in csv_files:
            size = file.stat().st_size
            files_info.append(f"- {file.name} ({size} bytes)")

        return f"Found {len(csv_files)} CSV files in '{directory}':\n" + "\n".join(files_info)
    except Exception as e:
        return f"Error finding CSV files: {e}"


async def main():
    """Run the simple CSV demo."""

    print("🚀 Simple CSV Demo - Easy LLM Setup")
    print("=" * 45)

    # Explicit Ollama setup
    try:
        chat_model, embed_model = _pick_ollama_models()
        llm = ChatOllama(model=chat_model, temperature=0.1)
        embeddings = OllamaEmbeddings(model=embed_model) if embed_model else None
        print(f"✅ LLM: {type(llm).__name__} ({getattr(llm, 'model', 'unknown')})")
        if embeddings:
            print(f"🧩 Embeddings: {embed_model}")
    except Exception as e:
        print(f"❌ LLM setup failed: {e}")
        return 1

    # Create a simple agent with tools
    tools = [find_csv_files, read_csv_sample, analyze_csv_structure]

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    print("\n🔧 Tools available:")
    for tool in tools:
        print(f"  • {tool.name}: {tool.description}")

    # Task: Analyze CSV files and create merge plan
    task = """
    Please help me analyze CSV files for a merge plan:

    1. Find CSV files in the examples/data/csv directory
    2. Read samples from each CSV file to understand their structure
    3. Analyze the structure of each file (columns, data types, etc.)
    4. Create a merge plan recommending:
       - Which columns could be used as join keys
       - What type of join would work best (inner, left, outer)
       - Any data cleaning or transformation needed
       - Potential issues or conflicts

    Provide a clear, actionable merge plan.
    """

    print(f"\n📋 Task: {task[:100]}...")

    try:
        # Simple execution without complex orchestration
        messages = [HumanMessage(content=task)]

        print("\n🤖 LLM working...")
        response = await llm_with_tools.ainvoke(messages)

        # Handle tool calls if any
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"🔧 Making {len(response.tool_calls)} tool calls...")

            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']

                print(f"  • Calling {tool_name}...")

                # Find and execute the tool
                for tool in tools:
                    if tool.name == tool_name:
                        try:
                            result = tool.invoke(tool_args)
                            print(f"    Result: {result[:100]}..." if len(result) > 100 else f"    Result: {result}")
                        except Exception as e:
                            print(f"    Error: {e}")
                        break

        print(f"\n📄 LLM Response:")
        print("─" * 50)
        content = response.content if hasattr(response, 'content') else str(response)
        print(content)

        # Write artifact
        artifact_dir = (Path(__file__).parent / "artifact")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        report_path = artifact_dir / f"{Path(__file__).stem}_report.md"
        report_path.write_text(content, encoding="utf-8")

        print("\n✅ Demo completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1

    print("\n🎯 Key Points:")
    print("  • Easy LLM setup: get_easy_llm('auto') - that's it!")
    print("  • Works with any LangChain LLM provider")
    print("  • Simple tool integration")
    print("  • No complex configuration needed")

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        raise SystemExit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted.")
        raise SystemExit(130)
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        raise SystemExit(1)