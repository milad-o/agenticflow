"""Agent implementation for AgenticFlow."""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Union, TYPE_CHECKING
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from agenticflow.core.models import get_chat_model
from agenticflow.registries.tool_registry import ToolRegistry
from pathlib import Path
import re

if TYPE_CHECKING:
    from agenticflow.core.config import AgentConfig
from langchain_core.callbacks.base import BaseCallbackHandler
from agenticflow.core.events import EventEmitter, EventType


class ReporterCallbackHandler(BaseCallbackHandler):
    """Logs tool usage events via Reporter if available."""
    def __init__(self, reporter=None, agent_name: str = "", run_id: str | None = None):
        self.reporter = reporter
        self.agent_name = agent_name
        self.run_id = run_id

    def on_tool_start(self, serialized, input_str, **kwargs):  # type: ignore[override]
        try:
            if self.reporter:
                name = (serialized or {}).get("name") or "tool"
                self.reporter.agent(
                    "tool_start",
                    agent=self.agent_name,
                    tool=name,
                    input=(str(input_str)[:200] if input_str else ""),
                )
        except Exception:
            pass

    def on_tool_end(self, output, **kwargs):  # type: ignore[override]
        try:
            if self.reporter:
                self.reporter.agent("tool_end", agent=self.agent_name, output=(str(output)[:200] if output is not None else ""))
        except Exception:
            pass

    def on_tool_error(self, error, **kwargs):  # type: ignore[override]
        try:
            if self.reporter:
                self.reporter.agent("tool_error", agent=self.agent_name, error=str(error))
        except Exception:
            pass


