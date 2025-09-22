from __future__ import annotations

from collections import defaultdict
from typing import Dict, Optional
import os


class Metrics:
    def __init__(self, namespace: str) -> None:
        self.namespace = namespace
        self.counters: Dict[str, int] = defaultdict(int)
        self.histograms: Dict[str, list[float]] = defaultdict(list)
        # Prometheus backend (optional)
        self._prom_enabled = False
        self._prom_counters: Dict[str, object] = {}
        self._prom_histos: Dict[str, object] = {}
        self._maybe_init_prom()

    def _maybe_init_prom(self) -> None:
        backend = os.environ.get("AGENTICFLOW_METRICS", "").lower()
        if backend != "prometheus":
            return
        try:
            from prometheus_client import Counter, Histogram, start_http_server  # type: ignore
            port = int(os.environ.get("AGENTICFLOW_PROM_PORT", "8000"))
            start_http_server(port)
            self._prom_enabled = True
            self._PromCounter = Counter  # type: ignore[attr-defined]
            self._PromHistogram = Histogram  # type: ignore[attr-defined]
        except Exception:
            self._prom_enabled = False

    def inc(self, name: str, value: int = 1) -> None:
        self.counters[name] += value
        if self._prom_enabled:
            c = self._prom_counters.get(name)
            if c is None:
                c = self._PromCounter(f"{self.namespace}_{name}".replace(".", "_"), f"Counter {name}")  # type: ignore[attr-defined]
                self._prom_counters[name] = c
            try:
                c.inc(value)  # type: ignore[attr-defined]
            except Exception:
                pass

    def record(self, name: str, value: float) -> None:
        self.histograms[name].append(value)
        if self._prom_enabled:
            h = self._prom_histos.get(name)
            if h is None:
                h = self._PromHistogram(f"{self.namespace}_{name}".replace(".", "_"), f"Histogram {name}")  # type: ignore[attr-defined]
                self._prom_histos[name] = h
            try:
                h.observe(value)  # type: ignore[attr-defined]
            except Exception:
                pass


# Backwards-compatible singleton-style meter
_global_meters: Dict[str, Metrics] = {}


def get_meter(name: str) -> Metrics:
    if name not in _global_meters:
        _global_meters[name] = Metrics(name)
    return _global_meters[name]
