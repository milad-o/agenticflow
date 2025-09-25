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

# New clean imports from restructured modules
from agenticflow import (
    Flow, FlowConfig, AgentConfig, AgentRole,
    FileSystemAgent, ReportingAgent, AnalysisAgent,
    AgentRegistry, AgentType,
    get_chat_model, Planner, ToolRegistry
)
from agenticflow.core.events import EventEmitter, EventType
from agenticflow.agent.strategies import HybridRPAVHAgent


# Example: Custom agent using the new OOP approach (no registry decorator needed for this demo)
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
    artifact_dir = workspace / "artifact"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    print("🚀 AgenticFlow Complete OOP Framework Demo")
    print("=" * 50)

    # Configure logging
    logging.getLogger().setLevel(logging.WARNING)

    # 1. Modern LLM Integration (explicit Ollama)
    print("\n📡 LLM Integration:")
    chat_model, embed_model = _pick_ollama_models()
    llm = ChatOllama(model=chat_model, temperature=0.1)
    embeddings = OllamaEmbeddings(model=embed_model) if embed_model else None
    print(f"  ✅ LangChain LLM: {type(llm).__name__}")
    print(f"  📋 Model: {getattr(llm, 'model_name', getattr(llm, 'model', 'unknown'))}")
    if embeddings:
        print(f"  🧩 Embeddings: {embed_model}")

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
        report_filename=str(artifact_dir / "oop_framework_report.md"),
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
    Please read the ssis packages in data/ssis/ and tell me
    what they are and prepare short report.
    """

    print("📋 Task:", request[:100] + "...")

    try:
        start_time = asyncio.get_event_loop().time()
        result = await flow.arun(request)
        execution_time = asyncio.get_event_loop().time() - start_time

        print(f"  ⏱️ Execution Time: {execution_time:.2f}s")
        print(f"  ✅ Success: {result.get('success', False)}")

        # Check for generated report
        report_path = artifact_dir / f"{Path(__file__).stem}_report.md"
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
        else:
            print("  ⚠️ Report not found:", report_path)

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