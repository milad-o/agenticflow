"""State management for AgenticFlow framework."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4


class MessageType(Enum):
    """Types of messages in the agent communication system."""
    USER = "user"
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    ORCHESTRATOR = "orchestrator"
    SYSTEM = "system"
    ERROR = "error"


class AgentStatus(Enum):
    """Status of an agent."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentMessage:
    """Message exchanged between agents and supervisors."""
    id: UUID = field(default_factory=uuid4)
    type: MessageType = MessageType.AGENT
    sender: str = ""
    receiver: Optional[str] = None
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": str(self.id),
            "type": self.type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class FlowState:
    """Global state container for the entire flow."""
    id: UUID = field(default_factory=uuid4)
    messages: List[AgentMessage] = field(default_factory=list)
    agent_statuses: Dict[str, AgentStatus] = field(default_factory=dict)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    active_agents: Dict[str, str] = field(default_factory=dict)  # agent_id -> current_task
    workspace_path: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Async synchronization
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    async def add_message(self, message: AgentMessage) -> None:
        """Thread-safe message addition."""
        async with self._lock:
            self.messages.append(message)
            self.updated_at = datetime.now(timezone.utc)

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> None:
        """Thread-safe agent status update."""
        async with self._lock:
            self.agent_statuses[agent_id] = status
            self.updated_at = datetime.now(timezone.utc)

    async def set_context(self, key: str, value: Any) -> None:
        """Thread-safe context update."""
        async with self._lock:
            self.shared_context[key] = value
            self.updated_at = datetime.now(timezone.utc)

    async def get_context(self, key: str, default: Any = None) -> Any:
        """Thread-safe context retrieval."""
        async with self._lock:
            return self.shared_context.get(key, default)

    async def get_messages_for_agent(self, agent_id: str) -> List[AgentMessage]:
        """Get messages relevant to a specific agent."""
        async with self._lock:
            return [
                msg for msg in self.messages
                if msg.receiver == agent_id or msg.receiver is None or msg.sender == agent_id
            ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "id": str(self.id),
            "messages": [msg.to_dict() for msg in self.messages],
            "agent_statuses": {k: v.value for k, v in self.agent_statuses.items()},
            "shared_context": self.shared_context,
            "active_agents": self.active_agents,
            "workspace_path": self.workspace_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }