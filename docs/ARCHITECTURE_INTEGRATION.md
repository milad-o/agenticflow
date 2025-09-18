# AgenticFlow Integrated Architecture

## Architecture Overview

AgenticFlow has been successfully integrated into a unified orchestration system. The enhanced TaskOrchestrator now serves as the central engine with embedded interactive control capabilities.

### Integrated Systems:

1. **Enhanced TaskOrchestrator** (`orchestration/task_orchestrator.py`)
   - Central orchestration engine with embedded interactive control
   - Complex workflow execution with DAGs
   - Task state management and dependencies
   - Built-in real-time streaming updates
   - Task interruption and coordination capabilities
   - Progress monitoring and retry policies
   - Coordinator registration and management

2. **A2A Communication** (`orchestration/a2a_handler.py`)
   - Agent-to-agent messaging protocol (now part of orchestration)
   - Request/response patterns, timeouts, retries
   - In-memory message bus integrated with TaskOrchestrator
   - Message types: DIRECT, BROADCAST, REQUEST, RESPONSE, NOTIFICATION

3. **Multi-Agent Topologies** (`workflows/topologies.py`)
   - Communication patterns and routing rules
   - Network topology definitions (star, mesh, hierarchical, etc.)
   - Integrated with TaskOrchestrator for coordination

## Current Integrated Architecture

### Layer 1: Communication Foundation
**Module**: `orchestration/` (Integrated)
- **A2A Protocol**: Low-level messaging between agents (now part of orchestration)
- **Event Bus**: Centralized event routing and subscriptions
- **Stream Management**: Real-time data streaming capabilities
- **Message Routing**: Topology-aware message routing integrated with TaskOrchestrator

```python
# Enhanced A2A with streaming and events
class A2AHandler:
    def __init__(self):
        self.event_bus = EventBus()
        self.stream_manager = StreamManager()
        self.message_router = MessageRouter()
    
    async def stream_updates(self, subscriber_id: str, filters: Dict) -> AsyncGenerator:
        # Real-time streaming using A2A as transport
        
    async def coordinate_task(self, task_id: str, coordination_data: Dict) -> Dict:
        # Task coordination using A2A messaging
```

### Layer 2: Orchestration & Coordination  
**Module**: `orchestration/` (Fully Integrated)
- **TaskOrchestrator**: Main workflow execution engine with embedded interactive control
- **CoordinationManager**: Built-in multi-agent coordination capabilities
- **StreamingWorkflowStatus**: Real-time status with integrated streaming updates
- **InteractiveTaskNode**: Task nodes with native interruption and streaming

```python
class TaskOrchestrator:
    def __init__(self):
        self.dag = TaskDAG()
        self.status = StreamingWorkflowStatus()  # Enhanced with streaming
        self.coordination = CoordinationManager()  # New coordination layer
        self.communication = A2AHandler()  # Integrated communication
    
    async def execute_workflow(self) -> AsyncGenerator:
        # Execute with real-time streaming and coordination
        async for update in self._execute_with_streaming():
            yield update
    
    async def interrupt_task(self, task_id: str, reason: str) -> bool:
        # Interactive interruption using communication layer
    
    def create_stream_subscription(self, coordinator_id: str, filters: Dict):
        # Create real-time subscriptions for coordinators
```

### Layer 3: Multi-Agent Workflows
**Module**: `workflows/` (Simplified)
- **MultiAgentSystem**: High-level multi-agent coordination using orchestration
- **Topologies**: Communication pattern definitions (routing rules)
- **SupervisorAgent**: Uses orchestration for task decomposition and coordination

```python
class MultiAgentSystem:
    def __init__(self):
        self.orchestrator = TaskOrchestrator()  # Uses integrated orchestration
        self.topology = StarTopology()  # Defines routing patterns
        self.supervisor = SupervisorAgent()  # Uses orchestrator internally
```

## Key Integration Points:

### 1. Communication → Orchestration
- TaskOrchestrator uses A2A for agent communication
- Stream subscriptions managed through A2A transport
- Task coordination messages sent via A2A protocol

### 2. Interactive Control → Orchestration (Completed) 
- Real-time streaming fully embedded into TaskOrchestrator
- Task interruption natively built into task execution
- Coordinator management integrated into TaskOrchestrator

### 3. Orchestration → Multi-Agent
- MultiAgentSystem uses TaskOrchestrator internally
- SupervisorAgent delegates to TaskOrchestrator for execution
- Topology patterns configure A2A message routing

## Benefits:

1. **Single Source of Truth**: TaskOrchestrator becomes the main execution engine
2. **Layered Architecture**: Clear separation of concerns across layers
3. **Reduced Complexity**: No duplicate functionality between modules
4. **Better Performance**: Unified streaming and communication pathways
5. **Easier Maintenance**: Single orchestration system to maintain

## Integration Status: ✅ COMPLETED

**All phases have been successfully completed:**

1. ✅ **Phase 1**: Enhanced TaskOrchestrator with streaming and coordination
2. ✅ **Phase 2**: Integrated A2A communication into orchestration
3. ✅ **Phase 3**: Moved interactive control capabilities to orchestration module
4. ✅ **Phase 4**: Updated MultiAgentSystem to use integrated orchestration
5. ✅ **Phase 5**: Deprecated standalone ITC and basic task manager

## Example Usage:

```python
from agenticflow.orchestration import TaskOrchestrator
from agenticflow.workflows import MultiAgentSystem, StarTopology

# Create integrated system
orchestrator = TaskOrchestrator(
    enable_streaming=True,
    enable_coordination=True,
    communication_config=A2AConfig()
)

# Add tasks with real-time capabilities
task_id = orchestrator.add_function_task(
    "data_analysis",
    "Analyze dataset",
    analyze_function,
    streaming=True,  # Enable real-time updates
    interruptible=True  # Allow interruption
)

# Create coordinator subscription
subscription = orchestrator.create_stream_subscription(
    coordinator_id="human_supervisor",
    task_filters={"task_id": task_id}
)

# Execute with real-time streaming
async for update in orchestrator.execute_workflow():
    print(f"Status: {update}")
    
    # Interactive control
    if some_condition:
        await orchestrator.interrupt_task(task_id, "Priority changed")

# Multi-agent system using integrated orchestration
system = MultiAgentSystem(
    orchestrator=orchestrator,  # Uses integrated system
    topology=StarTopology(),
    agents=[research_agent, analysis_agent]
)
```

This architecture provides a clean, integrated approach where each layer has clear responsibilities and minimal overlap.