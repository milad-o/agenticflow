from __future__ import annotations

import os
from typing import Optional

from . import tracing


def enable_tracing_from_env(default_service_name: str = "agenticflow") -> bool:
    """Enable OpenTelemetry tracing if AGENTICFLOW_OTEL_ENABLE is truthy.

    Returns True if OTel was successfully enabled, False otherwise (no-op).
    """
    flag = os.environ.get("AGENTICFLOW_OTEL_ENABLE", "").lower() in {"1", "true", "yes", "on"}
    if not flag:
        return False

    service = os.environ.get("AGENTICFLOW_SERVICE_NAME", default_service_name)
    exporter = os.environ.get("AGENTICFLOW_OTEL_EXPORTER", "console")
    endpoint = os.environ.get("AGENTICFLOW_OTEL_ENDPOINT")
    try:
        return tracing.enable_otel_tracing(service_name=service, exporter=exporter, endpoint=endpoint)
    except Exception:
        # Safety: never fail app startup due to tracing wiring
        return False


def start_metrics_from_env(default_port: int = 8000) -> bool:
    """Start Prometheus metrics HTTP server if AGENTICFLOW_PROMETHEUS_ENABLE is truthy.

    Returns True if server started, False otherwise.
    """
    flag = os.environ.get("AGENTICFLOW_PROMETHEUS_ENABLE", "").lower() in {"1", "true", "yes", "on"}
    if not flag:
        return False

    port_str = os.environ.get("AGENTICFLOW_METRICS_PORT", str(default_port))
    try:
        port = int(port_str)
    except ValueError:
        port = default_port

    try:
        from prometheus_client import start_http_server  # type: ignore

        start_http_server(port)
        return True
    except Exception:
        # If prometheus_client is not installed or cannot bind, silently no-op
        return False
