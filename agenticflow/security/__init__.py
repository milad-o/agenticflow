"""
AgenticFlow Security Module

Comprehensive security framework for multi-agent AI systems including:
- Authentication and authorization
- Input validation and sanitization
- Data encryption and secure storage
- Access control and permission management
- Security audit logging
- Threat detection and prevention

Submodules:
- auth: Authentication and authorization mechanisms
- validation: Input validation, sanitization, and security checks
- encryption: Data encryption, key management, and secure communication
- access_control: Role-based access control and permission management

Security is paramount in AI agent systems that handle sensitive data and
have access to system resources.
"""

from .auth import SecurityContext, AuthenticationManager, AuthorizationManager
from .validation import (
    PathGuard, InputValidator, OutputSanitizer, SecurityValidator
)
from .encryption import EncryptionManager, KeyManager, SecureStorage
# from .access_control import AccessControlManager, Permission, SecurityRole  # TODO: Implement

__all__ = [
    # Authentication & Authorization
    "SecurityContext",
    "AuthenticationManager",
    "AuthorizationManager",

    # Validation & Sanitization
    "PathGuard",
    "InputValidator",
    "OutputSanitizer",
    "SecurityValidator",

    # Encryption & Secure Storage
    "EncryptionManager",
    "KeyManager",
    "SecureStorage",

    # Access Control (TODO: Implement)
    # "AccessControlManager",
    # "Permission",
    # "SecurityRole"
]