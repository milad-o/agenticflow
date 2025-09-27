"""
AgenticFlow - Hierarchical Multi-Agent Framework

Clean implementation based on LangGraph hierarchical patterns:

Architecture: Flow → Supervisor → Workers

- Flow: Main orchestration and configuration
- Supervisor: Intelligent task coordination and worker selection
- Workers: Specialized agents for specific domains

Key Features:
- 🏗️ Hierarchical agent coordination via LangGraph
- 🎯 Intelligent supervisor-based task delegation
- ⚡ Direct worker specialization (no complex registries)
- 📊 Stateful team coordination
- 🔧 Simple, clean architecture

Quick Start:
    from agenticflow import Flow
    from agenticflow.agents import FileSystemWorker, ReportingWorker

    # Create specialized workers
    fs_worker = FileSystemWorker()
    reporter = ReportingWorker()

    # Create hierarchical flow
    flow = Flow()
    flow.add_worker("filesystem", fs_worker)
    flow.add_worker("reporter", reporter)

    # Execute with supervisor coordination
    result = await flow.execute("Analyze CSV files and create report")
"""

from .core import Flow
from .core.observable_flow import ObservableFlow
from .teams import SupervisorAgent, TeamState, TeamGraph
from .observability import EventTracker, FlowObserver, MetricsCollector

__version__ = "0.3.0"
__author__ = "AgenticFlow Team"
__description__ = "Hierarchical Multi-Agent Framework with Observability"

__all__ = [
    "Flow",
    "ObservableFlow",
    "SupervisorAgent",
    "TeamState",
    "TeamGraph",
    "EventTracker",
    "FlowObserver",
    "MetricsCollector"
]