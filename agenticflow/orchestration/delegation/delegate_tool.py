"""A LangChain tool that delegates a request to a named Agent.

The tool is constructed with a mapping from agent names to Agent instances.
It supports both sync and async invocation.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class DelegateInput(BaseModel):
    agent_name: str = Field(..., description="Target agent name to delegate to")
    request: str = Field(..., description="User request/message to send to the agent")
    thread_id: Optional[str] = Field(
        default=None, description="Optional thread id for the delegated agent"
    )


class DelegateTool(BaseTool):
    name: str = "delegate"
    description: str = (
        "Delegate a sub-task to a specific agent by name. "
        "Use this to route work to specialized agents."
    )
    args_schema: type[DelegateInput] = DelegateInput

    def __init__(self, agents: Dict[str, Any]):
        super().__init__()
        self._agents = agents

    def _run(self, agent_name: str, request: str, thread_id: Optional[str] = None) -> str:  # type: ignore[override]
        agent = self._agents.get(agent_name)
        if agent is None:
            return f"Agent '{agent_name}' not found. Available: {list(self._agents.keys())}"
        try:
            result = agent.run(request, thread_id=thread_id)
            return result.get("message") or result.get("final_response") or ""
        except Exception as e:
            return f"Delegation error: {e}"

    async def _arun(
        self, agent_name: str, request: str, thread_id: Optional[str] = None
    ) -> str:  # type: ignore[override]
        agent = self._agents.get(agent_name)
        if agent is None:
            return f"Agent '{agent_name}' not found. Available: {list(self._agents.keys())}"
        try:
            if hasattr(agent, "arun"):
                result = await agent.arun(request, thread_id=thread_id)
            else:
                # Fallback to sync in a thread (not strictly needed here)
                result = agent.run(request, thread_id=thread_id)
            return result.get("message") or result.get("final_response") or ""
        except Exception as e:
            return f"Delegation error: {e}"
