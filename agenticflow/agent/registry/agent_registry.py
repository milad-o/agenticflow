"""
Agent Registry

Centralized registry for all agent types, strategies, and pre-built agents.
Enables discovery and dynamic instantiation of agents.
"""

from typing import Dict, Type, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool


class AgentType(Enum):
    """Agent type classification."""
    BASE = "base"
    STRATEGY = "strategy"
    SPECIALIZED = "specialized"


@dataclass
class AgentInfo:
    """Agent registration information."""
    name: str
    agent_class: Type
    agent_type: AgentType
    description: str
    capabilities: List[str]
    requires_llm: bool = True


class AgentRegistry:
    """
    Central registry for all agent types in AgenticFlow.

    Provides discovery, registration, and factory methods for agents.
    """

    _instance: Optional['AgentRegistry'] = None
    _agents: Dict[str, AgentInfo] = {}

    def __new__(cls) -> 'AgentRegistry':
        """Singleton implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize registry with built-in agents."""
        if not self._agents:  # Only register once
            self._register_builtin_agents()

    def _register_builtin_agents(self):
        """Register all built-in agent types."""
        # Import here to avoid circular imports
        from ..base import Agent
        from ..strategies import RPAVHAgent, HybridRPAVHAgent
        from ..agents import FileSystemAgent, ReportingAgent, AnalysisAgent
        from ..agents import EnhancedFileSystemAgent, EnhancedReportingAgent

        # Base agents
        self._register(AgentInfo(
            name="Agent",
            agent_class=Agent,
            agent_type=AgentType.BASE,
            description="Base agent class with ReAct pattern",
            capabilities=["basic_reasoning", "tool_usage"],
            requires_llm=True
        ))

        # Strategy agents
        self._register(AgentInfo(
            name="RPAVHAgent",
            agent_class=RPAVHAgent,
            agent_type=AgentType.STRATEGY,
            description="Reflect-Plan-Act-Verify-Handoff pattern agent",
            capabilities=["reflection", "planning", "verification", "handoff"],
            requires_llm=True
        ))

        self._register(AgentInfo(
            name="HybridRPAVHAgent",
            agent_class=HybridRPAVHAgent,
            agent_type=AgentType.STRATEGY,
            description="Optimized RPAVH with selective LLM usage",
            capabilities=["fast_planning", "selective_llm", "rule_based", "direct_execution"],
            requires_llm=False  # Can work without LLM for some operations
        ))

        # Specialized agents
        self._register(AgentInfo(
            name="FileSystemAgent",
            agent_class=FileSystemAgent,
            agent_type=AgentType.SPECIALIZED,
            description="Fast filesystem operations and file discovery",
            capabilities=["file_discovery", "content_reading", "metadata_analysis"],
            requires_llm=False
        ))

        self._register(AgentInfo(
            name="EnhancedFileSystemAgent",
            agent_class=EnhancedFileSystemAgent,
            agent_type=AgentType.SPECIALIZED,
            description="Advanced filesystem agent with adaptive search",
            capabilities=["adaptive_search", "multi_pattern", "smart_recovery"],
            requires_llm=True
        ))

        self._register(AgentInfo(
            name="ReportingAgent",
            agent_class=ReportingAgent,
            agent_type=AgentType.SPECIALIZED,
            description="Professional report generation",
            capabilities=["report_generation", "content_synthesis", "formatting"],
            requires_llm=True
        ))

        self._register(AgentInfo(
            name="EnhancedReportingAgent",
            agent_class=EnhancedReportingAgent,
            agent_type=AgentType.SPECIALIZED,
            description="Multi-format adaptive report generation",
            capabilities=["multi_format", "adaptive_content", "smart_analysis"],
            requires_llm=True
        ))

        self._register(AgentInfo(
            name="AnalysisAgent",
            agent_class=AnalysisAgent,
            agent_type=AgentType.SPECIALIZED,
            description="Fast CSV analytics and data processing",
            capabilities=["csv_analysis", "chunked_processing", "aggregations"],
            requires_llm=False
        ))

    def _register(self, info: AgentInfo):
        """Register an agent."""
        self._agents[info.name] = info

    def register(self, name: str, agent_class: Type, agent_type: AgentType,
                description: str, capabilities: List[str], requires_llm: bool = True):
        """
        Register a custom agent type.

        Args:
            name: Unique agent name
            agent_class: Agent class
            agent_type: Type classification
            description: Human-readable description
            capabilities: List of capabilities
            requires_llm: Whether agent requires LLM
        """
        self._register(AgentInfo(
            name=name,
            agent_class=agent_class,
            agent_type=agent_type,
            description=description,
            capabilities=capabilities,
            requires_llm=requires_llm
        ))

    def get(self, name: str) -> Optional[AgentInfo]:
        """Get agent info by name."""
        return self._agents.get(name)

    def get_class(self, name: str) -> Optional[Type]:
        """Get agent class by name."""
        info = self.get(name)
        return info.agent_class if info else None

    def list_agents(self, agent_type: Optional[AgentType] = None) -> Dict[str, AgentInfo]:
        """List all agents, optionally filtered by type."""
        if agent_type is None:
            return self._agents.copy()
        return {name: info for name, info in self._agents.items()
                if info.agent_type == agent_type}

    def create(self, name: str, llm: Optional[BaseChatModel] = None,
               tools: Optional[List[BaseTool]] = None, **kwargs) -> Any:
        """
        Factory method to create agent instance.

        Args:
            name: Agent name
            llm: LangChain LLM instance
            tools: List of tools
            **kwargs: Additional arguments for agent constructor

        Returns:
            Agent instance

        Raises:
            ValueError: If agent not found or LLM required but not provided
        """
        info = self.get(name)
        if not info:
            raise ValueError(f"Agent '{name}' not found in registry")

        if info.requires_llm and llm is None:
            raise ValueError(f"Agent '{name}' requires LLM but none provided")

        # Prepare constructor arguments
        init_kwargs = kwargs.copy()
        if llm is not None:
            init_kwargs['llm'] = llm
        if tools is not None:
            init_kwargs['tools'] = tools

        try:
            return info.agent_class(**init_kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create agent '{name}': {e}")

    def get_capabilities(self, name: str) -> Optional[List[str]]:
        """Get agent capabilities."""
        info = self.get(name)
        return info.capabilities if info else None

    def requires_llm(self, name: str) -> bool:
        """Check if agent requires LLM."""
        info = self.get(name)
        return info.requires_llm if info else True


# Global registry instance
_registry = AgentRegistry()


def register_agent(name: str, agent_class: Type, agent_type: AgentType,
                  description: str, capabilities: List[str], requires_llm: bool = True):
    """
    Decorator and function to register custom agents.

    Usage as decorator:
        @register_agent("MyAgent", AgentType.SPECIALIZED, "Custom agent", ["capability1"])
        class MyAgent(HybridRPAVHAgent):
            pass

    Usage as function:
        register_agent("MyAgent", MyAgent, AgentType.SPECIALIZED, "Custom agent", ["capability1"])
    """
    _registry.register(name, agent_class, agent_type, description, capabilities, requires_llm)
    return agent_class


def get_agent_class(name: str) -> Optional[Type]:
    """Get agent class by name."""
    return _registry.get_class(name)


def create_agent(name: str, llm: Optional[BaseChatModel] = None,
                tools: Optional[List[BaseTool]] = None, **kwargs) -> Any:
    """Factory function to create agent."""
    return _registry.create(name, llm, tools, **kwargs)


def list_available_agents(agent_type: Optional[AgentType] = None) -> Dict[str, str]:
    """List available agents with descriptions."""
    agents = _registry.list_agents(agent_type)
    return {name: info.description for name, info in agents.items()}