class Agent:
    """Self-contained LangGraph agent using create_react_agent.

    Tools and static resources can be registered per-agent.
    When tools are updated, the internal graph is rebuilt automatically.
    """
    
    def __init__(
        self,
        config: Optional["AgentConfig"] = None,
        tools: Optional[List[BaseTool]] = None,
        model: Optional[BaseChatModel] = None,
        checkpointer: Optional[Any] = None,
        static_resources: Optional[Dict[str, Any]] = None,
        auto_discover: bool = True,
        # end-user friendly args (optional):
        name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        # Build config if only simple args are provided
        if config is None:
            from agenticflow.core.config import AgentConfig
            # Fallback defaults for convenience
            cfg_name = name or "agent"
            cfg_model = model_name or ""
            cfg_temp = 0.0 if temperature is None else float(temperature)
            config = AgentConfig(name=cfg_name, model=cfg_model, temperature=cfg_temp)
        self.config = config
        
        # Initialize EventEmitter using composition
        self._event_emitter = None  # Will be initialized when event_bus is available
        
        self.tools: List[BaseTool] = list(tools or [])
        # If a concrete chat model is provided, use it; else build from config
        self.model = model or get_chat_model(model_name=self.config.model, temperature=self.config.temperature)
        self.checkpointer = checkpointer or MemorySaver()
        self.resources: Dict[str, Any] = dict(static_resources or {})
        self.auto_discover: bool = auto_discover
        
        # Agent-specific tool registry for enhanced tool resolution
        self.tool_registry = ToolRegistry()
        self._flow_ref: Optional[Any] = None  # Reference to parent Flow for fallback tool resolution
        
        # Register initial tools in agent's registry
        for tool in self.tools:
            self.tool_registry.register_tool_instance(tool)
        
        self._rebuild_graph()
    
    def _rebuild_graph(self) -> None:
        """Rebuild the internal compiled graph based on current tools/model.
        Applies any active tool binding (subset) if set.
        Constructs system prompt from base prompt + rules.
        """
        tools = list(self.tools)
        try:
            if getattr(self, "_tool_binding", None):
                names = self._tool_binding.get("names") if isinstance(self._tool_binding, dict) else None
                if names:
                    tools = [t for t in tools if t.name in names]
        except Exception:
            pass
        
        # Build system prompt from base system_prompt + rules
        system_prompt = self._build_system_prompt()
        
        # Create agent with system prompt if available
        if system_prompt:
            self.compiled_graph = create_react_agent(
                model=self.model,
                tools=tools,
                checkpointer=self.checkpointer,
                prompt=SystemMessage(content=system_prompt)
            )
        else:
            self.compiled_graph = create_react_agent(
                model=self.model,
                tools=tools,
                checkpointer=self.checkpointer
            )
    
    def _build_system_prompt(self) -> Optional[str]:
        """Build complete system prompt from base system_prompt + rules.
        
        System Prompt: General agent identity and behavior
        Rules: Specific operational constraints and procedures
        """
        parts = []
        
        # Base system prompt (general agent behavior)
        base_prompt = getattr(self.config, 'system_prompt', None)
        if base_prompt:
            parts.append(base_prompt.strip())
        else:
            # Default system prompt if none provided
            default_prompt = f"""You are {self.config.name}, an AI agent in the AgenticFlow system.
            
Your role: {getattr(self.config, 'role', 'General Agent')}
Your capabilities: {', '.join(getattr(self.config, 'capabilities', []) or ['general'])}
            
You can use the available tools to accomplish tasks. Always use the appropriate tool for each operation."""
            parts.append(default_prompt.strip())
        
        # Add Rules (specific operational constraints)
        rules = getattr(self.config, 'rules', None)
        if rules:
            if isinstance(rules, str):
                # String rules - add directly
                parts.append("\n🚨 OPERATIONAL RULES - FOLLOW STRICTLY:")
                parts.append(rules.strip())
            elif hasattr(rules, 'get_rules_text'):
                # Rule object with get_rules_text method
                rules_text = rules.get_rules_text()
                if rules_text:
                    parts.append("\n🚨 OPERATIONAL RULES - FOLLOW STRICTLY:")
                    parts.append(rules_text.strip())
            elif hasattr(rules, '__str__'):
                # Any other object that can be converted to string
                rules_text = str(rules)
                if rules_text:
                    parts.append("\n🚨 OPERATIONAL RULES - FOLLOW STRICTLY:")
                    parts.append(rules_text.strip())
        
        return "\n\n".join(parts) if parts else None
    
    def set_tools(self, tools: List[BaseTool]) -> None:
        """Replace tools and rebuild the graph."""
        self.tools = list(tools)
        # Update agent's tool registry
        self.tool_registry = ToolRegistry()
        for tool in self.tools:
            self.tool_registry.register_tool_instance(tool)
        self._rebuild_graph()
    
    def add_tools(self, tools: List[BaseTool]) -> None:
        """Add tools (dedup by name) and rebuild the graph."""
        existing = {t.name for t in self.tools}
        for t in tools:
            if t.name not in existing:
                self.tools.append(t)
                existing.add(t.name)
                # Also add to agent's tool registry
                self.tool_registry.register_tool_instance(t)
        self._rebuild_graph()
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a single tool and rebuild the graph if new."""
        if all(t.name != tool.name for t in self.tools):
            self.tools.append(tool)
            # Also add to agent's tool registry
            self.tool_registry.register_tool_instance(tool)
            self._rebuild_graph()

    def register_tools(self, tools: List[BaseTool]) -> "Agent":
        """Register multiple tool instances at once (chainable)."""
        self.add_tools(tools)
        return self

    def bind_tools(self, names: Optional[List[str]] = None) -> "Agent":
        """Bind a subset of tools by names for subsequent runs and rebuild.
        Call bind_tools() with no args to clear the binding.
        """
        self._tool_binding = {"names": set(names)} if names else None
        self._rebuild_graph()
        return self
    
    def list_tool_names(self) -> List[str]:
        return [t.name for t in self.tools]
    
    def register_resource(self, name: str, resource: Any) -> None:
        """Register a static resource local to this agent."""
        self.resources[name] = resource
    
    def register_static_resources(self, resources: Dict[str, Any]) -> "Agent":
        """Register multiple static resources (dict name->instance)."""
        for k, v in resources.items():
            self.resources[k] = v
        return self
    
    def adopt_flow_tools(self, flow, names: List[str] | None = None, tags: List[str] | None = None) -> "Agent":
        """Discover and register tools from a Flow's registry by names and/or tags.
        If no names or tags specified, adopts all available tools.
        Also sets up flow reference for hierarchical tool resolution.
        """
        # Store flow reference for hierarchical tool resolution
        self._flow_ref = flow
        
        tools: List[BaseTool] = []
        if names:
            tools.extend(flow.tool_registry.get_tools_by_names(names))
        if tags:
            tools.extend(flow.tool_registry.get_tools_by_tags(set(tags)))
        # If no filters provided, adopt all tools
        if not names and not tags:
            tools.extend(flow.tool_registry.get_all_tools())
        # Dedup and register
        self.add_tools(tools)
        return self

    def adopt_flow_resources(self, flow, names: List[str] | None = None, resource_types: List[str] | None = None) -> "Agent":
        """Discover and attach shared resources from the Flow's resource registry.
        Also sets up flow reference if not already present.
        """
        # Ensure flow reference for hierarchical resolution
        if self._flow_ref is None:
            self._flow_ref = flow
        
        rr = flow.resource_registry
        to_attach: Dict[str, Any] = {}
        all_meta = rr.list_resources()
        for res_name, meta in all_meta.items():
            if names and res_name not in names:
                continue
            if resource_types and meta.resource_type not in resource_types:
                continue
            to_attach[res_name] = rr.get_resource(res_name)
        self.register_static_resources(to_attach)
        return self
    
    def get_resource(self, name: str) -> Any:
        return self.resources.get(name)
    
    def list_resources(self) -> List[str]:
        return list(self.resources.keys())
    
    def resolve_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """Hierarchical tool resolution: Agent registry → Flow registry → None.
        Returns None if tool not found anywhere, caller should emit missing_tool event.
        """
        # Step 1: Check agent's own tool registry
        try:
            return self.tool_registry.get_tool(name)
        except Exception:
            pass
        
        # Step 2: Check Flow's tool registry (if available)
        if self._flow_ref:
            try:
                return self._flow_ref.tool_registry.get_tool(name)
            except Exception:
                pass
        
        # Step 3: Tool not found anywhere
        return None
    
    def resolve_resource_by_name(self, name: str) -> Optional[Any]:
        """Hierarchical resource resolution: Agent resources → Flow resources → None.
        Returns None if resource not found anywhere, caller should emit missing_resource event.
        """
        # Step 1: Check agent's own resources
        if name in self.resources:
            return self.resources[name]
        
        # Step 2: Check Flow's resource registry (if available)
        if self._flow_ref:
            try:
                return self._flow_ref.resource_registry.get_resource(name)
            except Exception:
                pass
        
        # Step 3: Resource not found anywhere
        return None
    
    def emit_missing_tool_event(self, tool_name: str) -> None:
        """Emit missing_tool event via reporter if available."""
        if hasattr(self, "reporter") and self.reporter:
            try:
                self.reporter.agent(
                    "missing_tool",
                    agent=self.config.name,
                    tool_name=tool_name,
                    message=f"Tool '{tool_name}' not found in agent or flow registries"
                )
            except Exception:
                pass
    
    def emit_missing_resource_event(self, resource_name: str) -> None:
        """Emit missing_resource event via reporter if available."""
        if hasattr(self, "reporter") and self.reporter:
            try:
                self.reporter.agent(
                    "missing_resource",
                    agent=self.config.name,
                    resource_name=resource_name,
                    message=f"Resource '{resource_name}' not found in agent or flow registries"
                )
            except Exception:
                pass

    def describe(self) -> Dict[str, Any]:
        """Return a serializable description of this agent's tools/resources/capabilities."""
        try:
            tool_names = self.list_tool_names()
        except Exception:
            tool_names = []
        tags = []
        try:
            tags = list(getattr(self.config, "tags", []) or [])
        except Exception:
            tags = []
        return {
            "name": self.config.name,
            "tools": tool_names,
            "resources": self.list_resources(),
            "tags": tags,
        }
    
    def enable_dynamic_discovery(
        self,
        flow,
        names: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        resource_types: Optional[List[str]] = None,
    ) -> "Agent":
        """Subscribe to flow registries; auto-adopt matching tools/resources as they are registered."""
        self._dynamic_tokens = getattr(self, "_dynamic_tokens", [])
        name_set = set(names or [])
        tag_set = set(tags or [])

        def tool_cb(event: str, meta):
            try:
                if event != "register_tool":
                    return
                if name_set and meta.name not in name_set:
                    return
                if tag_set and not (meta.tags & tag_set):
                    return
                tool = flow.tool_registry.get_tool(meta.name)
                self.register_tool(tool)
            except Exception:
                pass

        tid = flow.tool_registry.add_listener(tool_cb)
        self._dynamic_tokens.append(("tool", tid))

        rtypes = set(resource_types or [])

        def res_cb(event: str, meta):
            try:
                if event != "register_resource":
                    return
                if name_set and meta.name not in name_set:
                    return
                if rtypes and meta.resource_type not in rtypes:
                    return
                inst = flow.resource_registry.get_resource(meta.name)
                self.register_resource(meta.name, inst)
            except Exception:
                pass

        rid = flow.resource_registry.add_listener(res_cb)
        self._dynamic_tokens.append(("res", rid))
        return self

    def disable_dynamic_discovery(self, flow) -> "Agent":
        for kind, token in getattr(self, "_dynamic_tokens", []):
            try:
                if kind == "tool":
                    flow.tool_registry.remove_listener(token)
                else:
                    flow.resource_registry.remove_listener(token)
            except Exception:
                pass
        self._dynamic_tokens = []
        return self
    
    def emit_event(self, event_type: EventType, data: Dict[str, Any] = None, 
                   channel: str = "default", target: Optional[str] = None):
        """Emit an event if event bus is available."""
        try:
            if hasattr(self, 'event_bus') and self.event_bus:
                from agenticflow.core.events import Event
                event = Event(
                    event_type=event_type,
                    source=self.config.name,
                    data=data or {},
                    channel=channel,
                    target=target
                )
                self.event_bus.emit(event)
                return event
        except Exception as e:
            # Don't fail if event emission fails
            pass
        return None
    
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
            # Attach reporter-based callback to log tool usage
            callbacks = []
            try:
                callbacks = [ReporterCallbackHandler(getattr(self, "reporter", None), self.config.name, getattr(self, "run_id", None))]
            except Exception:
                callbacks = []
            enriched_config = dict(config)
            enriched_config["callbacks"] = callbacks
            async for chunk in self.compiled_graph.astream(
                {"messages": msgs},
                config=enriched_config,
                **kwargs
            ):
                if "agent" in chunk:
                    final_message = chunk["agent"]["messages"][-1]
            return final_message

        # Initial - emit task started event
        if getattr(self, "reporter", None):
            try:
                self.reporter.agent("start", agent=self.config.name, thread_id=thread_id)
            except Exception:
                pass
        
        # Emit task started event
        try:
            self.emit_event(EventType.TASK_STARTED, {
                "task_id": thread_id or "default",
                "message": message[:200],  # Truncate for logging
                "agent_role": str(self.config.role) if self.config.role else "unknown"
            }, channel="tasks")
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
        
        # Emit task completed event
        try:
            self.emit_event(EventType.TASK_COMPLETED, {
                "task_id": thread_id or "default",
                "result": content[:500] if content else "",  # Truncate result
                "agent_role": str(self.config.role) if self.config.role else "unknown",
                "tool_calls_count": len(getattr(final_message, "tool_calls", []) if final_message else [])
            }, channel="tasks")
        except Exception:
            pass
        
        # Special handling: If this is a FileSystem agent, emit DATA_AVAILABLE event
        try:
            if (hasattr(self.config, 'role') and 
                str(self.config.role) == 'AgentRole.DATA_COLLECTOR' and 
                content and len(content) > 100):  # Has substantial content
                
                self.emit_event(EventType.DATA_AVAILABLE, {
                    "task_id": thread_id or "default",
                    "data_type": "ssis_files",
                    "data_summary": content[:1000],  # First 1000 chars as summary
                    "files_processed": len(getattr(final_message, "tool_calls", []) if final_message else []),
                    "source_agent": self.config.name
                }, channel="data_flow")
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