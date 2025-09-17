"""
AgenticFlow - A fully intelligent, agentic AI system framework.

AgenticFlow provides a comprehensive framework for building multi-agent AI systems
with async support, LangChain/LangGraph integration, and Agent-to-Agent communication.
"""

__version__ = "0.1.4"
__author__ = "AgenticFlow Team"

from .config.settings import AgenticFlowConfig, LLMProviderConfig
from .core.agent import Agent
from .core.supervisor import SupervisorAgent
from .core.task_manager import TaskManager, TaskPriority
from .workflows.multi_agent import MultiAgentSystem

# Import implemented components
__all__ = [
    "Agent",
    "SupervisorAgent",
    "TaskManager",
    "TaskPriority",
    "MultiAgentSystem",
    "AgenticFlowConfig",
    "LLMProviderConfig",
]
