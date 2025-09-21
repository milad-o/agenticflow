from __future__ import annotations

from collections import defaultdict
from typing import Dict


class Metrics:
    def __init__(self) -> None:
        self.counters: Dict[str, int] = defaultdict(int)

    def inc(self, name: str, value: int = 1) -> None:
        self.counters[name] += value
