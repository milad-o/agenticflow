"""AgenticFlow Agent Module

This module contains the complete agent system organized into submodules:

- base: Core agent abstractions
- strategies: Agent execution patterns (RPAVH, Hybrid RPAVH)
- state: Agent state management and lifecycle
- rules: Behavior rules and decision patterns
- roles: Agent role definitions and classifications
- agents: Pre-built specialized agents
- registry: Agent discovery and factory methods

Usage:
    from agenticflow.agent import FileSystemAgent, ReportingAgent, AgentRole
    from agenticflow.agent.strategies import HybridRPAVHAgent
    from agenticflow.agent.state import AgentState
    from agenticflow.agent.roles import AgentRole
"""

# Core agent classes
from .base import Agent
from .strategies import RPAVHAgent
from .state import AgentState, AgentStatus, AgentStateManager
from .rules import AgentRules, FileSystemAgentRules, ReportingAgentRules, AnalysisAgentRules
from .roles import AgentRole

# Registry for discovery and factory methods
from .registry import AgentRegistry, AgentType, register_agent, get_agent_class

# Pre-built specialized agents
from .agents import (
    FileSystemAgent,
    EnhancedFileSystemAgent,
    ReportingAgent,
    EnhancedReportingAgent,
    AnalysisAgent
)

__all__ = [
    # Core classes
    "Agent",
    "RPAVHAgent",

    # Agent fundamentals
    "AgentRole",

    # State management
    "AgentState",
    "AgentStatus",
    "AgentStateManager",

    # Rules
    "AgentRules",
    "FileSystemAgentRules",
    "ReportingAgentRules",
    "AnalysisAgentRules",

    # Registry
    "AgentRegistry",
    "AgentType",
    "register_agent",
    "get_agent_class",

    # Pre-built agents
    "FileSystemAgent",
    "EnhancedFileSystemAgent",
    "ReportingAgent",
    "EnhancedReportingAgent",
    "AnalysisAgent"
]