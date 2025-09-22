from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterator, Optional


_OTEL_ENABLED = False
_ot_trace = None


class NoopSpan:
    def __init__(self, name: str, attributes: Dict[str, object] | None = None):
        self.name = name
        self.attributes = attributes or {}

    def set_attributes(self, attrs: Dict[str, object]) -> None:
        self.attributes.update(attrs)

    def end(self) -> None:
        return None


class Tracer:
    @contextmanager
    def start_as_current_span(self, name: str, attributes: Dict[str, object] | None = None) -> Iterator[NoopSpan]:
        span = NoopSpan(name, attributes)
        try:
            yield span
        finally:
            span.end()


class _OtelTracerAdapter(Tracer):
    def __init__(self, name: str):
        # Late import to avoid hard dependency
        global _ot_trace
        tracer_provider = _ot_trace.get_tracer_provider()
        self._tracer = _ot_trace.get_tracer(name)

    @contextmanager
    def start_as_current_span(self, name: str, attributes: Dict[str, object] | None = None):
        span = self._tracer.start_span(name)
        if attributes:
            try:
                span.set_attributes(attributes)  # type: ignore[attr-defined]
            except Exception:
                pass
        try:
            yield span
        finally:
            try:
                span.end()
            except Exception:
                pass


def enable_otel_tracing(*, service_name: str, exporter: str = "console", endpoint: Optional[str] = None) -> bool:
    """Enable OpenTelemetry tracing if available.

    exporter: "console" (default) or "otlp". Endpoint used for OTLP if provided.
    """
    global _OTEL_ENABLED, _ot_trace
    try:
        from opentelemetry import trace as ot_trace  # type: ignore
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore

        if exporter == "otlp":
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # type: ignore
            span_exporter = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
        else:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter  # type: ignore
            span_exporter = ConsoleSpanExporter()

        resource = Resource.create({SERVICE_NAME: service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(span_exporter))
        ot_trace.set_tracer_provider(provider)

        _ot_trace = ot_trace
        _OTEL_ENABLED = True
        return True
    except Exception:
        _OTEL_ENABLED = False
        _ot_trace = None
        return False


def get_tracer(name: str) -> Tracer:
    if _OTEL_ENABLED and _ot_trace is not None:
        try:
            return _OtelTracerAdapter(name)  # type: ignore[return-value]
        except Exception:
            pass
    return Tracer()


def get_current_span_id() -> Optional[str]:
    """Return the current span id if OpenTelemetry is enabled, else None."""
    if not _OTEL_ENABLED or _ot_trace is None:
        return None
    try:
        span = _ot_trace.get_current_span()
        if span is None:
            return None
        ctx = span.get_span_context()  # type: ignore[attr-defined]
        sid = getattr(ctx, "span_id", None)
        if sid is None:
            return None
        # Normalize to hex string if it's an int, else str()
        try:
            return format(sid, "x") if isinstance(sid, int) else str(sid)
        except Exception:
            return str(sid)
    except Exception:
        return None


def inject_trace_context(headers: Dict[str, str]) -> None:
    """Inject current trace context into headers (W3C traceparent) if OTEL is enabled.

    Mutates headers in place; no-op if tracing not enabled or propagator unavailable.
    """
    if not _OTEL_ENABLED:
        return
    try:
        from opentelemetry.propagate import inject  # type: ignore
        inject(headers)
    except Exception:
        # Best-effort only
        pass


@contextmanager
def use_trace_context_from_headers(headers: Dict[str, str]):
    """Activate trace context from headers during the with-block if OTEL is enabled.

    No-op if tracing not enabled or propagator unavailable.
    """
    if not _OTEL_ENABLED:
        yield
        return
    token = None
    try:
        from opentelemetry.propagate import extract  # type: ignore
        from opentelemetry import context as context_api  # type: ignore
        ctx = extract(headers)
        token = context_api.attach(ctx)
        yield
    except Exception:
        # Fallback: still execute handler
        yield
    finally:
        if token is not None:
            try:
                from opentelemetry import context as context_api  # type: ignore
                context_api.detach(token)
            except Exception:
                pass
