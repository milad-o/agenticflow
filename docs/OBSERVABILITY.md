# AgenticFlow Observability
**Real-time monitoring and visualization for multi-agent workflows**

## 🔍 Overview

AgenticFlow includes comprehensive observability features that provide real-time insights into multi-agent workflow execution. Monitor agent activities, tool calls, performance metrics, and system events through a rich Streamlit dashboard.

## ✨ Features

### 📊 Real-time Event Tracking
- **Flow Events**: Start/end, state updates, coordination
- **Agent Events**: Activity tracking, reflections, tool calls
- **Tool Events**: Call/response monitoring, success/failure tracking
- **Error Events**: Comprehensive error tracking and context

### 🤖 Agent Monitoring
- **Agent Reflection**: Self-assessment and reasoning insights
- **Tool Call Monitoring**: Input/output tracking for all tool usage
- **Performance Metrics**: Success rates, execution times, error counts
- **Activity Timeline**: Chronological view of agent actions

### 📈 Performance Analytics
- **Execution Metrics**: Duration, throughput, success rates
- **Resource Usage**: Tool usage patterns, agent utilization
- **Trend Analysis**: Performance trends over time
- **Cross-agent Comparison**: Comparative performance analysis

### 🎨 Rich Streamlit UI
- **Real-time Dashboard**: Live updates during execution
- **Interactive Charts**: Plotly-powered visualizations
- **Event Stream**: Live event feed with filtering
- **Agent Details**: Drill-down views for specific agents

## 🚀 Quick Start

### Basic Observable Flow

```python
from agenticflow import ObservableFlow
from agenticflow.agents import FileSystemWorker, AnalysisWorker

# Create observable flow
flow = ObservableFlow()
flow.add_worker("filesystem", FileSystemWorker())
flow.add_worker("analysis", AnalysisWorker())

# Execute with automatic observability
result = flow.run("Analyze data files and generate insights")

# Access observability data
print(f"Events tracked: {len(flow.get_event_tracker().events)}")
print(f"Execution time: {result['execution_time_ms']:.2f}ms")
```

### Launch Real-time UI

```python
# Option 1: Built-in UI launcher
flow.create_ui()  # Launches Streamlit automatically

# Option 2: Manual launch
import streamlit as st
from agenticflow.observability.visualization import create_flow_visualizer

observer = flow.get_observer()
create_flow_visualizer(observer)
```

### Standalone UI

```bash
# Launch the standalone UI
uv run streamlit run ui_launcher.py

# Or use the comprehensive demo
uv run python observable_demo.py
```

## 📋 Components

### EventTracker
Comprehensive event tracking system:

```python
from agenticflow.observability import EventTracker

tracker = EventTracker()

# Track custom events
tracker.track_flow_start("My task", ["agent1", "agent2"])
tracker.track_agent_start("agent1", "FileSystemWorker", "Find files", ["file_search"])
tracker.track_tool_call("file_search", "agent1", {"pattern": "*.csv"})

# Get events
events = tracker.get_events(limit=10)
metrics = tracker.get_metrics()
```

### FlowObserver
Advanced monitoring and analysis:

```python
from agenticflow.observability import FlowObserver, EventTracker

observer = FlowObserver(EventTracker())

# Register real-time callbacks
def my_callback(event_data):
    print(f"Event: {event_data['type']} from {event_data.get('agent_name', 'system')}")

observer.register_callback(my_callback)

# Get real-time insights
status = observer.get_real_time_status()
analytics = observer.get_flow_analytics()
agent_insights = observer.get_agent_insights("my_agent")
```

### MetricsCollector
Performance metrics collection:

```python
from agenticflow.observability import MetricsCollector

metrics = MetricsCollector()

# Record metrics
metrics.record_flow_metric("execution_time", 1500.0)
metrics.record_agent_metric("agent1", "tool_calls", 5.0)
metrics.record_performance_metric("success_rate", 95.5)

# Analyze trends
trend = metrics.get_trend_analysis("performance", "success_rate")
throughput = metrics.calculate_throughput("flow", "execution_time")
```

## 🎯 Use Cases

### Development & Debugging
- **Real-time Debugging**: Watch agents execute in real-time
- **Performance Optimization**: Identify bottlenecks and inefficiencies
- **Error Analysis**: Comprehensive error tracking and context
- **Behavior Analysis**: Understand agent decision-making patterns

### Production Monitoring
- **System Health**: Monitor multi-agent system health
- **Performance Tracking**: Track KPIs and SLAs
- **Anomaly Detection**: Identify unusual patterns or behaviors
- **Capacity Planning**: Understand resource utilization

