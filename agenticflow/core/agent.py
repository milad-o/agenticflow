"""Base Agent class for individual worker agents."""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING, Union
from datetime import datetime, timezone

from .state import AgentMessage, AgentStatus, MessageType
from .command import create_agent_response_command, create_finish_command
from .langgraph_state import AgenticFlowState

try:
    from langgraph.types import Command
    HAS_COMMAND = True
except ImportError:
    HAS_COMMAND = False

if TYPE_CHECKING:
    from .orchestrator import Orchestrator
    from .supervisor import Supervisor
    from ..workspace.workspace import Workspace

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from langgraph.prebuilt import create_react_agent
    from langgraph.graph import START, END
    from langgraph.types import Command
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    # Define fallback types for type checking
    Command = Any
    HumanMessage = Any
    SystemMessage = Any
    ChatOpenAI = Any
    create_react_agent = Any
    START = Any
    END = Any


class Tool:
    """Represents a tool that an agent can use."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a tool.

        Args:
            name: Tool name
            description: Tool description for the agent
            func: The callable function
            parameters: Tool parameter schema
        """
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}

    async def execute(self, **kwargs) -> Any:
        """Execute the tool.

        Args:
            **kwargs: Arguments for the tool function

        Returns:
            Tool execution result
        """
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        else:
            return self.func(**kwargs)


