"""Observer for monitoring flow execution and agent operations."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from .metrics import Metrics


class Observer:
    """Observer for monitoring and tracking flow execution.

    The observer provides comprehensive monitoring capabilities including:
    - Flow lifecycle tracking
    - Agent execution monitoring
    - Message routing observation
    - Performance metrics collection
    - Error tracking and debugging
    """

    def __init__(
        self,
        enabled: bool = True,
        log_level: str = "INFO",
        metrics_enabled: bool = True,
        max_events: int = 10000,
    ):
        """Initialize the observer.

        Args:
            enabled: Whether observability is enabled
            log_level: Logging level for events
            metrics_enabled: Whether to collect metrics
            max_events: Maximum number of events to keep in metrics
        """
        self.enabled = enabled
        self.metrics_enabled = metrics_enabled

        # Setup logging
        self.logger = logging.getLogger("agenticflow.observer")
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Setup metrics collection
        self.metrics = Metrics(max_events=max_events) if metrics_enabled else None

        # Event tracking
        self.flow_events: List[Dict[str, Any]] = []
        self.agent_events: List[Dict[str, Any]] = []
        self.message_events: List[Dict[str, Any]] = []
        self.error_events: List[Dict[str, Any]] = []

    async def flow_started(self, flow_id: str, flow_name: str) -> None:
        """Record flow start event.

        Args:
            flow_id: Flow identifier
            flow_name: Flow name
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "flow_started",
            "flow_id": flow_id,
            "flow_name": flow_name,
        }

        self.flow_events.append(event)
        self.logger.info(f"Flow started: {flow_name} ({flow_id})")

        if self.metrics:
            self.metrics.record_event(
                event_type="flow_started",
                entity_id=flow_id,
                entity_type="flow",
                value=flow_name,
            )
            self.metrics.start_timer(f"flow_{flow_id}")

    async def flow_completed(self, flow_id: str) -> None:
        """Record flow completion event.

        Args:
            flow_id: Flow identifier
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "flow_completed",
            "flow_id": flow_id,
        }

        self.flow_events.append(event)
        self.logger.info(f"Flow completed: {flow_id}")

        if self.metrics:
            execution_time = self.metrics.end_timer(f"flow_{flow_id}")
            self.metrics.record_event(
                event_type="flow_completed",
                entity_id=flow_id,
                entity_type="flow",
                value=execution_time,
            )

    async def flow_stopped(self, flow_id: str) -> None:
        """Record flow stop event.

        Args:
            flow_id: Flow identifier
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "flow_stopped",
            "flow_id": flow_id,
        }

        self.flow_events.append(event)
        self.logger.info(f"Flow stopped: {flow_id}")

        if self.metrics:
            self.metrics.record_event(
                event_type="flow_stopped",
                entity_id=flow_id,
                entity_type="flow",
            )

    async def flow_error(self, flow_id: str, error_message: str) -> None:
        """Record flow error event.

        Args:
            flow_id: Flow identifier
            error_message: Error description
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "flow_error",
            "flow_id": flow_id,
            "error_message": error_message,
        }

        self.flow_events.append(event)
        self.error_events.append(event)
        self.logger.error(f"Flow error in {flow_id}: {error_message}")

        if self.metrics:
            self.metrics.record_event(
                event_type="flow_error",
                entity_id=flow_id,
                entity_type="flow",
                value=error_message,
            )
            self.metrics.increment_counter("flow_errors")

    async def agent_execution_started(self, agent_id: str, message_id: UUID) -> None:
        """Record agent execution start.

        Args:
            agent_id: Agent identifier
            message_id: Message being processed
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "agent_execution_started",
            "agent_id": agent_id,
            "message_id": str(message_id),
        }

        self.agent_events.append(event)
        self.logger.debug(f"Agent {agent_id} started processing message {message_id}")

        if self.metrics:
            self.metrics.record_event(
                event_type="agent_execution_started",
                entity_id=agent_id,
                entity_type="agent",
                value=str(message_id),
            )
            self.metrics.start_timer(f"agent_{agent_id}_{message_id}")

    async def agent_execution_completed(
        self,
        agent_id: str,
        message_id: UUID,
        success: bool = True,
        result: Optional[str] = None,
    ) -> None:
        """Record agent execution completion.

        Args:
            agent_id: Agent identifier
            message_id: Message that was processed
            success: Whether execution was successful
            result: Execution result or error message
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "agent_execution_completed",
            "agent_id": agent_id,
            "message_id": str(message_id),
            "success": success,
            "result": result,
        }

        self.agent_events.append(event)

        if success:
            self.logger.debug(f"Agent {agent_id} completed processing message {message_id}")
        else:
            self.logger.warning(f"Agent {agent_id} failed processing message {message_id}: {result}")
            self.error_events.append(event)

        if self.metrics:
            execution_time = self.metrics.end_timer(f"agent_{agent_id}_{message_id}")
            self.metrics.record_event(
                event_type="agent_execution_completed",
                entity_id=agent_id,
                entity_type="agent",
                value=execution_time,
                metadata={"success": success, "result": result},
            )

            if execution_time is not None:
                self.metrics.record_agent_execution(agent_id, execution_time, success)

            counter_name = "agent_executions_success" if success else "agent_executions_error"
            self.metrics.increment_counter(counter_name)

    async def agent_status_changed(self, agent_id: str, status: str) -> None:
        """Record agent status change.

        Args:
            agent_id: Agent identifier
            status: New status
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "agent_status_changed",
            "agent_id": agent_id,
            "status": status,
        }

        self.agent_events.append(event)
        self.logger.debug(f"Agent {agent_id} status changed to: {status}")

        if self.metrics:
            self.metrics.record_event(
                event_type="agent_status_changed",
                entity_id=agent_id,
                entity_type="agent",
                value=status,
            )

    async def message_processed(self, message_id: UUID, processor_id: str, target: str) -> None:
        """Record message processing event.

        Args:
            message_id: Message identifier
            processor_id: ID of the processor (orchestrator, supervisor, agent)
            target: Target that processed the message
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "message_processed",
            "message_id": str(message_id),
            "processor_id": processor_id,
            "target": target,
        }

        self.message_events.append(event)
        self.logger.debug(f"Message {message_id} processed by {processor_id} -> {target}")

        if self.metrics:
            self.metrics.record_event(
                event_type="message_processed",
                entity_id=str(message_id),
                entity_type="message",
                value=processor_id,
                metadata={"target": target},
            )
            self.metrics.increment_counter("messages_processed")

    async def routing_error(self, message_id: UUID, error_message: str) -> None:
        """Record message routing error.

        Args:
            message_id: Message identifier
            error_message: Error description
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "routing_error",
            "message_id": str(message_id),
            "error_message": error_message,
        }

        self.message_events.append(event)
        self.error_events.append(event)
        self.logger.error(f"Routing error for message {message_id}: {error_message}")

        if self.metrics:
            self.metrics.record_event(
                event_type="routing_error",
                entity_id=str(message_id),
                entity_type="message",
                value=error_message,
            )
            self.metrics.increment_counter("routing_errors")

    async def tool_execution(
        self,
        agent_id: str,
        tool_name: str,
        success: bool = True,
        execution_time: Optional[float] = None,
    ) -> None:
        """Record tool execution event.

        Args:
            agent_id: Agent identifier
            tool_name: Name of the tool executed
            success: Whether execution was successful
            execution_time: Time taken for execution
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "tool_execution",
            "agent_id": agent_id,
            "tool_name": tool_name,
            "success": success,
            "execution_time": execution_time,
        }

        self.agent_events.append(event)

        if success:
            self.logger.debug(f"Agent {agent_id} successfully executed tool {tool_name}")
        else:
            self.logger.warning(f"Agent {agent_id} failed to execute tool {tool_name}")
            self.error_events.append(event)

        if self.metrics:
            self.metrics.record_event(
                event_type="tool_execution",
                entity_id=agent_id,
                entity_type="agent",
                value=tool_name,
                metadata={"success": success, "execution_time": execution_time},
            )

            if execution_time is not None:
                self.metrics.record_histogram_value(f"tool_execution_time_{tool_name}", execution_time)

            counter_name = f"tool_{tool_name}_success" if success else f"tool_{tool_name}_error"
            self.metrics.increment_counter(counter_name)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics data.

        Returns:
            Dictionary with all metrics and events
        """
        if not self.enabled:
            return {"observability_disabled": True}

        base_metrics = {
            "enabled": self.enabled,
            "total_flow_events": len(self.flow_events),
            "total_agent_events": len(self.agent_events),
            "total_message_events": len(self.message_events),
            "total_error_events": len(self.error_events),
        }

        if self.metrics:
            base_metrics.update(self.metrics.get_flow_metrics())

        return base_metrics

    async def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Dictionary with agent-specific metrics
        """
        if not self.enabled or not self.metrics:
            return {"observability_disabled": True}

        return self.metrics.get_agent_metrics(agent_id)

    def get_recent_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get recent events.

        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        if not self.enabled:
            return []

        all_events = (
            self.flow_events + self.agent_events + self.message_events + self.error_events
        )

        if event_type:
            all_events = [event for event in all_events if event.get("event_type") == event_type]

        # Sort by timestamp (most recent first)
        all_events.sort(key=lambda x: x["timestamp"], reverse=True)

        return all_events[:limit]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors.

        Returns:
            Dictionary with error statistics
        """
        if not self.enabled:
            return {"observability_disabled": True}

        error_types = {}
        for event in self.error_events:
            event_type = event.get("event_type", "unknown")
            error_types[event_type] = error_types.get(event_type, 0) + 1

        return {
            "total_errors": len(self.error_events),
            "error_types": error_types,
            "recent_errors": self.error_events[-10:] if self.error_events else [],
        }

    async def export_data(self) -> Dict[str, Any]:
        """Export all observability data.

        Returns:
            Complete observability data export
        """
        data = {
            "enabled": self.enabled,
            "flow_events": self.flow_events,
            "agent_events": self.agent_events,
            "message_events": self.message_events,
            "error_events": self.error_events,
        }

        if self.metrics:
            data["metrics"] = self.metrics.export_metrics()

        return data

    def clear_data(self) -> None:
        """Clear all observability data."""
        self.flow_events.clear()
        self.agent_events.clear()
        self.message_events.clear()
        self.error_events.clear()

        if self.metrics:
            self.metrics.clear_metrics()