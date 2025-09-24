"""Core Flow container for AgenticFlow."""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
import structlog
import uuid

from .config import FlowConfig, AgentConfig
from ..orchestrator.orchestrator import Orchestrator
from ..agent.agent import Agent
from ..registry.tool_registry import ToolRegistry
from ..registry.resource_registry import ResourceRegistry
from .env import load_env
from ..observability.reporter import Reporter

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
        
        # Initialize components
        self.agents: Dict[str, Agent] = {}
        self.orchestrator: Optional[Orchestrator] = None
        self.planner = None
        self.capability_extractor = None
        self.reporter = Reporter()
        self.run_id: Optional[str] = None
        
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
        logger.info("Starting flow", flow_name=self.config.name, run_id=self.run_id)
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
        """Add an agent to the flow."""
        self.agents[name] = agent
        logger.info("Added agent", agent_name=name)
        
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
    
    def register_tool(self, name: str, tool_class: type, **kwargs) -> "Flow":
        """Register a new tool."""
        self.tool_registry.register_tool(name, tool_class, **kwargs)
        logger.info("Registered tool", tool_name=name)
        return self
    
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
    
    def stop(self) -> "Flow":
        """Stop the flow and cleanup resources."""
        logger.info("Stopping flow", flow_name=self.config.name)
        
        # For now, just reset components
        # In production, you'd handle graceful shutdown of active conversations
        self.orchestrator = None
        
        logger.info("Flow stopped")
        return self