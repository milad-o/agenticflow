#!/usr/bin/env python3
"""
Complete OOP Framework Demo

Demonstrates the fully restructured AgenticFlow framework with:
- Pure OOP design patterns
- Comprehensive module organization
- LangChain LLM integration
- Advanced agent registry system
- Modern Python practices

This example showcases the transformation from factory functions to
clean OOP architecture designed for developer productivity.
"""

import asyncio
import os
import logging
from pathlib import Path
from langchain_groq import ChatGroq

# New clean imports from restructured modules
from agenticflow import (
    Flow, FlowConfig, AgentConfig, AgentRole,
    FileSystemAgent, ReportingAgent, AnalysisAgent,
    AgentRegistry, AgentType, register_agent,
    get_chat_model, Planner, ToolRegistry
)
from agenticflow.core.events import EventEmitter, EventType
from agenticflow.agent.strategies import HybridRPAVHAgent


# Example: Custom agent using the new OOP approach
@register_agent(
    name="DataValidationAgent",
    agent_type=AgentType.SPECIALIZED,
    description="Validates data quality and integrity",
    capabilities=["data_validation", "quality_checks", "schema_validation"],
    requires_llm=True
)
class DataValidationAgent(HybridRPAVHAgent):
    """Custom data validation agent demonstrating OOP patterns."""

    def __init__(self, llm=None, validation_rules=None, **kwargs):
        config = AgentConfig(
            name="data_validator",
            model="",  # LLM instance provided directly
            temperature=0.0,  # Deterministic validation
            role=AgentRole.ANALYST,
            capabilities=["data_validation", "quality_checks"],
            system_prompt="""You are a data validation specialist.
            Validate data integrity, check schemas, and ensure quality standards."""
        )

        super().__init__(
            config=config,
            model=llm,
            use_llm_reflection=True,  # Smart error analysis
            **kwargs
        )

        self.validation_rules = validation_rules or []
        self.static_resources.update({
            "validation_rules": self.validation_rules,
            "quality_threshold": 0.95,
            "check_schema": True,
            "validate_types": True
        })


