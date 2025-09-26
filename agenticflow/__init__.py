"""
AgenticFlow - Advanced AI Multi-Agent Framework

A developer-focused, OOP-based framework for building sophisticated multi-agent AI systems.

Key Features:
- 🤖 Pure OOP agent design with LangChain integration
- 🏗️ Modular architecture with logical component separation
- 🔧 Comprehensive tool ecosystem with smart registration
- 🎯 Specialized pre-built agents (FileSystem, Reporting, Analysis)
- 🚀 Advanced orchestration with intelligent delegation
- 📊 Built-in observability and state management

Quick Start - Just Plug in ANY LangChain LLM:
    from agenticflow import Flow, FlowConfig, FileSystemAgent, ReportingAgent

    # Use ANY LangChain LLM - no wrappers needed!
    from langchain_groq import ChatGroq
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_ollama import ChatOllama

    # Pick your favorite LLM
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    # OR llm = AzureChatOpenAI(azure_endpoint="...", azure_deployment="gpt-4")
    # OR llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    # OR llm = ChatAnthropic(model="claude-3-haiku-20240307")
    # OR llm = ChatOllama(model="llama3.2:latest")

    # Create agents - just pass the LLM!
    fs_agent = FileSystemAgent(llm=llm, search_root="./data")
    reporter = ReportingAgent(llm=llm, report_filename="analysis.md")

    # Setup and run
    flow = Flow(FlowConfig(flow_name="MyWorkflow"))
    flow.add_agent("filesystem", fs_agent)
    flow.add_agent("reporter", reporter)

    result = await flow.arun("Analyze files and generate report")

Architecture:
    agenticflow/
    ├── agent/                  # Complete agent system
    │   ├── base/              # Core agent abstractions
    │   ├── strategies/        # Execution patterns (RPAVH, Hybrid)
    │   ├── state/             # State management and lifecycle
    │   ├── rules/             # Behavior rules and patterns
    │   ├── roles/             # Agent role definitions
    │   ├── agents/            # Pre-built specialized agents
    │   └── registry/          # Agent discovery and factory
    ├── core/                   # Core framework functionality
    │   ├── config/            # Configuration classes
    │   ├── models/            # LLM integration
    │   ├── events/            # Event bus system
    │   ├── tasks/             # Task management
    │   └── flows/             # Flow orchestration
    ├── orchestration/          # Multi-agent coordination
    │   ├── orchestrators/     # Agent coordination
    │   ├── planners/          # Task planning
    │   ├── delegation/        # Capability matching
    │   └── cards/             # Discovery cards for inter-agent coordination
    ├── tools/                  # Comprehensive tool ecosystem
    │   ├── file/              # File operations
    │   ├── data/              # Data processing
    │   ├── search/            # Search capabilities
    │   └── utilities/         # General utilities
    ├── registries/            # Unified registration system
    └── observability/         # Monitoring and reporting
"""

# Core framework components
from .core import Flow, FlowConfig, AgentConfig
from .agent import (
    # Base classes
    Agent, RPAVHAgent,
    # Agent fundamentals
    AgentRole,
    # Pre-built agents
    FileSystemAgent, ReportingAgent, AnalysisAgent,
    # Registry system
    AgentRegistry, AgentType, register_agent
)
from .orchestration import Orchestrator, Planner
from .registries import ToolRegistry, ResourceRegistry

# For convenience - super easy LLM and embedding setup
from .core.models import get_chat_model, get_easy_llm, get_embeddings

__version__ = "0.2.0"
__author__ = "AgenticFlow Team"
__description__ = "Advanced AI Multi-Agent Framework for Developers"

__all__ = [
    # Core
    "Flow",
    "FlowConfig",
    "AgentConfig",
    "AgentRole",
    "get_chat_model",
    "get_easy_llm",
    "get_embeddings",

    # Agents
    "Agent",
    "RPAVHAgent",
    "FileSystemAgent",
    "ReportingAgent",
    "AnalysisAgent",

    # Agent Registry
    "AgentRegistry",
    "AgentType",
    "register_agent",

    # Orchestration
    "Orchestrator",
    "Planner",

    # Registries
    "ToolRegistry",
    "ResourceRegistry",
]
