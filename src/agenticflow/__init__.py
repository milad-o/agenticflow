"""
AgenticFlow - A fully intelligent, agentic AI system framework.

AgenticFlow provides a comprehensive framework for building multi-agent AI systems
with async support, LangChain/LangGraph integration, and Agent-to-Agent communication.
"""

__version__ = "1.0.0"
__author__ = "AgenticFlow Team"

from .config.settings import (
    AgenticFlowConfig, 
    AgentConfig,
    LLMProviderConfig, 
    LLMProvider
)
from .core.agent import Agent
from .core.supervisor import SupervisorAgent
from .core.task_manager import TaskManager, TaskPriority
from .workflows.multi_agent import MultiAgentSystem
from .orchestration.task_orchestrator import TaskOrchestrator, InteractiveTaskNode
from .orchestration.task_management import FunctionTaskExecutor

# Import chatbot module components
from .chatbots import (
    RAGAgent,
    InteractiveChatbot,
    ChatbotConfig,
    KnowledgeMode,
    CitationStyle
)

# Import implemented components
__all__ = [
    # Core components
    "Agent",
    "SupervisorAgent",
    "TaskManager",
    "TaskPriority",
    "MultiAgentSystem",
    "TaskOrchestrator",
    "InteractiveTaskNode",
    "FunctionTaskExecutor",
    "AgenticFlowConfig",
    "AgentConfig",
    "LLMProviderConfig",
    "LLMProvider",
    
    # Chatbot components
    "RAGAgent",
    "InteractiveChatbot",
    "ChatbotConfig",
    "KnowledgeMode",
    "CitationStyle",
]