async def main() -> int:
    """Main demonstration function."""

    base = Path(__file__).resolve().parent.parent
    workspace = base / "examples"

    print("🚀 AgenticFlow Complete OOP Framework Demo")
    print("=" * 50)

    # Configure logging
    logging.getLogger().setLevel(logging.WARNING)

    # 1. Modern LLM Integration
    print("\n📡 LLM Integration:")
    llm = ChatGroq(
        model="llama-3.2-90b-text-preview",
        temperature=0.1,
        api_key=os.environ.get("GROQ_API_KEY")
    )
    print(f"  ✅ LangChain LLM: {type(llm).__name__}")
    print(f"  📋 Model: {llm.model_name}")

    # 2. Agent Registry Exploration
    print("\n🏗️ Agent Registry System:")
    registry = AgentRegistry()

    # List all available agents
    all_agents = registry.list_agents()
    print(f"  📊 Total Registered Agents: {len(all_agents)}")

    for agent_type in AgentType:
        agents = registry.list_agents(agent_type)
        print(f"  • {agent_type.value.title()}: {len(agents)} agents")

    # 3. Pure OOP Agent Creation
    print("\n🤖 Agent Creation (Pure OOP):")

    # Create specialized agents with clean constructors
    filesystem_agent = FileSystemAgent(
        llm=llm,
        name="modern_filesystem",
        file_pattern="*.py",
        search_root="examples",
        use_llm_reflection=True  # Smart adaptation
    )
    print(f"  ✅ Created: {filesystem_agent.__class__.__name__}")

    reporting_agent = ReportingAgent(
        llm=llm,
        name="modern_reporter",
        report_filename="oop_framework_report.md",
        temperature=0.2  # Creative report writing
    )
    print(f"  ✅ Created: {reporting_agent.__class__.__name__}")

    # Create custom agent
    custom_validator = DataValidationAgent(
        llm=llm,
        name="data_validator",
        validation_rules=["check_nulls", "validate_types", "schema_compliance"]
    )
    print(f"  ✅ Created: {custom_validator.__class__.__name__}")

    # 4. Registry Factory Pattern
    print("\n🏭 Registry Factory Creation:")
    try:
        registry_agent = registry.create(
            "AnalysisAgent",
            llm=llm,
            name="registry_analyzer",
            csv_path="data/example.csv"
        )
        print(f"  ✅ Factory Created: {registry_agent.__class__.__name__}")
    except Exception as e:
        print(f"  ⚠️ Factory creation note: {e}")

    # 5. Modern Flow Configuration
    print("\n⚙️ Flow Configuration:")

    # Advanced flow setup with new modular structure
    flow_config = FlowConfig(
        flow_name="CompleteOOPDemo",
        workspace_path=str(workspace),
        max_parallel_tasks=3,
        recursion_limit=15,
        enable_observability=True
    )

    flow = Flow(flow_config)
    print(f"  ✅ Flow Created: {flow.config.flow_name}")

    # Install tools using new organized structure
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast",
        "write_text_atomic",
        "file_stat"
    ])
    print(f"  🔧 Tools Installed: {len(flow.tool_registry.list_tools())} tools")

    # 6. Agent Registration and Orchestration
    print("\n🎭 Agent Orchestration:")

    # Register agents with flow
    flow.add_agent("filesystem", filesystem_agent)
    flow.add_agent("reporter", reporting_agent)
    flow.add_agent("validator", custom_validator)

    # Tool adoption with new organized approach
    filesystem_agent.adopt_flow_tools(flow, ["find_files", "read_text_fast", "file_stat"])
    reporting_agent.adopt_flow_tools(flow, ["write_text_atomic"])

    # Modern planner from orchestration module
    flow.set_planner(Planner())
    flow.start()

    print(f"  🚀 Flow Started with {len(flow.agents)} agents")

    # 7. Execute Advanced Workflow
    print("\n💼 Executing Advanced Workflow:")

    request = """
    Please analyze the Python files in the examples directory to understand
    the new OOP framework structure. Create a comprehensive report that highlights:
    1. The transition from factory patterns to pure OOP
    2. New module organization and separation of concerns
    3. LangChain integration improvements
    4. Developer experience enhancements

    Save the analysis as 'oop_framework_report.md' with executive summary.
    """

    print("📋 Task:", request[:100] + "...")

    try:
        start_time = asyncio.get_event_loop().time()
        result = await flow.arun(request)
        execution_time = asyncio.get_event_loop().time() - start_time

        print(f"  ⏱️ Execution Time: {execution_time:.2f}s")
        print(f"  ✅ Success: {result.get('success', False)}")

        # Check for generated report
        report_path = workspace / "oop_framework_report.md"
        if report_path.exists():
            print(f"  📄 Report Generated: {report_path}")
            file_size = report_path.stat().st_size
            print(f"  📊 Report Size: {file_size:,} bytes")

            # Show report preview
            preview = report_path.read_text(encoding="utf-8", errors="ignore")
            lines = preview.split('\n')[:10]
            print("\n📖 Report Preview:")
            print("─" * 40)
            for line in lines:
                print(f"  {line}")
            if len(preview.split('\n')) > 10:
                print("  ...")

    except Exception as e:
        print(f"  ❌ Execution Error: {e}")
        return 1

    # 8. Framework Summary
    print("\n🎯 Framework Transformation Summary:")
    print("  ✅ Legacy factory functions → Pure OOP classes")
    print("  ✅ Monolithic modules → Logical submodule organization")
    print("  ✅ String-based LLM config → LangChain integration")
    print("  ✅ Flat structure → Hierarchical architecture")
    print("  ✅ Manual agent creation → Registry-based discovery")
    print("  ✅ Mixed concerns → Separation of responsibilities")

    print("\n🏆 New Developer Experience:")
    print("  • Clean imports from logical modules")
    print("  • Type-safe constructors with clear parameters")
    print("  • Extensible through inheritance and composition")
    print("  • Discoverable via comprehensive registry system")
    print("  • Modern Python patterns and best practices")

    print("\n" + "=" * 50)
    print("🎉 Complete OOP Framework Demo Successful!")

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