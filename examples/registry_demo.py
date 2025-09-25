#!/usr/bin/env python3
"""
Agent Registry Demo

Demonstrates the new agent registry system and factory pattern.
Shows how to discover, create, and use agents dynamically.

Key features:
- Agent discovery through registry
- Dynamic agent creation using factory methods
- Custom agent registration
- Agent capability querying
"""

import asyncio
import os
from pathlib import Path
from langchain_groq import ChatGroq

from agenticflow import (
    Flow, FlowConfig, AgentConfig, AgentRole,
    AgentRegistry, AgentType, register_agent,
    HybridRPAVHAgent, FileSystemAgent, Planner
)


# Example: Register a custom agent using the decorator
@register_agent(
    name="CustomDataAgent",
    agent_type=AgentType.SPECIALIZED,
    description="Custom agent for specialized data processing tasks",
    capabilities=["data_validation", "format_conversion", "quality_checks"],
    requires_llm=True
)
class CustomDataAgent(HybridRPAVHAgent):
    """Custom agent example demonstrating registry integration."""

    def __init__(self, llm=None, **kwargs):
        config = AgentConfig(
            name="custom_data_agent",
            model="",
            temperature=0.2,
            role=AgentRole.ANALYST,
            capabilities=["data_validation", "format_conversion"],
            system_prompt="You are a specialized data processing agent."
        )

        super().__init__(
            config=config,
            model=llm,
            use_llm_reflection=True,
            **kwargs
        )


async def main() -> int:
    base = Path(__file__).resolve().parent.parent
    workspace = base / "examples"

    # Initialize LLM
    llm = ChatGroq(
        model="llama-3.2-90b-text-preview",
        temperature=0.1,
        api_key=os.environ.get("GROQ_API_KEY")
    )

    # Get registry instance
    registry = AgentRegistry()

    print("===== AGENT REGISTRY DEMO =====\n")

    # 1. Discover available agents
    print("🔍 Available Agents:")
    all_agents = registry.list_agents()
    for name, info in all_agents.items():
        status = "🔴 Requires LLM" if info.requires_llm else "🟢 LLM Optional"
        print(f"  • {name}: {info.description} [{status}]")
        print(f"    Type: {info.agent_type.value}, Capabilities: {', '.join(info.capabilities)}")
    print()

    # 2. Filter agents by type
    print("🏗️ Strategy Agents:")
    strategy_agents = registry.list_agents(AgentType.STRATEGY)
    for name, info in strategy_agents.items():
        print(f"  • {name}: {info.description}")
    print()

    print("🎯 Specialized Agents:")
    specialized_agents = registry.list_agents(AgentType.SPECIALIZED)
    for name, info in specialized_agents.items():
        print(f"  • {name}: {info.description}")
    print()

    # 3. Create agents using registry factory methods
    print("🏭 Creating Agents via Registry:")

    try:
        # Create filesystem agent
        fs_agent = registry.create(
            "FileSystemAgent",
            llm=llm,
            name="registry_filesystem",
            file_pattern="*.md",
            search_root="examples"
        )
        print(f"  ✅ Created {fs_agent.__class__.__name__}")

        # Create reporting agent
        reporter = registry.create(
            "ReportingAgent",
            llm=llm,
            name="registry_reporter",
            report_filename="registry_demo_report.md"
        )
        print(f"  ✅ Created {reporter.__class__.__name__}")

        # Create custom agent
        custom_agent = registry.create(
            "CustomDataAgent",
            llm=llm,
            name="my_custom_agent"
        )
        print(f"  ✅ Created {custom_agent.__class__.__name__}")

    except Exception as e:
        print(f"  ❌ Error creating agent: {e}")
        return 1
    print()

    # 4. Query agent capabilities
    print("📋 Agent Capabilities:")
    for agent_name in ["FileSystemAgent", "CustomDataAgent", "HybridRPAVHAgent"]:
        capabilities = registry.get_capabilities(agent_name)
        requires_llm = "Yes" if registry.requires_llm(agent_name) else "No"
        print(f"  • {agent_name}:")
        print(f"    Capabilities: {', '.join(capabilities or ['None'])}")
        print(f"    Requires LLM: {requires_llm}")
    print()

    # 5. Use agents in a workflow
    print("🚀 Running Registry-Created Agents in Workflow:")

    flow = Flow(
        FlowConfig(
            flow_name="RegistryDemo",
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

    # Register agents with flow
    flow.add_agent("filesystem", fs_agent)
    flow.add_agent("reporter", reporter)

    # Adopt tools
    fs_agent.adopt_flow_tools(flow, ["find_files", "read_text_fast", "file_stat"])
    reporter.adopt_flow_tools(flow, ["write_text_atomic"])

    # Set planner and start
    flow.set_planner(Planner())
    flow.start()

    # Execute task
    request = (
        "Find markdown files in the examples directory, read a few of them to understand "
        "the project structure, and create a summary report as 'registry_demo_report.md'."
    )

    print(f"Request: {request}")

    try:
        result = await flow.arun(request)
        print(f"✅ Task completed successfully")
        print(f"Response preview: {result.get('final_response', '')[:100]}...")

        # Check if report was created
        report_path = workspace / "registry_demo_report.md"
        if report_path.exists():
            print(f"📄 Report created: {report_path}")

    except Exception as e:
        print(f"❌ Task failed: {e}")
        return 1

    print("\n===== REGISTRY DEMO COMPLETE =====")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        raise SystemExit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(130)