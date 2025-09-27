"""
Flow Observer System
==================

Advanced observability and monitoring for AgenticFlow multi-agent systems.
"""

import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import threading
from .event_tracker import EventTracker, EventType


class FlowObserver:
    """Advanced observer for monitoring flow execution."""

    def __init__(self, event_tracker: EventTracker = None):
        self.event_tracker = event_tracker or EventTracker()
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.flow_state = {
            "status": "idle",
            "current_task": None,
            "workers": [],
            "start_time": None,
            "messages": [],
            "results": {}
        }
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()

    def register_callback(self, callback: Callable) -> None:
        """Register callback for real-time updates."""
        self._callbacks.append(callback)

    def _notify_callbacks(self, event_data: Dict[str, Any]) -> None:
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(event_data)
            except Exception as e:
                print(f"Callback error: {e}")

    def observe_flow_start(self, task: str, workers: List[str]) -> None:
        """Observe flow start."""
        with self._lock:
            self.flow_state.update({
                "status": "running",
                "current_task": task,
                "workers": workers,
                "start_time": datetime.now(),
                "messages": [],
                "results": {}
            })

        event_id = self.event_tracker.track_flow_start(task, workers)

        self._notify_callbacks({
            "type": "flow_start",
            "event_id": event_id,
            "task": task,
            "workers": workers,
            "timestamp": datetime.now().isoformat()
        })

    def observe_flow_end(self, success: bool, result: Dict[str, Any], duration_ms: float) -> None:
        """Observe flow end."""
        with self._lock:
            self.flow_state.update({
                "status": "completed" if success else "failed",
                "results": result
            })

        event_id = self.event_tracker.track_flow_end(success, result, duration_ms)

        self._notify_callbacks({
            "type": "flow_end",
            "event_id": event_id,
            "success": success,
            "result": result,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        })

    def observe_agent_activity(self, agent_name: str, activity_type: str,
                             details: Dict[str, Any] = None) -> None:
        """Observe agent activity."""
        with self._lock:
            if agent_name not in self.active_agents:
                self.active_agents[agent_name] = {
                    "status": "active",
                    "activities": [],
                    "start_time": datetime.now(),
                    "tool_calls": 0,
                    "errors": 0
                }

            self.active_agents[agent_name]["activities"].append({
                "type": activity_type,
                "timestamp": datetime.now(),
                "details": details or {}
            })

        # Track specific events
        if activity_type == "tool_call":
            tool_name = details.get("tool_name", "unknown") if details else "unknown"
            input_data = details.get("input_data", {}) if details else {}
            self.event_tracker.track_tool_call(tool_name, agent_name, input_data)

            with self._lock:
                self.active_agents[agent_name]["tool_calls"] += 1

        elif activity_type == "error":
            error_msg = details.get("error", "Unknown error") if details else "Unknown error"
            self.event_tracker.track_error(agent_name, "agent_error", error_msg, details)

            with self._lock:
                self.active_agents[agent_name]["errors"] += 1

        elif activity_type == "decision":
            decision = details.get("decision", "") if details else ""
            reasoning = details.get("reasoning", "") if details else ""
            options = details.get("options", []) if details else []
            self.event_tracker.track_decision(agent_name, decision, reasoning, options)

        self._notify_callbacks({
            "type": "agent_activity",
            "agent_name": agent_name,
            "activity_type": activity_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def observe_agent_reflection(self, agent_name: str, reflection: Dict[str, Any]) -> None:
        """Observe agent reflection/self-assessment."""
        with self._lock:
            if agent_name not in self.active_agents:
                self.active_agents[agent_name] = {
                    "status": "active",
                    "activities": [],
                    "start_time": datetime.now(),
                    "tool_calls": 0,
                    "errors": 0
                }

            self.active_agents[agent_name]["reflection"] = reflection

        # Track reflection event
        from .event_tracker import AgentEvent, EventType
        reflection_event = AgentEvent(
            event_type=EventType.AGENT_REFLECTION,
            source=agent_name,
            agent_name=agent_name,
            reflection=reflection
        )
        self.event_tracker.track_event(reflection_event)

        self._notify_callbacks({
            "type": "agent_reflection",
            "agent_name": agent_name,
            "reflection": reflection,
            "timestamp": datetime.now().isoformat()
        })

    def observe_state_update(self, state_data: Dict[str, Any]) -> None:
        """Observe flow state updates."""
        with self._lock:
            if "messages" in state_data:
                self.flow_state["messages"] = state_data["messages"]

        from .event_tracker import FlowEvent, EventType
        state_event = FlowEvent(
            event_type=EventType.STATE_UPDATE,
            source="flow",
            data=state_data
        )
        self.event_tracker.track_event(state_event)

        self._notify_callbacks({
            "type": "state_update",
            "state_data": state_data,
            "timestamp": datetime.now().isoformat()
        })

    def get_real_time_status(self) -> Dict[str, Any]:
        """Get current real-time status."""
        with self._lock:
            return {
                "flow_state": self.flow_state.copy(),
                "active_agents": self.active_agents.copy(),
                "metrics": self.event_tracker.get_metrics(),
                "recent_events": [
                    event.to_dict() for event in
                    self.event_tracker.get_events(limit=10)
                ]
            }

    def get_agent_insights(self, agent_name: str) -> Dict[str, Any]:
        """Get detailed insights for specific agent."""
        timeline = self.event_tracker.get_agent_timeline(agent_name)

        with self._lock:
            agent_data = self.active_agents.get(agent_name, {})

        return {
            "agent_name": agent_name,
            "status": agent_data.get("status", "unknown"),
            "activities": agent_data.get("activities", []),
            "timeline": timeline,
            "reflection": agent_data.get("reflection", {}),
            "stats": {
                "tool_calls": agent_data.get("tool_calls", 0),
                "errors": agent_data.get("errors", 0),
                "start_time": agent_data.get("start_time"),
                "active_duration": (
                    datetime.now() - agent_data["start_time"]
                ).total_seconds() if agent_data.get("start_time") else 0
            }
        }

    def get_flow_analytics(self) -> Dict[str, Any]:
        """Get comprehensive flow analytics."""
        metrics = self.event_tracker.get_metrics()
        tool_usage = self.event_tracker.get_tool_usage()

        with self._lock:
            flow_state = self.flow_state.copy()
            active_agents = self.active_agents.copy()

        # Calculate performance metrics
        total_agents = len(active_agents)
        total_tool_calls = sum(agent.get("tool_calls", 0) for agent in active_agents.values())
        total_errors = sum(agent.get("errors", 0) for agent in active_agents.values())

        success_rate = (
            (total_tool_calls - total_errors) / total_tool_calls * 100
            if total_tool_calls > 0 else 100
        )

        return {
            "flow_state": flow_state,
            "performance": {
                "total_agents": total_agents,
                "total_tool_calls": total_tool_calls,
                "total_errors": total_errors,
                "success_rate": success_rate,
                "events_tracked": metrics.get("total_events", 0)
            },
            "tool_usage": tool_usage,
            "agent_summary": {
                agent_name: {
                    "status": agent_data.get("status"),
                    "tool_calls": agent_data.get("tool_calls", 0),
                    "errors": agent_data.get("errors", 0)
                }
                for agent_name, agent_data in active_agents.items()
            }
        }