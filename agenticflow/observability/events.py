"""Event type definitions for observability."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union
from datetime import datetime
import uuid


@dataclass
class Event:
    """Base event class."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: str = ""
    flow_id: Optional[str] = None
    agent_name: Optional[str] = None
    team_name: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "flow_id": self.flow_id,
            "agent_name": self.agent_name,
            "team_name": self.team_name,
            "data": self.data
        }


# Flow Events
@dataclass
class FlowStarted(Event):
    """Flow execution started."""
    event_type: str = "flow_started"
    flow_name: str = ""
    message: str = ""
    
    def __post_init__(self):
        self.data.update({
            "flow_name": self.flow_name,
            "message": self.message
        })


@dataclass
class FlowCompleted(Event):
    """Flow execution completed."""
    event_type: str = "flow_completed"
    flow_name: str = ""
    duration_ms: float = 0.0
    total_messages: int = 0
    
    def __post_init__(self):
        self.data.update({
            "flow_name": self.flow_name,
            "duration_ms": self.duration_ms,
            "total_messages": self.total_messages
        })


@dataclass
class FlowError(Event):
    """Flow execution error."""
    event_type: str = "flow_error"
    flow_name: str = ""
    error_message: str = ""
    error_type: str = ""
    stack_trace: Optional[str] = None
    
    def __post_init__(self):
        self.data.update({
            "flow_name": self.flow_name,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace
        })


# Agent Events
@dataclass
class AgentStarted(Event):
    """Agent execution started."""
    event_type: str = "agent_started"
    agent_type: str = ""
    tools: list = field(default_factory=list)
    
    def __post_init__(self):
        self.data.update({
            "agent_type": self.agent_type,
            "tools": [tool.name if hasattr(tool, 'name') else str(tool) for tool in self.tools]
        })


@dataclass
class AgentCompleted(Event):
    """Agent execution completed."""
    event_type: str = "agent_completed"
    agent_type: str = ""
    duration_ms: float = 0.0
    tools_used: int = 0
    
    def __post_init__(self):
        self.data.update({
            "agent_type": self.agent_type,
            "duration_ms": self.duration_ms,
            "tools_used": self.tools_used
        })


@dataclass
class AgentReasoning(Event):
    """Agent reasoning and decision process."""
    event_type: str = "agent_reasoning"
    reasoning: str = ""
    decision: str = ""
    confidence: Optional[float] = None
    
    def __post_init__(self):
        self.data.update({
            "reasoning": self.reasoning,
            "decision": self.decision,
            "confidence": self.confidence
        })


@dataclass
class AgentError(Event):
    """Agent execution error."""
    event_type: str = "agent_error"
    agent_type: str = ""
    error_message: str = ""
    error_type: str = ""
    stack_trace: Optional[str] = None
    
    def __post_init__(self):
        self.data.update({
            "agent_type": self.agent_type,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace
        })


@dataclass
class AgentThinking(Event):
    """Agent is thinking/reasoning."""
    event_type: str = "agent_thinking"
    thinking_process: str = ""
    current_step: str = ""
    
    def __post_init__(self):
        self.data.update({
            "thinking_process": self.thinking_process,
            "current_step": self.current_step
        })


@dataclass
class AgentWorking(Event):
    """Agent is actively working on a task."""
    event_type: str = "agent_working"
    task_description: str = ""
    progress: Optional[float] = None
    
    def __post_init__(self):
        self.data.update({
            "task_description": self.task_description,
            "progress": self.progress
        })


# Tool Events
@dataclass
class ToolExecuted(Event):
    """Tool execution started."""
    event_type: str = "tool_executed"
    tool_name: str = ""
    tool_type: str = ""
    
    def __post_init__(self):
        self.data.update({
            "tool_name": self.tool_name,
            "tool_type": self.tool_type
        })


@dataclass
class ToolArgs(Event):
    """Tool arguments."""
    event_type: str = "tool_args"
    tool_name: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.data.update({
            "tool_name": self.tool_name,
            "args": self.args
        })


@dataclass
class ToolResult(Event):
    """Tool execution result."""
    event_type: str = "tool_result"
    tool_name: str = ""
    result: Any = ""
    duration_ms: float = 0.0
    success: bool = True
    
    def __post_init__(self):
        self.data.update({
            "tool_name": self.tool_name,
            "result": str(self.result)[:500] + "..." if len(str(self.result)) > 500 else str(self.result),
            "duration_ms": self.duration_ms,
            "success": self.success
        })


@dataclass
class ToolError(Event):
    """Tool execution error."""
    event_type: str = "tool_error"
    tool_name: str = ""
    error_message: str = ""
    error_type: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.data.update({
            "tool_name": self.tool_name,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "args": self.args
        })


# Message Events
@dataclass
class MessageRouted(Event):
    """Message routed between components."""
    event_type: str = "message_routed"
    from_component: str = ""
    to_component: str = ""
    message_content: str = ""
    routing_reason: str = ""
    
    def __post_init__(self):
        self.data.update({
            "from_component": self.from_component,
            "to_component": self.to_component,
            "message_content": self.message_content[:200] + "..." if len(self.message_content) > 200 else self.message_content,
            "routing_reason": self.routing_reason
        })


@dataclass
class MessageReceived(Event):
    """Message received by component."""
    event_type: str = "message_received"
    component_name: str = ""
    message_content: str = ""
    message_type: str = ""
    
    def __post_init__(self):
        self.data.update({
            "component_name": self.component_name,
            "message_content": self.message_content[:200] + "..." if len(self.message_content) > 200 else self.message_content,
            "message_type": self.message_type
        })


# Team Events
@dataclass
class TeamSupervisorCalled(Event):
    """Team supervisor called."""
    event_type: str = "team_supervisor_called"
    supervisor_name: str = ""
    team_agents: list = field(default_factory=list)
    decision: str = ""
    
    def __post_init__(self):
        self.data.update({
            "supervisor_name": self.supervisor_name,
            "team_agents": self.team_agents,
            "decision": self.decision
        })


@dataclass
class TeamAgentCalled(Event):
    """Team agent called by supervisor."""
    event_type: str = "team_agent_called"
    team_name: str = ""
    supervisor_decision: str = ""
    
    def __post_init__(self):
        self.data.update({
            "agent_name": self.agent_name,
            "team_name": self.team_name,
            "supervisor_decision": self.supervisor_decision
        })


# Custom Events
@dataclass
class CustomEvent(Event):
    """User-defined custom event."""
    event_type: str = "custom_event"
    custom_type: str = ""
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.data.update({
            "custom_type": self.custom_type,
            "custom_data": self.custom_data
        })
