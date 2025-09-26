"""
Card Registry

Centralized registry for all discoverable cards in the system.
Provides intelligent matching, discovery, and coordination capabilities.
"""

from typing import Dict, List, Any, Set, Optional, Union
from dataclasses import dataclass, field

from .base_card import BaseCard, CardType, MatchingCriteria
from .tool_card import ToolCard
from .resource_card import ResourceCard
from .agent_card import AgentCard


@dataclass
class RegistryStats:
    """Statistics about the card registry."""
    total_cards: int = 0
    tool_cards: int = 0
    resource_cards: int = 0
    agent_cards: int = 0
    available_cards: int = 0
    last_updated: Optional[str] = None


class CardRegistry:
    """
    Centralized registry for all discoverable cards in the system.
    
    Provides intelligent matching, discovery, and coordination capabilities
    for tools, resources, and agents.
    """
    
    def __init__(self):
        self.tool_cards: Dict[str, ToolCard] = {}
        self.resource_cards: Dict[str, ResourceCard] = {}
        self.agent_cards: Dict[str, AgentCard] = {}
        
        # Performance optimization
        self._capability_index: Dict[str, Set[str]] = {}
        self._tag_index: Dict[str, Set[str]] = {}
        self._type_index: Dict[CardType, Set[str]] = {
            CardType.TOOL: set(),
            CardType.RESOURCE: set(),
            CardType.AGENT: set()
        }
        
        # Usage tracking
        self._usage_stats: Dict[str, int] = {}
        self._match_history: List[Dict[str, Any]] = []
    
    def register_tool_card(self, card: ToolCard) -> None:
        """Register a tool card."""
        self.tool_cards[card.card_id] = card
        self._update_indexes(card)
    
    def register_resource_card(self, card: ResourceCard) -> None:
        """Register a resource card."""
        self.resource_cards[card.card_id] = card
        self._update_indexes(card)
    
    def register_agent_card(self, card: AgentCard) -> None:
        """Register an agent card."""
        self.agent_cards[card.card_id] = card
        self._update_indexes(card)
    
    def register_card(self, card: BaseCard) -> None:
        """Register any type of card."""
        if isinstance(card, ToolCard):
            self.register_tool_card(card)
        elif isinstance(card, ResourceCard):
            self.register_resource_card(card)
        elif isinstance(card, AgentCard):
            self.register_agent_card(card)
        else:
            raise ValueError(f"Unknown card type: {type(card)}")
    
    def _update_indexes(self, card: BaseCard) -> None:
        """Update performance indexes when a card is added."""
        # Type index
        self._type_index[card.card_type].add(card.card_id)
        
        # Capability index
        capabilities = card.get_capabilities() if hasattr(card, 'get_capabilities') else set()
        for capability in capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = set()
            self._capability_index[capability].add(card.card_id)
        
        # Tag index
        if card.metadata and card.metadata.tags:
            for tag in card.metadata.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(card.card_id)
    
    def find_by_capability(self, capability: str) -> List[BaseCard]:
        """Find all cards that provide a specific capability."""
        card_ids = self._capability_index.get(capability, set())
        cards = []
        
        for card_id in card_ids:
            card = self.get_card(card_id)
            if card:
                cards.append(card)
        
        return cards
    
    def find_by_tag(self, tag: str) -> List[BaseCard]:
        """Find all cards with a specific tag."""
        card_ids = self._tag_index.get(tag, set())
        cards = []
        
        for card_id in card_ids:
            card = self.get_card(card_id)
            if card:
                cards.append(card)
        
        return cards
    
    def find_by_type(self, card_type: CardType) -> List[BaseCard]:
        """Find all cards of a specific type."""
        card_ids = self._type_index.get(card_type, set())
        cards = []
        
        for card_id in card_ids:
            card = self.get_card(card_id)
            if card:
                cards.append(card)
        
        return cards
    
    def get_card(self, card_id: str) -> Optional[BaseCard]:
        """Get a card by ID."""
        if card_id in self.tool_cards:
            return self.tool_cards[card_id]
        elif card_id in self.resource_cards:
            return self.resource_cards[card_id]
        elif card_id in self.agent_cards:
            return self.agent_cards[card_id]
        return None
    
    def match_cards(self, criteria: MatchingCriteria, limit: int = 10) -> List[BaseCard]:
        """Find cards that match the given criteria, sorted by match score."""
        candidates = []
        
        # Get candidate cards based on type or capabilities
        if criteria.card_types:
            for card_type in criteria.card_types:
                candidates.extend(self.find_by_type(card_type))
        else:
            # Get all cards
            candidates.extend(self.tool_cards.values())
            candidates.extend(self.resource_cards.values())
            candidates.extend(self.agent_cards.values())
        
        # Calculate match scores
        scored_cards = []
        for card in candidates:
            if hasattr(card, 'calculate_match_score'):
                score = card.calculate_match_score(criteria)
                if score > 0:
                    scored_cards.append((card, score))
        
        # Sort by score and return top matches
        scored_cards.sort(key=lambda x: x[1], reverse=True)
        
        # Record match in history
        self._match_history.append({
            "criteria": criteria.to_dict() if hasattr(criteria, 'to_dict') else str(criteria),
            "results_count": len(scored_cards),
            "top_score": scored_cards[0][1] if scored_cards else 0
        })
        
        return [card for card, score in scored_cards[:limit]]
    
    def get_available_agents(self) -> List[AgentCard]:
        """Get all available agent cards for delegation."""
        return [
            card for card in self.agent_cards.values()
            if card.is_available_for_delegation()
        ]
    
    def get_tool_cards(self) -> List[ToolCard]:
        """Get all tool cards."""
        return list(self.tool_cards.values())
    
    def get_resource_cards(self) -> List[ResourceCard]:
        """Get all resource cards."""
        return list(self.resource_cards.values())
    
    def get_agent_cards(self) -> List[AgentCard]:
        """Get all agent cards."""
        return list(self.agent_cards.values())
    
    def remove_card(self, card_id: str) -> bool:
        """Remove a card from the registry."""
        removed = False
        
        if card_id in self.tool_cards:
            del self.tool_cards[card_id]
            removed = True
        elif card_id in self.resource_cards:
            del self.resource_cards[card_id]
            removed = True
        elif card_id in self.agent_cards:
            del self.agent_cards[card_id]
            removed = True
        
        if removed:
            self._rebuild_indexes()
        
        return removed
    
    def _rebuild_indexes(self) -> None:
        """Rebuild performance indexes."""
        self._capability_index.clear()
        self._tag_index.clear()
        for card_type in self._type_index:
            self._type_index[card_type].clear()
        
        # Rebuild indexes for all cards
        for card in self.tool_cards.values():
            self._update_indexes(card)
        for card in self.resource_cards.values():
            self._update_indexes(card)
        for card in self.agent_cards.values():
            self._update_indexes(card)
    
    def get_stats(self) -> RegistryStats:
        """Get statistics about the registry."""
        available_count = 0
        
        # Count available cards
        for card in self.tool_cards.values():
            if getattr(card, 'available', True):
                available_count += 1
        
        for card in self.resource_cards.values():
            if card.is_available():
                available_count += 1
        
        for card in self.agent_cards.values():
            if card.is_available_for_delegation():
                available_count += 1
        
        total = len(self.tool_cards) + len(self.resource_cards) + len(self.agent_cards)
        
        return RegistryStats(
            total_cards=total,
            tool_cards=len(self.tool_cards),
            resource_cards=len(self.resource_cards),
            agent_cards=len(self.agent_cards),
            available_cards=available_count
        )
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get usage statistics for cards."""
        return self._usage_stats.copy()
    
    def record_usage(self, card_id: str) -> None:
        """Record usage of a card."""
        self._usage_stats[card_id] = self._usage_stats.get(card_id, 0) + 1
    
    def clear(self) -> None:
        """Clear all cards from the registry."""
        self.tool_cards.clear()
        self.resource_cards.clear()
        self.agent_cards.clear()
        self._rebuild_indexes()
        self._usage_stats.clear()
        self._match_history.clear()
    
    def export_cards(self) -> Dict[str, Any]:
        """Export all cards to a dictionary."""
        return {
            "tool_cards": [card.to_dict() for card in self.tool_cards.values()],
            "resource_cards": [card.to_dict() for card in self.resource_cards.values()],
            "agent_cards": [card.to_dict() for card in self.agent_cards.values()],
            "stats": self.get_stats().__dict__,
            "usage_stats": self.get_usage_stats()
        }
    
    def create_matching_criteria(
        self,
        required_capabilities: Optional[Set[str]] = None,
        preferred_capabilities: Optional[Set[str]] = None,
        excluded_capabilities: Optional[Set[str]] = None,
        card_types: Optional[List[CardType]] = None,
        **kwargs
    ) -> MatchingCriteria:
        """Create matching criteria for card discovery."""
        return MatchingCriteria(
            required_capabilities=required_capabilities or set(),
            preferred_capabilities=preferred_capabilities or set(),
            excluded_capabilities=excluded_capabilities or set(),
            card_types=card_types,
            **kwargs
        )