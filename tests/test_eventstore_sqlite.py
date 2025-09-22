import asyncio
import os
import tempfile
from uuid import uuid4

import pytest

from agenticflow.core.events.event import AgenticEvent
from agenticflow.adapters.store.sqlite import SQLiteEventStore


@pytest.mark.asyncio
async def test_sqlite_event_store_persist_and_replay(tmp_path):
    db_path = tmp_path / "ev.sqlite3"
    store = SQLiteEventStore(db_path)

    stream_id = "s-1"
    evs = [
        AgenticEvent.create("task_assigned", {"a": 1}, trace_id="t1"),
        AgenticEvent.create("task_completed", {"b": 2}, trace_id="t1"),
    ]

    await store.append(stream_id, evs)

    # Read back sequentially
    out = []
    async for e in store.read_stream(stream_id):
        out.append(e)

    assert len(out) == 2
    assert out[0].event_type == "task_assigned"
    assert out[1].event_type == "task_completed"

    # Replay returns identical sequence
    replayed = await store.replay(stream_id)
    assert [e.id for e in replayed] == [e.id for e in evs]
    assert [e.payload for e in replayed] == [e.payload for e in evs]
