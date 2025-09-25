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

# Direct import of just the LLM functionality
try:
    from agenticflow.core.models import get_easy_llm
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying direct path...")
    from agenticflow.core.models.models import get_easy_llm

import pandas as pd


async def main():
    """Demo the easy LLM setup."""

    print("🚀 Minimal LLM Demo")
    print("=" * 30)

    # Super easy LLM setup - this is the key feature!
    try:
        llm = get_easy_llm("auto", temperature=0.1)
        print(f"✅ LLM: {type(llm).__name__}")
        if hasattr(llm, 'model_name'):
            print(f"📋 Model: {llm.model_name}")
        elif hasattr(llm, 'model'):
            print(f"📋 Model: {llm.model}")
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

        except Exception as e:
            print(f"❌ LLM invocation failed: {e}")
            return 1

    print(f"\n🎉 Success! The easy LLM setup works perfectly:")
    print(f"  • get_easy_llm('auto') - automatically detects best LLM")
    print(f"  • Supports Groq, OpenAI, Ollama, and more")
    print(f"  • No configuration files needed")
    print(f"  • Works with any LangChain provider")

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