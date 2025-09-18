"""
Agent-to-Agent (A2A) Communication Handler for AgenticFlow.

Provides basic A2A communication capabilities without external SDK dependencies.
This is a simplified implementation for internal agent communication.
"""

import asyncio
import json
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict

import structlog

logger = structlog.get_logger(__name__)


class MessageType(str, Enum):
    """Types of A2A messages."""
    DIRECT = "direct"
    BROADCAST = "broadcast"
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class MessagePriority(str, Enum):
    """Message priorities."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class A2AMessage:
    """A2A message structure."""
    
    id: str
    type: MessageType
    sender_id: str
    recipient_id: Optional[str]  # None for broadcast
    content: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = 0.0
    expires_at: Optional[float] = None
    correlation_id: Optional[str] = None  # For request/response pairing
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """Create message from dictionary."""
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class A2AHandler:
    """
    Simple A2A communication handler for internal agent communication.
    
    This implementation provides basic messaging capabilities without
    requiring external SDK dependencies.
    """
    
    def __init__(
        self,
        agent_id: str,
        message_timeout: int = 30,
        max_message_size: int = 1024 * 1024,
        max_retries: int = 3
    ):
        """Initialize A2A handler."""
        self.agent_id = agent_id
        self.message_timeout = message_timeout
        self.max_message_size = max_message_size
        self.max_retries = max_retries
        self.logger = logger.bind(component="a2a_handler", agent_id=agent_id)
        
        # Message storage and routing
        self._message_handlers: Dict[MessageType, List[Callable]] = {
            MessageType.DIRECT: [],
            MessageType.BROADCAST: [],
            MessageType.REQUEST: [],
            MessageType.RESPONSE: [],
            MessageType.NOTIFICATION: []
        }
        
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        
        # Simple in-memory message registry (shared across instances)
        if not hasattr(A2AHandler, '_global_message_bus'):
            A2AHandler._global_message_bus = {}
            A2AHandler._agent_registry = {}
    
    async def start(self) -> None:
        """Start the A2A handler."""
        if self._running:
            return
        
        self.logger.info("Starting A2A communication handler")
        
        # Register this agent
        A2AHandler._agent_registry[self.agent_id] = self
        
        # Start message processing
        self._running = True
        self._worker_task = asyncio.create_task(self._message_worker())
        
        self.logger.info("A2A handler started successfully")
    
    async def stop(self) -> None:
        """Stop the A2A handler."""
        if not self._running:
            return
        
        self.logger.info("Stopping A2A communication handler")
        
        self._running = False
        
        # Cancel worker task
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Unregister agent
        A2AHandler._agent_registry.pop(self.agent_id, None)
        
        self.logger.info("A2A handler stopped")
    
    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[A2AMessage], None]
    ) -> None:
        """Register a message handler for a specific message type."""
        self._message_handlers[message_type].append(handler)
        self.logger.debug(f"Registered handler for {message_type}")
    
    async def send_message(
        self,
        message: A2AMessage,
        wait_for_response: bool = False,
        timeout: Optional[int] = None
    ) -> Optional[A2AMessage]:
        """Send an A2A message."""
        if not self._running:
            raise RuntimeError("A2A handler is not running")
        
        # Validate message size
        message_size = len(json.dumps(message.to_dict()).encode('utf-8'))
        if message_size > self.max_message_size:
            raise ValueError(f"Message size {message_size} exceeds limit {self.max_message_size}")
        
        self.logger.debug(f"Sending message {message.id} to {message.recipient_id or 'broadcast'}")
        
        # Set expiration if not set
        if message.expires_at is None:
            message.expires_at = time.time() + (timeout or self.message_timeout)
        
        # If waiting for response, set up future
        response_future = None
        if wait_for_response and message.type == MessageType.REQUEST:
            response_future = asyncio.Future()
            self._pending_requests[message.id] = response_future
        
        # Route message
        await self._route_message(message)
        
        # Wait for response if requested
        if response_future:
            try:
                response = await asyncio.wait_for(
                    response_future, 
                    timeout=timeout or self.message_timeout
                )
                return response
            except asyncio.TimeoutError:
                self.logger.warning(f"Message {message.id} timed out waiting for response")
                self._pending_requests.pop(message.id, None)
                return None
        
        return None
    
    async def send_direct_message(
        self,
        recipient_id: str,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> None:
        """Send a direct message to another agent."""
        message = A2AMessage(
            id=str(uuid.uuid4()),
            type=MessageType.DIRECT,
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            content=content,
            priority=priority
        )
        await self.send_message(message)
    
    async def broadcast_message(
        self,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> None:
        """Broadcast a message to all agents."""
        message = A2AMessage(
            id=str(uuid.uuid4()),
            type=MessageType.BROADCAST,
            sender_id=self.agent_id,
            recipient_id=None,
            content=content,
            priority=priority
        )
        await self.send_message(message)
    
    async def send_request(
        self,
        recipient_id: str,
        content: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Optional[A2AMessage]:
        """Send a request and wait for response."""
        message = A2AMessage(
            id=str(uuid.uuid4()),
            type=MessageType.REQUEST,
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            content=content,
            priority=MessagePriority.NORMAL
        )
        return await self.send_message(message, wait_for_response=True, timeout=timeout)
    
    async def send_response(
        self,
        request_message: A2AMessage,
        content: Dict[str, Any]
    ) -> None:
        """Send a response to a request message."""
        response = A2AMessage(
            id=str(uuid.uuid4()),
            type=MessageType.RESPONSE,
            sender_id=self.agent_id,
            recipient_id=request_message.sender_id,
            content=content,
            correlation_id=request_message.id
        )
        await self.send_message(response)
    
    async def _route_message(self, message: A2AMessage) -> None:
        """Route message to appropriate recipients."""
        if message.type == MessageType.BROADCAST:
            # Send to all registered agents except sender
            for agent_id, handler in A2AHandler._agent_registry.items():
                if agent_id != message.sender_id:
                    await handler._receive_message(message)
        else:
            # Direct message to specific recipient
            if message.recipient_id in A2AHandler._agent_registry:
                handler = A2AHandler._agent_registry[message.recipient_id]
                await handler._receive_message(message)
            else:
                self.logger.warning(f"Recipient {message.recipient_id} not found")
    
    async def _receive_message(self, message: A2AMessage) -> None:
        """Receive and queue a message for processing."""
        if message.is_expired():
            self.logger.debug(f"Ignoring expired message {message.id}")
            return
        
        await self._message_queue.put(message)
    
    async def _message_worker(self) -> None:
        """Process incoming messages."""
        while self._running:
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                
                # Process the message
                await self._process_message(message)
                
            except asyncio.TimeoutError:
                # Continue loop - this is normal
                continue
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    async def _process_message(self, message: A2AMessage) -> None:
        """Process a received message."""
        self.logger.debug(f"Processing message {message.id} from {message.sender_id}")
        
        # Handle responses to pending requests
        if message.type == MessageType.RESPONSE and message.correlation_id:
            if message.correlation_id in self._pending_requests:
                future = self._pending_requests.pop(message.correlation_id)
                if not future.done():
                    future.set_result(message)
                return
        
        # Call registered handlers
        handlers = self._message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                self.logger.error(f"Error in message handler: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get A2A handler statistics."""
        return {
            "agent_id": self.agent_id,
            "running": self._running,
            "pending_requests": len(self._pending_requests),
            "queued_messages": self._message_queue.qsize(),
            "registered_handlers": {
                msg_type.value: len(handlers) 
                for msg_type, handlers in self._message_handlers.items()
            }
        }


# Convenience functions for creating messages
def create_direct_message(
    sender_id: str,
    recipient_id: str,
    content: Dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL
) -> A2AMessage:
    """Create a direct message."""
    return A2AMessage(
        id=str(uuid.uuid4()),
        type=MessageType.DIRECT,
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=content,
        priority=priority
    )


def create_broadcast_message(
    sender_id: str,
    content: Dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL
) -> A2AMessage:
    """Create a broadcast message."""
    return A2AMessage(
        id=str(uuid.uuid4()),
        type=MessageType.BROADCAST,
        sender_id=sender_id,
        recipient_id=None,
        content=content,
        priority=priority
    )