from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

_JSON_ENABLED = False
_DEFAULT_LEVEL = logging.INFO


def enable_json_logging(level: str | int = "INFO") -> None:
    global _JSON_ENABLED, _DEFAULT_LEVEL
    _JSON_ENABLED = True
    _DEFAULT_LEVEL = _to_level(level)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(_DEFAULT_LEVEL)
    handler = logging.StreamHandler()
    handler.setLevel(_DEFAULT_LEVEL)

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
            payload: Dict[str, Any] = {
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            # Include extra if present
            for key in ("trace_id", "correlation_id", "workflow_id", "task_id", "agent_id"):
                val = getattr(record, key, None)
                if val is not None:
                    payload[key] = val
            return json.dumps(payload, ensure_ascii=False)

    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


def enable_text_logging(level: str | int = "INFO") -> None:
    global _JSON_ENABLED, _DEFAULT_LEVEL
    _JSON_ENABLED = False
    _DEFAULT_LEVEL = _to_level(level)
    logging.basicConfig(level=_DEFAULT_LEVEL, format="%(levelname)s %(name)s: %(message)s")


def _to_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    return getattr(logging, str(level).upper(), logging.INFO)


def get_logger(name: str) -> logging.Logger:
    # Configure from environment if first call
    _maybe_init_from_env()
    return logging.getLogger(name)


def _maybe_init_from_env() -> None:
    global _JSON_ENABLED
    if logging.getLogger().handlers:
        return
    log_format = os.environ.get("AGENTICFLOW_LOG_FORMAT", "json").lower()
    log_level = os.environ.get("AGENTICFLOW_LOG_LEVEL", "INFO")
    if log_format == "json":
        enable_json_logging(log_level)
    else:
        enable_text_logging(log_level)
    # Suppress noisy third-party loggers by default (e.g., httpx)
    try:
        logging.getLogger("httpx").setLevel(max(_to_level(log_level), logging.WARNING))
    except Exception:
        pass


def log_event(logger: logging.Logger, event_type: str, message: str, **fields: Any) -> None:
    extra = {k: v for k, v in fields.items() if v is not None}
    logger.info(f"{event_type}: {message}", extra=extra)