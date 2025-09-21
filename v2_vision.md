# AgenticFlow V2: Technical Framework Vision

## Framework Overview

**AgenticFlow V2** is a production-grade, open-source Python framework for building distributed multi-agent AI systems. It provides the foundational abstractions, reliability patterns, and operational tooling needed to deploy sophisticated agent-based applications that can handle real-world complexity and scale.

The framework is built on three core technical pillars:
1. **Event-Driven Architecture**: Immutable events with causality tracking for distributed consistency
2. **Fault-Tolerant Operations**: Circuit breakers, retries, and graceful degradation at every layer
3. **Observable Systems**: Comprehensive telemetry, tracing, and debugging capabilities

---

## Core Technical Architecture

### **1. Event-Sourced Foundation**

All system state changes flow through immutable events, providing natural auditability, debugging, and distributed consistency.

```python
@dataclass(frozen=True)
class AgenticEvent:
    """Immutable event with causality tracking"""
    id: UUID
    event_type: str
    payload: FrozenDict[str, Any]
    timestamp: int  # nanoseconds
    trace_id: str
    span_id: Optional[str]
    causality_vector: VectorClock
    
    def with_causality(self, actor_id: str) -> 'AgenticEvent':
        """Create new event with updated causality vector"""
        new_vector = self.causality_vector.increment(actor_id)
        return replace(self, causality_vector=new_vector)

class EventStore:
    """Persistent, queryable event storage"""
    async def append(self, stream_id: str, events: List[AgenticEvent]) -> None
    async def read_stream(self, stream_id: str, from_version: int = 0) -> AsyncIterator[AgenticEvent]
    async def query_events(self, predicate: EventPredicate) -> AsyncIterator[AgenticEvent]
```

### **2. Agent State Machines**

Agents manage complex behaviors through explicit finite state machines with observable transitions.

```python
class AgentState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING_RESOURCE = "waiting_resource"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    SUSPENDED = "suspended"

class Agent:
    """Finite state machine-based agent with observability"""
    
    def __init__(self, agent_id: str, capabilities: Set[str], 
                 state_machine: StateMachine):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.state_machine = state_machine
        self.current_state = AgentState.IDLE
        
        # Observability
        self.metrics = AgentMetrics(agent_id)
        self.tracer = get_tracer(f"agent.{agent_id}")
        
        # Tool execution with circuit breakers
        self.tool_registry = ToolRegistry()
        self.tool_circuits: Dict[str, CircuitBreaker] = {}
    
    async def handle_event(self, event: AgenticEvent) -> None:
        """Process event through state machine"""
        with self.tracer.start_as_current_span("agent_handle_event") as span:
            span.set_attributes({
                "agent_id": self.agent_id,
                "event_type": event.event_type,
                "current_state": self.current_state.value
            })
            
            try:
                # Attempt state transition
                new_state = await self.state_machine.transition(
                    self.current_state, event
                )
                
                if new_state and new_state != self.current_state:
                    await self._transition_state(new_state, event)
                
                # Execute state behavior
                await self._execute_state_behavior(event)
                
            except Exception as e:
                span.record_exception(e)
                await self._handle_error(e, event)
    
    async def invoke_tool_parallel(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """Execute multiple tools concurrently with circuit breakers"""
        semaphore = asyncio.Semaphore(MAX_PARALLEL_TOOLS)
        
        async def _protected_invoke(tool_call: ToolCall) -> ToolResult:
            circuit = self._get_tool_circuit(tool_call.tool_name)
            async with semaphore, circuit:
                return await self.tool_registry.invoke(tool_call)
        
        tasks = [_protected_invoke(call) for call in tool_calls]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### **3. Task Orchestration Engine**

Dynamic task graphs with dependency resolution, parallel execution, and failure recovery.

```python
@dataclass
class TaskNode:
    task_id: str
    agent_id: str
    task_type: str
    params: Dict[str, Any]
    dependencies: Set[str] = field(default_factory=set)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout_seconds: int = 300

