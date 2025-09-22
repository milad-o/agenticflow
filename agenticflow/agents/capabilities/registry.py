from __future__ import annotations

from typing import Dict, Iterable, List, Set


class CapabilityRegistry:
    """In-memory capability registry mapping capabilities to agent IDs.

    Framework-agnostic registry to decouple capability assignment from Agent implementation.
    """

    def __init__(self) -> None:
        self._cap_to_agents: Dict[str, Set[str]] = {}
        self._agent_to_caps: Dict[str, Set[str]] = {}

    def register(self, agent_id: str, capabilities: Iterable[str]) -> None:
        caps = set(map(str, capabilities))
        self._agent_to_caps.setdefault(agent_id, set()).update(caps)
        for c in caps:
            self._cap_to_agents.setdefault(c, set()).add(agent_id)

    def unregister(self, agent_id: str) -> None:
        caps = self._agent_to_caps.pop(agent_id, set())
        for c in caps:
            s = self._cap_to_agents.get(c)
            if s:
                s.discard(agent_id)
                if not s:
                    self._cap_to_agents.pop(c, None)

    def agents_for(self, capability: str) -> List[str]:
        return sorted(self._cap_to_agents.get(capability, set()))

    def capabilities_for(self, agent_id: str) -> List[str]:
        return sorted(self._agent_to_caps.get(agent_id, set()))