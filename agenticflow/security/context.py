from __future__ import annotations

from typing import Dict

from ..core.exceptions.base import SecurityError


class SecurityContext:
    def __init__(self, permissions: Dict[str, bool] | None = None) -> None:
        self.perms = permissions or {}

    async def authorize(self, operation: str, resource: str) -> None:
        key = f"{operation}:{resource}"
        if not self.perms.get(key, False):
            raise SecurityError(f"Access denied for {key}")
