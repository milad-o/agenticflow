"""
Input Validation and Output Sanitization

Security validators for agent inputs and outputs to prevent security vulnerabilities.
"""

import re
import html
import json
from typing import Any, Dict, List, Optional, Set, Union, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class InputValidator:
    """
    Validates and sanitizes inputs to prevent security vulnerabilities.

    Protects against injection attacks, malformed data, and unsafe operations.
    """

    def __init__(self, strict_mode: bool = True):
        """
        Initialize input validator.

        Args:
            strict_mode: Whether to use strict validation rules
        """
        self.strict_mode = strict_mode
        self._unsafe_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',               # JavaScript URLs
            r'on\w+\s*=',                # Event handlers
            r'eval\s*\(',                # eval() calls
            r'exec\s*\(',                # exec() calls
            r'import\s+os',              # OS imports
            r'import\s+subprocess',      # Subprocess imports
            r'__import__',               # Dynamic imports
            r'\.\./\.\./',               # Path traversal
            r'\.\.\\\.\.\\',             # Windows path traversal
        ]
        self._compiled_patterns = [re.compile(pattern, re.IGNORECASE)
                                 for pattern in self._unsafe_patterns]

    def validate_string(self, value: str, max_length: Optional[int] = None,
                       allow_html: bool = False) -> str:
        """
        Validate and sanitize string input.

        Args:
            value: String to validate
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML content

        Returns:
            str: Validated and sanitized string

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value).__name__}")

        if max_length and len(value) > max_length:
            raise ValidationError(f"String exceeds maximum length of {max_length}")

        # Check for unsafe patterns
        for pattern in self._compiled_patterns:
            if pattern.search(value):
                if self.strict_mode:
                    raise ValidationError("Input contains potentially unsafe content")
                else:
                    logger.warning("Potentially unsafe content detected in input")

        # Sanitize HTML if not allowed
        if not allow_html:
            value = html.escape(value)

        return value

    def validate_path(self, path: Union[str, Path],
                     must_exist: bool = False,
                     allowed_extensions: Optional[Set[str]] = None,
                     base_directory: Optional[str] = None) -> Path:
        """
        Validate file system path for security.

        Args:
            path: Path to validate
            must_exist: Whether path must exist
            allowed_extensions: Set of allowed file extensions
            base_directory: Base directory to restrict access to

        Returns:
            Path: Validated path object

        Raises:
            ValidationError: If validation fails
        """
        path_obj = Path(path)

        # Check for path traversal attacks
        if '..' in str(path_obj):
            raise ValidationError("Path traversal detected")

        # Resolve to absolute path
        try:
            resolved_path = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            raise ValidationError(f"Invalid path: {e}")

        # Check base directory restriction
        if base_directory:
            base_path = Path(base_directory).resolve()
            try:
                resolved_path.relative_to(base_path)
            except ValueError:
                raise ValidationError("Path outside allowed base directory")

        # Check existence if required
        if must_exist and not resolved_path.exists():
            raise ValidationError("Path does not exist")

        # Check file extension
        if allowed_extensions and resolved_path.is_file():
            if resolved_path.suffix.lower() not in allowed_extensions:
                raise ValidationError(f"File extension not allowed: {resolved_path.suffix}")

        return resolved_path

    def validate_json(self, value: Union[str, Dict, List]) -> Union[Dict, List]:
        """
        Validate JSON data.

        Args:
            value: JSON data to validate

        Returns:
            Parsed and validated JSON data

        Raises:
            ValidationError: If validation fails
        """
        if isinstance(value, str):
            try:
                data = json.loads(value)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON: {e}")
        else:
            data = value

        # Check for potentially unsafe content in JSON
        json_str = json.dumps(data)
        for pattern in self._compiled_patterns:
            if pattern.search(json_str):
                if self.strict_mode:
                    raise ValidationError("JSON contains potentially unsafe content")
                else:
                    logger.warning("Potentially unsafe content detected in JSON")

        return data

    def validate_command_args(self, args: List[str],
                            allowed_commands: Optional[Set[str]] = None) -> List[str]:
        """
        Validate command line arguments for safety.

        Args:
            args: Command arguments to validate
            allowed_commands: Set of allowed commands

        Returns:
            List[str]: Validated arguments

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(args, list):
            raise ValidationError("Command args must be a list")

        if not args:
            raise ValidationError("Command args cannot be empty")

        # Check if command is allowed
        command = args[0]
        if allowed_commands and command not in allowed_commands:
            raise ValidationError(f"Command not allowed: {command}")

        # Check for dangerous patterns in arguments
        for arg in args:
            if not isinstance(arg, str):
                raise ValidationError("All command arguments must be strings")

            # Check for command injection patterns
            dangerous_chars = ['|', '&', ';', '`', '$', '<', '>', '\n', '\r']
            if any(char in arg for char in dangerous_chars):
                raise ValidationError("Command argument contains dangerous characters")

        return args

    def validate_numeric(self, value: Union[int, float, str],
                        min_value: Optional[float] = None,
                        max_value: Optional[float] = None,
                        integer_only: bool = False) -> Union[int, float]:
        """
        Validate numeric input.

        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            integer_only: Whether to allow only integers

        Returns:
            Validated numeric value

        Raises:
            ValidationError: If validation fails
        """
        if isinstance(value, str):
            try:
                if integer_only:
                    value = int(value)
                else:
                    value = float(value)
            except ValueError:
                raise ValidationError("Invalid numeric value")

        if not isinstance(value, (int, float)):
            raise ValidationError("Value must be numeric")

        if integer_only and not isinstance(value, int):
            raise ValidationError("Value must be an integer")

        if min_value is not None and value < min_value:
            raise ValidationError(f"Value must be at least {min_value}")

        if max_value is not None and value > max_value:
            raise ValidationError(f"Value must be at most {max_value}")

        return value


