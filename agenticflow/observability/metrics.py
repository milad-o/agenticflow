"""Metrics collection and aggregation for AgenticFlow."""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class MetricEvent:
    """Individual metric event."""
    timestamp: datetime
    event_type: str
    entity_id: str
    entity_type: str  # 'flow', 'agent', 'supervisor', 'message'
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


class Metrics:
    """Metrics collection and aggregation system."""

    def __init__(self, max_events: int = 10000, retention_hours: int = 24):
        """Initialize metrics collector.

        Args:
            max_events: Maximum number of events to keep in memory
            retention_hours: Hours to retain metrics data
        """
        self.max_events = max_events
        self.retention_hours = retention_hours

        # Event storage
        self.events: deque = deque(maxlen=max_events)

        # Performance tracking
        self.start_times: Dict[str, float] = {}
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)

        # Agent-specific metrics
        self.agent_execution_times: Dict[str, List[float]] = defaultdict(list)
        self.agent_success_rates: Dict[str, Dict[str, int]] = defaultdict(lambda: {"success": 0, "error": 0})

    def record_event(
        self,
        event_type: str,
        entity_id: str,
        entity_type: str,
        value: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a metric event.

        Args:
            event_type: Type of event (e.g., 'execution_start', 'message_sent')
            entity_id: ID of the entity (agent, flow, etc.)
            entity_type: Type of entity ('flow', 'agent', 'supervisor', 'message')
            value: Event value
            metadata: Additional metadata
        """
        event = MetricEvent(
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            entity_id=entity_id,
            entity_type=entity_type,
            value=value,
            metadata=metadata or {},
        )

        self.events.append(event)
        self._cleanup_old_events()

    def start_timer(self, timer_id: str) -> None:
        """Start a timer for measuring execution time.

        Args:
            timer_id: Unique identifier for the timer
        """
        self.start_times[timer_id] = time.time()

    def end_timer(self, timer_id: str) -> Optional[float]:
        """End a timer and return the elapsed time.

        Args:
            timer_id: Unique identifier for the timer

        Returns:
            Elapsed time in seconds, or None if timer wasn't found
        """
        if timer_id not in self.start_times:
            return None

        elapsed = time.time() - self.start_times[timer_id]
        del self.start_times[timer_id]
        return elapsed

    def increment_counter(self, counter_name: str, value: int = 1) -> None:
        """Increment a counter.

        Args:
            counter_name: Name of the counter
            value: Value to increment by
        """
        self.counters[counter_name] += value

    def set_gauge(self, gauge_name: str, value: float) -> None:
        """Set a gauge value.

        Args:
            gauge_name: Name of the gauge
            value: Value to set
        """
        self.gauges[gauge_name] = value

    def record_histogram_value(self, histogram_name: str, value: float) -> None:
        """Record a value in a histogram.

        Args:
            histogram_name: Name of the histogram
            value: Value to record
        """
        self.histograms[histogram_name].append(value)

        # Keep only last 1000 values per histogram
        if len(self.histograms[histogram_name]) > 1000:
            self.histograms[histogram_name] = self.histograms[histogram_name][-1000:]

    def record_agent_execution(self, agent_id: str, execution_time: float, success: bool) -> None:
        """Record agent execution metrics.

        Args:
            agent_id: Agent identifier
            execution_time: Time taken for execution
            success: Whether execution was successful
        """
        self.agent_execution_times[agent_id].append(execution_time)

        # Keep only last 100 execution times per agent
        if len(self.agent_execution_times[agent_id]) > 100:
            self.agent_execution_times[agent_id] = self.agent_execution_times[agent_id][-100:]

        # Update success rates
        if success:
            self.agent_success_rates[agent_id]["success"] += 1
        else:
            self.agent_success_rates[agent_id]["error"] += 1

    def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Dictionary with agent metrics
        """
        execution_times = self.agent_execution_times.get(agent_id, [])
        success_data = self.agent_success_rates.get(agent_id, {"success": 0, "error": 0})

        metrics = {
            "agent_id": agent_id,
            "total_executions": len(execution_times),
            "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "min_execution_time": min(execution_times) if execution_times else 0,
            "max_execution_time": max(execution_times) if execution_times else 0,
            "success_count": success_data["success"],
            "error_count": success_data["error"],
            "success_rate": (
                success_data["success"] / (success_data["success"] + success_data["error"])
                if (success_data["success"] + success_data["error"]) > 0
                else 0
            ),
        }

        return metrics

    def get_flow_metrics(self) -> Dict[str, Any]:
        """Get overall flow metrics.

        Returns:
            Dictionary with flow-wide metrics
        """
        # Calculate event statistics
        event_types = defaultdict(int)
        entity_types = defaultdict(int)

        for event in self.events:
            event_types[event.event_type] += 1
            entity_types[event.entity_type] += 1

        # Calculate histogram statistics
        histogram_stats = {}
        for name, values in self.histograms.items():
            if values:
                histogram_stats[name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }

        return {
            "total_events": len(self.events),
            "event_types": dict(event_types),
            "entity_types": dict(entity_types),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": histogram_stats,
            "active_timers": len(self.start_times),
            "retention_hours": self.retention_hours,
        }

    def get_events_by_type(self, event_type: str, limit: Optional[int] = None) -> List[MetricEvent]:
        """Get events of a specific type.

        Args:
            event_type: Type of events to retrieve
            limit: Maximum number of events to return (most recent first)

        Returns:
            List of metric events
        """
        matching_events = [event for event in self.events if event.event_type == event_type]

        # Sort by timestamp (most recent first)
        matching_events.sort(key=lambda x: x.timestamp, reverse=True)

        if limit:
            matching_events = matching_events[:limit]

        return matching_events

    def get_events_by_entity(
        self,
        entity_id: str,
        entity_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[MetricEvent]:
        """Get events for a specific entity.

        Args:
            entity_id: Entity identifier
            entity_type: Optional entity type filter
            limit: Maximum number of events to return (most recent first)

        Returns:
            List of metric events
        """
        matching_events = []
        for event in self.events:
            if event.entity_id == entity_id:
                if entity_type is None or event.entity_type == entity_type:
                    matching_events.append(event)

        # Sort by timestamp (most recent first)
        matching_events.sort(key=lambda x: x.timestamp, reverse=True)

        if limit:
            matching_events = matching_events[:limit]

        return matching_events

    def get_events_in_timerange(
        self,
        start_time: datetime,
        end_time: datetime,
        event_type: Optional[str] = None,
    ) -> List[MetricEvent]:
        """Get events within a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range
            event_type: Optional event type filter

        Returns:
            List of metric events
        """
        matching_events = []
        for event in self.events:
            if start_time <= event.timestamp <= end_time:
                if event_type is None or event.event_type == event_type:
                    matching_events.append(event)

        # Sort by timestamp
        matching_events.sort(key=lambda x: x.timestamp)

        return matching_events

    def clear_metrics(self) -> None:
        """Clear all metrics data."""
        self.events.clear()
        self.start_times.clear()
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.agent_execution_times.clear()
        self.agent_success_rates.clear()

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics data.

        Returns:
            Dictionary with all metrics data
        """
        return {
            "events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "entity_id": event.entity_id,
                    "entity_type": event.entity_type,
                    "value": event.value,
                    "metadata": event.metadata,
                }
                for event in self.events
            ],
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {name: list(values) for name, values in self.histograms.items()},
            "agent_execution_times": {
                agent: list(times) for agent, times in self.agent_execution_times.items()
            },
            "agent_success_rates": dict(self.agent_success_rates),
        }

    def _cleanup_old_events(self) -> None:
        """Remove events older than retention period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)

        # Remove old events from the left of the deque
        while self.events and self.events[0].timestamp < cutoff_time:
            self.events.popleft()