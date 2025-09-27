"""
Metrics Collection System
========================

Advanced metrics collection for AgenticFlow performance monitoring.
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading


class MetricsCollector:
    """Comprehensive metrics collection for flow performance."""

    def __init__(self, window_size_minutes: int = 60):
        self.window_size = timedelta(minutes=window_size_minutes)
        self.metrics_data = {
            "flow_metrics": defaultdict(list),
            "agent_metrics": defaultdict(lambda: defaultdict(list)),
            "tool_metrics": defaultdict(lambda: defaultdict(list)),
            "performance_metrics": defaultdict(list)
        }
        self._lock = threading.Lock()

    def record_flow_metric(self, metric_name: str, value: float, metadata: Dict[str, Any] = None) -> None:
        """Record a flow-level metric."""
        with self._lock:
            timestamp = datetime.now()
            self.metrics_data["flow_metrics"][metric_name].append({
                "timestamp": timestamp,
                "value": value,
                "metadata": metadata or {}
            })
            self._cleanup_old_data("flow_metrics", metric_name, timestamp)

    def record_agent_metric(self, agent_name: str, metric_name: str, value: float,
                           metadata: Dict[str, Any] = None) -> None:
        """Record an agent-specific metric."""
        with self._lock:
            timestamp = datetime.now()
            self.metrics_data["agent_metrics"][agent_name][metric_name].append({
                "timestamp": timestamp,
                "value": value,
                "metadata": metadata or {}
            })
            self._cleanup_old_data("agent_metrics", (agent_name, metric_name), timestamp)

    def record_tool_metric(self, tool_name: str, metric_name: str, value: float,
                          metadata: Dict[str, Any] = None) -> None:
        """Record a tool-specific metric."""
        with self._lock:
            timestamp = datetime.now()
            self.metrics_data["tool_metrics"][tool_name][metric_name].append({
                "timestamp": timestamp,
                "value": value,
                "metadata": metadata or {}
            })
            self._cleanup_old_data("tool_metrics", (tool_name, metric_name), timestamp)

    def record_performance_metric(self, metric_name: str, value: float,
                                 metadata: Dict[str, Any] = None) -> None:
        """Record a performance metric."""
        with self._lock:
            timestamp = datetime.now()
            self.metrics_data["performance_metrics"][metric_name].append({
                "timestamp": timestamp,
                "value": value,
                "metadata": metadata or {}
            })
            self._cleanup_old_data("performance_metrics", metric_name, timestamp)

    def _cleanup_old_data(self, category: str, key: Any, current_time: datetime) -> None:
        """Remove data older than the window size."""
        cutoff_time = current_time - self.window_size

        if category == "agent_metrics":
            agent_name, metric_name = key
            data_list = self.metrics_data[category][agent_name][metric_name]
        elif category == "tool_metrics":
            tool_name, metric_name = key
            data_list = self.metrics_data[category][tool_name][metric_name]
        else:
            data_list = self.metrics_data[category][key]

        # Remove old entries
        while data_list and data_list[0]["timestamp"] < cutoff_time:
            data_list.pop(0)

    def get_flow_metrics(self, metric_name: str = None) -> Dict[str, Any]:
        """Get flow metrics."""
        with self._lock:
            if metric_name:
                return {
                    metric_name: self.metrics_data["flow_metrics"].get(metric_name, [])
                }
            return dict(self.metrics_data["flow_metrics"])

    def get_agent_metrics(self, agent_name: str = None, metric_name: str = None) -> Dict[str, Any]:
        """Get agent metrics."""
        with self._lock:
            if agent_name and metric_name:
                return {
                    agent_name: {
                        metric_name: self.metrics_data["agent_metrics"][agent_name].get(metric_name, [])
                    }
                }
            elif agent_name:
                return {
                    agent_name: dict(self.metrics_data["agent_metrics"][agent_name])
                }
            return {
                agent: dict(metrics)
                for agent, metrics in self.metrics_data["agent_metrics"].items()
            }

    def get_tool_metrics(self, tool_name: str = None, metric_name: str = None) -> Dict[str, Any]:
        """Get tool metrics."""
        with self._lock:
            if tool_name and metric_name:
                return {
                    tool_name: {
                        metric_name: self.metrics_data["tool_metrics"][tool_name].get(metric_name, [])
                    }
                }
            elif tool_name:
                return {
                    tool_name: dict(self.metrics_data["tool_metrics"][tool_name])
                }
            return {
                tool: dict(metrics)
                for tool, metrics in self.metrics_data["tool_metrics"].items()
            }

    def get_performance_metrics(self, metric_name: str = None) -> Dict[str, Any]:
        """Get performance metrics."""
        with self._lock:
            if metric_name:
                return {
                    metric_name: self.metrics_data["performance_metrics"].get(metric_name, [])
                }
            return dict(self.metrics_data["performance_metrics"])

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        with self._lock:
            now = datetime.now()
            stats = {
                "collection_window_minutes": self.window_size.total_seconds() / 60,
                "data_points": 0,
                "agents_tracked": len(self.metrics_data["agent_metrics"]),
                "tools_tracked": len(self.metrics_data["tool_metrics"]),
                "flow_metrics_count": len(self.metrics_data["flow_metrics"]),
                "performance_metrics_count": len(self.metrics_data["performance_metrics"]),
                "oldest_data": None,
                "newest_data": None
            }

            # Count total data points and find date range
            all_timestamps = []

            for metric_data in self.metrics_data["flow_metrics"].values():
                stats["data_points"] += len(metric_data)
                all_timestamps.extend([d["timestamp"] for d in metric_data])

            for agent_metrics in self.metrics_data["agent_metrics"].values():
                for metric_data in agent_metrics.values():
                    stats["data_points"] += len(metric_data)
                    all_timestamps.extend([d["timestamp"] for d in metric_data])

            for tool_metrics in self.metrics_data["tool_metrics"].values():
                for metric_data in tool_metrics.values():
                    stats["data_points"] += len(metric_data)
                    all_timestamps.extend([d["timestamp"] for d in metric_data])

            for metric_data in self.metrics_data["performance_metrics"].values():
                stats["data_points"] += len(metric_data)
                all_timestamps.extend([d["timestamp"] for d in metric_data])

            if all_timestamps:
                stats["oldest_data"] = min(all_timestamps).isoformat()
                stats["newest_data"] = max(all_timestamps).isoformat()

            return stats

    def calculate_throughput(self, category: str, key: str, time_window_minutes: int = 5) -> float:
        """Calculate throughput for a specific metric."""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

            if category == "flow":
                data_list = self.metrics_data["flow_metrics"].get(key, [])
            elif category == "performance":
                data_list = self.metrics_data["performance_metrics"].get(key, [])
            else:
                return 0.0

            recent_data = [d for d in data_list if d["timestamp"] >= cutoff_time]
            return len(recent_data) / time_window_minutes  # items per minute

    def calculate_average_latency(self, category: str, key: str, time_window_minutes: int = 5) -> float:
        """Calculate average latency for a specific metric."""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

            if category == "performance":
                data_list = self.metrics_data["performance_metrics"].get(key, [])
            else:
                return 0.0

            recent_data = [d["value"] for d in data_list if d["timestamp"] >= cutoff_time]

            if not recent_data:
                return 0.0

            return sum(recent_data) / len(recent_data)

    def get_trend_analysis(self, category: str, key: str, time_window_minutes: int = 30) -> Dict[str, Any]:
        """Get trend analysis for a metric."""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

            if category == "flow":
                data_list = self.metrics_data["flow_metrics"].get(key, [])
            elif category == "performance":
                data_list = self.metrics_data["performance_metrics"].get(key, [])
            else:
                return {}

            recent_data = [d for d in data_list if d["timestamp"] >= cutoff_time]

            if len(recent_data) < 2:
                return {
                    "trend": "insufficient_data",
                    "data_points": len(recent_data),
                    "time_span_minutes": 0
                }

            values = [d["value"] for d in recent_data]
            timestamps = [d["timestamp"] for d in recent_data]

            # Simple trend calculation
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]

            if first_half and second_half:
                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)

                if second_avg > first_avg * 1.1:
                    trend = "increasing"
                elif second_avg < first_avg * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "unknown"

            return {
                "trend": trend,
                "data_points": len(recent_data),
                "time_span_minutes": (max(timestamps) - min(timestamps)).total_seconds() / 60,
                "min_value": min(values),
                "max_value": max(values),
                "avg_value": sum(values) / len(values),
                "latest_value": values[-1] if values else 0
            }