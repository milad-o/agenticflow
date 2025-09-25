"""AgenticFlow Core Module

Core functionality organized into logical submodules:

- config: Configuration classes and role definitions
- models: Language model integration and management
- events: Event bus system for inter-component communication
- tasks: Task definitions, status tracking, and lifecycle management
- flows: Flow orchestration and execution management

For backward compatibility, common imports are available at the core level.
"""

# Core submodules
from .config import AgentConfig, FlowConfig
from .models import get_chat_model, ModelProvider
from .events import EventEmitter, EventType, get_event_bus
from .tasks import Task, TaskStatus, TaskStatusTracker
from .flows import Flow

# Legacy imports for backward compatibility (deprecated)
# from .env import EnvConfig  # Moved to core.config
# from .path_guard import PathGuard  # Moved to security.validation

__all__ = [
    # Configuration
    "AgentConfig",
    "FlowConfig",

    # Models
    "get_chat_model",
    "ModelProvider",

    # Events
    "EventEmitter",
    "EventType",
    "get_event_bus",

    # Tasks
    "Task",
    "TaskStatus",
    "TaskStatusTracker",

    # Flows
    "Flow",

    # Legacy (deprecated) - moved to other modules
    # "EnvConfig",  # -> core.config.env_config
    # "PathGuard"   # -> security.validation.path_guard
]