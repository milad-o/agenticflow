from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from ..core.events.event import AgenticEvent
from ..core.events.store import EventStore


@dataclass
class WorkflowSummary:
    workflow_id: str
    event_counts: Dict[str, int]
    unique_tasks: int
    unique_agents: int
    started_ns: Optional[int]
    completed_ns: Optional[int]
    duration_s: Optional[float]
    status: str | None = None  # "completed", "failed", or "in_progress"
    first_event: Optional[str] = None
    last_event: Optional[str] = None
    failed_task_id: Optional[str] = None


@dataclass
class DebugInterface:
    event_store: EventStore

    async def list_workflows(self, limit: Optional[int] = None, status: Optional[str] = None) -> List[str]:
        """List workflow IDs by scanning events.

        If status is provided (completed|failed|cancelled|timed_out|in_progress), filter accordingly.
        If limit is provided, return only the most recent N matching.
        """
        wf_last_event: Dict[str, str] = {}
        async for ev in self.event_store.query_all():
            try:
                if ev.event_type == "workflow_started":
                    wid = ev.payload.get("workflow_id")
                    if wid:
                        wf_last_event[str(wid)] = ev.event_type
                else:
                    # Any event with a workflow_id in payload
                    wid = (ev.payload or {}).get("workflow_id") if isinstance(ev.payload, dict) else None
                    if wid:
                        wf_last_event[str(wid)] = ev.event_type
            except Exception:
                pass
        ids = list(wf_last_event.keys())
        if status:
            def _to_status(ev_type: str) -> str:
                if ev_type == "workflow_completed":
                    return "completed"
                if ev_type == "workflow_failed":
                    return "failed"
                if ev_type == "workflow_cancelled":
                    return "cancelled"
                if ev_type == "workflow_timed_out":
                    return "timed_out"
                return "in_progress"
            ids = [wid for wid in ids if _to_status(wf_last_event.get(wid, "")) == status]
        if limit is not None and limit >= 0:
            return ids[-limit:]
        return ids

    async def list_workflow_summaries(self, limit: Optional[int] = None, status: Optional[str] = None) -> List[WorkflowSummary]:
        """Return summaries for workflows, optionally filtered by status and limited.

        Results are ordered by discovery order (roughly chronological by last seen event in scan).
        """
        ids = await self.list_workflows(limit=limit, status=status)
        out: List[WorkflowSummary] = []
        for wid in ids:
            try:
                out.append(await self.get_workflow_summary(wid))
            except Exception:
                # If one workflow fails to summarize, continue with others
                continue
        return out

    async def get_workflow_timeline(
        self,
        workflow_id: str,
        *,
        event_types: Optional[Iterable[str]] = None,
        since_ns: Optional[int] = None,
        until_ns: Optional[int] = None,
    ) -> List[AgenticEvent]:
        """Return filtered events for a workflow ordered by timestamp."""
        events = await self.event_store.replay(workflow_id)
        out: List[AgenticEvent] = []
        for ev in events:
            if event_types and ev.event_type not in event_types:
                continue
            if since_ns is not None and ev.timestamp_ns < since_ns:
                continue
            if until_ns is not None and ev.timestamp_ns > until_ns:
                continue
            out.append(ev)
        return sorted(out, key=lambda e: e.timestamp_ns)

    async def get_agent_timeline(
        self,
        agent_id: str,
        *,
        event_types: Optional[Iterable[str]] = None,
        since_ns: Optional[int] = None,
        until_ns: Optional[int] = None,
    ) -> List[AgenticEvent]:
        """Return filtered events mentioning this agent, across all workflows."""
        results: List[AgenticEvent] = []
        async for ev in self.event_store.query_all():
            try:
                if ev.payload.get("agent_id") != agent_id:
                    continue
                if event_types and ev.event_type not in event_types:
                    continue
                if since_ns is not None and ev.timestamp_ns < since_ns:
                    continue
                if until_ns is not None and ev.timestamp_ns > until_ns:
                    continue
                results.append(ev)
            except Exception:
                # Some events may not have payload shaped as expected; ignore
                pass
        return sorted(results, key=lambda e: e.timestamp_ns)

    async def get_workflow_summary(self, workflow_id: str) -> WorkflowSummary:
        events = await self.event_store.replay(workflow_id)
        if not events:
            return WorkflowSummary(
                workflow_id=workflow_id,
                event_counts={},
                unique_tasks=0,
                unique_agents=0,
                started_ns=None,
                completed_ns=None,
                duration_s=None,
                status=None,
                first_event=None,
                last_event=None,
                failed_task_id=None,
            )
        counts: Dict[str, int] = {}
        tasks: set[str] = set()
        agents: set[str] = set()
        for ev in events:
            counts[ev.event_type] = counts.get(ev.event_type, 0) + 1
            # Collect seen tasks/agents if present
            t = ev.payload.get("task_id") if isinstance(ev.payload, dict) else None
            a = ev.payload.get("agent_id") if isinstance(ev.payload, dict) else None
            if t:
                tasks.add(str(t))
            if a:
                agents.add(str(a))
        started = min(e.timestamp_ns for e in events)
        completed = max(e.timestamp_ns for e in events)
        duration_s = (completed - started) / 1e9 if completed and started else None
        # Lifecycle status
        status = "in_progress"
        failed_task_id = None
        if any(e.event_type == "workflow_failed" for e in events):
            status = "failed"
            # Try to fetch failed task id from last failure
            for e in reversed(events):
                if e.event_type == "workflow_failed":
                    failed_task_id = (e.payload or {}).get("failed_task_id")
                    break
        if any(e.event_type == "workflow_completed" for e in events):
            status = "completed"
        first_event = events[0].event_type
        last_event = events[-1].event_type
        return WorkflowSummary(
            workflow_id=workflow_id,
            event_counts=counts,
            unique_tasks=len(tasks),
            unique_agents=len(agents),
            started_ns=started,
            completed_ns=completed,
            duration_s=duration_s,
            status=status,
            first_event=first_event,
            last_event=last_event,
            failed_task_id=failed_task_id,
        )
