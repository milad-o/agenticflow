"""
Observable Flow - Enhanced Flow with Comprehensive Observability
==============================================================

Enhanced Flow class with integrated observability, event tracking, and monitoring.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
import os

from .flow import Flow
from ..observability import EventTracker, FlowObserver, MetricsCollector
from ..teams import SupervisorAgent, TeamState, TeamGraph


class ObservableFlow(Flow):
    """Enhanced Flow with comprehensive observability and monitoring."""

    def __init__(self, llm: Optional[BaseChatModel] = None, enable_observability: bool = True):
        super().__init__(llm)

        # Observability components
        self.enable_observability = enable_observability
        if enable_observability:
            self.event_tracker = EventTracker()
            self.observer = FlowObserver(self.event_tracker)
            self.metrics_collector = MetricsCollector()
        else:
            self.event_tracker = None
            self.observer = None
            self.metrics_collector = None

        # Execution tracking
        self.current_execution_id: Optional[str] = None
        self.execution_start_time: Optional[float] = None

    def add_worker(self, name: str, worker: Any) -> "ObservableFlow":
        """Add a specialized worker agent with observability tracking."""
        # Add worker using parent method
        super().add_worker(name, worker)

        # Track worker addition
        if self.observer:
            self.observer.observe_agent_activity(
                name,
                "worker_added",
                {
                    "worker_type": type(worker).__name__,
                    "capabilities": getattr(worker, "capabilities", []),
                    "total_workers": len(self.workers)
                }
            )

        return self

    def remove_worker(self, name: str) -> "ObservableFlow":
        """Remove a worker with observability tracking."""
        if name in self.workers and self.observer:
            self.observer.observe_agent_activity(
                name,
                "worker_removed",
                {"remaining_workers": len(self.workers) - 1}
            )

        super().remove_worker(name)
        return self

    async def execute(self, task: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task with comprehensive observability tracking."""
        if not self.team_graph:
            raise ValueError("No workers added to the team. Use add_worker() first.")

        # Start observability tracking
        self.execution_start_time = time.time()
        worker_names = list(self.workers.keys())

        if self.observer:
            self.observer.observe_flow_start(task, worker_names)

        if self.metrics_collector:
            self.metrics_collector.record_flow_metric("execution_start", 1.0, {"task": task})

        print(f"🚀 Executing hierarchical team task: {task}")
        print(f"   Team: {', '.join(worker_names)}")

        try:
            # Track that supervisor is coordinating (not all workers starting)
            if self.observer:
                self.observer.observe_agent_activity(
                    "supervisor",
                    "coordination_start",
                    {
                        "task": task,
                        "available_workers": worker_names,
                        "coordination_strategy": "intelligent_routing"
                    }
                )

            # Execute using enhanced team graph with observability
            final_state = await self._execute_with_tracking(task, config)

            # Calculate execution time
            execution_time_ms = (time.time() - self.execution_start_time) * 1000

            # Build result
            result = {
                "success": final_state.is_complete and not final_state.error_message,
                "task": final_state.current_task,
                "workers_used": final_state.completed_workers,
                "messages": final_state.messages,
                "results": final_state.worker_results,
                "error": final_state.error_message,
                "summary": final_state.get_summary(),
                "execution_time_ms": execution_time_ms,
                "observability_data": self._get_execution_summary() if self.observer else None
            }

            # Track completion
            if self.observer:
                self.observer.observe_flow_end(result["success"], result, execution_time_ms)

            if self.metrics_collector:
                self.metrics_collector.record_flow_metric(
                    "execution_time_ms",
                    execution_time_ms,
                    {"success": result["success"], "workers_count": len(final_state.completed_workers)}
                )
                self.metrics_collector.record_performance_metric("task_completion", 1.0)

            # Print summary
            if result["success"]:
                print(f"✅ Task completed successfully!")
                print(f"   Workers used: {', '.join(final_state.completed_workers)}")
                print(f"   Execution time: {execution_time_ms:.2f}ms")
            else:
                print(f"❌ Task failed: {final_state.error_message}")

            return result

        except Exception as e:
            # Track error
            execution_time_ms = (time.time() - self.execution_start_time) * 1000

            if self.observer:
                self.observer.observe_flow_end(False, {"error": str(e)}, execution_time_ms)
                self.event_tracker.track_error("flow", "execution_error", str(e), {"task": task})

            if self.metrics_collector:
                self.metrics_collector.record_performance_metric("task_error", 1.0)

            print(f"❌ Execution failed: {e}")
            raise

    async def _execute_with_tracking(self, task: str, config: Optional[Dict[str, Any]] = None) -> TeamState:
        """Execute task with detailed tracking of each step."""
        # Enhanced execution with observability hooks
        final_state = await self.team_graph.execute_team_task(task, config)

        # Track worker results and activities
        if self.observer:
            for worker_name, worker_result in final_state.worker_results.items():
                # Track worker completion
                self.observer.observe_agent_activity(
                    worker_name,
                    "execution_complete",
                    {
                        "result_action": worker_result.get("action", "unknown"),
                        "success": "error" not in worker_result,
                        "result_size": len(str(worker_result))
                    }
                )

                # Track tool usage if available
                if "action" in worker_result:
                    self.observer.observe_agent_activity(
                        worker_name,
                        "tool_call",
                        {
                            "tool_name": worker_result["action"],
                            "input_data": {"task": task},
                            "output_data": worker_result
                        }
                    )

                # Record metrics
                if self.metrics_collector:
                    self.metrics_collector.record_agent_metric(
                        worker_name,
                        "task_completion",
                        1.0,
                        {"action": worker_result.get("action")}
                    )

        # Track state updates
        if self.observer:
            self.observer.observe_state_update({
                "messages_count": len(final_state.messages),
                "completed_workers": final_state.completed_workers,
                "is_complete": final_state.is_complete
            })

        return final_state

    def _get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary with observability data."""
        if not self.observer:
            return {}

        return {
            "real_time_status": self.observer.get_real_time_status(),
            "flow_analytics": self.observer.get_flow_analytics(),
            "metrics_summary": self.metrics_collector.get_summary_stats() if self.metrics_collector else {},
            "event_count": len(self.event_tracker.events) if self.event_tracker else 0
        }

    def get_observer(self) -> Optional[FlowObserver]:
        """Get the flow observer for UI integration."""
        return self.observer

    def get_event_tracker(self) -> Optional[EventTracker]:
        """Get the event tracker."""
        return self.event_tracker

    def get_metrics_collector(self) -> Optional[MetricsCollector]:
        """Get the metrics collector."""
        return self.metrics_collector

    def get_agent_insights(self, agent_name: str) -> Dict[str, Any]:
        """Get detailed insights for a specific agent."""
        if not self.observer:
            return {"error": "Observability not enabled"}

        return self.observer.get_agent_insights(agent_name)

    def export_observability_data(self, filename: str = None) -> str:
        """Export all observability data."""
        if not self.event_tracker:
            raise ValueError("Observability not enabled")

        return self.event_tracker.export_events(filename)

    def create_ui(self) -> None:
        """Create and launch the Streamlit UI for this flow."""
        if not self.observer:
            raise ValueError("Observability not enabled - cannot create UI")

        from .ui_app import create_flow_ui
        create_flow_ui(self)

    def describe_team(self) -> Dict[str, Any]:
        """Enhanced team description with observability info."""
        base_description = super().describe_team()

        if self.observer:
            status = self.observer.get_real_time_status()
            analytics = self.observer.get_flow_analytics()

            base_description.update({
                "observability_enabled": True,
                "active_agents": len(status["active_agents"]),
                "total_events": status["metrics"]["total_events"],
                "performance": analytics["performance"]
            })
        else:
            base_description["observability_enabled"] = False

        return base_description

    # Enhanced convenience methods
    def run_with_ui(self, task: str) -> Dict[str, Any]:
        """Run task and launch UI for monitoring."""
        if not self.observer:
            raise ValueError("Observability not enabled")

        # Start execution in background
        import threading
        result_container = {}

        def execute_task():
            result_container['result'] = self.run(task)

        execution_thread = threading.Thread(target=execute_task)
        execution_thread.start()

        # Launch UI
        self.create_ui()

        # Wait for execution to complete
        execution_thread.join()

        return result_container.get('result', {})