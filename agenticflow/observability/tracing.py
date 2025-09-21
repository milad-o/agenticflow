from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterator


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


def get_tracer(name: str) -> Tracer:
    return Tracer()
