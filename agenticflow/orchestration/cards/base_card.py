"""
Base Card Interface

Provides foundational card interface that integrates with existing agenticflow patterns.
Cards are metadata layers that enhance existing registry and orchestration systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from enum import Enum

from ...core.config import AgentConfig


class CardType(Enum):
    """Types of cards in the system."""
    TOOL = "tool"
    RESOURCE = "resource" 
    AGENT = "agent"
    CAPABILITY = "capability"
    SERVICE = "service"


class MatchingStrategy(Enum):
    """Strategies for card matching."""
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    HEURISTIC = "heuristic"


@dataclass
class CardMetadata:
    """Standard metadata for all cards."""
    created_at: float = field(default_factory=lambda: __import__('time').time())
    updated_at: float = field(default_factory=lambda: __import__('time').time())
    version: str = "1.0.0"
    source: str = "auto_generated"
    confidence: float = 1.0
    tags: Set[str] = field(default_factory=set)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchingCriteria:
    """Criteria used for card matching."""
    required_capabilities: Set[str] = field(default_factory=set)
    preferred_capabilities: Set[str] = field(default_factory=set)
    excluded_capabilities: Set[str] = field(default_factory=set)
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    resource_constraints: Dict[str, Any] = field(default_factory=dict)
    matching_strategy: MatchingStrategy = MatchingStrategy.HEURISTIC


class BaseCard(ABC):
    """
    Base class for all discoverable cards in the system.
    
    Cards provide enhanced metadata and matching capabilities for existing
    framework components (agents, tools, resources) without replacing them.
    """
    
    def __init__(
        self,
        card_id: str,
        name: str,
        description: str,
        card_type: CardType,
        capabilities: List[str] = None,
        metadata: CardMetadata = None
    ):
        self.card_id = card_id
        self.name = name
        self.description = description
        self.card_type = card_type
        self.capabilities = capabilities or []
        self.metadata = metadata or CardMetadata()
        
        # Matching and availability
        self._available = True
        self._match_score = 0.0
        self._usage_stats = {
            "invocation_count": 0,
            "success_count": 0,
            "avg_execution_time": 0.0,
            "last_used": None
        }
    
    @property
    def available(self) -> bool:
        """Check if this card is available for matching."""
        return self._available
    
    @available.setter
    def available(self, value: bool):
        """Set availability status."""
        self._available = value
    
    @property
    def match_score(self) -> float:
        """Get current match score (set during matching process)."""
        return self._match_score
    
    @match_score.setter
    def match_score(self, score: float):
        """Set match score during matching process."""
        self._match_score = max(0.0, min(1.0, score))
    
    @abstractmethod
    def calculate_match_score(self, criteria: MatchingCriteria) -> float:
        """
        Calculate how well this card matches the given criteria.
        
        Args:
            criteria: Matching criteria to evaluate against
            
        Returns:
            Match score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Set[str]:
        """
        Get all capabilities provided by this card.
        
        Returns:
            Set of capability strings
        """
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """
        Get dependencies required by this card.
        
        Returns:
            List of dependency identifiers
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate parameters for using this card.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if parameters are valid
        """
        pass
    
    def update_usage_stats(self, execution_time: float = None, success: bool = True):
        """Update usage statistics for this card."""
        self._usage_stats["invocation_count"] += 1
        if success:
            self._usage_stats["success_count"] += 1
        
        if execution_time is not None:
            # Update rolling average
            count = self._usage_stats["invocation_count"]
            current_avg = self._usage_stats["avg_execution_time"]
            self._usage_stats["avg_execution_time"] = (
                (current_avg * (count - 1) + execution_time) / count
            )
        
        self._usage_stats["last_used"] = __import__('time').time()
        self.metadata.updated_at = self._usage_stats["last_used"]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this card."""
        total_invocations = self._usage_stats["invocation_count"]
        success_rate = (
            self._usage_stats["success_count"] / total_invocations
            if total_invocations > 0 else 0.0
        )
        
        return {
            "success_rate": success_rate,
            "avg_execution_time": self._usage_stats["avg_execution_time"],
            "total_invocations": total_invocations,
            "last_used": self._usage_stats["last_used"]
        }
    
    def add_tag(self, tag: str):
        """Add a tag to this card."""
        self.metadata.tags.add(tag)
        self.metadata.updated_at = __import__('time').time()
    
    def remove_tag(self, tag: str):
        """Remove a tag from this card."""
        self.metadata.tags.discard(tag)
        self.metadata.updated_at = __import__('time').time()
    
    def has_tag(self, tag: str) -> bool:
        """Check if card has a specific tag."""
        return tag in self.metadata.tags
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert card to dictionary representation."""
        return {
            "card_id": self.card_id,
            "name": self.name,
            "description": self.description,
            "card_type": self.card_type.value,
            "capabilities": self.capabilities,
            "available": self.available,
            "match_score": self.match_score,
            "metadata": {
                "created_at": self.metadata.created_at,
                "updated_at": self.metadata.updated_at,
                "version": self.metadata.version,
                "source": self.metadata.source,
                "confidence": self.metadata.confidence,
                "tags": list(self.metadata.tags),
                "custom_attributes": self.metadata.custom_attributes
            },
            "performance_metrics": self.get_performance_metrics()
        }
    
    def __str__(self) -> str:
        return f"{self.card_type.value.title()}Card({self.name})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(card_id='{self.card_id}', name='{self.name}')"