class OutputSanitizer:
    """
    Sanitizes outputs to prevent information leakage and security issues.
    """

    def __init__(self):
        """Initialize output sanitizer."""
        self._sensitive_patterns = [
            r'password["\']?\s*[:=]\s*["\']?[\w@#$%]+',
            r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w\-]+',
            r'token["\']?\s*[:=]\s*["\']?[\w\-\.]+',
            r'secret["\']?\s*[:=]\s*["\']?[\w\-]+',
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
        ]
        self._compiled_sensitive = [re.compile(pattern, re.IGNORECASE)
                                  for pattern in self._sensitive_patterns]

    def sanitize_output(self, output: str, mask_sensitive: bool = True) -> str:
        """
        Sanitize output content.

        Args:
            output: Output to sanitize
            mask_sensitive: Whether to mask sensitive information

        Returns:
            str: Sanitized output
        """
        if not isinstance(output, str):
            return str(output)

        sanitized = output

        if mask_sensitive:
            # Mask sensitive information
            for pattern in self._compiled_sensitive:
                sanitized = pattern.sub('***REDACTED***', sanitized)

        # Remove potential HTML/JavaScript
        sanitized = html.escape(sanitized)

        return sanitized

    def sanitize_error_message(self, error: Exception) -> str:
        """
        Sanitize error messages to prevent information leakage.

        Args:
            error: Exception to sanitize

        Returns:
            str: Sanitized error message
        """
        error_msg = str(error)

        # Remove file paths that might contain sensitive info
        error_msg = re.sub(r'/[^\s]*', '***PATH***', error_msg)
        error_msg = re.sub(r'[A-Z]:\\[^\s]*', '***PATH***', error_msg)

        # Remove potential sensitive data
        for pattern in self._compiled_sensitive:
            error_msg = pattern.sub('***REDACTED***', error_msg)

        return error_msg


class SecurityValidator:
    """
    High-level security validator that combines multiple validation strategies.
    """

    def __init__(self, strict_mode: bool = True):
        """
        Initialize security validator.

        Args:
            strict_mode: Whether to use strict validation
        """
        self.input_validator = InputValidator(strict_mode)
        self.output_sanitizer = OutputSanitizer()
        self.strict_mode = strict_mode

    def validate_agent_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input data for agent operations.

        Args:
            data: Input data to validate

        Returns:
            Dict[str, Any]: Validated input data

        Raises:
            ValidationError: If validation fails
        """
        validated = {}

        for key, value in data.items():
            # Validate key
            safe_key = self.input_validator.validate_string(key, max_length=100)

            # Validate value based on type
            if isinstance(value, str):
                validated[safe_key] = self.input_validator.validate_string(value, max_length=10000)
            elif isinstance(value, (int, float)):
                validated[safe_key] = self.input_validator.validate_numeric(value)
            elif isinstance(value, (dict, list)):
                validated[safe_key] = self.input_validator.validate_json(value)
            elif isinstance(value, Path):
                validated[safe_key] = self.input_validator.validate_path(value)
            else:
                # Convert to string and validate
                validated[safe_key] = self.input_validator.validate_string(str(value))

        return validated

    def validate_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool parameters for security.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters to validate

        Returns:
            Dict[str, Any]: Validated parameters

        Raises:
            ValidationError: If validation fails
        """
        # Validate tool name
        safe_tool_name = self.input_validator.validate_string(tool_name, max_length=100)

        # Validate parameters
        validated_params = self.validate_agent_input(parameters)

        # Tool-specific validation
        if 'path' in validated_params:
            # Extra path validation for file operations
            validated_params['path'] = self.input_validator.validate_path(
                validated_params['path']
            )

        if 'command' in validated_params:
            # Validate command execution parameters
            if isinstance(validated_params['command'], list):
                validated_params['command'] = self.input_validator.validate_command_args(
                    validated_params['command']
                )

        return validated_params