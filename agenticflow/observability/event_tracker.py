"""
Event Tracking System for AgenticFlow
====================================

Comprehensive event tracking for multi-agent workflows.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import threading
import json


class EventType(Enum):
    """Types of events in the flow."""
    FLOW_START = "flow_start"
    FLOW_END = "flow_end"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_REFLECTION = "agent_reflection"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    STATE_UPDATE = "state_update"
    ERROR = "error"
    DECISION = "decision"
    COORDINATION = "coordination"


@dataclass
class FlowEvent:
    """Base event class for all flow events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: EventType = EventType.FLOW_START
    source: str = "flow"
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "source": self.source,
            "data": self.data,
            "duration_ms": self.duration_ms
        }


@dataclass
class AgentEvent(FlowEvent):
    """Agent-specific event."""
    agent_name: str = ""
    agent_type: str = ""
    task: str = ""
    status: str = "running"
    capabilities: List[str] = field(default_factory=list)
    reflection: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "task": self.task,
            "status": self.status,
            "capabilities": self.capabilities,
            "reflection": self.reflection
        })
        return base


@dataclass
class ToolEvent(FlowEvent):
    """Tool call event."""
    tool_name: str = ""
    agent_name: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "tool_name": self.tool_name,
            "agent_name": self.agent_name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "success": self.success,
            "error_message": self.error_message
        })
        return base


