from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import AsyncIterator, Iterable, List
from uuid import UUID

from ...core.events.event import AgenticEvent
from ...core.events.store import EventStore


_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    stream_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    timestamp_ns INTEGER NOT NULL,
    trace_id TEXT NOT NULL,
    span_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_stream ON events(stream_id, idx);
"""


class SQLiteEventStore(EventStore):
    def __init__(self, db_path: str | Path = "events.sqlite3") -> None:
        self.db_path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            conn.commit()

    async def append(self, stream_id: str, events: Iterable[AgenticEvent]) -> None:
        items = list(events)
        if not items:
            return
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(idx)+1, 0) FROM events WHERE stream_id=?", (stream_id,))
            base_idx_row = cur.fetchone()
            base_idx = int(base_idx_row[0] if base_idx_row and base_idx_row[0] is not None else 0)
            for offset, ev in enumerate(items):
                payload_text = json.dumps(ev.payload)
                cur.execute(
                    "INSERT INTO events (id, stream_id, idx, event_type, payload, timestamp_ns, trace_id, span_id)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(ev.id),
                        stream_id,
                        base_idx + offset,
                        ev.event_type,
                        payload_text,
                        ev.timestamp_ns,
                        ev.trace_id,
                        ev.span_id,
                    ),
                )
            conn.commit()

    async def read_stream(self, stream_id: str, from_offset: int = 0) -> AsyncIterator[AgenticEvent]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, event_type, payload, timestamp_ns, trace_id, span_id FROM events"
                " WHERE stream_id=? AND idx>=? ORDER BY idx ASC",
                (stream_id, from_offset),
            )
            for row in cur.fetchall():
                yield self._row_to_event(row)

    async def query_all(self) -> AsyncIterator[AgenticEvent]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, event_type, payload, timestamp_ns, trace_id, span_id FROM events ORDER BY rowid ASC")
            for row in cur.fetchall():
                yield self._row_to_event(row)

    async def replay(self, stream_id: str) -> List[AgenticEvent]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, event_type, payload, timestamp_ns, trace_id, span_id FROM events"
                " WHERE stream_id=? ORDER BY idx ASC",
                (stream_id,),
            )
            return [self._row_to_event(row) for row in cur.fetchall()]

    def _row_to_event(self, row: tuple) -> AgenticEvent:
        id_text, event_type, payload_text, timestamp_ns, trace_id, span_id = row
        return AgenticEvent(
            id=UUID(id_text),
            event_type=event_type,
            payload=json.loads(payload_text),
            timestamp_ns=int(timestamp_ns),
            trace_id=trace_id,
            span_id=span_id,
        )
