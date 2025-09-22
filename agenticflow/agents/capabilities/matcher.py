from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional

from .registry import CapabilityRegistry


class CapabilityMatcher(ABC):
    @abstractmethod
    async def find_agent_for(self, required_capability: str) -> Optional[str]:
        ...


class DictCapabilityMatcher(CapabilityMatcher):
    def __init__(self, mapping: Dict[str, str] | None = None):
        self.mapping = mapping or {}

    async def find_agent_for(self, required_capability: str) -> Optional[str]:
        return self.mapping.get(required_capability)

    def set(self, capability: str, agent_id: str) -> None:
        self.mapping[capability] = agent_id


class RegistryCapabilityMatcher(CapabilityMatcher):
    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    async def find_agent_for(self, required_capability: str) -> Optional[str]:
        agents = self.registry.agents_for(required_capability)
        return agents[0] if agents else None