### Research & Analysis
- **Agent Behavior**: Study agent interaction patterns
- **Tool Usage**: Analyze tool effectiveness and usage
- **Performance Comparison**: Compare different agent configurations
- **Workflow Optimization**: Optimize multi-agent workflows

## 📊 UI Features

### Main Dashboard
- **Flow Status**: Current execution state and progress
- **Agent Overview**: Active agents and their status
- **Event Stream**: Real-time event feed
- **Performance Metrics**: Key performance indicators

### Agent Details
- **Activity Timeline**: Chronological agent activities
- **Tool Usage**: Tools used and their outcomes
- **Reflection Data**: Agent self-assessment and reasoning
- **Performance Stats**: Individual agent metrics

### Analytics Views
- **Tool Usage Charts**: Visual tool usage patterns
- **Performance Trends**: Time-series performance data
- **Error Analysis**: Error patterns and frequency
- **Agent Comparison**: Comparative performance metrics

## 🛠️ Configuration

### Enabling Observability

```python
# Default: observability enabled
flow = ObservableFlow()

# Explicitly enable/disable
flow = ObservableFlow(enable_observability=True)
flow = ObservableFlow(enable_observability=False)  # Disable for production
```

### Custom Event Tracking

```python
class MyAgent:
    def execute(self, task):
        # Track custom agent reflection
        observer.observe_agent_reflection("my_agent", {
            "reasoning": "Chose approach X because...",
            "confidence": 0.85,
            "alternatives_considered": ["approach_a", "approach_b"]
        })

        # Track custom activity
        observer.observe_agent_activity("my_agent", "custom_analysis", {
            "data_size": 1000,
            "processing_method": "statistical_analysis"
        })
```

### UI Customization

```python
# Custom callback for real-time updates
def custom_callback(event_data):
    if event_data["type"] == "agent_reflection":
        # Custom handling for agent reflections
        save_reflection_to_db(event_data)

observer.register_callback(custom_callback)
```

## 📁 Data Export

### Export Events

```python
# Export all events to JSON
filename = flow.export_observability_data()
print(f"Data exported to: {filename}")

# Custom export
tracker = flow.get_event_tracker()
tracker.export_events("my_export.json")
```

### Export Metrics

```python
# Get comprehensive metrics
metrics = flow.get_observer().get_flow_analytics()

# Export to your preferred format
import json
with open("metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
```

## 🔧 Advanced Usage

### Custom Metrics

```python
# Record custom business metrics
metrics_collector = flow.get_metrics_collector()
metrics_collector.record_flow_metric("customer_satisfaction", 4.2)
metrics_collector.record_agent_metric("sales_agent", "deals_closed", 3.0)
```

### Real-time Integration

```python
# Integrate with external monitoring systems
def send_to_monitoring(event_data):
    if event_data["type"] == "flow_end":
        send_metric_to_datadog(event_data)

observer.register_callback(send_to_monitoring)
```

### Performance Monitoring

```python
# Set up performance thresholds
def performance_monitor(event_data):
    if event_data.get("duration_ms", 0) > 30000:  # 30 seconds
        alert_slow_execution(event_data)

observer.register_callback(performance_monitor)
```

## 🎨 Screenshots

The Streamlit UI provides:

1. **Main Dashboard**: Real-time overview of flow execution
2. **Agent Monitor**: Individual agent activity and performance
3. **Event Stream**: Live feed of all system events
4. **Tool Analytics**: Visual analysis of tool usage patterns
5. **Performance Charts**: Time-series performance visualization

## 🔗 Integration

### With Existing Flows

```python
# Convert existing Flow to ObservableFlow
from agenticflow import Flow, ObservableFlow

# Replace
flow = Flow()

# With
flow = ObservableFlow()

# All existing code works the same!
```

### With External Systems

```python
# Integration with logging systems
import logging

def log_events(event_data):
    logging.info(f"AgenticFlow Event: {event_data}")

observer.register_callback(log_events)

# Integration with metrics systems
def send_metrics(event_data):
    if event_data["type"] == "flow_end":
        prometheus_client.counter.inc()

observer.register_callback(send_metrics)
```

## 📚 Examples

See the included demo files:

- **`observable_demo.py`**: Comprehensive demo with UI
- **`ui_launcher.py`**: Standalone UI launcher
- **`examples/`**: Various use case examples

## 🎯 Best Practices

1. **Development**: Enable full observability for debugging
2. **Testing**: Use observability to validate agent behavior
3. **Production**: Consider performance impact of observability
4. **Monitoring**: Set up real-time callbacks for critical events
5. **Analysis**: Export data for offline analysis and reporting

---

**Ready to see your agents in action?** 🚀

```bash
uv run python observable_demo.py
```

Open http://localhost:8501 and watch your multi-agent workflows come to life!