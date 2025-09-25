"""Core Flow container for AgenticFlow."""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator, Iterable
import structlog
import uuid

from ..config import FlowConfig, AgentConfig
from ...orchestration.orchestrators.orchestrator import Orchestrator
from ...agent import Agent
from ...registries.tool_registry import ToolRegistry
from ...registries.resource_registry import ResourceRegistry
from ..config.env import load_env
from ...observability.reporter import Reporter
from ...security.validation.path_guard import PathGuard
from ...registries.tool_repo import ToolRepo
from ...registries.toolset import ToolSet
from ..events import EventBus, EventType, TaskLifecycleManager
from ...agent.state.agent_state import AgentStateManager

logger = structlog.get_logger()


from typing import TYPE_CHECKING

class Flow:
    """
    Main container for AgenticFlow system.
    
    Handles system assembly, configuration loading, and exposes run/stream interfaces.
    Backed by LangGraph compiled graphs with observability and checkpointing.
    """
    
    def __init__(
        self,
        config: Optional[FlowConfig] = None,
        config_path: Optional[Path] = None
    ):
        # Load .env first so env-based overrides work in dev
        load_env()

        # Load configuration
        if config_path:
            self.config = FlowConfig.from_yaml(config_path).merge_with_env()
        elif config:
            self.config = config.merge_with_env()
        else:
            self.config = FlowConfig.from_env()
        
        # Initialize registries
        self.tool_registry = ToolRegistry()
        self.resource_registry = ResourceRegistry()
        self.tool_repo = ToolRepo()
        
        # Initialize event bus, task management, and agent state tracking
        self.event_bus = EventBus()
        self.task_manager = TaskLifecycleManager(self.event_bus)
        self.agent_state_manager = AgentStateManager()
        
        # Initialize components
        self.agents: Dict[str, Agent] = {}
        self.orchestrator: Optional[Orchestrator] = None
        self.planner = None
        self.capability_extractor = None
        self.reporter = Reporter()
        self.run_id: Optional[str] = None
        self._workspace_guard: PathGuard | None = None
        
        logger.info("Flow initialized", flow_name=self.config.name)
    
    def _create_agents(self) -> Dict[str, Agent]:
        """Create agents from configuration."""
        agents = {}
        
        # If no agents configured, leave empty and let demos configure agents explicitly
        if not self.config.agents:
            logger.warning("No agents configured in FlowConfig; demos should add agents explicitly")
        else:
            # Create configured agents
            for agent_name, agent_config in self.config.agents.items():
                logger.info("Creating agent", agent_name=agent_name)
                
                # Get tools for this agent
                tools = self.tool_registry.get_tools_by_names(agent_config.tools)
                
                # Add tools by tags if specified
                if agent_config.tags:
                    tagged_tools = self.tool_registry.get_tools_by_tags(set(agent_config.tags))
                    tools.extend(tagged_tools)
                
                # Remove duplicates
                tool_names = set()
                unique_tools = []
                for tool in tools:
                    if tool.name not in tool_names:
                        unique_tools.append(tool)
                        tool_names.add(tool.name)
                
                agents[agent_name] = Agent(agent_config, unique_tools)
        
        return agents
    
    def _create_orchestrator(self) -> Orchestrator:
        """Create the orchestrator with configured agents."""
        orch = Orchestrator(
            config=self.config.orchestrator,
            agents=self.agents,
            tool_registry=self.tool_registry,
            planner=self.planner,
            capability_extractor=self.capability_extractor,
        )
        # attach reporter/run_id
        try:
            setattr(orch, "reporter", self.reporter)
            setattr(orch, "run_id", self.run_id)
        except Exception:
            pass
        return orch
    
    def start(self) -> "Flow":
        """Start the flow by creating all components."""
        # Assign a run_id for observability
        self.run_id = str(uuid.uuid4())
        self.reporter.set_run_id(self.run_id)
        # Disable LangSmith/LangChain tracing to avoid telemetry uploads
        try:
            import os as _os
            _os.environ["LANGCHAIN_TRACING_V2"] = "false"
            _os.environ["LANGSMITH_TRACING"] = "false"
            _os.environ["LANGCHAIN_ENDPOINT"] = ""
        except Exception:
            pass
        logger.info("Starting flow", flow_name=self.config.name, run_id=self.run_id)
        # Minimal console logs; detailed transcript goes to file at end of run
        try:
            self.reporter.set_console_verbosity(minimal=True)
        except Exception:
            pass
        self.reporter.flow("starting", flow_name=self.config.name)
        
        # Create agents from config only if agents not preconfigured
        if not self.agents:
            self.agents = self._create_agents()
            logger.info("Created agents from config", agent_count=len(self.agents))
        else:
            logger.info("Using preconfigured agents", agent_count=len(self.agents))
        # Attach reporter/run_id to agents
        for name, agent in self.agents.items():
            try:
                setattr(agent, "reporter", self.reporter)
                setattr(agent, "run_id", self.run_id)
                # Provide a back-reference to the Flow for agents that can use it (e.g., to access orchestrator/task context)
                if hasattr(agent, "set_flow_reference"):
                    try:
                        agent.set_flow_reference(self)
                    except Exception:
                        pass
            except Exception:
                pass

        # Enforce architecture contract: at least one agent must exist
        if not self.agents:
            raise ValueError(
                "No agents are configured or pre-registered. Per architecture, an Orchestrator must have at least one Agent. "
                "Add an agent programmatically before start() or provide agents in config.yaml."
            )
        
        # Create orchestrator
        self.orchestrator = self._create_orchestrator()
        logger.info("Created orchestrator")
        
        logger.info("Flow started successfully", run_id=self.run_id)
        self.reporter.flow("started", agent_count=len(self.agents))
        return self
    
    async def arun(
        self,
        request: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Run a request through the flow asynchronously."""
        if not self.orchestrator:
            raise RuntimeError("Flow not started. Call start() first.")
        
        logger.info("Processing request", request=request, thread_id=thread_id, run_id=self.run_id)
        self.reporter.flow("request_start", thread_id=thread_id, request=request)
        try:
            result = await self.orchestrator.arun(request, thread_id, **kwargs)
            logger.info("Request completed successfully", thread_id=thread_id, run_id=self.run_id)
            self.reporter.flow("request_end", thread_id=thread_id)
            # Persist human-readable transcript to a file (quiet console)
            try:
                path = self.reporter.dump_transcript_to_file()
                if path:
                    logger.info("Transcript written", path=path)
            except Exception:
                pass
            return result
        except Exception as e:
            logger.error("Request failed", error=str(e), thread_id=thread_id, run_id=self.run_id)
            self.reporter.flow("request_error", thread_id=thread_id, error=str(e))
            raise
    
    async def astream(
        self,
        request: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream the execution of a request."""
        if not self.orchestrator:
            raise RuntimeError("Flow not started. Call start() first.")
        
        logger.info("Streaming request", request=request, thread_id=thread_id)
        
        try:
            async for chunk in self.orchestrator.astream(request, thread_id, **kwargs):
                yield chunk
            logger.info("Stream completed successfully", thread_id=thread_id)
        except Exception as e:
            logger.error("Stream failed", error=str(e), thread_id=thread_id)
            raise
    
    def run(
        self,
        request: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Synchronous wrapper for arun."""
        return asyncio.run(self.arun(request, thread_id, **kwargs))
    
    def stream(
        self,
        request: str,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ):
        """Synchronous wrapper for astream."""
        async def _stream():
            async for chunk in self.astream(request, thread_id, **kwargs):
                yield chunk
        
        return asyncio.run(self._sync_stream_wrapper(_stream()))
    
    async def _sync_stream_wrapper(self, async_gen):
        """Helper to convert async generator to sync."""
        chunks = []
        async for chunk in async_gen:
            chunks.append(chunk)
        return chunks
    
    def add_agent(self, name: str, agent: Agent) -> "Flow":
        """Add an agent to the flow.
        If the agent has auto_discover=True (default), adopt current Flow tools/resources and
        enable dynamic discovery for future registrations.
        """
        self.agents[name] = agent
        logger.info("Added agent", agent_name=name)
        
        # Attach reporter/run_id, event bus, and register in state manager
        try:
            setattr(agent, "reporter", self.reporter)
            setattr(agent, "run_id", self.run_id)
            setattr(agent, "event_bus", self.event_bus)
            
            # Register agent in state manager with specialized tools
            tool_names = [t.name for t in agent.tools] if hasattr(agent, 'tools') else []
            agent_state = self.agent_state_manager.register_agent(name, tool_names)
            setattr(agent, "agent_state", agent_state)
        except Exception:
            pass
        
        # Auto adopt/discover
        try:
            if getattr(agent, "auto_discover", True):
                if hasattr(agent, "adopt_flow_tools"):
                    agent.adopt_flow_tools(self)
                if hasattr(agent, "adopt_flow_resources"):
                    agent.adopt_flow_resources(self)
                if hasattr(agent, "enable_dynamic_discovery"):
                    agent.enable_dynamic_discovery(self)
        except Exception:
            logger.debug("Auto-discovery setup failed for agent", agent=name)
        
        # Recreate orchestrator if it exists
        if self.orchestrator:
            self.orchestrator = self._create_orchestrator()
        
        return self
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all agent names."""
        return list(self.agents.keys())

    def describe_agents(self) -> List[Dict[str, Any]]:
        """Return a catalog of agents with tools and inferred capabilities for planning."""
        catalog: List[Dict[str, Any]] = []
        # build a quick lookup for tool metadata
        try:
            tool_meta = self.tool_registry.list_tools()
        except Exception:
            tool_meta = {}
        for name, agent in self.agents.items():
            desc = agent.describe()
            caps = set()
            # tags from config
            for tag in desc.get("tags", []) or []:
                caps.add(tag)
            # from tools -> add registered capabilities
            for tname in desc.get("tools", []) or []:
                meta = tool_meta.get(tname)
                if meta:
                    for c in (meta.capabilities or set()):
                        caps.add(c)
                # simple heuristic as fallback
                if tname in ("write_file", "write_text_atomic"):
                    caps.add("file_write")
                if tname in ("read_file", "read_text_fast", "read_bytes_fast"):
                    caps.add("file_read")
                if tname in ("regex_search_dir", "regex_search_file", "find_files"):
                    caps.add("search")
                if tname in ("dir_tree", "list_dir", "list_directory"):
                    caps.add("dir_walk")
                if tname == "file_stat":
                    caps.add("file_meta")
            catalog.append({
                "name": name,
                "tools": desc.get("tools", []),
                "resources": desc.get("resources", []),
                "capabilities": sorted(caps),
                "tags": desc.get("tags", []),
            })
        return catalog
    
    def register_tools(self, *objs: Any) -> "Flow":
        """Register tools or toolsets.
        Accepts:
        - BaseTool instances
        - ToolSet instances (or any object with instantiate() -> List[BaseTool])
        - Iterables (lists/tuples) of the above, nested arbitrarily
        """
        from langchain_core.tools import BaseTool

        def extract(obj: Any) -> List[BaseTool]:
            out: List[BaseTool] = []
            if obj is None:
                return out
            # Tool instance
            if isinstance(obj, BaseTool):
                out.append(obj)
                return out
            # ToolSet-like (duck typing)
            inst_meth = getattr(obj, "instantiate", None)
            if callable(inst_meth):
                try:
                    items = inst_meth()
                    for it in items:
                        out.extend(extract(it))
                    return out
                except Exception:
                    pass
            # Iterable
            if isinstance(obj, (list, tuple, set)):
                for it in obj:
                    out.extend(extract(it))
                return out
            # Unknown
            logger.warning("register_tools: skipping unsupported object", obj=type(obj).__name__)
            return out

        all_tools: List[BaseTool] = []
        for o in objs:
            all_tools.extend(extract(o))
        for t in all_tools:
            self.tool_registry.register_tool_instance(t)
            logger.info("Registered tool", tool_name=getattr(t, "name", t.__class__.__name__))
        return self

    # Backward-compat aliases
    def register_tool(self, *args, **kwargs) -> "Flow":
        """Deprecated: prefer register_tools(tool[, tool2, ...]).
        Supports both old class-based signature and instance-based pass-through.
        """
        from langchain_core.tools import BaseTool
        if args and isinstance(args[0], BaseTool):
            return self.register_tools(args[0])
        # Old signature: (name, tool_class, ...)
        if len(args) >= 2:
            name, tool_class = args[0], args[1]
            self.tool_registry.register_tool(name, tool_class, **kwargs)
            logger.info("Registered tool", tool_name=name)
            return self
        logger.warning("register_tool: called with unsupported arguments; use register_tools(tool)")
        return self

    def register_tool_instance(self, tool, **kwargs) -> "Flow":
        """Deprecated: prefer register_tools(tool)."""
        return self.register_tools(tool)
    
    def register_resource(self, name: str, resource_type: str, factory, **kwargs) -> "Flow":
        """Register a new resource."""
        self.resource_registry.register_resource(name, resource_type, factory, **kwargs)
        logger.info("Registered resource", resource_name=name, resource_type=resource_type)
        return self

    def set_planner(self, planner) -> "Flow":
        """Attach a Planner before starting the flow."""
        self.planner = planner
        logger.info("Planner set on flow")
        return self
    
    def set_capability_extractor(self, extractor) -> "Flow":
        """Attach a CapabilityExtractor before starting the flow."""
        self.capability_extractor = extractor
        logger.info("Capability extractor set on flow")
        return self
    
    def set_workspace(self, root: str | Path, allow_read_outside: bool = False) -> "Flow":
        """Restrict all filesystem tools to a workspace root.
        - Writes are forbidden outside the workspace.
        - Reads outside allowed only if allow_read_outside=True.
        Applies to all current and future tools via ToolRegistry.
        """
        guard = PathGuard(root, allow_read_outside=allow_read_outside)
        self._workspace_guard = guard
        try:
            self.tool_registry.set_path_guard(guard)
            logger.info("Workspace guard set", workspace=str(guard.workspace_root), allow_read_outside=allow_read_outside)
        except Exception as e:
            logger.warning("Failed to set workspace guard on registry", error=str(e))
        return self

    def install_tools_from_repo(
        self,
        names: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        sets: Optional[List[str]] = None,
    ) -> "Flow":
        """Instantiate tools from the ToolRepo and register them.
        - names: list of tool names
        - tags: list of tags (any match)
        - sets: list of predefined toolset names (e.g., 'filesystem')
        """
        selected: List[Any] = []
        if sets:
            for s in sets:
                try:
                    selected.extend(self.tool_repo.instantiate_set(s))
                except Exception:
                    pass
        if names:
            try:
                selected.extend(self.tool_repo.instantiate(names=names))
            except Exception:
                pass
        if tags:
            try:
                selected.extend(self.tool_repo.instantiate(tags=set(tags)))
            except Exception:
                pass
        if selected:
            self.register_tools(selected)
        return self

    def stop(self) -> "Flow":
        """Stop the flow and cleanup resources."""
        logger.info("Stopping flow", flow_name=self.config.name)
        
        # For now, just reset components
        # In production, you'd handle graceful shutdown of active conversations
        self.orchestrator = None
        
        logger.info("Flow stopped")
        return self