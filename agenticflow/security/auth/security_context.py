"""
Security Context

Manages security context for agent operations including user identity,
permissions, and security policies.
"""

from typing import Dict, Set, Optional, Any, List
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime, timedelta


class SecurityLevel(Enum):
    """Security levels for operations."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class SecurityUser:
    """Represents a user in the security context."""
    user_id: str
    username: str
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    security_level: SecurityLevel = SecurityLevel.PUBLIC
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecuritySession:
    """Represents a security session."""
    session_id: str
    user: SecurityUser
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None


class SecurityContext:
    """
    Central security context for agent operations.

    Manages user authentication, authorization, and security policies
    throughout the agent execution lifecycle.
    """

    def __init__(self, enable_security: bool = True):
        """
        Initialize security context.

        Args:
            enable_security: Whether to enforce security checks
        """
        self.enable_security = enable_security
        self._current_session: Optional[SecuritySession] = None
        self._security_policies: Dict[str, Any] = {}
        self._audit_log: List[Dict[str, Any]] = []

    @property
    def current_user(self) -> Optional[SecurityUser]:
        """Get current authenticated user."""
        return self._current_session.user if self._current_session else None

    @property
    def current_session(self) -> Optional[SecuritySession]:
        """Get current security session."""
        return self._current_session

    @property
    def is_authenticated(self) -> bool:
        """Check if current context has authenticated user."""
        return (
            self._current_session is not None
            and self._current_session.is_active
            and not self._is_session_expired()
        )

    def authenticate_user(
        self,
        username: str,
        credentials: Dict[str, Any],
        session_duration: Optional[timedelta] = None
    ) -> SecuritySession:
        """
        Authenticate user and create security session.

        Args:
            username: Username to authenticate
            credentials: Authentication credentials
            session_duration: Session duration (default: 1 hour)

        Returns:
            SecuritySession: Created security session

        Raises:
            SecurityError: If authentication fails
        """
        if not self.enable_security:
            # Create anonymous user for non-secure mode
            user = SecurityUser(
                user_id="anonymous",
                username="anonymous",
                roles={"public"},
                security_level=SecurityLevel.PUBLIC
            )
        else:
            # In real implementation, validate credentials here
            user = self._validate_credentials(username, credentials)

        # Create session
        session_duration = session_duration or timedelta(hours=1)
        session = SecuritySession(
            session_id=f"session_{int(time.time())}_{username}",
            user=user,
            expires_at=datetime.utcnow() + session_duration,
            source_ip=credentials.get("source_ip"),
            user_agent=credentials.get("user_agent")
        )

        self._current_session = session
        self._audit_security_event("user_authenticated", {
            "username": username,
            "session_id": session.session_id
        })

        return session

    def logout(self) -> bool:
        """
        Logout current user and invalidate session.

        Returns:
            bool: True if logout successful
        """
        if self._current_session:
            self._audit_security_event("user_logged_out", {
                "username": self._current_session.user.username,
                "session_id": self._current_session.session_id
            })
            self._current_session.is_active = False
            self._current_session = None
            return True
        return False

    def check_permission(self, permission: str) -> bool:
        """
        Check if current user has required permission.

        Args:
            permission: Permission to check

        Returns:
            bool: True if user has permission
        """
        if not self.enable_security:
            return True

        if not self.is_authenticated:
            return False

        user = self.current_user
        return (
            permission in user.permissions
            or any(role in permission for role in user.roles)
            or "admin" in user.roles
        )

    def require_permission(self, permission: str) -> None:
        """
        Require specific permission, raise exception if not granted.

        Args:
            permission: Required permission

        Raises:
            SecurityError: If permission not granted
        """
        if not self.check_permission(permission):
            self._audit_security_event("permission_denied", {
                "permission": permission,
                "user": self.current_user.username if self.current_user else "anonymous"
            })
            raise SecurityError(f"Permission denied: {permission}")

    def check_security_level(self, required_level: SecurityLevel) -> bool:
        """
        Check if current user meets required security level.

        Args:
            required_level: Required security level

        Returns:
            bool: True if user meets requirement
        """
        if not self.enable_security:
            return True

        if not self.is_authenticated:
            return required_level == SecurityLevel.PUBLIC

        user_level = self.current_user.security_level
        level_hierarchy = {
            SecurityLevel.PUBLIC: 0,
            SecurityLevel.INTERNAL: 1,
            SecurityLevel.CONFIDENTIAL: 2,
            SecurityLevel.RESTRICTED: 3
        }

        return level_hierarchy[user_level] >= level_hierarchy[required_level]

    def _validate_credentials(self, username: str, credentials: Dict[str, Any]) -> SecurityUser:
        """
        Validate user credentials.

        In a real implementation, this would integrate with your authentication system.
        """
        # Placeholder implementation
        if credentials.get("password") == "correct":
            return SecurityUser(
                user_id=f"user_{username}",
                username=username,
                roles={"user"},
                permissions={"read", "write"},
                security_level=SecurityLevel.INTERNAL
            )
        else:
            raise SecurityError("Invalid credentials")

    def _is_session_expired(self) -> bool:
        """Check if current session is expired."""
        if not self._current_session or not self._current_session.expires_at:
            return False
        return datetime.utcnow() > self._current_session.expires_at

    def _audit_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log security event for audit purposes."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details
        }
        self._audit_log.append(event)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get security audit log."""
        return self._audit_log.copy()


class SecurityError(Exception):
    """Security-related exception."""
    pass