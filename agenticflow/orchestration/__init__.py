"""
Orchestration System

Multi-agent orchestration, planning, and delegation capabilities.

Submodules:
- orchestrators: Multi-agent coordination and execution
- planners: Task planning and decomposition
- delegation: Agent capability matching and task delegation
"""

from .orchestrators import Orchestrator
from .planners import Planner
from .delegation import DelegateTool, CapabilityExtractor
# from .cards import CardRegistry, AgentCard  # Cards system is optional

__all__ = [
    "Orchestrator",
    "Planner", 
    "DelegateTool",
    "CapabilityExtractor"
    # Card system exports would go here when needed
]
