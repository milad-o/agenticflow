class AgenticFlowError(Exception):
    """Base exception for AgenticFlow."""


class SecurityError(AgenticFlowError):
    pass


class ToolNotFoundError(AgenticFlowError):
    pass


class InvalidTransitionError(AgenticFlowError):
    pass


class CircuitOpenError(AgenticFlowError):
    """Raised when a circuit breaker is open and execution is blocked."""
    pass