class EventTracker:
    """Event tracking system for AgenticFlow."""

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events: List[FlowEvent] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.metrics: Dict[str, Any] = {
            "total_events": 0,
            "agent_counts": {},
            "tool_counts": {},
            "error_count": 0,
            "start_time": None,
            "end_time": None
        }
        self._lock = threading.Lock()

    def track_event(self, event: FlowEvent) -> None:
        """Track a new event."""
        with self._lock:
            self.events.append(event)

            # Maintain max events limit
            if len(self.events) > self.max_events:
                self.events.pop(0)

            # Update metrics
            self.metrics["total_events"] += 1

            if isinstance(event, AgentEvent):
                agent_type = event.agent_type or "unknown"
                self.metrics["agent_counts"][agent_type] = \
                    self.metrics["agent_counts"].get(agent_type, 0) + 1

            if isinstance(event, ToolEvent):
                tool_name = event.tool_name or "unknown"
                self.metrics["tool_counts"][tool_name] = \
                    self.metrics["tool_counts"].get(tool_name, 0) + 1

            if event.event_type == EventType.ERROR:
                self.metrics["error_count"] += 1

            if event.event_type == EventType.FLOW_START:
                self.metrics["start_time"] = event.timestamp

            if event.event_type == EventType.FLOW_END:
                self.metrics["end_time"] = event.timestamp

    def track_flow_start(self, task: str, workers: List[str]) -> str:
        """Track flow start event."""
        event = FlowEvent(
            event_type=EventType.FLOW_START,
            source="flow",
            data={
                "task": task,
                "workers": workers,
                "worker_count": len(workers)
            }
        )
        self.track_event(event)
        return event.event_id

    def track_flow_end(self, success: bool, result: Dict[str, Any], duration_ms: float) -> str:
        """Track flow end event."""
        event = FlowEvent(
            event_type=EventType.FLOW_END,
            source="flow",
            data={
                "success": success,
                "result_summary": str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
                "workers_used": result.get("workers_used", [])
            },
            duration_ms=duration_ms
        )
        self.track_event(event)
        return event.event_id

    def track_agent_start(self, agent_name: str, agent_type: str, task: str, capabilities: List[str]) -> str:
        """Track agent start event."""
        event = AgentEvent(
            event_type=EventType.AGENT_START,
            source=agent_name,
            agent_name=agent_name,
            agent_type=agent_type,
            task=task,
            status="started",
            capabilities=capabilities
        )
        self.track_event(event)
        return event.event_id

    def track_agent_end(self, agent_name: str, agent_type: str, status: str,
                       result: Dict[str, Any], duration_ms: float, reflection: Dict[str, Any] = None) -> str:
        """Track agent end event."""
        event = AgentEvent(
            event_type=EventType.AGENT_END,
            source=agent_name,
            agent_name=agent_name,
            agent_type=agent_type,
            status=status,
            data=result,
            duration_ms=duration_ms,
            reflection=reflection or {}
        )
        self.track_event(event)
        return event.event_id

    def track_tool_call(self, tool_name: str, agent_name: str, input_data: Dict[str, Any]) -> str:
        """Track tool call event."""
        event = ToolEvent(
            event_type=EventType.TOOL_CALL,
            source=agent_name,
            tool_name=tool_name,
            agent_name=agent_name,
            input_data=input_data
        )
        self.track_event(event)
        return event.event_id

    def track_tool_response(self, tool_name: str, agent_name: str, output_data: Dict[str, Any],
                          success: bool, error_message: str = "", duration_ms: float = None) -> str:
        """Track tool response event."""
        event = ToolEvent(
            event_type=EventType.TOOL_RESPONSE,
            source=agent_name,
            tool_name=tool_name,
            agent_name=agent_name,
            output_data=output_data,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        )
        self.track_event(event)
        return event.event_id

    def track_decision(self, agent_name: str, decision: str, reasoning: str, options: List[str]) -> str:
        """Track agent decision event."""
        event = FlowEvent(
            event_type=EventType.DECISION,
            source=agent_name,
            data={
                "decision": decision,
                "reasoning": reasoning,
                "options": options,
                "agent": agent_name
            }
        )
        self.track_event(event)
        return event.event_id

    def track_error(self, source: str, error_type: str, error_message: str, context: Dict[str, Any] = None) -> str:
        """Track error event."""
        event = FlowEvent(
            event_type=EventType.ERROR,
            source=source,
            data={
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {}
            }
        )
        self.track_event(event)
        return event.event_id

    def get_events(self, event_type: EventType = None, source: str = None,
                   limit: int = None) -> List[FlowEvent]:
        """Get events with optional filtering."""
        with self._lock:
            events = self.events.copy()

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if source:
            events = [e for e in events if e.source == source]

        # Apply limit
        if limit:
            events = events[-limit:]

        return events

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        with self._lock:
            metrics = self.metrics.copy()

            # Calculate duration if we have start/end times
            if metrics["start_time"] and metrics["end_time"]:
                duration = (metrics["end_time"] - metrics["start_time"]).total_seconds() * 1000
                metrics["total_duration_ms"] = duration

            # Add recent activity
            recent_events = self.events[-10:] if self.events else []
            metrics["recent_events"] = len(recent_events)

            return metrics

    def get_agent_timeline(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get timeline for specific agent."""
        agent_events = self.get_events(source=agent_name)
        return [event.to_dict() for event in agent_events]

    def get_tool_usage(self) -> Dict[str, Dict[str, Any]]:
        """Get tool usage statistics."""
        tool_events = self.get_events(event_type=EventType.TOOL_CALL)
        tool_stats = {}

        for event in tool_events:
            if isinstance(event, ToolEvent):
                tool_name = event.tool_name
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {
                        "call_count": 0,
                        "success_count": 0,
                        "error_count": 0,
                        "agents_using": set()
                    }

                tool_stats[tool_name]["call_count"] += 1
                tool_stats[tool_name]["agents_using"].add(event.agent_name)

                if event.success:
                    tool_stats[tool_name]["success_count"] += 1
                else:
                    tool_stats[tool_name]["error_count"] += 1

        # Convert sets to lists for JSON serialization
        for tool_name in tool_stats:
            tool_stats[tool_name]["agents_using"] = list(tool_stats[tool_name]["agents_using"])

        return tool_stats

    def export_events(self, filename: str = None) -> str:
        """Export events to JSON file."""
        if not filename:
            filename = f"agenticflow_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "metrics": self.get_metrics(),
            "events": [event.to_dict() for event in self.events]
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        return filename

    def clear_events(self) -> None:
        """Clear all events and reset metrics."""
        with self._lock:
            self.events.clear()
            self.metrics = {
                "total_events": 0,
                "agent_counts": {},
                "tool_counts": {},
                "error_count": 0,
                "start_time": None,
                "end_time": None
            }