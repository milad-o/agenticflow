from __future__ import annotations

"""Minimal DB utility placeholders for future expansion.

These helpers keep DB dependencies optional and out of core orchestration logic.
"""

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class QueryResult:
    rows: List[Tuple[Any, ...]]


def sqlite_query(db_path: str, sql: str, params: Iterable[Any] | None = None) -> QueryResult:
    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(sql, tuple(params or []))
        rows = cur.fetchall()
        return QueryResult(rows=rows)
    finally:
        conn.close()