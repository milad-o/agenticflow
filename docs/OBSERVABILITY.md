# Observability & Monitoring

AgenticFlow provides comprehensive observability features to monitor, debug, and analyze your agent workflows in real-time.

## 🎯 Overview

The observability system is built around an event-driven architecture that captures every aspect of your workflow execution:

- **Flow Events**: High-level workflow lifecycle
- **Agent Events**: Individual agent activities and reasoning
- **Tool Events**: Detailed tool execution and results
- **Team Events**: Supervisor decisions and agent routing
- **Custom Events**: User-defined events for specific use cases

## 🚀 Quick Start

### Basic Observability

```python
from agenticflow import Flow, Agent, create_file, search_web

# Create a flow
flow = Flow("my_workflow")
flow.add_agent(Agent("researcher", tools=[search_web]))
flow.add_agent(Agent("writer", tools=[create_file]))

# Enable observability
flow.enable_observability()

# Run with monitoring
result = await flow.run("Research and write a report")
```

### Rich Console Output

```python
# Enable beautiful terminal output
flow.enable_observability(rich_console=True)

# This provides:
# - Tree structure showing hierarchy
# - Color-coded events
# - Real-time progress updates
# - Detailed tool arguments and results
# - Performance metrics
```

## 📊 Event Types

### Flow Events

| Event | Description | Data |
|-------|-------------|------|
| `flow_started` | Workflow initialization | `flow_name`, `message` |
| `flow_completed` | Successful completion | `duration_ms`, `total_messages` |
| `flow_error` | Workflow failure | `error_message`, `error_type`, `stack_trace` |

### Agent Events

| Event | Description | Data |
|-------|-------------|------|
| `agent_started` | Agent activation | `agent_name`, `agent_type`, `tools` |
| `agent_completed` | Agent completion | `duration_ms`, `tools_used` |
| `agent_thinking` | Reasoning process | `thinking_process`, `current_step` |
| `agent_working` | Task execution | `task_description`, `progress` |
| `agent_error` | Agent failure | `error_message`, `error_type`, `stack_trace` |

### Tool Events

| Event | Description | Data |
|-------|-------------|------|
| `tool_args` | Tool arguments | `tool_name`, `args` |
| `tool_executed` | Tool execution start | `tool_name`, `tool_type` |
| `tool_result` | Tool completion | `result`, `duration_ms`, `success` |
| `tool_error` | Tool failure | `error_message`, `error_type` |

### Team Events

| Event | Description | Data |
|-------|-------------|------|
| `team_supervisor_called` | Supervisor activation | `team_name`, `team_agents` |
| `team_agent_called` | Agent routing | `agent_name`, `supervisor_decision` |

## 🎨 Console Output Styles

### Standard Console

```python
flow.enable_observability(console_output=True)
```

Provides:
- Emoji-based event indicators
- Hierarchical indentation
- Timestamp information
- Event details and summaries

### Rich Console

```python
flow.enable_observability(rich_console=True)
```

Provides:
- Beautiful tree structures
- Color-coded events
- Tables for arguments and results
- Progress indicators
- Role indicators (Orchestrator, Supervisor, Agent, Tool)

## 📝 Event Logging

### In-Memory Logging

```python
# Default - events stored in memory
flow.enable_observability()

# Access events
events = flow._event_logger.get_events()
for event in events:
    print(f"{event.event_type}: {event.data}")
```

### Persistent Logging

```python
# SQLite backend (default)
flow.enable_observability(
    persistent=True,
    backend="sqlite3"
)

# File logging
flow.enable_observability(
    file_logging=True,
    log_file="workflow_events.log"
)
```

### Custom Event Logging

```python
# Emit custom events
flow.emit_custom_event("milestone_reached", {
    "milestone": "data_processing_complete",
    "processed_files": 42,
    "success_rate": 0.95
})
```

## 📈 Metrics & Analytics

### Flow Metrics

```python
# Get comprehensive metrics
metrics = flow.get_metrics()
print(f"Total Duration: {metrics['total_duration_ms']}ms")
print(f"Tool Executions: {metrics['tool_executions']}")
print(f"Agents Used: {metrics['agents_used']}")
print(f"Events Generated: {metrics['total_events']}")
```

### Flow Summary

```python
# Get flow-specific summary
summary = flow.get_flow_summary()
print(f"Flow: {summary['flow_name']}")
print(f"Duration: {summary['duration_ms']}ms")
print(f"Messages: {summary['total_messages']}")
print(f"Success: {summary['success']}")
```

