from __future__ import annotations

import sys
from typing import Any, Dict


class AuditLogger:
    def __init__(self) -> None:
        self._out = sys.stdout

    async def log(self, record: Dict[str, Any]) -> None:
        print({k: v for k, v in record.items()}, file=self._out)
