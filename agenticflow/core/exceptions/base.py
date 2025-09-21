class AgenticFlowError(Exception):
    """Base exception for AgenticFlow."""


class SecurityError(AgenticFlowError):
    pass


class ToolNotFoundError(AgenticFlowError):
    pass