## 🔧 Configuration Options

### Observability Settings

```python
flow.enable_observability(
    # Console output
    console_output=True,           # Enable console output
    rich_console=True,            # Use rich console (beautiful output)
    
    # Persistence
    persistent=True,              # Enable persistent storage
    backend="sqlite3",           # Storage backend (sqlite3, chroma)
    
    # File logging
    file_logging=True,           # Enable file logging
    log_file="events.log"        # Log file path
)
```

### Subscriber Configuration

```python
from agenticflow.observability import ConsoleSubscriber, FileSubscriber, MetricsCollector

# Custom console subscriber
console_sub = ConsoleSubscriber(
    show_timestamps=True,
    show_details=True
)

# Custom file subscriber
file_sub = FileSubscriber(
    log_file="custom_events.log",
    format="json"  # or "text"
)

# Add subscribers manually
flow._event_logger.get_event_bus().add_subscriber(console_sub)
flow._event_logger.get_event_bus().add_subscriber(file_sub)
```

## 🎯 Use Cases

### Debugging Workflows

```python
# Enable detailed logging for debugging
flow.enable_observability(
    rich_console=True,
    file_logging=True,
    log_file="debug.log"
)

# Run workflow
result = await flow.run("Complex multi-step task")

# Analyze events
events = flow._event_logger.get_events()
error_events = [e for e in events if e.event_type.endswith('_error')]
print(f"Found {len(error_events)} errors")
```

### Performance Monitoring

```python
# Monitor performance
flow.enable_observability(persistent=True)

# Run multiple workflows
for i in range(10):
    await flow.run(f"Task {i}")

# Analyze performance
metrics = flow.get_metrics()
print(f"Average duration: {metrics['total_duration_ms'] / 10}ms")
print(f"Tool efficiency: {metrics['tool_executions'] / metrics['total_duration_ms'] * 1000} tools/sec")
```

### Production Monitoring

```python
# Production setup with file logging
flow.enable_observability(
    console_output=False,  # Disable console in production
    file_logging=True,
    log_file="/var/log/agenticflow/workflow.log",
    persistent=True,
    backend="sqlite3"
)

# Monitor in production
try:
    result = await flow.run("Production task")
except Exception as e:
    # Log error and continue
    flow.emit_custom_event("production_error", {
        "error": str(e),
        "timestamp": time.time()
    })
```

## 🔍 Advanced Features

### Custom Event Types

```python
from agenticflow.observability import CustomEvent

# Create custom event
custom_event = CustomEvent(
    flow_id="my_flow",
    custom_type="business_metric",
    custom_data={
        "revenue": 10000,
        "customers": 150,
        "conversion_rate": 0.12
    }
)

# Emit custom event
flow._event_logger.get_event_bus().emit_event_sync(custom_event)
```

### Event Filtering

```python
# Filter events by type
events = flow._event_logger.get_events()
tool_events = [e for e in events if e.event_type.startswith('tool_')]
agent_events = [e for e in events if e.event_type.startswith('agent_')]

# Filter by agent
researcher_events = [e for e in events if e.agent_name == 'researcher']
```

### Real-time Monitoring

```python
import asyncio
from agenticflow.observability import BaseSubscriber

class CustomSubscriber(BaseSubscriber):
    async def handle_event(self, event):
        if event.event_type == "tool_result":
            print(f"Tool {event.tool_name} completed in {event.duration_ms}ms")
        
        if event.event_type == "agent_completed":
            print(f"Agent {event.agent_name} finished with {event.tools_used} tools")

# Add custom subscriber
flow._event_logger.get_event_bus().add_subscriber(CustomSubscriber())
```

## 🚨 Troubleshooting

### Common Issues

1. **No console output**: Ensure `console_output=True` or `rich_console=True`
2. **Missing tool events**: Check that agents have tools and observability is enabled
3. **Performance impact**: Use `console_output=False` in production
4. **Large log files**: Implement log rotation or use in-memory logging

### Debug Mode

```python
# Enable debug mode for detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

flow.enable_observability(
    rich_console=True,
    file_logging=True,
    log_file="debug.log"
)
```

## 📚 Examples

See the `examples/` directory for comprehensive observability examples:

- `rich_console_demo.py` - Rich console output demonstration
- `rich_teams_demo.py` - Team workflow with observability
- `console_comparison_demo.py` - Compare different console styles
- `researcher_writer_teams.py` - Multi-team coordination with monitoring
