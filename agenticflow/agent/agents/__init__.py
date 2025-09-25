"""
AgenticFlow Agents

This module provides high-level agent classes for common tasks:
- FileSystemAgent: Fast file discovery and content reading
- ReportingAgent: Professional report generation
- AnalysisAgent: Data analysis and CSV processing

All agents now accept LangChain LLM objects for easy switching between providers.
"""

from .filesystem import FileSystemAgent, EnhancedFileSystemAgent
from .reporting import ReportingAgent, EnhancedReportingAgent
from .analysis import AnalysisAgent

__all__ = [
    "FileSystemAgent",
    "EnhancedFileSystemAgent",
    "ReportingAgent",
    "EnhancedReportingAgent",
    "AnalysisAgent"
]