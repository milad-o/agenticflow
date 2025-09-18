# AgenticFlow Workflow Examples

This directory showcases AgenticFlow's powerful multi-agent workflow capabilities, including various topologies, real-world applications, and advanced orchestration patterns.

## 📁 Examples

### [`realistic_data_analysis.py`](./realistic_data_analysis.py)
**Complete data analysis workflow**

```bash
uv run python examples/workflows/realistic_data_analysis.py
```

Demonstrates multi-agent data analysis with specialized agents for collection, processing, and visualization.

### [`real_web_search_example.py`](./real_web_search_example.py)
**Web search and content processing**

```bash
uv run python examples/workflows/real_web_search_example.py
```

Shows web search integration with content analysis and report generation.

### [`realistic_ecommerce_processing.py`](./realistic_ecommerce_processing.py)
**E-commerce workflow automation**

```bash
uv run python examples/workflows/realistic_ecommerce_processing.py
```

End-to-end e-commerce processing with inventory, pricing, and customer service agents.

### [`realistic_content_workflow.py`](./realistic_content_workflow.py)
**Content creation and management**

```bash
uv run python examples/workflows/realistic_content_workflow.py
```

Content pipeline with research, writing, editing, and publication agents.

### [`mesh_topology_example.py`](./mesh_topology_example.py)
**Advanced topology demonstration**

```bash
uv run python examples/workflows/mesh_topology_example.py
```

Explores complex agent interconnections with mesh topology patterns.

## 🏗️ Workflow Topologies

### Star Topology
- **Central supervisor** coordinating worker agents
- **Best for** simple delegation and coordination
- **Use cases** Document processing, task distribution

### Hierarchical Topology  
- **Tree-like structure** with multiple supervision levels
- **Best for** complex organizations and reporting
- **Use cases** Enterprise workflows, approval chains

### Pipeline Topology
- **Sequential processing** with feedback loops
- **Best for** linear workflows with stages
- **Use cases** Content creation, data processing pipelines

### Mesh Topology
- **Flexible connections** between specialized agents
- **Best for** complex collaborative workflows
- **Use cases** Research teams, creative processes

### Peer-to-Peer Topology
- **Equal agents** collaborating directly
- **Best for** brainstorming and consensus building
- **Use cases** Decision making, collaborative analysis

## 🚀 Quick Start

### Basic Multi-Agent Workflow

```python
from agenticflow.workflows.multi_agent import MultiAgentSystem
from agenticflow.workflows.topologies import TopologyType
from agenticflow import Agent, AgentConfig

# Create specialized agents
data_agent = Agent(AgentConfig(
    name="data_collector",
    instructions="Collect and validate data from various sources",
    tools=[web_search_tool, database_tool]
))

analysis_agent = Agent(AgentConfig(
    name="data_analyst", 
    instructions="Analyze data and generate insights",
    tools=[pandas_tool, visualization_tool]
))

# Create workflow system
workflow = MultiAgentSystem(
    supervisor=supervisor_agent,
    agents=[data_agent, analysis_agent],
    topology=TopologyType.STAR
)

# Execute workflow
result = await workflow.execute("Analyze sales trends for Q4")
```

### Pipeline Workflow

```python
from agenticflow.workflows.orchestration import TaskOrchestrator
from agenticflow.workflows.task_management import TaskPriority

# Create orchestrator
orchestrator = TaskOrchestrator(max_concurrent_tasks=4)

# Add pipeline tasks
orchestrator.add_agent_task(
    "data_collection", 
    "Collect customer data", 
    data_agent,
    priority=TaskPriority.HIGH
)

orchestrator.add_agent_task(
    "analysis",
    "Analyze customer patterns", 
    analysis_agent,
    dependencies=["data_collection"]
)

orchestrator.add_agent_task(
    "report_generation",
    "Generate final report",
    report_agent, 
    dependencies=["analysis"]
)

# Execute pipeline
results = await orchestrator.execute_workflow()
```

### Advanced Mesh Topology

```python
from agenticflow.workflows.topologies import MeshTopology

# Define agent connections
connections = {
    "researcher": ["writer", "fact_checker"],
    "writer": ["editor", "researcher"],
    "editor": ["writer", "publisher"],
    "fact_checker": ["researcher", "editor"],
    "publisher": ["editor"]
}

mesh_workflow = MeshTopology(
    agents={
        "researcher": research_agent,
        "writer": writing_agent,
        "editor": editing_agent,
        "fact_checker": fact_check_agent,
        "publisher": publish_agent
    },
    connections=connections
)

# Execute with dynamic routing
result = await mesh_workflow.execute(
    "Create comprehensive article on AI trends",
    enable_dynamic_routing=True
)
```

## 🎯 Key Features Demonstrated

### 🤝 Multi-Agent Coordination
- **Task decomposition** with intelligent distribution
- **Inter-agent communication** with message passing
- **Conflict resolution** and consensus building
- **Dynamic load balancing** across agents

