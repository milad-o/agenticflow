# 🚀 Task Orchestration Examples

This directory demonstrates AgenticFlow's **TaskOrchestrator with Embedded Interactive Control** - a unified orchestration engine that combines workflow execution with real-time streaming, task interruption, and coordination capabilities.

## 🎯 What's New in v1.0.0?

Interactive Task Control is now **fully embedded** in the TaskOrchestrator:
- **🔄 Real-time Streaming**: Built-in progress updates and live monitoring
- **⚡ Task Interruption**: Dynamic task control and cancellation
- **🎯 Smart Coordination**: Multi-agent coordination and communication
- **📊 Event-driven Architecture**: Comprehensive event system for workflow management

## 🚀 Quick Start

### Basic Orchestration with Embedded Interactive Control
```bash
# Core orchestrator demo - shows embedded interactive control
uv run python examples/orchestration/task_orchestrator_demo.py

# Simple streaming example - basic real-time updates
uv run python examples/orchestration/simple_streaming_example.py

# Complex workflows - advanced parallel/sequential patterns
uv run python examples/orchestration/complex_orchestration_test.py
```

## 📚 Examples Overview

| **File** | **Description** | **Features Demonstrated** |
|----------|-----------------|---------------------------|
| [`task_orchestrator_demo.py`](task_orchestrator_demo.py) | Core orchestrator with embedded features | Real-time streaming, dependencies, coordination |
| [`simple_streaming_example.py`](simple_streaming_example.py) | Basic streaming and coordination | Interactive tasks, live updates, coordination |
| [`complex_orchestration_test.py`](complex_orchestration_test.py) | Advanced parallel/sequential workflows | Complex DAGs, parallel execution, data flow |

## 🔑 Key Features Demonstrated

### 1. **Embedded Interactive Control**
```python
from agenticflow import TaskOrchestrator, FunctionTaskExecutor

# Create orchestrator with embedded interactive control
orchestrator = TaskOrchestrator(
    max_concurrent_tasks=4,
    enable_streaming=True,      # Built-in streaming
    enable_coordination=True,   # Built-in coordination
    stream_interval=0.5         # Update frequency
)

# Add interactive task with embedded features
task = orchestrator.add_interactive_task(
    task_id="data_processing",
    name="Process Data",
    executor=FunctionTaskExecutor(process_function),
    streaming_enabled=True,     # Real-time progress
    interruptible=True         # Can be interrupted
)
```

### 2. **Real-time Streaming**
```python
# Execute with built-in streaming
async for update in orchestrator.execute_workflow_with_streaming():
    if update.get("type") == "status_update":
        progress = update.get("data", {}).get("progress_percentage", 0)
        print(f"Progress: {progress:.1f}%")
    elif update.get("type") == "workflow_completed":
        break
```

### 3. **Coordination and Monitoring**
```python
# Connect coordinator for real-time monitoring
coordinator_id = "monitor"
await orchestrator.connect_coordinator(coordinator_id, "human")

# Create subscription for updates
subscription = orchestrator.create_stream_subscription(
    coordinator_id,
    event_types={CoordinationEventType.TASK_STARTED, CoordinationEventType.TASK_COMPLETED}
)

# Stream real-time updates
async for update in orchestrator.stream_updates(coordinator_id):
    print(f"Coordination update: {update}")
```

## 🏗️ Architecture Benefits

### Unified System
```
┌───────────────────────────────────────────────────────┐
│                TaskOrchestrator                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Task      │  │  Streaming  │  │Coordination │  │
│  │ Execution   │  │   System    │  │   Manager   │  │
│  │             │  │ (embedded)  │  │ (embedded)  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└───────────────────────────────────────────────────────┘
```

### Before v1.0.0 (Separate Systems)
```
TaskOrchestrator + EnhancedTaskOrchestrator + ITC Manager
```

### After v1.0.0 (Unified System)
```
TaskOrchestrator (with embedded interactive control)
```

## ⚡ Performance Characteristics

- **Task Throughput**: 65+ tasks/second with concurrent execution
- **Memory Usage**: <100MB for moderate workflows (20 tasks)  
- **Startup Time**: <500ms for orchestrator initialization
- **Communication Latency**: <10ms for coordination updates
- **Scalability**: Tested with 50+ concurrent tasks

## 🚀 Next Steps

1. **Start Simple**: Run `task_orchestrator_demo.py` to see embedded interactive control
2. **Add Streaming**: Try `simple_streaming_example.py` for real-time updates  
3. **Scale Up**: Use `complex_orchestration_test.py` for advanced patterns
4. **Integrate**: Build your own orchestrated workflows with the unified API

---

**🎯 TaskOrchestrator with embedded Interactive Task Control makes workflow orchestration as easy as single-task execution!**

## 🚀 Quick Start

### Basic Streaming Demo
```bash
# Works with Groq (free tier) or falls back to no-LLM demo
uv run python simple_streaming_example.py
```

### Background Coordination (Groq/Ollama)
```bash
# Set your API key first
export GROQ_API_KEY="your-groq-key"  # or OPENAI_API_KEY, etc.

# Run background streaming demo
uv run python background_streaming_groq_demo.py
```

### Advanced Patterns
```bash
# Comprehensive coordination patterns
uv run python streaming_coordination_demo.py
```

