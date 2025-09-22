from __future__ import annotations

from typing import Dict, Any, Optional

from ..core.exceptions.base import SecurityError
from .audit import AuditLogger


class SecurityContext:
    def __init__(self, principal: str = "anonymous", permissions: Dict[str, bool] | None = None, *, audit_logger: Optional[AuditLogger] = None) -> None:
        self.principal = principal
        self.perms = permissions or {}
        self.audit_logger = audit_logger or AuditLogger()

    async def authorize(self, operation: str, resource: str) -> None:
        key = f"{operation}:{resource}"
        if not self.perms.get(key, False):
            await self.audit_logger.log({
                "principal": self.principal,
                "operation": operation,
                "resource": resource,
                "status": "denied",
            })
            raise SecurityError(f"Access denied for {key}")
        await self.audit_logger.log({
            "principal": self.principal,
            "operation": operation,
            "resource": resource,
            "status": "granted",
        })
