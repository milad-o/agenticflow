# Task Orchestration with Embedded Interactive Control

## Overview

As of AgenticFlow v1.0.0, Interactive Task Control (ITC) is fully **embedded** within the TaskOrchestrator, providing a unified interface for workflow execution with built-in real-time streaming, task coordination, and monitoring capabilities.

## Key Features

### 1. **Embedded Interactive Control**

All interactive features are now built directly into the TaskOrchestrator:
- **Unified API**: Single point of entry for all orchestration and coordination
- **Built-in Streaming**: Real-time progress updates without separate configuration
- **Integrated Coordination**: Multi-agent communication embedded in workflow execution
- **Event-driven Architecture**: Comprehensive event system for monitoring

### 2. **Real-time Streaming**

**Automatic Progress Updates**
- Tasks automatically stream progress during execution
- Real-time status updates with customizable intervals
- Live workflow monitoring and metrics

**Coordinator Connections**
- Connect coordinators for real-time monitoring
- Stream subscriptions with event filtering
- Heartbeat mechanism for connection health

### 3. **Task Coordination**

**Interactive Task Management**
- Tasks can be interrupted dynamically during execution
- Coordinator connections for multi-agent systems
- Real-time coordination with structured data exchange

### 4. **Simplified Configuration**

**Direct TaskOrchestrator Parameters**
```python
# All configuration is now direct parameters
TaskOrchestrator(
    max_concurrent_tasks=10,
    enable_streaming=True,        # Built-in streaming
    enable_coordination=True,     # Built-in coordination  
    stream_interval=0.5,         # Update frequency
    coordination_timeout=60      # Coordination timeout
)
```

## Usage Patterns

### 1. Basic Orchestration with Embedded Interactive Control

```python
from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import FunctionTaskExecutor

# Create orchestrator with embedded interactive control
orchestrator = TaskOrchestrator(
    max_concurrent_tasks=4,
    enable_streaming=True,
    enable_coordination=True,
    stream_interval=0.5
)

# Add task with executor
orchestrator.add_function_task(
    task_id="process_data",
    description="Process Data",
    func=process_function,
    dependencies=[],
    interruptible=True
)
```

### 2. Real-time Streaming

```python
# Execute with built-in streaming
async for update in orchestrator.execute_workflow_with_streaming():
    if update.get("type") == "status_update":
        data = update.get("data", {})
        progress = data.get("progress_percentage", 0)
        print(f"Progress: {progress:.1f}%")
    elif update.get("type") == "workflow_completed":
        break
```

### 3. Coordinator Connections and Monitoring

```python
# Connect coordinator for real-time monitoring
coordinator_id = "monitor"
await orchestrator.connect_coordinator(
    coordinator_id=coordinator_id,
    coordinator_type="human",
    capabilities={"streaming": True, "interruption": True}
)

# Create stream subscription
subscription = orchestrator.create_stream_subscription(
    coordinator_id=coordinator_id,
    event_types={"task_started", "task_completed", "task_progress"}
)

# Stream real-time updates
async for update in orchestrator.stream_task_updates(coordinator_id):
    print(f"Coordination update: {update}")
```

### 4. Task Interruption

```python
# Interrupt specific task
success = await orchestrator.interrupt_task("process_data", "User requested stop")

# Interrupt all tasks
interrupted_tasks = await orchestrator.interrupt_all_tasks("Emergency stop")

# Get comprehensive status
status = orchestrator.get_comprehensive_status()
print(f"Active tasks: {status['workflow_status']['running_tasks']}")
```

## Architecture Changes

### Core Components

1. **TaskOrchestrator** - Central engine with embedded interactive control
2. **StreamSubscription** - Manages real-time update subscriptions  
3. **ConnectedCoordinator** - Tracks connected coordinator state
4. **InteractiveTask** - Enhanced with streaming and subscriber tracking

### Event System

- **Real-time Events**: `STREAM_START`, `STREAM_DATA`, `STREAM_END`
- **Coordinator Events**: `COORDINATOR_CONNECTED`, `COORDINATOR_DISCONNECTED`
- **Progress Events**: Enhanced with streaming support
- **Coordination Events**: `AGENT_COORDINATION`, `PLAN_MODIFICATION`

### Integration

- **Agent Class**: Automatic orchestrator registration and task tracking
- **Task Progress**: Real-time streaming of progress updates
- **Error Handling**: Proper cleanup on disconnection or errors

## Examples

See the following example files:
- `examples/orchestration/simple_streaming_example.py` - Basic streaming between agents
- `examples/orchestration/complex_orchestration_test.py` - Advanced coordination patterns

## Benefits

1. **Real-time Coordination**: Agents can coordinate dynamically during execution
2. **Flexible Communication**: Both streaming and polling patterns supported
3. **Scalable**: Handles multiple concurrent coordinators and subscriptions
4. **Robust**: Proper error handling and connection management
5. **Observable**: Complete event tracking and statistics

## Architecture Evolution

- All legacy components have been successfully integrated
- Standalone Interactive Task Control (ITC) system deprecated
- TaskOrchestrator now provides unified orchestration with embedded interactive features
- Backward compatibility maintained through updated examples

This unified orchestration system enables sophisticated multi-agent coordination patterns with real-time streaming communication, fulfilling all requirements for connected agents to communicate in real-time or poll status for long-running tasks.
