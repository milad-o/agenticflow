#!/usr/bin/env python3
"""
Azure OpenAI Demo

Shows how to use Azure OpenAI with AgenticFlow.
Just plug in your Azure OpenAI LLM - no configuration needed!
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Azure OpenAI from LangChain
from langchain_openai import AzureChatOpenAI


async def main():
    """Demo Azure OpenAI integration."""

    print("🚀 AgenticFlow + Azure OpenAI Demo")
    print("=" * 45)

    # Check for Azure OpenAI environment variables
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("⚠️ Missing required environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\n📋 To use Azure OpenAI, set these environment variables:")
        print("   export AZURE_OPENAI_API_KEY='your-api-key'")
        print("   export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("   export AZURE_OPENAI_DEPLOYMENT='your-deployment-name'  # optional")
        print("   export AZURE_OPENAI_API_VERSION='2024-02-15-preview'  # optional")

        # Show code example instead
        print(f"\n💡 Here's how you'd use Azure OpenAI with AgenticFlow:")
        print_azure_code_example()
        return 0

    # Create Azure OpenAI LLM - just like any other LangChain LLM!
    print("🤖 Creating Azure OpenAI LLM...")

    try:
        llm = AzureChatOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            temperature=0.1,
            api_key=os.environ["AZURE_OPENAI_API_KEY"]
        )
        print(f"✅ Azure OpenAI LLM created successfully!")
        print(f"   Endpoint: {llm.azure_endpoint}")
        print(f"   Deployment: {llm.deployment_name}")
        print(f"   API Version: {llm.openai_api_version}")

    except Exception as e:
        print(f"❌ Failed to create Azure OpenAI LLM: {e}")
        return 1

    # Test the LLM
    print(f"\n🧠 Testing Azure OpenAI LLM...")

    test_prompt = "Explain the benefits of using Azure OpenAI in enterprise environments in 2 sentences."

    try:
        response = await llm.ainvoke(test_prompt)
        result = response.content if hasattr(response, 'content') else str(response)

        print(f"📄 Azure OpenAI Response:")
        print("─" * 40)
        print(result)

    except Exception as e:
        print(f"❌ Azure OpenAI invocation failed: {e}")
        return 1

    # Show AgenticFlow integration
    print_azure_integration_example(llm)

    return 0


def print_azure_code_example():
    """Show how to use Azure OpenAI with AgenticFlow."""

    print("```python")
    print("from agenticflow import FileSystemAgent, ReportingAgent")
    print("from langchain_openai import AzureChatOpenAI")
    print("")
    print("# Create Azure OpenAI LLM")
    print("llm = AzureChatOpenAI(")
    print("    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],")
    print("    azure_deployment='gpt-4',  # your deployment name")
    print("    api_version='2024-02-15-preview',")
    print("    temperature=0.1")
    print(")")
    print("")
    print("# Use with AgenticFlow agents - just pass the llm!")
    print("fs_agent = FileSystemAgent(llm=llm, search_root='./data')")
    print("reporter = ReportingAgent(llm=llm, report_filename='analysis.md')")
    print("")
    print("# That's it! AgenticFlow works with ANY LangChain LLM")
    print("```")


def print_azure_integration_example(llm):
    """Show AgenticFlow integration example."""

    print(f"\n🏗️ AgenticFlow Integration Example:")
    print("=" * 45)

    print("With your Azure OpenAI LLM, you can now use it with ANY AgenticFlow agent:")
    print("")
    print("```python")
    print("from agenticflow import Flow, FlowConfig")
    print("from agenticflow import FileSystemAgent, ReportingAgent, AnalysisAgent")
    print("")
    print("# Your Azure OpenAI LLM (already configured above)")
    print(f"# llm = AzureChatOpenAI(...)")
    print("")
    print("# Create agents - just pass your Azure OpenAI LLM!")
    print("filesystem_agent = FileSystemAgent(")
    print("    llm=llm,  # ← Your Azure OpenAI LLM")
    print("    search_root='./data',")
    print("    file_pattern='*.csv'")
    print(")")
    print("")
    print("reporting_agent = ReportingAgent(")
    print("    llm=llm,  # ← Same Azure OpenAI LLM")
    print("    report_filename='azure_analysis.md'")
    print(")")
    print("")
    print("analysis_agent = AnalysisAgent(")
    print("    llm=llm,  # ← Same Azure OpenAI LLM")
    print("    csv_path='data.csv'")
    print(")")
    print("")
    print("# Setup flow")
    print("flow = Flow(FlowConfig(flow_name='AzureWorkflow'))")
    print("flow.add_agent('filesystem', filesystem_agent)")
    print("flow.add_agent('reporter', reporting_agent)")
    print("flow.add_agent('analyzer', analysis_agent)")
    print("")
    print("# Run with Azure OpenAI powering all agents!")
    print("result = await flow.arun('Analyze data and create report')")
    print("```")

    print(f"\n🎯 Key Benefits:")
    print(f"  ✅ Enterprise-grade Azure OpenAI integration")
    print(f"  ✅ Full compliance and security features")
    print(f"  ✅ Same simple interface: llm=your_azure_llm")
    print(f"  ✅ Works across all AgenticFlow agents")
    print(f"  ✅ Easy to switch between different Azure deployments")


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