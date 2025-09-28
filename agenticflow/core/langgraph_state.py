"""LangGraph state integration for AgenticFlow."""

from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage


class AgenticFlowState(MessagesState):
    """Extended state for AgenticFlow with LangGraph integration.
    
    This extends LangGraph's MessagesState to include AgenticFlow-specific
    context and routing information.
    """
    
    # Orchestrator-level context
    orchestrator_context: Dict[str, Any] = {}
    
    # Team-level contexts
    team_contexts: Dict[str, Dict[str, Any]] = {}
    
    # Current routing state
    current_team: Optional[str] = None
    current_agent: Optional[str] = None
    
    # Execution tracking
    execution_path: List[str] = []  # Track the execution path
    completion_status: Dict[str, bool] = {}  # Track completion of teams/agents
    
    # Flow metadata
    flow_id: Optional[str] = None
    flow_name: Optional[str] = None
    workspace_path: Optional[str] = None


class RoutingDecision(TypedDict):
    """Structured output for routing decisions."""
    next: str
    reasoning: str


class TeamRoutingDecision(TypedDict):
    """Structured output for team routing decisions."""
    next: str
    reasoning: str
