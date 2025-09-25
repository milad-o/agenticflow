#!/usr/bin/env python3
"""
Minimal LLM Demo - Direct Import

Shows the core easy LLM functionality without any framework overhead.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Explicit Ollama LLM and Embeddings setup
from langchain_ollama import ChatOllama, OllamaEmbeddings


def _pick_ollama_models():
    """Detect available Ollama models and pick preferred chat and embedding models."""
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

import pandas as pd


async def main():
    """Demo the easy LLM setup."""

    print("🚀 Minimal LLM Demo")
    print("=" * 30)

    # Explicit Ollama LLM + Embeddings setup
    try:
        chat_model, embed_model = _pick_ollama_models()
        llm = ChatOllama(model=chat_model, temperature=0.1)
        embeddings = OllamaEmbeddings(model=embed_model) if embed_model else None
        print(f"✅ LLM: {type(llm).__name__}")
        print(f"📋 Model: {getattr(llm, 'model_name', getattr(llm, 'model', 'unknown'))}")
        if embeddings:
            print(f"🧩 Embeddings: OllamaEmbeddings ({embed_model})")
    except Exception as e:
        print(f"❌ LLM setup failed: {e}")
        return 1

    # Test basic LLM functionality
    print("\n🧠 Testing LLM...")

    # Analyze the CSV files we created
    csv_dir = Path("examples/data/csv")
    csv_files = list(csv_dir.glob("*.csv")) if csv_dir.exists() else []

    if csv_files:
        print(f"📊 Found {len(csv_files)} CSV files")
        artifact_dir = (Path(__file__).parent / "artifact")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        report_path = artifact_dir / f"{Path(__file__).stem}_report.md"

        # Read samples from each file
        file_summaries = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, nrows=3)
                summary = f"{csv_file.name}: {len(df)} rows, columns: {', '.join(df.columns.tolist())}"
                file_summaries.append(summary)
                print(f"  • {summary}")
            except Exception as e:
                print(f"  • {csv_file.name}: Error reading - {e}")

        # Ask LLM to analyze the CSV structure and suggest merge strategy
        prompt = f"""
        I have the following CSV files:
        {chr(10).join(file_summaries)}

        Please analyze these CSV files and suggest:
        1. Which columns could be used as join keys
        2. What type of join would work best
        3. Any potential data issues or conflicts
        4. A step-by-step merge plan

        Keep it concise and practical.
        """

        print("\n🤖 Asking LLM to analyze CSV merge strategy...")

        try:
            response = await llm.ainvoke(prompt)
            result = response.content if hasattr(response, 'content') else str(response)

            print("\n📄 LLM Analysis:")
            print("─" * 50)
            print(result)
            # Write artifact
            (report_path).write_text(str(result), encoding="utf-8")

        except Exception as e:
            print(f"❌ LLM invocation failed: {e}")
            return 1

    else:
        # Simple test without CSV files
        test_prompt = "Explain in 2 sentences what makes a good merge strategy for CSV files."

        try:
            response = await llm.ainvoke(test_prompt)
            result = response.content if hasattr(response, 'content') else str(response)

            print(f"\n📄 LLM Response:")
            print("─" * 30)
            print(result)

            # Write artifact
            artifact_dir = (Path(__file__).parent / "artifact")
            artifact_dir.mkdir(parents=True, exist_ok=True)
            report_path = artifact_dir / f"{Path(__file__).stem}_report.md"
            report_path.write_text(str(result), encoding="utf-8")

        except Exception as e:
            print(f"❌ LLM invocation failed: {e}")
            return 1

    print(f"\n🎉 Success! Explicit Ollama setup works:")
    print(f"  • Chat model: {getattr(llm, 'model', 'unknown')}")
    print(f"  • Embeddings: {getattr(embeddings, 'model', 'none') if 'embeddings' in locals() else 'none'}")
    print(f"  • Local-first, zero secrets required")
    print(f"  • Still compatible with any LangChain LLM if you swap it in")

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