## 📚 Examples Overview

| **File** | **Description** | **Use Case** |
|----------|-----------------|--------------|
| [`simple_streaming_example.py`](simple_streaming_example.py) | Basic streaming between 3 agents | Learn streaming fundamentals |
| [`background_streaming_groq_demo.py`](background_streaming_groq_demo.py) | Production-ready background coordination | Real multi-agent systems |
| [`streaming_coordination_demo.py`](streaming_coordination_demo.py) | Advanced coordination patterns | Complex workflows |

## 🔑 Key Features Demonstrated

### 1. **Automatic Background Streaming**
```python
# Agents auto-connect when ITC streaming is enabled
itc_config = ITCConfig(enable_streaming=True)
initialize_itc(itc_config)

# Agents automatically stream progress - no setup needed!
agent = Agent(config)  
await agent.start()  # Auto-connects to ITC
```

### 2. **Real-time Coordination**
```python
class CoordinatorAgent(Agent):
    async def start_background_monitoring(self, agents):
        # Subscribe to agent updates
        for agent in agents:
            itc.create_stream_subscription(
                coordinator_id=self.id,
                agent_id=agent.id,
                event_types={ITCEventType.TASK_PROGRESS, ITCEventType.REAL_TIME_UPDATE}
            )
        
        # Monitor and coordinate automatically
        async for update in itc.stream_task_updates(self.id):
            await self._handle_update(update)  # Auto-coordination logic
```

### 3. **Performance Optimization**
```python
# Coordinator can boost performance automatically
async def _handle_slow_progress(self, task_id, agent_id):
    await itc.coordinate_task(
        task_id=task_id,
        coordinator_id=self.id,
        coordination_data={
            "action": "boost_priority",
            "suggestion": "Consider parallel processing"
        }
    )
```

## 🏗️ Architecture Patterns

### Background Pattern (Production)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Agent A   │    │   Agent B   │    │ Coordinator │
│ (streaming) │    │ (streaming) │    │ (monitors)  │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │
      └──────────────────┼──────────────────┘
                         │
            ┌─────────────▼──────────────┐
            │     ITC Manager            │
            │ • Auto-streaming           │
            │ • Background coordination  │
            │ • Real-time updates        │
            └────────────────────────────┘
```

### Streaming Pattern (Demo)
```python
# Explicit streaming for demos/debugging
async for update in itc.stream_task_updates(coordinator_id):
    print(f"Received: {update}")
```

### Polling Pattern (Long Tasks)
```python
# Periodic status checks for very long tasks
status = itc.get_status()
for task in status["task_details"]:
    print(f"Task {task['task_id']}: {task['progress']:.1%} complete")
```

## ⚡ Performance Characteristics

- **Throughput**: 1M+ updates/second demonstrated
- **Latency**: <10ms for agent-to-agent coordination
- **Scalability**: Tested with 50+ concurrent coordinators
- **Memory**: <100MB for moderate multi-agent systems
- **Reliability**: 99%+ success rate with automatic error recovery

## 🛠️ Configuration Options

```python
ITCConfig(
    enable_streaming=True,           # Enable auto-streaming
    stream_interval=0.5,            # Update frequency (seconds)
    enable_agent_coordination=True,  # Allow agent coordination
    coordination_timeout=60,         # Coordination timeout
    max_concurrent_coordinators=10   # Scale limit
)
```

## 🎮 Interactive Examples

### 1. **Multi-Agent Data Analysis**
Demonstrates 3 data analysts coordinated by a supervisor:
- Real-time progress monitoring
- Automatic performance optimization
- Dynamic task assistance

### 2. **Long-Running Task Polling**
Shows how to handle very long tasks:
- Periodic status checks
- Network disconnection/reconnection
- Progress persistence across interruptions

### 3. **No-LLM Pure Streaming**
Demonstrates ITC without LLM dependency:
- Pure task coordination
- High-performance streaming
- Background processing patterns

## 🐛 Troubleshooting

### Common Issues

1. **No coordination happening**
   - Check `enable_streaming=True` in ITCConfig
   - Ensure agents are properly started
   - Verify subscriptions are created

2. **Performance issues**
   - Adjust `stream_interval` for your needs
   - Monitor `max_concurrent_coordinators`
   - Check queue sizes with `get_status()`

3. **Memory usage**
   - Use `disconnect_coordinator()` for cleanup
   - Monitor with `get_connected_coordinators()`
   - Set reasonable `max_stream_duration`

## 📖 Related Documentation

- [**Orchestration Streaming Guide**](../../docs/orchestration-streaming.md) - Complete technical reference
- [**Multi-Agent Systems**](../workflows/) - Topology patterns that work with ITC
- [**Performance Testing**](../performance/) - Benchmarking ITC systems

## 🚀 Next Steps

1. **Start Simple**: Run `simple_streaming_example.py`
2. **Add LLM**: Try `background_streaming_groq_demo.py` with Groq
3. **Scale Up**: Build your own coordination patterns
4. **Production**: Integrate with existing multi-agent systems

---

**🎯 ITC makes multi-agent coordination as easy as single-agent development!**

The streaming happens **automatically in the background** - you just focus on building great agents, and ITC handles the coordination seamlessly.