class Agent(ABC):
    """Base class for all agents in the framework."""

    def __init__(
        self,
        name: str,
        description: str = "",
        keywords: Optional[List[str]] = None,
        max_retries: int = 3,
    ):
        """Initialize the agent.

        Args:
            name: Agent name (must be unique within flow)
            description: Agent description
            keywords: Keywords for message routing
            max_retries: Maximum number of retries for failed operations
        """
        self.name = name
        self.description = description
        self.keywords = keywords or []
        self.max_retries = max_retries

        # State management
        self.status = AgentStatus.IDLE
        self.current_task: Optional[str] = None
        self.tools: Dict[str, Tool] = {}
        self.static_resources: Dict[str, Any] = {}

        # Framework integration
        self.orchestrator: Optional["Orchestrator"] = None
        self.supervisor: Optional["Supervisor"] = None
        self.workspace: Optional["Workspace"] = None

        # Execution tracking
        self.message_history: List[AgentMessage] = []
        self.execution_count = 0
        self.last_execution: Optional[datetime] = None

        # Async control
        self._stop_event = asyncio.Event()
        self._current_task: Optional[asyncio.Task] = None

    def set_orchestrator(self, orchestrator: "Orchestrator") -> None:
        """Set the orchestrator reference.

        Args:
            orchestrator: The orchestrator this agent belongs to
        """
        self.orchestrator = orchestrator

    def set_workspace(self, workspace: "Workspace") -> None:
        """Set the workspace reference.

        Args:
            workspace: The workspace this agent can access
        """
        self.workspace = workspace

    def set_supervisor(self, supervisor: "Supervisor") -> None:
        """Set the supervisor reference.

        Args:
            supervisor: The supervisor this agent belongs to
        """
        self.supervisor = supervisor
        if supervisor.orchestrator and supervisor.orchestrator.flow:
            self.workspace = supervisor.orchestrator.flow.workspace

    def add_tool(self, tool: Tool) -> "Agent":
        """Add a tool to the agent.

        Args:
            tool: The tool to add

        Returns:
            Self for method chaining
        """
        self.tools[tool.name] = tool
        return self

    def add_static_resource(self, name: str, resource: Any) -> "Agent":
        """Add a static resource to the agent.

        Args:
            name: Resource name
            resource: The resource object

        Returns:
            Self for method chaining
        """
        self.static_resources[name] = resource
        return self

    def _create_agent_node(self):
        """Create LangGraph agent node for agent execution.
        
        This is a base implementation that should be overridden by concrete agent classes.
        
        Returns:
            Function that can be used as a LangGraph node
        """
        if not HAS_LANGCHAIN:
            raise ImportError("LangChain is required for LangGraph integration")
        
        def agent_node(state: AgenticFlowState) -> Any:
            """LangGraph node for agent execution."""
            try:
                # Get the last message from state
                messages = state.get("messages", [])
                if not messages:
                    return Command(goto=END, update={})  # type: ignore
                
                last_message = messages[-1]
                
                # Create AgentMessage from the last message
                if hasattr(last_message, 'content'):
                    agent_message = AgentMessage(
                        type=MessageType.USER,
                        sender="user",
                        content=str(last_message.content),
                    )
                else:
                    agent_message = AgentMessage(
                        type=MessageType.USER,
                        sender="user",
                        content=str(last_message),
                    )
                
                # Execute the agent's logic
                response_command = asyncio.run(self.execute(agent_message))
                
                # Extract response from command
                if response_command and hasattr(response_command, 'update') and response_command.update:
                    response_messages = response_command.update.get("messages", [])
                    if response_messages:
                        response_message = response_messages[0]
                        
                        # Update execution path
                        execution_path = state.get("execution_path", [])
                        execution_path.append(f"agent_{self.name}_completed")
                        
                        # Determine next step based on command
                        goto = response_command.goto if hasattr(response_command, 'goto') else "supervisor"
                        
                        return Command(  # type: ignore
                            goto=goto,
                            update={
                                "messages": [response_message],
                                "execution_path": execution_path,
                                "completion_status": {
                                    **state.get("completion_status", {}),
                                    self.name: True
                                }
                            }
                        )
                
                # Fallback if no response
                return Command(goto="supervisor", update={})  # type: ignore
                
            except Exception as e:
                # Return error command
                error_msg = AgentMessage(
                    type=MessageType.ERROR,
                    sender=self.name,
                    content=f"Agent execution failed: {str(e)}",
                    metadata={"error_type": type(e).__name__},
                )
                
                return Command(  # type: ignore
                    goto="supervisor",
                    update={
                        "messages": [error_msg],
                        "completion_status": {
                            **state.get("completion_status", {}),
                            f"{self.name}_error": True
                        }
                    }
                )

        return agent_node

    @abstractmethod
    async def execute(self, message: AgentMessage) -> Any:
        """Execute the agent's main logic and return a Command.

        This method must be implemented by concrete agent classes.

        Args:
            message: The message to process

        Returns:
            Command indicating next steps and state updates
        """
        pass

    async def process_message(self, message: AgentMessage) -> Any:
        """Process a message and return a Command.

        Args:
            message: The message to process

        Returns:
            Command with response and routing information
        """
        if self.status == AgentStatus.ERROR:
            error_msg = AgentMessage(
                type=MessageType.ERROR,
                sender=self.name,
                content=f"Agent {self.name} is in error state",
            )
            return create_agent_response_command(error_msg)

        # Add to history
        self.message_history.append(message)

        # Set status to busy
        await self._set_status(AgentStatus.BUSY)

        try:
            # Execute the agent's logic
            command = await self.execute(message)

            # Update execution tracking
            self.execution_count += 1
            self.last_execution = datetime.now(timezone.utc)

            # Set status back to idle
            await self._set_status(AgentStatus.IDLE)

            return command

        except Exception as e:
            await self._set_status(AgentStatus.ERROR)
            error_msg = AgentMessage(
                type=MessageType.ERROR,
                sender=self.name,
                content=f"Error processing message: {str(e)}",
                metadata={"error_type": type(e).__name__, "original_message": message.to_dict()},
            )
            self.message_history.append(error_msg)
            return create_agent_response_command(error_msg)

    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Use a tool by name.

        Args:
            tool_name: Name of the tool to use
            **kwargs: Arguments for the tool

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]
        return await tool.execute(**kwargs)

    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent.

        Returns:
            Dictionary with agent status information
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "current_task": self.current_task,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "available_tools": list(self.tools.keys()),
            "static_resources": list(self.static_resources.keys()),
            "message_history_count": len(self.message_history),
        }

    async def stop(self) -> None:
        """Stop the agent."""
        self._stop_event.set()

        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass

        await self._set_status(AgentStatus.IDLE)

    async def reset(self) -> None:
        """Reset the agent to initial state."""
        await self.stop()
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.message_history.clear()
        self.execution_count = 0
        self.last_execution = None
        self._stop_event.clear()

    async def _set_status(self, status: AgentStatus) -> None:
        """Set the agent status and update flow state if available.

        Args:
            status: The new status
        """
        self.status = status

        # Update flow state if connected
        if self.orchestrator and self.orchestrator.flow:
            await self.orchestrator.flow.state.update_agent_status(self.name, status)

        # Notify observer if available
        if self.orchestrator and self.orchestrator.flow and self.orchestrator.flow.observer:
            await self.orchestrator.flow.observer.agent_status_changed(
                self.name, status.value
            )

    def is_available(self) -> bool:
        """Check if the agent is available to process messages.

        Returns:
            True if agent is idle and not stopped
        """
        return self.status == AgentStatus.IDLE and not self._stop_event.is_set()