class TaskGraph:
    """DAG of tasks with dependency tracking"""
    
    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.dependents: Dict[str, Set[str]] = defaultdict(set)
        self.completed: Set[str] = set()
        self.failed: Set[str] = set()
    
    def add_task(self, task: TaskNode) -> None:
        self.nodes[task.task_id] = task
        for dep in task.dependencies:
            self.dependents[dep].add(task.task_id)
    
    def get_ready_tasks(self) -> List[TaskNode]:
        """Get tasks whose dependencies are satisfied"""
        ready = []
        for task_id, task in self.nodes.items():
            if (task_id not in self.completed and 
                task_id not in self.failed and
                task.dependencies.issubset(self.completed)):
                ready.append(task)
        return ready

class WorkflowOrchestrator:
    """Execute task graphs with parallelism and fault tolerance"""
    
    def __init__(self, event_bus: EventBus, agent_registry: AgentRegistry):
        self.event_bus = event_bus
        self.agent_registry = agent_registry
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.metrics = OrchestratorMetrics()
    
    async def execute_workflow(self, workflow_def: WorkflowDefinition) -> str:
        """Execute workflow with full observability"""
        workflow_id = str(uuid4())
        
        with get_tracer("orchestrator").start_as_current_span("execute_workflow") as span:
            span.set_attributes({
                "workflow_id": workflow_id,
                "task_count": len(workflow_def.tasks)
            })
            
            try:
                # Build task graph
                task_graph = self._build_task_graph(workflow_def)
                
                # Create execution context
                execution = WorkflowExecution(
                    workflow_id=workflow_id,
                    task_graph=task_graph,
                    started_at=datetime.utcnow()
                )
                self.active_workflows[workflow_id] = execution
                
                # Execute graph
                await self._execute_task_graph(execution)
                
                return workflow_id
                
            except Exception as e:
                span.record_exception(e)
                await self._handle_workflow_failure(workflow_id, e)
                raise
    
    async def _execute_task_graph(self, execution: WorkflowExecution) -> None:
        """Execute task graph with parallelism and fault recovery"""
        task_graph = execution.task_graph
        
        while not task_graph.is_complete():
            # Get tasks ready for execution
            ready_tasks = task_graph.get_ready_tasks()
            
            if not ready_tasks:
                if task_graph.has_failed_tasks():
                    # Apply recovery strategies
                    await self._attempt_task_recovery(execution)
                    continue
                else:
                    # Deadlock or completion
                    break
            
            # Execute ready tasks in parallel
            task_futures = []
            for task in ready_tasks:
                future = asyncio.create_task(
                    self._execute_single_task(execution, task)
                )
                task_futures.append((task.task_id, future))
            
            # Wait for at least one task to complete
            if task_futures:
                done, pending = await asyncio.wait(
                    [future for _, future in task_futures],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task_id, future in task_futures:
                    if future in done:
                        try:
                            result = await future
                            task_graph.mark_completed(task_id, result)
                            self.metrics.record_task_success(task_id)
                        except Exception as e:
                            task_graph.mark_failed(task_id, e)
                            self.metrics.record_task_failure(task_id, str(e))
```

### **4. Communication Patterns**

Sophisticated agent interaction patterns with real-time capabilities and fault tolerance.

```python
class CommunicationProtocol(ABC):
    """Abstract protocol for agent communication"""
    
    @abstractmethod
    async def send_message(self, message: AgentMessage) -> bool:
        pass
    
    @abstractmethod 
    async def broadcast(self, message: AgentMessage, group: str) -> int:
        pass
    
    @abstractmethod
    async def subscribe(self, pattern: str, handler: MessageHandler) -> str:
        pass

class InteractionPattern(ABC):
    """Base for sophisticated multi-agent interactions"""
    
    @abstractmethod
    async def execute(self, participants: List[str], 
                     context: Dict[str, Any]) -> InteractionResult:
        pass

class NegotiationPattern(InteractionPattern):
    """Multi-round negotiation with convergence detection"""
    
    async def execute(self, participants: List[str], 
                     context: Dict[str, Any]) -> InteractionResult:
        max_rounds = context.get("max_rounds", 10)
        convergence_threshold = context.get("convergence_threshold", 0.95)
        
        proposals = {}
        convergence_history = []
        
        for round_num in range(max_rounds):
            # Collect proposals from all participants
            round_proposals = await self._collect_proposals(
                participants, context, round_num
            )
            proposals[round_num] = round_proposals
            
            # Calculate convergence
            convergence = self._calculate_convergence(round_proposals)
            convergence_history.append(convergence)
            
            if convergence >= convergence_threshold:
                return InteractionResult(
                    status="converged",
                    final_proposals=round_proposals,
                    rounds=round_num + 1,
                    convergence_history=convergence_history
                )
            
            # Prepare feedback for next round
            context["previous_rounds"] = proposals
            context["convergence_trend"] = convergence_history
        
        # Max rounds reached without convergence
        return InteractionResult(
            status="max_rounds_reached",
            final_proposals=proposals[max_rounds - 1],
            rounds=max_rounds,
            convergence_history=convergence_history
        )

class CommunicationBus:
    """Multi-protocol communication with interaction patterns"""
    
    def __init__(self, protocols: Dict[str, CommunicationProtocol]):
        self.protocols = protocols
        self.routing_table: Dict[str, str] = {}
        self.interaction_patterns: Dict[str, InteractionPattern] = {}
        self.message_history = MessageHistory()
    
    async def start_interaction(self, pattern_name: str, 
                              participants: List[str],
                              context: Dict[str, Any]) -> str:
        """Initiate sophisticated multi-agent interaction"""
        interaction_id = str(uuid4())
        
        pattern = self.interaction_patterns.get(pattern_name)
        if not pattern:
            raise ValueError(f"Unknown interaction pattern: {pattern_name}")
        
        # Execute interaction asynchronously
        asyncio.create_task(
            self._execute_interaction(interaction_id, pattern, participants, context)
        )
        
        return interaction_id
```

### **5. Supervisor & Task Decomposition**

AI-powered meta-agents that decompose complex queries into executable workflows.

```python
class TaskDecomposer:
    """AI-powered task decomposition with workflow generation"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.workflow_templates = WorkflowTemplateRegistry()
        self.capability_matcher = CapabilityMatcher()
    
    async def decompose_query(self, query: str, 
                            context: Dict[str, Any]) -> WorkflowDefinition:
        """Decompose natural language query into executable workflow"""
        
        # Analyze query complexity and requirements
        analysis = await self._analyze_query(query, context)
        
        # Check for existing templates
        template = await self.workflow_templates.find_matching_template(analysis)
        
        if template:
            # Customize template for specific query
            workflow = await self._customize_template(template, query, context)
        else:
            # Generate new workflow from scratch
            workflow = await self._generate_workflow(analysis, context)
        
        # Validate and optimize workflow
        workflow = await self._optimize_workflow(workflow)
        
        return workflow
    
    async def _generate_workflow(self, analysis: QueryAnalysis, 
                               context: Dict[str, Any]) -> WorkflowDefinition:
        """Generate workflow using LLM reasoning"""
        
        prompt = self._build_decomposition_prompt(analysis, context)
        
        response = await self.llm_client.generate(
            prompt,
            schema=WorkflowDefinitionSchema,
            temperature=0.1  # Low temperature for consistent decomposition
        )
        
        # Parse LLM response into workflow definition
        workflow_spec = WorkflowParser.parse(response.content)
        
        # Assign agents based on capabilities
        for task in workflow_spec.tasks:
            required_caps = task.required_capabilities
            agent_id = await self.capability_matcher.find_best_agent(required_caps)
            task.agent_id = agent_id
        
        return workflow_spec

class SupervisorAgent(Agent):
    """Meta-agent for workflow management and user intervention"""
    
    def __init__(self, supervisor_id: str, orchestrator: WorkflowOrchestrator):
        super().__init__(supervisor_id, {"task_decomposition", "workflow_management"})
        self.orchestrator = orchestrator
        self.task_decomposer = TaskDecomposer(LLMClient())
        self.user_intervention_handler = UserInterventionHandler()
    
    async def handle_user_query(self, query: str, 
                              user_context: Dict[str, Any]) -> str:
        """Decompose user query and orchestrate execution"""
        
        with self.tracer.start_as_current_span("supervisor_handle_query") as span:
            span.set_attributes({
                "query_length": len(query),
                "supervisor_id": self.agent_id
            })
            
            # Decompose query into workflow
            workflow_def = await self.task_decomposer.decompose_query(query, user_context)
            
            # Execute workflow
            workflow_id = await self.orchestrator.execute_workflow(workflow_def)
            
            # Set up intervention monitoring
            await self.user_intervention_handler.monitor_workflow(
                workflow_id, user_context.get("user_id")
            )
            
            return workflow_id
    
    async def handle_intervention(self, workflow_id: str, 
                                intervention: UserIntervention) -> None:
        """Handle real-time user intervention in active workflow"""
        
        execution = self.orchestrator.get_execution(workflow_id)
        if not execution:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if intervention.type == "pause":
            await execution.pause()
        elif intervention.type == "resume":
            await execution.resume()
        elif intervention.type == "modify":
            await self._modify_workflow(execution, intervention.modifications)
        elif intervention.type == "abort":
            await execution.abort(intervention.reason)
        else:
            raise ValueError(f"Unknown intervention type: {intervention.type}")
```

### **6. Observability & Debugging**

Comprehensive telemetry, tracing, and debugging capabilities for complex multi-agent systems.

```python
class DistributedTracing:
    """OpenTelemetry-based distributed tracing"""
    
    def __init__(self, service_name: str):
        self.tracer = trace.get_tracer(service_name)
        self.span_processors = [
            BatchSpanProcessor(JaegerExporter()),
            BatchSpanProcessor(ConsoleSpanExporter())
        ]
    
    @contextmanager
    def trace_agent_interaction(self, from_agent: str, to_agent: str,
                              interaction_type: str):
        """Trace agent-to-agent interactions"""
        with self.tracer.start_as_current_span(f"agent_interaction") as span:
            span.set_attributes({
                "from_agent": from_agent,
                "to_agent": to_agent,
                "interaction_type": interaction_type,
                "interaction_id": str(uuid4())
            })
            yield span

class SystemMetrics:
    """Comprehensive metrics collection"""
    
    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.gauges: Dict[str, Gauge] = {}
    
    def record_agent_state_transition(self, agent_id: str, 
                                    from_state: str, to_state: str):
        """Record agent state transitions"""
        counter = self._get_counter("agent_state_transitions", {
            "agent_id": agent_id,
            "from_state": from_state, 
            "to_state": to_state
        })
        counter.inc()
    
    def record_task_execution_time(self, task_type: str, duration_seconds: float):
        """Record task execution times"""
        histogram = self._get_histogram("task_execution_duration", {
            "task_type": task_type
        })
        histogram.observe(duration_seconds)

class DebugInterface:
    """Real-time debugging interface for agent systems"""
    
    def __init__(self, event_store: EventStore, orchestrator: WorkflowOrchestrator):
        self.event_store = event_store
        self.orchestrator = orchestrator
        self.live_streams: Dict[str, AsyncIterator] = {}
    
    async def get_agent_timeline(self, agent_id: str, 
                               time_range: TimeRange) -> List[AgenticEvent]:
        """Get chronological event timeline for agent"""
        predicate = EventPredicate(
            actor_id=agent_id,
            time_range=time_range
        )
        
        events = []
        async for event in self.event_store.query_events(predicate):
            events.append(event)
        
        return sorted(events, key=lambda e: e.timestamp)
    
    async def trace_workflow_execution(self, workflow_id: str) -> WorkflowTrace:
        """Get detailed execution trace for workflow"""
        execution = self.orchestrator.get_execution(workflow_id)
        if not execution:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Build execution trace
        trace = WorkflowTrace(workflow_id)
        
        for task_id, task_result in execution.task_results.items():
            task_trace = await self._build_task_trace(task_id, task_result)
            trace.add_task_trace(task_trace)
        
        return trace
    
    async def stream_agent_events(self, agent_id: str) -> AsyncIterator[AgenticEvent]:
        """Stream real-time events for agent"""
        stream_id = f"agent_stream_{agent_id}_{uuid4()}"
        
        predicate = EventPredicate(actor_id=agent_id)
        
        async for event in self.event_store.stream_events(predicate):
            yield event
```

### **7. Security & Sandboxing**

Comprehensive security model with isolation, encryption, and audit trails.

```python
class SecurityContext:
    """Zero-trust security context for agent operations"""
    
    def __init__(self, principal: str, roles: Set[str], 
                 session_id: str, encryption_key: bytes):
        self.principal = principal
        self.roles = roles
        self.session_id = session_id
        self.encryption_key = encryption_key
        self.permissions = self._resolve_permissions()
        self.audit_logger = AuditLogger()
    
    async def authorize_operation(self, operation: str, 
                                resource: str, context: Dict[str, Any]) -> bool:
        """Authorize operation with fine-grained permissions"""
        required_permission = f"{operation}:{resource}"
        
        if required_permission not in self.permissions:
            await self.audit_logger.log_access_denied(
                self.principal, operation, resource, "insufficient_permissions"
            )
            return False
        
        # Context-based authorization
        if not await self._validate_context(operation, resource, context):
            await self.audit_logger.log_access_denied(
                self.principal, operation, resource, "context_validation_failed"
            )
            return False
        
        await self.audit_logger.log_access_granted(
            self.principal, operation, resource
        )
        return True

class ExecutionSandbox:
    """Isolated execution environment for agent tools"""
    
    def __init__(self, sandbox_id: str, resource_limits: ResourceLimits):
        self.sandbox_id = sandbox_id
        self.resource_limits = resource_limits
        self.file_system = SandboxedFileSystem(sandbox_id)
        self.network_policy = NetworkPolicy()
        
    @asynccontextmanager
    async def execution_context(self):
        """Create sandboxed execution context"""
        # Apply resource limits
        await self._apply_resource_limits()
        
        try:
            # Create isolated namespace
            await self._create_namespace()
            
            yield SandboxContext(
                file_system=self.file_system,
                network_policy=self.network_policy,
                resource_monitor=self.resource_monitor
            )
        finally:
            # Cleanup sandbox
            await self._cleanup_sandbox()
    
    async def _apply_resource_limits(self):
        """Apply CPU, memory, and I/O limits"""
        # Implementation would use cgroups on Linux
        resource.setrlimit(resource.RLIMIT_AS, 
                          (self.resource_limits.max_memory, 
                           self.resource_limits.max_memory))
        
        resource.setrlimit(resource.RLIMIT_CPU,
                          (self.resource_limits.max_cpu_time,
                           self.resource_limits.max_cpu_time))

class EncryptedStorage:
    """Encrypted storage for sensitive agent data"""
    
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        self.storage_backend = StorageBackend()
    
    async def store(self, key: str, value: Any) -> None:
        """Store encrypted value"""
        serialized = pickle.dumps(value)
        encrypted = self.cipher.encrypt(serialized)
        await self.storage_backend.put(key, encrypted)
    
    async def retrieve(self, key: str) -> Any:
        """Retrieve and decrypt value"""
        encrypted = await self.storage_backend.get(key)
        if not encrypted:
            raise KeyError(f"Key {key} not found")
        
        decrypted = self.cipher.decrypt(encrypted)
        return pickle.loads(decrypted)
```

---

## Framework Design Principles

### **1. Composition Over Inheritance**
Components are designed as composable building blocks rather than deep inheritance hierarchies.

```python
# Good: Composition-based design
class Agent:
    def __init__(self, capabilities: Set[str], tools: ToolRegistry, 
                 memory: MemoryStore, communication: CommunicationBus):
        self.capabilities = capabilities
        self.tools = tools
        self.memory = memory
        self.communication = communication

# Rather than deep inheritance chains
```

### **2. Explicit Error Handling**
All failure modes are explicit and recoverable, with no silent failures.

```python
class TaskResult:
    """Explicit result type with error handling"""
    
    @classmethod
    def success(cls, value: Any) -> 'TaskResult':
        return cls(value=value, error=None, status="success")
    
    @classmethod
    def failure(cls, error: Exception) -> 'TaskResult':
        return cls(value=None, error=error, status="failed")
    
    def is_success(self) -> bool:
        return self.status == "success"
    
    def unwrap(self) -> Any:
        if self.error:
            raise self.error
        return self.value
```

### **3. Observable by Default**
Every component emits telemetry data for monitoring and debugging.

```python
@observable
class Agent:
    """All methods automatically instrumented"""
    
    @trace_calls
    @measure_latency
    async def process_task(self, task: Task) -> TaskResult:
        # Automatic tracing and metrics collection
        pass
```

### **4. Resource-Bounded Operations**
All operations have explicit resource limits and timeouts.

```python
@resource_bounded(max_memory="1GB", max_cpu_time="30s", timeout="60s")
async def execute_tool(tool: Tool, params: Dict[str, Any]) -> ToolResult:
    # Execution automatically bounded by resource limits
    pass
```

### **5. Immutable Data Structures**
Core data structures are immutable to prevent race conditions and enable safe concurrent access.

```python
@dataclass(frozen=True)
class TaskDefinition:
    """Immutable task definition"""
    task_id: str
    agent_id: str
    task_type: str
    params: FrozenDict[str, Any]
    dependencies: FrozenSet[str]
```

---

## Implementation Roadmap

### **Phase 1: Core Infrastructure (4 weeks)**
- [ ] Event store with persistence and replay
- [ ] Basic agent framework with FSM
- [ ] Task orchestration engine
- [ ] Security framework and sandboxing
- [ ] Testing infrastructure

### **Phase 2: Communication & Patterns (4 weeks)**
- [ ] Multi-protocol communication bus
- [ ] Basic interaction patterns (request/response, broadcast)
- [ ] Message persistence and replay
- [ ] Circuit breakers and retries
- [ ] Metrics collection framework

### **Phase 3: Advanced Features (6 weeks)**
- [ ] Supervisor agent with task decomposition
- [ ] Advanced interaction patterns (negotiation, auction)
- [ ] Distributed tracing integration
- [ ] Real-time debugging interface
- [ ] Comprehensive observability dashboard

### **Phase 4: Production Hardening (4 weeks)**
- [ ] Performance optimization and load testing
- [ ] Security audit and penetration testing
- [ ] Documentation and examples
- [ ] CI/CD pipeline and release automation
- [ ] Community setup (GitHub, discussions, contributing guide)

### **Phase 5: Ecosystem (Ongoing)**
- [ ] Tool and utility marketplace
- [ ] Integration connectors
- [ ] Example applications
- [ ] Community contributions and governance

---

## Technical Dependencies

### **Core Runtime**
```yaml
python: ">=3.11"
asyncio: ">=3.4.3"
typing_extensions: ">=4.5.0"
pydantic: ">=2.0.0"
structlog: ">=23.1.0"
```

### **Communication & Networking**
```yaml
aiohttp: ">=3.8.0"
websockets: ">=11.0.0"  
aioredis: ">=2.0.0"
nats-py: ">=2.3.0"
```

### **Observability**
```yaml
opentelemetry-api: ">=1.20.0"
opentelemetry-sdk: ">=1.20.0"
prometheus-client: ">=0.17.0"
jaeger-client: ">=4.8.0"
```

### **Security & Persistence**
```yaml
cryptography: ">=41.0.0"
sqlalchemy: ">=2.0.0"
alembic: ">=1.12.0"
psycopg: ">=3.1.0"
```

### **Development & Testing**
```yaml
pytest: ">=7.4.0"
pytest-asyncio: ">=0.21.0"
hypothesis: ">=6.80.0"
mypy: ">=1.5.0"
black: ">=23.7.0"
ruff: ">=0.0.285"
```

---

## Getting Started

### **Installation**
```bash
# Install from source (development)
git clone https://github.com/agenticflow/agenticflow.git
cd agenticflow
pip install -e ".[dev]"

# Run tests
pytest

# Start example
python examples/basic_workflow.py
```

### **Basic Usage**
```python
import asyncio
from agenticflow import Agent, Orchestrator, EventBus

async def main():
    # Create event bus
    event_bus = EventBus()
    
    # Create agents
    analyst = Agent("analyst", {"data_analysis"})
    reporter = Agent("reporter", {"report_generation"})
    
    # Create orchestrator
    orchestrator = Orchestrator(event_bus)
    orchestrator.register_agent(analyst)
    orchestrator.register_agent(reporter)
    
    # Define workflow
    workflow = WorkflowDefinition([
        TaskDefinition("analyze_data", "analyst", "analyze", {"dataset": "sales.csv"}),
        TaskDefinition("generate_report", "reporter", "create_report", 
                      dependencies={"analyze_data"})
    ])
    
    # Execute
    workflow_id = await orchestrator.execute_workflow(workflow)
    print(f"Started workflow: {workflow_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Contributing

AgenticFlow is an open-source project welcoming contributions from the community. See our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code style and standards
- Testing requirements
- Documentation guidelines
- Pull request process
- Community guidelines

**Repository**: https://github.com/milad-o/agenticflow
**License**: MIT
**Python**: 3.11+