#!/usr/bin/env python3
"""
Direct LLM Demo - Pure LangChain Integration

Shows how to use ANY LangChain LLM directly with AgenticFlow.
No wrapper functions needed - just plug in your LangChain LLM!
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import ANY LangChain LLM you want to use
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

# Direct import of just the LLM functionality
try:
    from agenticflow.core.models.models import get_easy_llm
except ImportError:
    get_easy_llm = None

import pandas as pd


async def demo_direct_llm_usage():
    """Demo using LangChain LLMs directly - no wrappers needed!"""

    print("🚀 Direct LangChain LLM Integration Demo")
    print("=" * 50)

    # Method 1: Use ANY LangChain LLM directly
    print("\n🎯 Method 1: Direct LangChain LLM Usage")

    # Example 1: Groq (fast and free)
    if os.getenv("GROQ_API_KEY"):
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            api_key=os.environ.get("GROQ_API_KEY")
        )
        print(f"✅ Using: {type(llm).__name__} with {llm.model_name}")

    # Example 2: Azure OpenAI (enterprise)
    elif os.getenv("AZURE_OPENAI_API_KEY"):
        llm = AzureChatOpenAI(
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            temperature=0.1
        )
        print(f"✅ Using: {type(llm).__name__} (Azure)")

    # Example 3: OpenAI
    elif os.getenv("OPENAI_API_KEY"):
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        print(f"✅ Using: {type(llm).__name__} with {llm.model_name}")

    # Example 4: Anthropic Claude
    elif os.getenv("ANTHROPIC_API_KEY"):
        llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.1,
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        print(f"✅ Using: {type(llm).__name__} with {llm.model}")

    # Example 5: Local Ollama
    else:
        try:
            llm = ChatOllama(
                model="llama3.2:latest",
                temperature=0.1
            )
            print(f"✅ Using: {type(llm).__name__} with {llm.model}")
        except Exception as e:
            print(f"❌ No LLM available. Set API keys or install Ollama. Error: {e}")
            return 1

    # Method 2: Optional - use helper function for convenience
    if get_easy_llm:
        print(f"\n🛠️ Method 2: Helper Function (Optional)")
        try:
            helper_llm = get_easy_llm("auto")
            print(f"✅ Helper detected: {type(helper_llm).__name__}")
        except Exception as e:
            print(f"⚠️ Helper function issue: {e}")

    # Now use the LLM - exact same way regardless of provider!
    print(f"\n🧠 Testing LLM with CSV Analysis...")

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
                print(f"  • {csv_file.name}: Error - {e}")

        prompt = f"""
        I have these CSV files:
        {chr(10).join(file_summaries)}

        Create a concise merge strategy covering:
        1. Best join columns
        2. Join type recommendation
        3. Potential issues
        4. Python pandas code

        Keep it practical and brief.
        """

        print(f"\n🤖 Asking {type(llm).__name__} for analysis...")

        try:
            response = await llm.ainvoke(prompt)
            result = response.content if hasattr(response, 'content') else str(response)

            print(f"\n📄 Analysis from {type(llm).__name__}:")
            print("─" * 50)
            print(result)

        except Exception as e:
            print(f"❌ LLM failed: {e}")
            return 1

    else:
        # Simple test
        test_prompt = "In 2 sentences, explain what makes LangChain great for LLM integration."

        try:
            response = await llm.ainvoke(test_prompt)
            result = response.content if hasattr(response, 'content') else str(response)

            print(f"\n📄 Response from {type(llm).__name__}:")
            print("─" * 40)
            print(result)

        except Exception as e:
            print(f"❌ LLM failed: {e}")
            return 1

    return llm


async def show_agent_integration(llm):
    """Show how the LLM integrates with AgenticFlow agents."""

    print(f"\n🤖 AgenticFlow Agent Integration")
    print("=" * 40)

    print(f"In AgenticFlow, you'd use this LLM like:")
    print(f"")
    print(f"```python")
    print(f"# Just pass ANY LangChain LLM to the llm parameter!")
    print(f"from agenticflow import FileSystemAgent, ReportingAgent")
    print(f"")
    print(f"# Your LLM (any LangChain LLM)")
    print(f"llm = {type(llm).__name__}(")
    if hasattr(llm, 'model_name'):
        print(f"    model='{llm.model_name}',")
    elif hasattr(llm, 'model'):
        print(f"    model='{llm.model}',")
    print(f"    temperature=0.1")
    print(f")")
    print(f"")
    print(f"# Create agents - just pass the llm!")
    print(f"fs_agent = FileSystemAgent(llm=llm, search_root='./data')")
    print(f"reporter = ReportingAgent(llm=llm, report_filename='analysis.md')")
    print(f"```")

    print(f"\n🎯 Key Benefits:")
    print(f"  ✅ Works with ANY LangChain LLM")
    print(f"  ✅ No wrapper functions needed")
    print(f"  ✅ Same interface across all providers")
    print(f"  ✅ Easy to switch providers")
    print(f"  ✅ Full LangChain ecosystem compatibility")


async def main():
    """Main demo function."""

    try:
        # Demo direct LLM usage
        llm = await demo_direct_llm_usage()

        # Show agent integration
        await show_agent_integration(llm)

        print(f"\n🏆 Summary:")
        print(f"  • AgenticFlow accepts ANY LangChain LLM directly")
        print(f"  • No need for wrapper functions or helpers")
        print(f"  • Same clean interface: llm=your_langchain_llm")
        print(f"  • Works with Groq, Azure OpenAI, OpenAI, Anthropic, Ollama, etc.")
        print(f"  • Pure LangChain compatibility")

        return 0

    except Exception as e:
        print(f"💥 Demo failed: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        raise SystemExit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted.")
        raise SystemExit(130)