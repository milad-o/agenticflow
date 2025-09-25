"""AgentsRepo - Pre-configured specialized agents for common use cases.

This module provides a repository of commonly used specialized agents that can be
easily instantiated and used in multi-agent workflows. Each agent comes pre-configured
with appropriate tools, capabilities, and settings for their specific domain.

Available Agents:
- FileSystemAgent: Specialized for file operations, directory navigation, and data discovery
- ReportingAgent: Specialized for generating reports, summaries, and documentation
- AnalysisAgent: Specialized for data analysis and pattern recognition

Usage:
    from agenticflow.agents_repo import AgentsRepo
    
    # Get pre-configured agents
    fs_agent = AgentsRepo.filesystem_agent()
    reporter = AgentsRepo.reporting_agent()
    
    # Add to flow
    flow.add_agent("fs_agent", fs_agent)
    flow.add_agent("reporter", reporter)
"""

from typing import Dict, Any
from .filesystem_agent import create_filesystem_agent, get_filesystem_agent_info
from .reporting_agent import create_reporting_agent, get_reporting_agent_info
from .analysis_agent import create_analysis_agent, get_analysis_agent_info


class AgentsRepo:
    """Repository of pre-configured specialized agents."""
    
    # Static methods that delegate to the individual modules
    @staticmethod
    def filesystem_agent(*args, **kwargs):
        """Create a pre-configured FileSystem agent."""
        return create_filesystem_agent(*args, **kwargs)
    
    @staticmethod
    def reporting_agent(*args, **kwargs):
        """Create a pre-configured Reporting agent."""
        return create_reporting_agent(*args, **kwargs)
    
    @staticmethod
    def analysis_agent(*args, **kwargs):
        """Create a pre-configured Analysis agent."""
        return create_analysis_agent(*args, **kwargs)
    
    @staticmethod
    def list_available_agents() -> Dict[str, Dict[str, Any]]:
        """List all available pre-configured agents and their capabilities."""
        return {
            "filesystem_agent": get_filesystem_agent_info(),
            "reporting_agent": get_reporting_agent_info(),
            "analysis_agent": get_analysis_agent_info()
        }


# Convenience aliases for easier imports
filesystem_agent = AgentsRepo.filesystem_agent
reporting_agent = AgentsRepo.reporting_agent  
analysis_agent = AgentsRepo.analysis_agent

__all__ = [
    "AgentsRepo", 
    "filesystem_agent", 
    "reporting_agent", 
    "analysis_agent",
    "create_filesystem_agent",
    "create_reporting_agent", 
    "create_analysis_agent"
]
