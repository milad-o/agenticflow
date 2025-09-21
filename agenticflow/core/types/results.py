from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class TaskResult(Generic[T]):
    value: Optional[T]
    error: Optional[Exception]
    status: str

    @classmethod
    def success(cls, value: T) -> "TaskResult[T]":
        return cls(value=value, error=None, status="success")

    @classmethod
    def failure(cls, error: Exception) -> "TaskResult[T]":
        return cls(value=None, error=error, status="failed")

    def is_success(self) -> bool:
        return self.status == "success"

    def unwrap(self) -> T:
        if self.error is not None:
            raise self.error
        assert self.value is not None
        return self.value
