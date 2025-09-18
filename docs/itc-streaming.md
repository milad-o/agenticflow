# ITC Streaming and Real-time Coordination Features

## Overview

The Interactive Task Control (ITC) system has been enhanced with comprehensive streaming and real-time coordination capabilities, enabling connected agents to communicate in real-time or poll status for long-running tasks.

## Key Features

### 1. Real-time Streaming Communication

**Connected Coordinators**
- Agents can connect as coordinators for real-time interaction
- Support for different coordinator types: `agent`, `supervisor`, `coordinator_agent`, `human`
- Connection capabilities tracking (streaming, interruption, task coordination)

**Stream Subscriptions**
- Flexible subscription system for real-time updates
- Filter by task ID, agent ID, or event types
- Event types: `TASK_PROGRESS`, `REAL_TIME_UPDATE`, `TASK_COMPLETED`, etc.

**Real-time Updates**
- Agents can stream progress updates automatically
- Custom real-time updates with structured data
- Heartbeat mechanism for connection monitoring

### 2. Task Coordination

**Inter-agent Coordination**
- Coordinators can modify running tasks dynamically
- Real-time coordination with structured coordination data
- Locking mechanism to prevent coordination conflicts

**Task Monitoring**
- Real-time task progress tracking
- Status polling for long-running tasks
- Connected coordinator tracking and management

### 3. Enhanced Configuration

**ITCConfig Settings**
```python
class ITCConfig(BaseModel):
    enable_streaming: bool = True
    stream_interval: float = 0.5  # seconds
    max_stream_duration: int = 3600  # seconds
    enable_agent_coordination: bool = True
    coordination_timeout: int = 60  # seconds
    max_concurrent_coordinators: int = 10
```

## Usage Patterns

### 1. Streaming Communication
For real-time task monitoring and coordination:

```python
# Connect coordinator for streaming
await itc.connect_coordinator(
    coordinator_id=agent.id,
    coordinator_type="coordinator_agent",
    capabilities={"streaming": True, "interruption": True}
)

# Subscribe to streams
subscription_id = itc.create_stream_subscription(
    coordinator_id=agent.id,
    event_types={ITCEventType.TASK_PROGRESS, ITCEventType.REAL_TIME_UPDATE}
)

# Stream updates
async for update in itc.stream_task_updates(agent.id):
    # Handle real-time updates
    if update.get("type") == "real_time_update":
        await handle_update(update)
```

### 2. Polling Communication
For long-running tasks or periodic status checks:

```python
# Poll system status periodically
status = itc.get_status()
active_tasks = len(status["task_details"])

for task in status["task_details"]:
    task_id = task["task_id"]
    progress = task["progress"] 
    duration = task["duration"]
    print(f"{task_id}: {progress:.0%} complete, {duration:.1f}s running")
```

### 3. Task Coordination
Coordinators can dynamically modify tasks:

```python
# Coordinate running task
result = await itc.coordinate_task(
    task_id=task_id,
    coordinator_id=coordinator.id,
    coordination_data={
        "action": "boost_priority",
        "suggestion": "Consider parallel processing"
    }
)
```

## Architecture Changes

### Core Components

1. **ITCManager** - Enhanced with streaming and coordination
2. **StreamSubscription** - Manages real-time update subscriptions  
3. **ConnectedCoordinator** - Tracks connected coordinator state
4. **InteractiveTask** - Enhanced with streaming and subscriber tracking

### Event System

- **Real-time Events**: `STREAM_START`, `STREAM_DATA`, `STREAM_END`
- **Coordinator Events**: `COORDINATOR_CONNECTED`, `COORDINATOR_DISCONNECTED`
- **Progress Events**: Enhanced with streaming support
- **Coordination Events**: `AGENT_COORDINATION`, `PLAN_MODIFICATION`

### Integration

- **Agent Class**: Automatic ITC registration and task tracking
- **Task Progress**: Real-time streaming of progress updates
- **Error Handling**: Proper cleanup on disconnection or errors

## Examples

See the following example files:
- `examples/itc/simple_streaming_example.py` - Basic streaming between agents
- `examples/itc/streaming_coordination_demo.py` - Advanced coordination patterns

## Benefits

1. **Real-time Coordination**: Agents can coordinate dynamically during execution
2. **Flexible Communication**: Both streaming and polling patterns supported
3. **Scalable**: Handles multiple concurrent coordinators and subscriptions
4. **Robust**: Proper error handling and connection management
5. **Observable**: Complete event tracking and statistics

## Migration from HITL

- All HITL references removed from core system
- HITL examples preserved for backward compatibility
- ITC provides superset of HITL functionality with real-time enhancements

This enhanced ITC system enables sophisticated multi-agent coordination patterns with real-time streaming communication, fulfilling the requirement for connected agents to communicate in real-time or poll status for long-running tasks.