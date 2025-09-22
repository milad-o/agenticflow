from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Optional
import random
from uuid import uuid4

from ..tasks.graph import TaskGraph, TaskNode
from ...core.events.event import AgenticEvent
from ...adapters.bus.memory import InMemoryEventBus
from ...adapters.store.memory import InMemoryEventStore
from ...agents.base.agent import Agent
from ...observability.tracing import get_tracer
from ...observability.metrics import get_meter
from ...observability.logging import get_logger, log_event
from ...security.context import SecurityContext
from ...core.exceptions.base import SecurityError


@dataclass(frozen=True)
class WorkflowDefinition:
    tasks: List[TaskNode]
    retry_backoff_base: Optional[float] = None
    retry_jitter: Optional[float] = None
    retry_max_backoff: Optional[float] = None
    max_duration_seconds: Optional[int] = None
    enable_compensation: bool = False


class Orchestrator:
    def __init__(
        self,
        *,
        event_bus=None,
        event_store=None,
        emit_workflow_started: bool = False,
        emit_workflow_lifecycle: bool = False,
        security: Optional[SecurityContext] = None,
        retry_backoff_base: float = 0.0,
        retry_jitter: float = 0.0,
        retry_max_backoff: Optional[float] = None,
        # Circuit breaker
        circuit_failure_threshold: int = 0,
        circuit_reset_seconds: float = 30.0,
        # Rate limiting
        default_agent_qps: Optional[float] = None,
        agent_rate_limits: Optional[Dict[str, float]] = None,
        # Concurrency
        max_parallelism: Optional[int] = None,
        per_agent_concurrency: Optional[int] = None,
    ) -> None:
        self._active: Dict[str, TaskGraph] = {}
        self._agents: Dict[str, Agent] = {}
        self._cancelled: Dict[str, str] = {}
        self._completed_order: Dict[str, List[str]] = {}
        self._task_results: Dict[str, Dict[str, Dict[str, object]]] = {}
        self._agent_failures: Dict[str, int] = {}
        self._circuit_until: Dict[str, float] = {}
        self._agent_next_ts: Dict[str, float] = {}
        self.event_bus = event_bus or InMemoryEventBus()
        self.event_store = event_store or InMemoryEventStore()
        self._emit_workflow_started = emit_workflow_started
        self._emit_workflow_lifecycle = emit_workflow_lifecycle
        self.security = security
        self._retry_backoff_base = retry_backoff_base
        self._retry_jitter = retry_jitter
        self._retry_max_backoff = retry_max_backoff
        # Circuit breaker and rate limits
        self._circuit_failure_threshold = circuit_failure_threshold
        self._circuit_reset_seconds = circuit_reset_seconds
        self._default_agent_qps = default_agent_qps
        self._agent_rate_limits = agent_rate_limits or {}
        # Concurrency
        self._max_parallelism = max_parallelism
        self._per_agent_concurrency = per_agent_concurrency
        # Optional task schema registry & policy guard
        self._task_schema_registry = None
        self._policy_guard = None
        try:
            from ...security.policy import TaskSchemaRegistry  # type: ignore
            # Attach later via setter for clarity
        except Exception:
            pass
        # Meter
        self._meter = get_meter("orchestrator")
        self._log = get_logger("orchestrator")

    def set_task_schema_registry(self, registry) -> None:
        self._task_schema_registry = registry

    def set_policy_guard(self, guard) -> None:
        self._policy_guard = guard

    def register_agent(self, agent: Agent) -> None:
        self._agents[agent.agent_id] = agent

    async def cancel_workflow(self, workflow_id: str, *, reason: str = "user_cancelled") -> None:
        self._cancelled[workflow_id] = reason

    def get_last_workflow_id(self) -> Optional[str]:
        return getattr(self, "_last_workflow_id", None)

    async def execute_workflow(self, defn: WorkflowDefinition, *, workflow_id: Optional[str] = None) -> str:
        # Build graph
        graph = TaskGraph()
        for t in defn.tasks:
            graph.add_task(t)
        # Preserve whether the caller supplied an ID for collision detection
        supplied_id = workflow_id
        workflow_id = workflow_id or f"wf-{uuid4()}"
        # If user supplied an explicit ID, enforce collision detection against active set and event store
        if supplied_id is not None:
            if workflow_id in self._active:
                raise ValueError(f"Workflow ID collision: '{workflow_id}' is already active")
            prev_events = await self.event_store.replay(workflow_id)
            if prev_events:
                raise ValueError(f"Workflow ID collision: '{workflow_id}' already exists in the event store")
        self._active[workflow_id] = graph
        self._last_workflow_id = workflow_id

        # Optionally persist workflow_started with DAG definition
        if self._emit_workflow_started:
            tasks_payload = [
                {
                    "task_id": t.task_id,
                    "agent_id": t.agent_id,
                    "task_type": t.task_type,
                    "params": dict(t.params),
                    "dependencies": list(t.dependencies),
                    "retries": t.retries,
                    "timeout_seconds": t.timeout_seconds,
                }
                for t in defn.tasks
            ]
            started = AgenticEvent.create(
                "workflow_started",
                {
                    "workflow_id": workflow_id,
                    "tasks": tasks_payload,
                    "retry_backoff_base": defn.retry_backoff_base,
                    "retry_jitter": defn.retry_jitter,
                    "retry_max_backoff": defn.retry_max_backoff,
                    "max_duration_seconds": defn.max_duration_seconds,
                    "enable_compensation": defn.enable_compensation,
                },
                trace_id=workflow_id,
            )
            await self.event_store.append(workflow_id, [started])
            await self.event_bus.publish(started)

        # Simple dependency-resolution loop (sequential)
        completed: Set[str] = set()
        attempts: Dict[str, int] = {}
        # Effective retry policy for this workflow
        eff_backoff = defn.retry_backoff_base if defn.retry_backoff_base is not None else self._retry_backoff_base
        eff_jitter = defn.retry_jitter if defn.retry_jitter is not None else self._retry_jitter
        eff_max = defn.retry_max_backoff if defn.retry_max_backoff is not None else self._retry_max_backoff
        await self._continue_workflow(
            workflow_id,
            graph,
            completed,
            attempts,
            eff_backoff,
            eff_jitter,
            eff_max,
            max_duration_seconds=defn.max_duration_seconds,
            enable_compensation=defn.enable_compensation,
        )
        return workflow_id

    async def resume_workflow(self, workflow_id: str) -> str:
        # Reconstruct DAG from workflow_started event
        events = await self.event_store.replay(workflow_id)
        start_ev = next((e for e in events if e.event_type == "workflow_started"), None)
        if not start_ev:
            raise ValueError(f"No workflow_started event found for {workflow_id}; cannot resume")
        tasks = start_ev.payload.get("tasks", [])
        graph = TaskGraph()
        for td in tasks:
            node = TaskNode(
                task_id=str(td["task_id"]),
                agent_id=str(td["agent_id"]),
                task_type=str(td["task_type"]),
                params=dict(td.get("params", {})),
                dependencies=set(map(str, td.get("dependencies", []))),
                retries=int(td.get("retries", 0)),
                timeout_seconds=int(td.get("timeout_seconds", 30)),
            )
            graph.add_task(node)
        # Compute completed and attempts
        completed: Set[str] = set()
        last_attempt: Dict[str, int] = {}
        for ev in events:
            if ev.event_type == "task_completed":
                tid = str(ev.payload.get("task_id"))
                if tid:
                    completed.add(tid)
            if ev.event_type in ("task_assigned", "task_failed", "task_completed"):
                tid = str(ev.payload.get("task_id"))
                if not tid:
                    continue
                att = ev.payload.get("attempt")
                if att is None:
                    # derive from correlation_id suffix if present
                    cid = ev.payload.get("correlation_id")
                    try:
                        if cid and ":" in cid:
                            att = int(cid.split(":")[-1])
                    except Exception:
                        att = None
                if isinstance(att, int):
                    last_attempt[tid] = max(last_attempt.get(tid, -1), att)
        attempts = {tid: last_attempt.get(tid, -1) + 1 for tid in graph.nodes.keys()}
        # Continue
        # Effective retry policy from stored event (fallback to orchestrator defaults)
        eff_backoff = start_ev.payload.get("retry_backoff_base")
        eff_jitter = start_ev.payload.get("retry_jitter")
        eff_max = start_ev.payload.get("retry_max_backoff")
        if eff_backoff is None:
            eff_backoff = self._retry_backoff_base
        if eff_jitter is None:
            eff_jitter = self._retry_jitter
        if eff_max is None:
            eff_max = self._retry_max_backoff
        await self._continue_workflow(
            workflow_id,
            graph,
            completed,
            attempts,
            eff_backoff,
            eff_jitter,
            eff_max,
            max_duration_seconds=start_ev.payload.get("max_duration_seconds"),
            enable_compensation=bool(start_ev.payload.get("enable_compensation", False)),
        )
        return workflow_id

    async def _continue_workflow(
        self,
        workflow_id: str,
        graph: TaskGraph,
        completed: Set[str],
        attempts: Dict[str, int],
        backoff_base: float,
        jitter: float,
        max_backoff: Optional[float],
        *,
        max_duration_seconds: Optional[int] = None,
        enable_compensation: bool = False,
    ) -> None:
        import time
        start_ns = time.time_ns()
        self._completed_order.setdefault(workflow_id, [])
        self._task_results.setdefault(workflow_id, {})
        remaining = set(graph.nodes.keys()) - set(completed)
        while remaining:
            # find ready tasks
            ready = [
                graph.nodes[tid]
                for tid in list(remaining)
                if graph.nodes[tid].dependencies.issubset(completed)
            ]
            if not ready:
                raise RuntimeError(f"Deadlock or missing dependencies in workflow {workflow_id}")

            # Check cancellation or max duration
            if workflow_id in self._cancelled:
                reason = self._cancelled[workflow_id]
                await self._emit_cancel_or_timeout(workflow_id, graph, completed, reason, enable_compensation)
                return
            if max_duration_seconds is not None:
                import time as _t
                if (_t.time_ns() - start_ns) / 1e9 > max_duration_seconds:
                    await self._emit_cancel_or_timeout(
                        workflow_id,
                        graph,
                        completed,
                        reason="max_duration_exceeded",
                        enable_compensation=enable_compensation,
                        timed_out=True,
                    )
                    return

            # Concurrency controls
            import asyncio as _asyncio
            class _Noop:
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc, tb):
                    return False
            global_sema = _asyncio.Semaphore(self._max_parallelism) if (self._max_parallelism and self._max_parallelism > 0) else None
            agent_semas: dict[str, _asyncio.Semaphore] = {}
            def _agent_lock(agent_id: str):
                if self._per_agent_concurrency and self._per_agent_concurrency > 0:
                    if agent_id not in agent_semas:
                        agent_semas[agent_id] = _asyncio.Semaphore(self._per_agent_concurrency)
                    return agent_semas[agent_id]
                return None

            async def _execute_task_once(task):
                # Optional concurrency locks
                gl = global_sema or _Noop()
                al = _agent_lock(task.agent_id) or _Noop()
                async with gl, al:
                    # BEGIN original per-task body
                    # Correlate attempt
                    corr_id = f"{workflow_id}:{task.task_id}:{attempts.get(task.task_id, 0)}"

                    # Security check before assignment
                    if self.security is not None:
                        try:
                            await self.security.authorize("assign:task", f"{task.agent_id}:{task.task_type}")
                            auth_event = AgenticEvent.create(
                                "task_authorized",
                                {
                                    "workflow_id": workflow_id,
                                    "task_id": task.task_id,
                                    "agent_id": task.agent_id,
                                    "task_type": task.task_type,
                                    "principal": self.security.principal,
                                },
                                trace_id=workflow_id,
                            )
                            await self.event_store.append(workflow_id, [auth_event])
                            await self.event_bus.publish(auth_event)
                        except SecurityError as se:
                            deny_event = AgenticEvent.create(
                                "task_authorization_denied",
                                {
                                    "workflow_id": workflow_id,
                                    "task_id": task.task_id,
                                    "agent_id": task.agent_id,
                                    "task_type": task.task_type,
                                    "principal": self.security.principal,
                                    "error": str(se),
                                    "correlation_id": corr_id,
                                },
                                trace_id=workflow_id,
                            )
                            await self.event_store.append(workflow_id, [deny_event])
                            await self.event_bus.publish(deny_event)
                            # Also emit workflow_failed if lifecycle enabled
                            if self._emit_workflow_lifecycle:
                                failed_wf = AgenticEvent.create(
                                    "workflow_failed",
                                    {
                                        "workflow_id": workflow_id,
                                        "failed_task_id": task.task_id,
                                        "agent_id": task.agent_id,
                                        "error": str(se),
                                        "attempt": attempts.get(task.task_id, 0),
                                        "correlation_id": corr_id,
                                    },
                                    trace_id=workflow_id,
                                )
                                await self.event_store.append(workflow_id, [failed_wf])
                                await self.event_bus.publish(failed_wf)
                            raise

                    # Circuit breaker check
                    import time as _t
                    now = _t.time()
                    until = self._circuit_until.get(task.agent_id, 0.0)
                    if until and now < until:
                        # Circuit open; block this task
                        blocked = AgenticEvent.create(
                            "task_circuit_blocked",
                            {
                                "workflow_id": workflow_id,
                                "task_id": task.task_id,
                                "agent_id": task.agent_id,
                                "reason": "circuit_open",
                                "until": until,
                                "correlation_id": corr_id,
                            },
                            trace_id=workflow_id,
                        )
                        await self.event_store.append(workflow_id, [blocked])
                        await self.event_bus.publish(blocked)
                        if self._emit_workflow_lifecycle:
                            failed_wf = AgenticEvent.create(
                                "workflow_failed",
                                {
                                    "workflow_id": workflow_id,
                                    "failed_task_id": task.task_id,
                                    "agent_id": task.agent_id,
                                    "error": "circuit_open",
                                    "attempt": attempts.get(task.task_id, 0),
                                    "correlation_id": corr_id,
                                },
                                trace_id=workflow_id,
                            )
                            await self.event_store.append(workflow_id, [failed_wf])
                            await self.event_bus.publish(failed_wf)
                        raise RuntimeError("circuit_open")
                    elif until and now >= until:
                        # Circuit closed
                        self._circuit_until.pop(task.agent_id, None)
                        if self._emit_workflow_lifecycle:
                            closed = AgenticEvent.create(
                                "circuit_closed",
                                {"agent_id": task.agent_id},
                                trace_id=workflow_id,
                            )
                            await self.event_store.append(workflow_id, [closed])
                            await self.event_bus.publish(closed)

                    # Rate limiting per agent (simple QPS)
                    qps = self._agent_rate_limits.get(task.agent_id, self._default_agent_qps)
                    if qps and qps > 0:
                        next_ts = self._agent_next_ts.get(task.agent_id, 0.0)
                        now = _t.time()
                        if now < next_ts:
                            wait = next_ts - now
                            throttle = AgenticEvent.create(
                                "agent_throttled",
                                {
                                    "agent_id": task.agent_id,
                                    "wait_seconds": wait,
                                    "workflow_id": workflow_id,
                                    "task_id": task.task_id,
                                },
                                trace_id=workflow_id,
                            )
                            await self.event_store.append(workflow_id, [throttle])
                            await self.event_bus.publish(throttle)
                            await _asyncio.sleep(wait)

                    # Optional params schema validation before assignment
                    if self._task_schema_registry is not None:
                        try:
                            self._task_schema_registry.validate(task.agent_id, task.task_type, dict(task.params))
                        except Exception as ve:
                            deny_event = AgenticEvent.create(
                                "task_validation_failed",
                                {
                                    "workflow_id": workflow_id,
                                    "task_id": task.task_id,
                                    "agent_id": task.agent_id,
                                    "task_type": task.task_type,
                                    "error": str(ve),
                                    "correlation_id": corr_id,
                                },
                                trace_id=workflow_id,
                            )
                            await self.event_store.append(workflow_id, [deny_event])
                            await self.event_bus.publish(deny_event)
                            if self._emit_workflow_lifecycle:
                                failed_wf = AgenticEvent.create(
                                    "workflow_failed",
                                    {
                                        "workflow_id": workflow_id,
                                        "failed_task_id": task.task_id,
                                        "agent_id": task.agent_id,
                                        "error": "task_params_invalid",
                                        "attempt": attempts.get(task.task_id, 0),
                                        "correlation_id": corr_id,
                                    },
                                    trace_id=workflow_id,
                                )
                                await self.event_store.append(workflow_id, [failed_wf])
                                await self.event_bus.publish(failed_wf)
                            raise

                    # Optional policy guard before assignment
                    if getattr(self, "_policy_guard", None) is not None:
                        try:
                            self._policy_guard.check(task.agent_id, task.task_type, dict(task.params))
                        except Exception as pe:
                            deny_event = AgenticEvent.create(
                                "task_policy_denied",
                                {
                                    "workflow_id": workflow_id,
                                    "task_id": task.task_id,
                                    "agent_id": task.agent_id,
                                    "task_type": task.task_type,
                                    "error": str(pe),
                                    "correlation_id": corr_id,
                                },
                                trace_id=workflow_id,
                            )
                            await self.event_store.append(workflow_id, [deny_event])
                            await self.event_bus.publish(deny_event)
                            if self._emit_workflow_lifecycle:
                                failed_wf = AgenticEvent.create(
                                    "workflow_failed",
                                    {
                                        "workflow_id": workflow_id,
                                        "failed_task_id": task.task_id,
                                        "agent_id": task.agent_id,
                                        "error": "task_policy_denied",
                                        "attempt": attempts.get(task.task_id, 0),
                                        "correlation_id": corr_id,
                                    },
                                    trace_id=workflow_id,
                                )
                                await self.event_store.append(workflow_id, [failed_wf])
                                await self.event_bus.publish(failed_wf)
                            raise

                    # Emit task_assigned
                    assigned = AgenticEvent.create(
                        "task_assigned",
                        {
                            "workflow_id": workflow_id,
                            "task_id": task.task_id,
                            "agent_id": task.agent_id,
                            "task_type": task.task_type,
                            "params": dict(task.params),
                            "correlation_id": corr_id,
                        },
                        trace_id=workflow_id,
                    )
                    await self.event_store.append(workflow_id, [assigned])
                    await self.event_bus.publish(assigned)
                    log_event(self._log, "task_assigned", f"{task.task_id} -> {task.agent_id}", workflow_id=workflow_id, task_id=task.task_id, agent_id=task.agent_id, correlation_id=corr_id)
                    # Update rate limit next_ts
                    qps = self._agent_rate_limits.get(task.agent_id, self._default_agent_qps)
                    if qps and qps > 0:
                        self._agent_next_ts[task.agent_id] = _t.time() + (1.0 / qps)
                    # Metrics
                    try:
                        self._meter.inc("tasks.assigned")
                    except Exception:
                        pass

                    # Execute via agent with tracing span
                    agent = self._agents.get(task.agent_id)
                    if not agent:
                        # Emit task_failed
                        failed = AgenticEvent.create(
                            "task_failed",
                            {
                                "workflow_id": workflow_id,
                                "task_id": task.task_id,
                                "agent_id": task.agent_id,
                                "reason": "agent_not_found",
                                "attempt": attempts.get(task.task_id, 0),
                                "correlation_id": corr_id,
                            },
                            trace_id=workflow_id,
                        )
                        await self.event_store.append(workflow_id, [failed])
                        await self.event_bus.publish(failed)
                        raise RuntimeError(f"Agent {task.agent_id} not found")

                    attempt = attempts.get(task.task_id, 0)
                    tr = get_tracer("orchestrator")
                    exec_span_id = None
                    try:
                        import asyncio
                        from ...observability.tracing import get_current_span_id
                        with tr.start_as_current_span(
                            "task_execute",
                            attributes={
                                "workflow_id": workflow_id,
                                "task_id": task.task_id,
                                "agent_id": task.agent_id,
                                "task_type": task.task_type,
                                "attempt": attempt,
                                "correlation_id": corr_id,
                            },
                        ):
                            exec_span_id = get_current_span_id()
                            import time as _t2
                            t0 = _t2.perf_counter()
                            # Install progress emitter for mid-task events
                            from ...observability.progress import set_progress_emitter, reset_progress_emitter
                            async def _emit(kind: str, data: dict) -> None:
                                ev = AgenticEvent.create(
                                    "task_progress",
                                    {
                                        "workflow_id": workflow_id,
                                        "task_id": task.task_id,
                                        "agent_id": task.agent_id,
                                        "task_type": task.task_type,
                                        "kind": kind,
                                        "data": data,
                                        "correlation_id": corr_id,
                                    },
                                    trace_id=workflow_id,
                                )
                                await self.event_store.append(workflow_id, [ev])
                                await self.event_bus.publish(ev)
                            _tok = set_progress_emitter(_emit)
                            try:
                                result = await asyncio.wait_for(
                                    agent.perform_task(task.task_type, task.params),
                                    timeout=task.timeout_seconds,
                                )
                            finally:
                                reset_progress_emitter(_tok)
                            dur = _t2.perf_counter() - t0
                            self._task_results[workflow_id][task.task_id] = result if isinstance(result, dict) else {"result": result}
                            try:
                                self._meter.record("tasks.exec_ms", dur * 1000.0)
                            except Exception:
                                pass
                        # Emit task_completed (idempotent)
                        if task.task_id not in completed:
                            completed_event = AgenticEvent.create(
                                "task_completed",
                                {
                                    "workflow_id": workflow_id,
                                    "task_id": task.task_id,
                                    "agent_id": task.agent_id,
                                    "task_type": task.task_type,
                                    "attempt": attempt,
                                    "correlation_id": corr_id,
                                },
                                trace_id=workflow_id,
                                span_id=exec_span_id,
                            )
                            await self.event_store.append(workflow_id, [completed_event])
                            await self.event_bus.publish(completed_event)
                            log_event(self._log, "task_completed", f"{task.task_id}", workflow_id=workflow_id, task_id=task.task_id, agent_id=task.agent_id, correlation_id=corr_id)
                            try:
                                self._meter.inc("tasks.completed")
                            except Exception:
                                pass
                            return ("completed", task.task_id)
                    except Exception as e:
                        will_retry = attempt < task.retries
                        failed = AgenticEvent.create(
                            "task_failed",
                            {
                                "workflow_id": workflow_id,
                                "task_id": task.task_id,
                                "agent_id": task.agent_id,
                                "error": str(e),
                                "attempt": attempt,
                                "will_retry": will_retry,
                                "correlation_id": corr_id,
                            },
                            trace_id=workflow_id,
                            span_id=exec_span_id,
                        )
                        await self.event_store.append(workflow_id, [failed])
                        await self.event_bus.publish(failed)
                        log_event(self._log, "task_failed", f"{task.task_id}: {e}", workflow_id=workflow_id, task_id=task.task_id, agent_id=task.agent_id, correlation_id=corr_id)
                        self._agent_failures[task.agent_id] = self._agent_failures.get(task.agent_id, 0) + 1
                        try:
                            self._meter.inc("tasks.failed")
                        except Exception:
                            pass
                        # Circuit open?
                        if self._circuit_failure_threshold and self._agent_failures[task.agent_id] >= self._circuit_failure_threshold:
                            until = _t.time() + self._circuit_reset_seconds
                            prev_until = self._circuit_until.get(task.agent_id, 0.0)
                            self._circuit_until[task.agent_id] = until
                            if not prev_until or _t.time() >= prev_until:
                                if self._emit_workflow_lifecycle:
                                    opened = AgenticEvent.create(
                                        "circuit_open",
                                        {"agent_id": task.agent_id, "until": until},
                                        trace_id=workflow_id,
                                    )
                                    await self.event_store.append(workflow_id, [opened])
                                    await self.event_bus.publish(opened)
                        if will_retry:
                            delay = 0.0
                            try:
                                self._meter.inc("tasks.retried")
                            except Exception:
                                pass
                            eff_backoff = task.retry_backoff_base if task.retry_backoff_base is not None else backoff_base
                            eff_jitter = task.retry_jitter if task.retry_jitter is not None else jitter
                            eff_max = task.retry_max_backoff if task.retry_max_backoff is not None else max_backoff
                            if eff_backoff and eff_backoff > 0:
                                delay = eff_backoff * (2 ** attempt)
                                if eff_max is not None:
                                    delay = min(delay, eff_max)
                                if eff_jitter and eff_jitter > 0:
                                    j = random.uniform(-eff_jitter, eff_jitter)
                                    delay = max(0.0, delay * (1.0 + j))
                            attempts[task.task_id] = attempt + 1
                            if delay > 0:
                                await _asyncio.sleep(delay)
                            return ("retry", task.task_id)
                        else:
                            if self._emit_workflow_lifecycle:
                                failed_wf = AgenticEvent.create(
                                    "workflow_failed",
                                    {
                                        "workflow_id": workflow_id,
                                        "failed_task_id": task.task_id,
                                        "agent_id": task.agent_id,
                                        "error": str(e),
                                        "attempt": attempt,
                                        "correlation_id": corr_id,
                                    },
                                    trace_id=workflow_id,
                                )
                                await self.event_store.append(workflow_id, [failed_wf])
                                await self.event_bus.publish(failed_wf)
                            # Optional compensation on failure
                            if enable_compensation:
                                await self._run_compensation(workflow_id, graph, completed)
                            raise
                # END per-task body

            # Run ready tasks concurrently with bounds
            coros = [_execute_task_once(task) for task in ready]
            results = await _asyncio.gather(*coros, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    raise res
                if not res:
                    continue
                status, tid = res
                if status == "completed":
                    completed.add(tid)
                    self._completed_order[workflow_id].append(tid)
                    remaining.remove(tid)
                elif status == "retry":
                    # keep in remaining for next loop
                    pass

        # If we exit loop, workflow completed
        if self._emit_workflow_lifecycle:
            completed_wf = AgenticEvent.create(
                "workflow_completed",
                {
                    "workflow_id": workflow_id,
                    "tasks_total": len(graph.nodes),
                    "tasks_completed": len(completed),
                },
                trace_id=workflow_id,
            )
            await self.event_store.append(workflow_id, [completed_wf])
            await self.event_bus.publish(completed_wf)
            try:
                self._meter.inc("workflow.completed")
            except Exception:
                pass

    async def _emit_cancel_or_timeout(
        self,
        workflow_id: str,
        graph: TaskGraph,
        completed: Set[str],
        reason: str,
        enable_compensation: bool,
        *,
        timed_out: bool = False,
    ) -> None:
        evt_type = "workflow_timed_out" if timed_out else "workflow_cancelled"
        evt = AgenticEvent.create(
            evt_type,
            {
                "workflow_id": workflow_id,
                "reason": reason,
                "tasks_completed": len(completed),
            },
            trace_id=workflow_id,
        )
        await self.event_store.append(workflow_id, [evt])
        await self.event_bus.publish(evt)
        if enable_compensation:
            await self._run_compensation(workflow_id, graph, completed)

    async def _run_compensation(self, workflow_id: str, graph: TaskGraph, completed: Set[str]) -> None:
        # Run compensation in reverse order of completion
        for tid in reversed(self._completed_order.get(workflow_id, [])):
            node = graph.nodes.get(tid)
            if not node or not node.enable_compensation:
                continue
            agent = self._agents.get(node.agent_id)
            if not agent:
                continue
            try:
                result = self._task_results.get(workflow_id, {}).get(tid)
                await agent.compensate_task(node.task_type, dict(node.compensation_params or {}), result)
                comp = AgenticEvent.create(
                    "task_compensated",
                    {
                        "workflow_id": workflow_id,
                        "task_id": tid,
                        "agent_id": node.agent_id,
                    },
                    trace_id=workflow_id,
                )
                await self.event_store.append(workflow_id, [comp])
                await self.event_bus.publish(comp)
            except Exception as _:
                # Best-effort compensation; continue
                pass
