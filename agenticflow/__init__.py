"""
AgenticFlow - A fully async, OOP, modular framework for hierarchical multi-agent systems.

Inspired by LangGraph's hierarchical agent teams pattern, this framework provides:
- Flow: Main container for orchestrating agent workflows
- Orchestrator: Top-level coordination of teams and individual agents
- Supervisor: Team-level coordination of multiple agents
- Agent: Individual workers with specific tools and capabilities
- Observability: Monitoring and tracking of agent operations
- Workspace: Shared filesystem access for all agents
"""

from .core.flow import Flow
from .core.orchestrator import Orchestrator
from .core.agent import Agent, SimpleAgent, ReActAgent, Tool
from .core.supervisor import Supervisor
from .core.state import FlowState, AgentMessage, AgentStatus, MessageType
from .core.command import Command
from .workspace.workspace import Workspace
from .observability.observer import Observer
from .observability.metrics import Metrics

__version__ = "0.1.0"
__all__ = [
    "Flow",
    "Orchestrator",
    "Agent",
    "SimpleAgent",
    "ReActAgent",
    "Tool",
    "Supervisor",
    "FlowState",
    "AgentMessage",
    "AgentStatus",
    "MessageType",
    "Command",
    "Workspace",
    "Observer",
    "Metrics",
]