### 🔄 Workflow Orchestration
- **DAG-based task management** with dependencies
- **Parallel execution** with concurrency control
- **Error handling** with retry policies
- **Progress tracking** with real-time monitoring

### 📊 Advanced Topologies
- **6 different topology types** for various use cases
- **Custom topology definition** with flexible connections
- **Dynamic reconfiguration** during execution
- **Performance optimization** for each topology

### 🛠️ Production Features
- **Workflow persistence** with state management
- **Monitoring and logging** throughout execution
- **Resource management** with limits and quotas
- **Failure recovery** with checkpoint restoration

## 📊 Performance Metrics

From the examples, typical performance characteristics:

| Topology | Setup Time | Execution Speed | Memory Usage | Best For |
|----------|------------|-----------------|--------------|----------|
| **Star** | Fast | Very Fast | Low | Simple delegation |
| **Pipeline** | Medium | Fast | Medium | Sequential processing |
| **Hierarchical** | Medium | Medium | Medium | Complex organizations |
| **Mesh** | Slow | Variable | High | Complex collaboration |
| **P2P** | Fast | Medium | Medium | Consensus building |

## 🔧 Configuration Examples

### Workflow with Custom Settings

```python
from agenticflow.workflows.orchestration import TaskOrchestratorConfig

config = TaskOrchestratorConfig(
    max_concurrent_tasks=8,
    task_timeout_seconds=300,
    retry_policy={
        "max_retries": 3,
        "retry_delay": 1.0,
        "exponential_backoff": True
    },
    enable_checkpoints=True,
    checkpoint_interval=10
)

orchestrator = TaskOrchestrator(config=config)
```

### Agent Communication Patterns

```python
from agenticflow.communication.protocols import A2AProtocol

# Setup agent-to-agent communication
communication = A2AProtocol(
    enable_message_history=True,
    message_retention_hours=24,
    enable_routing=True,
    routing_strategy="load_balanced"
)

workflow = MultiAgentSystem(
    agents=agents,
    communication_protocol=communication,
    topology=TopologyType.MESH
)
```

### Monitoring and Metrics

```python
from agenticflow.workflows.monitoring import WorkflowMonitor

monitor = WorkflowMonitor(
    enable_metrics=True,
    metrics_interval=1.0,
    enable_logging=True,
    log_level="INFO"
)

workflow = MultiAgentSystem(
    agents=agents,
    monitor=monitor
)

# Get real-time metrics
metrics = await workflow.get_metrics()
print(f"Tasks completed: {metrics.tasks_completed}")
print(f"Average task time: {metrics.avg_task_duration}s")
```

## 🤝 Integration Examples

### With Memory Systems

```python
from agenticflow.memory import EnhancedMemory

# Shared memory across workflow
shared_memory = EnhancedMemory(
    enable_vector_search=True,
    enable_cross_references=True
)

# Agents share workflow context
for agent in agents:
    agent.memory = shared_memory

workflow = MultiAgentSystem(agents=agents)
```

### With External Tools

```python
from agenticflow.tools import ToolRegistry

# Register workflow-specific tools
registry = ToolRegistry()
registry.register("web_search", web_search_tool)
registry.register("database", database_tool)
registry.register("email", email_tool)

# Make tools available to workflow agents
workflow = MultiAgentSystem(
    agents=agents,
    tool_registry=registry
)
```

## 🧪 Testing and Validation

### Workflow Testing

```python
import pytest
from agenticflow.workflows.testing import WorkflowTestHarness

@pytest.mark.asyncio
async def test_data_analysis_workflow():
    # Setup test harness
    harness = WorkflowTestHarness(
        workflow=data_analysis_workflow,
        mock_external_apis=True
    )
    
    # Execute test
    result = await harness.run_test(
        input_data="test_dataset.csv",
        expected_outputs=["analysis_report", "visualizations"]
    )
    
    # Validate results
    assert result.success
    assert "analysis_report" in result.outputs
    assert result.execution_time < 30.0  # seconds
```

### Performance Benchmarking

```python
from agenticflow.workflows.benchmarks import WorkflowBenchmark

# Benchmark different topologies
benchmark = WorkflowBenchmark()

results = await benchmark.compare_topologies(
    task="document_processing",
    topologies=[TopologyType.STAR, TopologyType.PIPELINE, TopologyType.MESH],
    iterations=10
)

print("Performance Comparison:")
for topology, metrics in results.items():
    print(f"{topology}: {metrics.avg_duration}s avg, {metrics.throughput} tasks/s")
```

## 📚 Learn More

- **[AgenticFlow Documentation](../../README.md)**: Main project documentation
- **[Agent Examples](../agent/README.md)**: Individual agent capabilities  
- **[Memory Examples](../memory/README.md)**: Shared memory systems
- **[Tools Examples](../tools/README.md)**: Tool integration

---

**🏗️ AgenticFlow Workflows enable sophisticated multi-agent collaboration for any complex automation challenge!**