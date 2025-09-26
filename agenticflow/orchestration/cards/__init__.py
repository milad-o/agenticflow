"""
Card System for Agent Framework

This module provides a discoverable card-based system for agents, tools, and resources.
Cards enable intelligent matching and delegation in multi-agent systems.
"""

from .base_card import BaseCard, CardType, CardMetadata, MatchingCriteria
from .tool_card import ToolCard, ToolAnalyzer
from .resource_card import ResourceCard
from .agent_card import AgentCard, AgentPerformanceProfile, AgentAnalyzer
from .registry import CardRegistry, RegistryStats
# from .factory import CardFactory  # Will be created if needed

__all__ = [
    # Base components
    "BaseCard", "CardType", "CardMetadata", "MatchingCriteria",
    
    # Specific card types
    "ToolCard", "ToolAnalyzer",
    "ResourceCard", 
    "AgentCard", "AgentPerformanceProfile", "AgentAnalyzer",
    
    # Registry system
    "CardRegistry", "RegistryStats",
    # "CardFactory"  # Will be added when created
]