class SimpleAgent(Agent):
    """A simple agent implementation for basic use cases."""

    def __init__(
        self,
        name: str,
        description: str = "",
        response_template: str = "Agent {name} processed: {content}",
        **kwargs
    ):
        """Initialize the simple agent.

        Args:
            name: Agent name
            description: Agent description
            response_template: Template for response messages
            **kwargs: Additional arguments for base Agent
        """
        super().__init__(name, description, **kwargs)
        self.response_template = response_template

    async def execute(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Execute simple message processing.

        Args:
            message: The message to process

        Returns:
            Simple response message
        """
        # Simulate some processing time
        await asyncio.sleep(0.1)

        response_content = self.response_template.format(
            name=self.name,
            content=message.content,
            sender=message.sender,
        )

        response_msg = AgentMessage(
            type=MessageType.AGENT,
            sender=self.name,
            content=response_content,
            metadata={"processed_message_id": str(message.id)},
        )

        return create_agent_response_command(response_msg)  # type: ignore


class ReActAgent(Agent):
    """LLM-powered ReAct agent that uses reasoning and tools."""

    def __init__(
        self,
        name: str,
        description: str = "",
        keywords: Optional[List[str]] = None,
        max_retries: int = 3,
        llm_model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        initialize_llm: bool = True,
    ):
        """Initialize ReAct agent.

        Args:
            name: Agent name
            description: Agent description
            keywords: Keywords for routing
            max_retries: Maximum retries for failed operations
            llm_model: LLM model to use
            api_key: OpenAI API key
            system_prompt: Custom system prompt for the agent
            initialize_llm: Whether to initialize the LLM immediately (set to False for testing)
        """
        super().__init__(name, description, keywords, max_retries)

        if not HAS_LANGCHAIN:
            raise ImportError("LangChain is required for ReAct agents. Install with: pip install langchain-openai langchain-core langgraph")

        self.llm = None
        if initialize_llm:
            self.llm = ChatOpenAI(  # type: ignore
                model=llm_model,
                api_key=api_key or os.getenv("OPENAI_API_KEY"),  # type: ignore
                temperature=0.1
            )

        self.system_prompt = system_prompt or f"""You are {name}, {description}.

You have access to tools to help you complete tasks. Use them as needed.
Always report back with your results when finished.

Your capabilities: {', '.join(keywords) if keywords else 'General assistance'}
"""

        # This will be set when tools are added
        self._react_agent = None

    def _build_react_agent(self):
        """Build the LangChain ReAct agent with current tools."""
        if not self.tools:
            # No tools, use simple LLM agent
            return None

        # Convert our tools to LangChain tools
        langchain_tools = []
        for tool in self.tools.values():
            # Create a simple LangChain tool wrapper
            def tool_func(**kwargs):
                return asyncio.run(tool.execute(**kwargs))

            langchain_tools.append(tool_func)

        try:
            if self.llm:
                self._react_agent = create_react_agent(  # type: ignore
                    self.llm,
                    langchain_tools,
                    prompt=self.system_prompt
                )
        except Exception as e:
            # Fallback if ReAct agent creation fails
            self._react_agent = None

    async def execute(self, message: AgentMessage) -> Any:
        """Execute using ReAct pattern."""
        # Rebuild react agent if tools changed
        if self._react_agent is None and self.tools:
            self._build_react_agent()

        try:
            if self._react_agent:
                # Use ReAct agent
                state = {"messages": [HumanMessage(content=message.content)]}  # type: ignore
                result = await self._react_agent.ainvoke(state)

                response_content = str(result["messages"][-1].content)
            elif self.llm:
                # Fallback to simple LLM processing
                messages = [
                    SystemMessage(content=self.system_prompt),  # type: ignore
                    HumanMessage(content=message.content)  # type: ignore
                ]
                result = await self.llm.ainvoke(messages)
                response_content = str(result.content)
            else:
                response_content = f"Agent {self.name} processed: {message.content}"

            response_msg = AgentMessage(
                type=MessageType.AGENT,
                sender=self.name,
                content=response_content,
                metadata={"agent_type": "react", "tools_used": list(self.tools.keys())},
            )

            return create_agent_response_command(response_msg)

        except Exception as e:
            # Return error command
            error_msg = AgentMessage(
                type=MessageType.ERROR,
                sender=self.name,
                content=f"ReAct execution failed: {str(e)}",
                metadata={"error_type": type(e).__name__},
            )
            return create_agent_response_command(error_msg)