"""
Enhanced logging configuration for AgenticFlow.

Provides component-aware, user-friendly logging with clear context about:
- Which agent/component is generating logs
- User-relevant vs internal technical details
- Progress tracking and status updates
"""

import logging
import structlog
import sys
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(Enum):
    """Log levels for different audiences."""
    USER = "user"          # User-facing progress updates
    TECHNICAL = "technical"  # Developer debugging info
    INTERNAL = "internal"   # Framework internals


class ComponentLogger:
    """Enhanced logger with component awareness and user-friendly formatting."""

    def __init__(self, component_name: str, component_type: str = "system"):
        self.component_name = component_name
        self.component_type = component_type
        self._logger = structlog.get_logger()

    def _log(self, level: str, message: str, log_type: LogLevel = LogLevel.TECHNICAL, **kwargs):
        """Internal logging method with component context."""
        extra_context = {
            "component": self.component_name,
            "component_type": self.component_type,
            "log_type": log_type.value,
            **kwargs
        }

        # Route based on log type
        if log_type == LogLevel.USER:
            # Always show user messages with clear formatting
            getattr(self._logger, level)(f"[{self.component_name}] {message}", **extra_context)
        elif log_type == LogLevel.TECHNICAL:
            # Show technical details if in verbose mode
            getattr(self._logger, level)(message, **extra_context)
        else:  # INTERNAL
            # Only show in debug mode
            self._logger.debug(message, **extra_context)

    # User-facing methods (always visible)
    def user_info(self, message: str, **kwargs):
        """Log user-facing informational message."""
        self._log("info", f"🔄 {message}", LogLevel.USER, **kwargs)

    def user_success(self, message: str, **kwargs):
        """Log user-facing success message."""
        self._log("info", f"✅ {message}", LogLevel.USER, **kwargs)

    def user_warning(self, message: str, **kwargs):
        """Log user-facing warning message."""
        self._log("warning", f"⚠️ {message}", LogLevel.USER, **kwargs)

    def user_error(self, message: str, **kwargs):
        """Log user-facing error message."""
        self._log("error", f"❌ {message}", LogLevel.USER, **kwargs)

    def user_progress(self, message: str, step: int = None, total: int = None, **kwargs):
        """Log user-facing progress update."""
        progress_info = f" ({step}/{total})" if step and total else ""
        self._log("info", f"🚀 {message}{progress_info}", LogLevel.USER, **kwargs)

    # Technical methods (visible in verbose mode)
    def info(self, message: str, **kwargs):
        """Log technical information."""
        self._log("info", message, LogLevel.TECHNICAL, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log technical warning."""
        self._log("warning", message, LogLevel.TECHNICAL, **kwargs)

    def error(self, message: str, **kwargs):
        """Log technical error."""
        self._log("error", message, LogLevel.TECHNICAL, **kwargs)

    # Internal methods (debug only)
    def debug(self, message: str, **kwargs):
        """Log internal debug information."""
        self._log("debug", message, LogLevel.INTERNAL, **kwargs)

    def trace(self, message: str, **kwargs):
        """Log detailed trace information."""
        self._log("debug", f"TRACE: {message}", LogLevel.INTERNAL, **kwargs)


def configure_logging(
    level: str = "INFO",
    show_technical: bool = False,
    show_internal: bool = False
):
    """Configure structlog for AgenticFlow with component awareness."""

    def add_component_info(logger, method_name, event_dict):
        """Add component information to log records."""
        if 'component' in event_dict:
            component = event_dict['component']
            component_type = event_dict.get('component_type', 'system')
            log_type = event_dict.get('log_type', 'technical')

            # Format based on log type and visibility settings
            if log_type == 'user':
                # Always show user messages
                pass
            elif log_type == 'technical' and not show_technical:
                # Skip technical messages unless enabled
                event_dict['level'] = 'debug'
            elif log_type == 'internal' and not show_internal:
                # Skip internal messages unless enabled
                event_dict['level'] = 'debug'

        return event_dict

    def custom_renderer(logger, name, event_dict):
        """Custom renderer for user-friendly output."""
        log_type = event_dict.get('log_type', 'technical')
        component = event_dict.get('component', 'system')
        component_type = event_dict.get('component_type', 'system')

        # Clean up the event dict for output
        clean_dict = {k: v for k, v in event_dict.items()
                     if k not in ['component', 'component_type', 'log_type']}

        if log_type == 'user':
            # User messages: clean format
            message = clean_dict.get('event', '')
            extra = {k: v for k, v in clean_dict.items() if k != 'event'}
            if extra:
                return f"{message} {extra}"
            return message
        else:
            # Technical/internal: include component context
            timestamp = clean_dict.get('timestamp', '')
            level = clean_dict.get('level', 'INFO').upper()
            message = clean_dict.get('event', '')

            # Format: [TIMESTAMP] [LEVEL] [COMPONENT] MESSAGE
            return f"[{component_type}:{component}] {message}"

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            add_component_info,
            custom_renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_component_logger(component_name: str, component_type: str = "system") -> ComponentLogger:
    """Get a component-aware logger instance."""
    return ComponentLogger(component_name, component_type)


# Auto-configure on import with sensible defaults
configure_logging(level="INFO", show_technical=True, show_internal=False)