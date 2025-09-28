"""Main Flow class - the container for all agent operations."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ..core.state import FlowState, AgentMessage, MessageType
from ..workspace.workspace import Workspace
from ..observability.observer import Observer
from .orchestrator import Orchestrator
from .langgraph_state import AgenticFlowState

# LangGraph is required for the framework
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage


class Flow:
    """Main container for orchestrating agent workflows.

    The Flow class is the entry point for creating and managing multi-agent workflows.
    It provides workspace management, observability, and orchestration capabilities.
    """

    def __init__(
        self,
        name: str,
        workspace_path: Optional[Union[str, Path]] = None,
        auto_create_workspace: bool = True,
        enable_observability: bool = True,
    ):
        """Initialize the Flow.

        Args:
            name: Name of the flow
            workspace_path: Path to workspace directory (auto-generated if None)
            auto_create_workspace: Whether to create workspace automatically
            enable_observability: Whether to enable observability features
        """
        self.name = name
        self.id = str(uuid4())

        # Initialize workspace
        if workspace_path is None:
            workspace_path = Path.cwd() / "workspaces" / f"flow_{self.name}_{self.id[:8]}"

        self.workspace = Workspace(workspace_path, create_if_not_exists=auto_create_workspace)

        # Initialize state
        self.state = FlowState(workspace_path=str(self.workspace.workspace_path))

        # Initialize observability
        self.observer = Observer(enabled=enable_observability) if enable_observability else None

        # Initialize orchestrator
        self.orchestrator: Optional[Orchestrator] = None

        # LangGraph integration - core architecture
        self._enable_langgraph = True
        self._graph: Optional[Any] = None
        self._compiled_graph: Optional[Any] = None

        # Flow execution state
        self._running = False
        self._tasks: List[asyncio.Task] = []

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Flow(name='{self.name}', id='{self.id[:8]}')"

    def add_orchestrator(self, orchestrator: Orchestrator) -> "Flow":
        """Add an orchestrator to the flow.

        Args:
            orchestrator: The orchestrator instance

        Returns:
            Self for method chaining
        """
        self.orchestrator = orchestrator
        orchestrator.set_flow(self)
        
        # Build LangGraph when orchestrator is added
        self._build_langgraph()
        
        return self

    async def start(self, initial_message: str, context: Optional[Dict[str, Any]] = None, continuous: bool = False) -> None:
        """Start the flow execution.

        Args:
            initial_message: Initial message to start the flow
            context: Additional context to set in the flow state
            continuous: If True, keep the flow running for additional messages
        """
        if self._running:
            raise RuntimeError("Flow is already running")

        if self.orchestrator is None:
            raise ValueError("No orchestrator configured")

        self._running = True

        try:
            # Set initial context
            if context:
                for key, value in context.items():
                    await self.state.set_context(key, value)

            # Create initial message
            initial_msg = AgentMessage(
                type=MessageType.USER,
                sender="user",
                content=initial_message,
            )

            await self.state.add_message(initial_msg)

            if self.observer:
                await self.observer.flow_started(self.id, self.name)

            # Execute with LangGraph (core architecture)
            if self._compiled_graph:
                # Use LangGraph execution (following tutorial pattern)
                initial_state = {
                    "messages": [("user", initial_message)],  # Use tuple format like tutorial
                    "orchestrator_context": {},
                    "team_contexts": {},
                    "execution_path": [],
                    "completion_status": {},
                    "flow_id": self.id,
                    "flow_name": self.name,
                    "workspace_path": str(self.workspace.workspace_path),
                }
                
                # Execute the graph and get final result
                result = await self._compiled_graph.ainvoke(initial_state, {"recursion_limit": 100})
                
                # Convert all messages from LangGraph result to our AgentMessage format
                if "messages" in result:
                    for msg in result["messages"]:
                        if hasattr(msg, 'content') and msg.content:
                            # Determine message type and sender
                            sender = getattr(msg, 'name', 'system')
                            if hasattr(msg, 'type') and msg.type == 'human':
                                msg_type = MessageType.USER
                            elif sender == 'user':
                                msg_type = MessageType.USER
                            elif 'failed' in msg.content.lower() or 'error' in msg.content.lower():
                                msg_type = MessageType.ERROR
                            else:
                                msg_type = MessageType.AGENT
                                
                            agent_msg = AgentMessage(
                                type=msg_type,
                                sender=sender,
                                content=msg.content,
                                metadata=getattr(msg, 'additional_kwargs', {})
                            )
                            await self.state.add_message(agent_msg)
            else:
                # Fallback to original async messaging
                await self.orchestrator.process(initial_msg)

            # If continuous mode, keep running
            if continuous:
                return  # Keep _running = True and return without completing

        except Exception as e:
            if self.observer:
                await self.observer.flow_error(self.id, str(e))
            raise
        finally:
            # Only complete if not in continuous mode
            if not continuous:
                self._running = False
                if self.observer:
                    await self.observer.flow_completed(self.id)

    async def stop(self) -> None:
        """Stop the flow execution."""
        was_running = self._running
        self._running = False

        # Cancel all running tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()

        # Clean up compiled graph to free memory
        if hasattr(self, '_compiled_graph') and self._compiled_graph:
            del self._compiled_graph
            self._compiled_graph = None

        if self.observer and was_running:
            await self.observer.flow_completed(self.id)
            await self.observer.flow_stopped(self.id)

    async def send_message(self, content: str, sender: str = "user") -> None:
        """Send a message to the flow during execution.

        Args:
            content: Message content
            sender: Message sender identifier
        """
        if not self._running:
            raise RuntimeError("Flow is not running")

        message = AgentMessage(
            type=MessageType.USER if sender == "user" else MessageType.AGENT,
            sender=sender,
            content=content,
        )

        await self.state.add_message(message)

        if self.orchestrator:
            await self.orchestrator.process(message)

    async def get_messages(self, limit: Optional[int] = None) -> List[AgentMessage]:
        """Get messages from the flow.

        Args:
            limit: Maximum number of messages to return (most recent first)

        Returns:
            List of messages
        """
        messages = self.state.messages
        if limit:
            messages = messages[-limit:]
        return messages

    async def get_workspace_files(self, pattern: str = "*") -> List[str]:
        """Get list of files in the workspace.

        Args:
            pattern: Glob pattern for file matching

        Returns:
            List of file paths relative to workspace
        """
        return await self.workspace.list_files(pattern=pattern)

    async def export_state(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Export the current flow state.

        Args:
            file_path: Optional file path to save state (relative to workspace)

        Returns:
            Dictionary representation of the flow state
        """
        state_dict = {
            "flow_id": self.id,
            "flow_name": self.name,
            "workspace_path": str(self.workspace.workspace_path),
            "state": self.state.to_dict(),
        }

        if file_path:
            await self.workspace.write_json(file_path, state_dict)

        return state_dict

    async def get_metrics(self) -> Dict[str, Any]:
        """Get flow execution metrics.

        Returns:
            Dictionary with flow metrics
        """
        if not self.observer:
            return {"observability_disabled": True}

        return await self.observer.get_metrics()

    def is_running(self) -> bool:
        """Check if the flow is currently running.

        Returns:
            True if flow is running
        """
        return self._running

    async def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for the flow to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if flow completed, False if timeout
        """
        try:
            if self._tasks:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=timeout
                )
            return True
        except asyncio.TimeoutError:
            return False

    def _build_langgraph(self) -> None:
        """Build LangGraph StateGraph from orchestrator structure."""
        # LangGraph is required for the framework
        
        if not self.orchestrator:
            return
        
        # Create the StateGraph
        self._graph = StateGraph(AgenticFlowState)  # type: ignore
        
        # Add orchestrator node
        self._graph.add_node("orchestrator", self.orchestrator._create_supervisor_node())  # type: ignore
        
        # Add team nodes
        for team_name, supervisor in self.orchestrator.teams.items():
            self._graph.add_node(team_name, supervisor._create_supervisor_node())  # type: ignore
            
            # Add agent nodes within teams
            for agent_name, agent in supervisor.agents.items():
                agent_node_name = f"{team_name}_{agent_name}"
                self._graph.add_node(agent_node_name, agent._create_agent_node())  # type: ignore
        
        # Add individual agent nodes (if any)
        for agent_name, agent in self.orchestrator.agents.items():
            self._graph.add_node(agent_name, agent._create_agent_node())  # type: ignore
        
        # Define edges - Command pattern handles routing automatically
        self._graph.add_edge(START, "orchestrator")  # type: ignore
        
        # For Command pattern, we don't need explicit edges between nodes
        # Command objects handle the routing automatically
        
        # Clean up previous graph if it exists
        if hasattr(self, '_compiled_graph') and self._compiled_graph:
            del self._compiled_graph
            
        # Compile the graph
        self._compiled_graph = self._graph.compile()  # type: ignore

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._running:
            await self.stop()