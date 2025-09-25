"""
Authentication and Authorization Managers

Centralized authentication and authorization management for the framework.
"""

from typing import Dict, Set, Optional, Any, List, Callable
from abc import ABC, abstractmethod
from .security_context import SecurityContext, SecurityUser, SecuritySession, SecurityError


class AuthenticationProvider(ABC):
    """Abstract base class for authentication providers."""

    @abstractmethod
    async def authenticate(self, username: str, credentials: Dict[str, Any]) -> SecurityUser:
        """Authenticate user with provided credentials."""
        pass

    @abstractmethod
    async def validate_token(self, token: str) -> Optional[SecurityUser]:
        """Validate authentication token."""
        pass


class AuthorizationProvider(ABC):
    """Abstract base class for authorization providers."""

    @abstractmethod
    async def check_permission(self, user: SecurityUser, permission: str) -> bool:
        """Check if user has specific permission."""
        pass

    @abstractmethod
    async def get_user_permissions(self, user: SecurityUser) -> Set[str]:
        """Get all permissions for user."""
        pass


class AuthenticationManager:
    """
    Manages authentication across the framework.

    Supports multiple authentication providers and handles session management.
    """

    def __init__(self, security_context: SecurityContext):
        """
        Initialize authentication manager.

        Args:
            security_context: Security context to manage
        """
        self.security_context = security_context
        self._providers: Dict[str, AuthenticationProvider] = {}
        self._default_provider: Optional[str] = None

    def register_provider(self, name: str, provider: AuthenticationProvider,
                         set_as_default: bool = False) -> None:
        """
        Register authentication provider.

        Args:
            name: Provider name
            provider: Authentication provider instance
            set_as_default: Whether to set as default provider
        """
        self._providers[name] = provider
        if set_as_default or not self._default_provider:
            self._default_provider = name

    async def authenticate(
        self,
        username: str,
        credentials: Dict[str, Any],
        provider: Optional[str] = None
    ) -> SecuritySession:
        """
        Authenticate user using specified or default provider.

        Args:
            username: Username to authenticate
            credentials: Authentication credentials
            provider: Specific provider to use (optional)

        Returns:
            SecuritySession: Created security session

        Raises:
            SecurityError: If authentication fails
        """
        provider_name = provider or self._default_provider
        if not provider_name or provider_name not in self._providers:
            raise SecurityError(f"Authentication provider '{provider_name}' not found")

        auth_provider = self._providers[provider_name]

        try:
            user = await auth_provider.authenticate(username, credentials)
            return self.security_context.authenticate_user(username, credentials)
        except Exception as e:
            raise SecurityError(f"Authentication failed: {str(e)}")

    async def validate_token(self, token: str, provider: Optional[str] = None) -> Optional[SecurityUser]:
        """
        Validate authentication token.

        Args:
            token: Token to validate
            provider: Specific provider to use (optional)

        Returns:
            SecurityUser if token is valid, None otherwise
        """
        provider_name = provider or self._default_provider
        if not provider_name or provider_name not in self._providers:
            return None

        auth_provider = self._providers[provider_name]
        return await auth_provider.validate_token(token)


class AuthorizationManager:
    """
    Manages authorization across the framework.

    Handles permission checking and role-based access control.
    """

    def __init__(self, security_context: SecurityContext):
        """
        Initialize authorization manager.

        Args:
            security_context: Security context to use
        """
        self.security_context = security_context
        self._providers: Dict[str, AuthorizationProvider] = {}
        self._default_provider: Optional[str] = None
        self._permission_cache: Dict[str, Dict[str, bool]] = {}

    def register_provider(self, name: str, provider: AuthorizationProvider,
                         set_as_default: bool = False) -> None:
        """
        Register authorization provider.

        Args:
            name: Provider name
            provider: Authorization provider instance
            set_as_default: Whether to set as default provider
        """
        self._providers[name] = provider
        if set_as_default or not self._default_provider:
            self._default_provider = name

    async def check_permission(self, permission: str, user: Optional[SecurityUser] = None) -> bool:
        """
        Check if user has specific permission.

        Args:
            permission: Permission to check
            user: User to check (uses current user if None)

        Returns:
            bool: True if user has permission
        """
        target_user = user or self.security_context.current_user
        if not target_user:
            return False

        # Check cache first
        cache_key = f"{target_user.user_id}:{permission}"
        if cache_key in self._permission_cache:
            return self._permission_cache[cache_key]

        # Use security context for basic check
        if self.security_context.check_permission(permission):
            self._permission_cache[cache_key] = True
            return True

        # Use authorization provider for advanced checks
        if self._default_provider and self._default_provider in self._providers:
            provider = self._providers[self._default_provider]
            result = await provider.check_permission(target_user, permission)
            self._permission_cache[cache_key] = result
            return result

        return False

    async def require_permission(self, permission: str, user: Optional[SecurityUser] = None) -> None:
        """
        Require specific permission, raise exception if not granted.

        Args:
            permission: Required permission
            user: User to check (uses current user if None)

        Raises:
            SecurityError: If permission not granted
        """
        if not await self.check_permission(permission, user):
            username = user.username if user else "unknown"
            raise SecurityError(f"Permission '{permission}' denied for user '{username}'")

    def clear_permission_cache(self, user_id: Optional[str] = None) -> None:
        """
        Clear permission cache.

        Args:
            user_id: Specific user ID to clear (clears all if None)
        """
        if user_id:
            keys_to_remove = [key for key in self._permission_cache.keys()
                             if key.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self._permission_cache[key]
        else:
            self._permission_cache.clear()


# Built-in providers
class SimpleAuthenticationProvider(AuthenticationProvider):
    """Simple authentication provider for development/testing."""

    def __init__(self, users: Dict[str, Dict[str, Any]] = None):
        """
        Initialize with user database.

        Args:
            users: Dict of username -> user data
        """
        self.users = users or {
            "admin": {
                "password": "admin123",
                "roles": {"admin", "user"},
                "permissions": {"read", "write", "delete", "admin"}
            },
            "user": {
                "password": "user123",
                "roles": {"user"},
                "permissions": {"read", "write"}
            }
        }

    async def authenticate(self, username: str, credentials: Dict[str, Any]) -> SecurityUser:
        """Authenticate against simple user database."""
        if username not in self.users:
            raise SecurityError("User not found")

        user_data = self.users[username]
        if credentials.get("password") != user_data["password"]:
            raise SecurityError("Invalid password")

        return SecurityUser(
            user_id=f"user_{username}",
            username=username,
            roles=set(user_data.get("roles", [])),
            permissions=set(user_data.get("permissions", []))
        )

    async def validate_token(self, token: str) -> Optional[SecurityUser]:
        """Simple token validation (not recommended for production)."""
        # This is a placeholder - implement proper token validation
        return None


class SimpleAuthorizationProvider(AuthorizationProvider):
    """Simple authorization provider for development/testing."""

    async def check_permission(self, user: SecurityUser, permission: str) -> bool:
        """Check permission against user's permissions and roles."""
        return (
            permission in user.permissions
            or any(role in permission for role in user.roles)
            or "admin" in user.roles
        )

    async def get_user_permissions(self, user: SecurityUser) -> Set[str]:
        """Get all permissions for user."""
        permissions = user.permissions.copy()

        # Add role-based permissions
        if "admin" in user.roles:
            permissions.update({"read", "write", "delete", "admin"})
        if "user" in user.roles:
            permissions.update({"read", "write"})

        return permissions