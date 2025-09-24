"""Agent implementation for AgenticFlow."""

import asyncio
from typing import Dict, List, Optional, Any
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from agenticflow.core.config import AgentConfig
from agenticflow.core.models import get_chat_model
from pathlib import Path
import re


class Agent:
    """Self-contained LangGraph agent using create_react_agent.

    Tools and static resources can be registered per-agent.
    When tools are updated, the internal graph is rebuilt automatically.
    """
    
    def __init__(
        self,
        config: AgentConfig,
        tools: List[BaseTool],
        model: Optional[BaseChatModel] = None,
        checkpointer: Optional[Any] = None,
        static_resources: Optional[Dict[str, Any]] = None,
    ):
        self.config = config
        self.tools: List[BaseTool] = list(tools)
        self.model = model or get_chat_model(model_name=config.model, temperature=config.temperature)
        self.checkpointer = checkpointer or MemorySaver()
        self.resources: Dict[str, Any] = dict(static_resources or {})
        
        self._rebuild_graph()
    
    def _rebuild_graph(self) -> None:
        """Rebuild the internal compiled graph based on current tools/model."""
        self.compiled_graph = create_react_agent(
            model=self.model,
            tools=self.tools,
            checkpointer=self.checkpointer
        )
    
    def set_tools(self, tools: List[BaseTool]) -> None:
        """Replace tools and rebuild the graph."""
        self.tools = list(tools)
        self._rebuild_graph()
    
    def add_tools(self, tools: List[BaseTool]) -> None:
        """Add tools (dedup by name) and rebuild the graph."""
        existing = {t.name for t in self.tools}
        for t in tools:
            if t.name not in existing:
                self.tools.append(t)
                existing.add(t.name)
        self._rebuild_graph()
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a single tool and rebuild the graph if new."""
        if all(t.name != tool.name for t in self.tools):
            self.tools.append(tool)
            self._rebuild_graph()
    
    def list_tool_names(self) -> List[str]:
        return [t.name for t in self.tools]
    
    def register_resource(self, name: str, resource: Any) -> None:
        """Register a static resource local to this agent."""
        self.resources[name] = resource
    
    def get_resource(self, name: str) -> Any:
        return self.resources.get(name)
    
    def list_resources(self) -> List[str]:
        return list(self.resources.keys())
    
    async def arun(
        self,
        message: str,
        thread_id: Optional[str] = None,
        verify: bool = True,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Run the agent asynchronously with optional self-verification and one retry."""
        config = {"configurable": {"thread_id": thread_id or "default"}}

        async def _invoke(msgs):
            final_message = None
            async for chunk in self.compiled_graph.astream(
                {"messages": msgs},
                config=config,
                **kwargs
            ):
                if "agent" in chunk:
                    final_message = chunk["agent"]["messages"][-1]
            return final_message

        # Initial
        if getattr(self, "reporter", None):
            try:
                self.reporter.agent("start", agent=self.config.name, thread_id=thread_id)
            except Exception:
                pass
        final_message = await _invoke([("human", message)])
        content = final_message.content if final_message else ""

        # Self-verification with one retry: content-based signals OR missing FS targets
        missing_hints = self._missing_targets(message)
        should_retry = self._should_retry(content) or bool(missing_hints)
        if verify and should_retry:
            hint = self._tool_usage_hint()
            if missing_hints:
                hint += "\nYou must ensure these targets exist: " + ", ".join(missing_hints) + "."
            sys_msg = SystemMessage(content=hint)
            final_message = await _invoke([("system", sys_msg.content), ("human", message)])
            content = final_message.content if final_message else content

        if getattr(self, "reporter", None):
            try:
                self.reporter.agent("end", agent=self.config.name, thread_id=thread_id, preview=(content or "")[:160])
            except Exception:
                pass
        return {
            "agent_name": self.config.name,
            "message": content,
            "tool_calls": getattr(final_message, "tool_calls", []) if final_message else []
        }
    
    async def astream(
        self,
        message: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ):
        """Stream agent responses."""
        config = {"configurable": {"thread_id": thread_id or "default"}}
        
        async for chunk in self.compiled_graph.astream(
            {"messages": [("human", message)]},
            config=config,
            **kwargs
        ):
            yield {
                "agent_name": self.config.name,
                "chunk": chunk
            }
    
    def run(self, message: str, thread_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Synchronous wrapper for arun."""
        return asyncio.run(self.arun(message, thread_id, **kwargs))
    
    def get_state(self, thread_id: str = "default") -> Dict[str, Any]:
        """Get the current state of the agent conversation."""
        config = {"configurable": {"thread_id": thread_id}}
        return self.compiled_graph.get_state(config)
    
    def update_state(
        self,
        values: Dict[str, Any],
        thread_id: str = "default",
        as_node: Optional[str] = None
    ) -> None:
        """Update the agent's state."""
        config = {"configurable": {"thread_id": thread_id}}
        self.compiled_graph.update_state(config, values, as_node)

    # Discovery helpers
    def discover_tools_by_names(self, registry, names: List[str]) -> None:
        tools = registry.get_tools_by_names(names)
        self.add_tools(tools)

    def discover_tools_by_tags(self, registry, tags: List[str]) -> None:
        tools = registry.get_tools_by_tags(set(tags))
        self.add_tools(tools)

    def _should_retry(self, content: str) -> bool:
        if not content:
            return False
        signals = [
            "not available",
            "cannot",
            "no such tool",
            "unknown tool",
            "can't",
            "do not have",
        ]
        return any(s in content.lower() for s in signals)

    def _tool_usage_hint(self) -> str:
        names = [t.name for t in self.tools]
        hints = []
        if "mkdir" in names or "shell" in names:
            hints.append("To create directories use 'mkdir' (or shell with mkdir -p).")
        if "write_file" in names:
            hints.append("To create or edit files use 'write_file'.")
        if "read_file" in names:
            hints.append("To read files use 'read_file'.")
        if "list_dir" in names or "list_directory" in names:
            hints.append("To list directories use 'list_dir' or 'list_directory'.")
        if "shell" in names:
            hints.append("For general system operations use 'shell' with safe commands.")
        return "You have the following tools available: " + ", ".join(names) + ". " + " ".join(hints)

    def _missing_targets(self, original_message: str) -> List[str]:
        """Parse likely targets (dirs/files) from instruction and check FS presence."""
        targets: List[str] = []
        # folder patterns
        for m in re.finditer(r"folder named '([^']+)'|folder '([^']+)'|directory '([^']+)'", original_message, re.IGNORECASE):
            for g in m.groups():
                if g:
                    targets.append(g)
        # file patterns in quotes
        for m in re.finditer(r"'([^']+\.[a-zA-Z0-9]{1,8})'", original_message):
            if m.group(1):
                targets.append(m.group(1))
        missing = []
        for t in targets:
            p = Path(t)
            if (p.suffix and not p.exists()) or (not p.suffix and not p.exists()):
                missing.append(t)
        return missing
    
    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name
    
    @property
    def description(self) -> str:
        """Get agent description."""
        return self.config.description or f"ReAct agent with {len(self.tools)} tools"