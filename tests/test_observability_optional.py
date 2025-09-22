import os
import pytest

from agenticflow.observability.exporters import enable_tracing_from_env, start_metrics_from_env
from agenticflow.observability.tracing import get_tracer


@pytest.mark.asyncio
async def test_enable_tracing_noop_without_deps(monkeypatch):
    monkeypatch.setenv("AGENTICFLOW_OTEL_ENABLE", "true")
    # Force exporter to otlp to exercise branch; no deps expected
    monkeypatch.setenv("AGENTICFLOW_OTEL_EXPORTER", "otlp")

    res = enable_tracing_from_env()
    # Regardless of result, tracer must be usable
    tr = get_tracer("test")
    with tr.start_as_current_span("span") as span:
        if hasattr(span, "set_attributes"):
            try:
                span.set_attributes({"k": "v"})
            except Exception:
                pass
    assert isinstance(res, bool)


def test_start_metrics_noop_without_deps(monkeypatch):
    monkeypatch.setenv("AGENTICFLOW_PROMETHEUS_ENABLE", "true")
    monkeypatch.setenv("AGENTICFLOW_METRICS_PORT", "8001")

    res = start_metrics_from_env()
    assert isinstance(res, bool)
