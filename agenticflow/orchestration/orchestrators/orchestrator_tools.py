"""Helper tools for the Orchestrator-as-Agent.

These tools wrap common intents and delegate to appropriate sub-agents via natural language instructions.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class CreateFileInput(BaseModel):
    file_name: str
    content: str
    thread_id: Optional[str] = None


class CreateFileTool(BaseTool):
    name: str = "create_file"
    description: str = "Create a file with provided content using underlying file-capable agent"
    args_schema: type[CreateFileInput] = CreateFileInput

    def __init__(self, agents: Dict[str, Any]):
        super().__init__()
        self._agents = agents

    def _run(self, file_name: str, content: str, thread_id: Optional[str] = None) -> str:  # type: ignore[override]
        # Prefer an agent that has write_file tool if available
        target = None
        for name, agent in self._agents.items():
            try:
                tools = getattr(agent, "tools", [])
                if any(getattr(t, "name", "") == "write_file" for t in tools):
                    target = agent
                    break
            except Exception:
                continue
        if target is None and self._agents:
            target = list(self._agents.values())[0]
        prompt = f"Create a file named '{file_name}' with the exact content: {content}"
        try:
            result = target.run(prompt, thread_id=thread_id)
            return result.get("message") or result.get("final_response") or ""
        except Exception as e:
            return f"CreateFile error: {e}"

    async def _arun(self, file_name: str, content: str, thread_id: Optional[str] = None) -> str:  # type: ignore[override]
        target = None
        for name, agent in self._agents.items():
            try:
                tools = getattr(agent, "tools", [])
                if any(getattr(t, "name", "") == "write_file" for t in tools):
                    target = agent
                    break
            except Exception:
                continue
        if target is None and self._agents:
            target = list(self._agents.values())[0]
        prompt = f"Create a file named '{file_name}' with the exact content: {content}"
        try:
            if hasattr(target, "arun"):
                result = await target.arun(prompt, thread_id=thread_id)
            else:
                result = target.run(prompt, thread_id=thread_id)
            return result.get("message") or result.get("final_response") or ""
        except Exception as e:
            return f"CreateFile error: {e}"


class ListDirectoryInput(BaseModel):
    path: Optional[str] = Field(default=".", description="Directory to list")
    thread_id: Optional[str] = None


class ListDirectoryTool(BaseTool):
    name: str = "list_directory"
    description: str = "List files in a directory using a shell-capable agent"
    args_schema: type[ListDirectoryInput] = ListDirectoryInput

    def __init__(self, agents: Dict[str, Any]):
        super().__init__()
        self._agents = agents

    def _run(self, path: Optional[str] = ".", thread_id: Optional[str] = None) -> str:  # type: ignore[override]
        # Prefer agent with shell tool
        target = None
        for name, agent in self._agents.items():
            try:
                tools = getattr(agent, "tools", [])
                if any(getattr(t, "name", "") == "shell" for t in tools):
                    target = agent
                    break
            except Exception:
                continue
        if target is None and self._agents:
            target = list(self._agents.values())[0]
        prompt = f"List the files in directory: {path}"
        try:
            result = target.run(prompt, thread_id=thread_id)
            return result.get("message") or result.get("final_response") or ""
        except Exception as e:
            return f"ListDirectory error: {e}"

    async def _arun(self, path: Optional[str] = ".", thread_id: Optional[str] = None) -> str:  # type: ignore[override]
        target = None
        for name, agent in self._agents.items():
            try:
                tools = getattr(agent, "tools", [])
                if any(getattr(t, "name", "") == "shell" for t in tools):
                    target = agent
                    break
            except Exception:
                continue
        if target is None and self._agents:
            target = list(self._agents.values())[0]
        prompt = f"List the files in directory: {path}"
        try:
            if hasattr(target, "arun"):
                result = await target.arun(prompt, thread_id=thread_id)
            else:
                result = target.run(prompt, thread_id=thread_id)
            return result.get("message") or result.get("final_response") or ""
        except Exception as e:
            return f"ListDirectory error: {e}"
