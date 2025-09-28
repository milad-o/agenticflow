"""Supervisor class for managing teams of agents."""

import asyncio
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel

from .state import AgentMessage, AgentStatus, MessageType
from .agent import Agent
from .langgraph_state import AgenticFlowState, TeamRoutingDecision

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from langgraph.types import Command
    from langgraph.graph import START, END
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    # Define fallback types for type checking
    Command = Any
    HumanMessage = Any
    SystemMessage = Any
    ChatOpenAI = Any
    START = Any
    END = Any


class Supervisor:
    """LLM-powered supervisor for managing a team of agents.

    The supervisor uses an LLM to intelligently route messages between agents
    and manages team-level execution.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        keywords: Optional[List[str]] = None,
        max_concurrent_agents: int = 5,
        llm_model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        initialize_llm: bool = True,
    ):
        """Initialize the LLM-powered supervisor.

        Args:
            name: Supervisor name
            description: Supervisor description
            keywords: Keywords for message routing to this team
            max_concurrent_agents: Maximum number of agents to run concurrently
            llm_model: LLM model to use for routing decisions
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if None)
            initialize_llm: Whether to initialize the LLM immediately (set to False for testing)
        """
        self.name = name
        self.description = description
        self.keywords = keywords or []
        self.max_concurrent_agents = max_concurrent_agents

        if not HAS_LANGCHAIN:
            raise ImportError("LangChain is required for LLM-based supervisor. Install with: pip install langchain-openai langchain-core")

        self.llm = None
        if initialize_llm:
            self.llm = ChatOpenAI(  # type: ignore
                model=llm_model,
                api_key=api_key or os.getenv("OPENAI_API_KEY"),  # type: ignore
                temperature=0.1
            )

        # Agent management
        self.agents: Dict[str, Agent] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}

        # Framework integration
        self.orchestrator: Optional["Orchestrator"] = None

        # Execution tracking
        self.message_history: List[AgentMessage] = []
        self.completion_order: List[str] = []

        # Control
        self._stop_event = asyncio.Event()
        self._semaphore = asyncio.Semaphore(max_concurrent_agents)

    def set_orchestrator(self, orchestrator: "Orchestrator") -> None:
        """Set the orchestrator reference.

        Args:
            orchestrator: The orchestrator this supervisor belongs to
        """
        self.orchestrator = orchestrator

        # Set orchestrator for all agents
        for agent in self.agents.values():
            agent.set_supervisor(self)

    def add_agent(self, agent: Agent) -> "Supervisor":
        """Add an agent to the team.

        Args:
            agent: The agent to add

        Returns:
            Self for method chaining
        """
        self.agents[agent.name] = agent
        agent.set_supervisor(self)

        # Set workspace if available through orchestrator
        if self.orchestrator and self.orchestrator.flow and self.orchestrator.flow.workspace:
            agent.set_workspace(self.orchestrator.flow.workspace)

        return self

    def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent from the team.

        Args:
            agent_name: Name of the agent to remove

        Returns:
            True if agent was removed, False if not found
        """
        if agent_name not in self.agents:
            return False

        # Stop the agent if it's running
        if agent_name in self.agent_tasks:
            task = self.agent_tasks[agent_name]
            if not task.done():
                task.cancel()
            del self.agent_tasks[agent_name]

        # Remove the agent
        del self.agents[agent_name]
        return True

    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process a message by routing it to appropriate agents.

        Args:
            message: The message to process

        Returns:
            Aggregated response from agents
        """
        if self._stop_event.is_set():
            return AgentMessage(
                type=MessageType.ERROR,
                sender=self.name,
                content=f"Supervisor {self.name} is stopped",
            )

        # Add to history
        self.message_history.append(message)

        try:
            # Use LLM to route the message
            target_agent = await self._llm_route_message(message)

            # Route to specific agent or process with all agents
            command_result: Any = (
                await self._process_with_agent(message, target_agent) 
                if target_agent 
                else await self._process_with_all_agents(message)
            )

            # Extract response from command
            if command_result and hasattr(command_result, 'update') and command_result.update and "messages" in command_result.update:
                response = command_result.update["messages"][0] if command_result.update["messages"] else None  # type: ignore
            else:
                response = None

            return response

        except Exception as e:
            error_msg = AgentMessage(
                type=MessageType.ERROR,
                sender=self.name,
                content=f"Error in supervisor {self.name}: {str(e)}",
                metadata={"error_type": type(e).__name__},
            )
            self.message_history.append(error_msg)
            return error_msg

    async def _llm_route_message(self, message: AgentMessage) -> Optional[str]:
        """Use LLM to route message to appropriate agent.

        Args:
            message: The message to route

        Returns:
            Agent name to route to, or None for broadcast
        """
        available_agents = [
            name for name, agent in self.agents.items()
            if agent.is_available()
        ]

        if not available_agents:
            return None

        # Build agent descriptions
        agent_descriptions = []
        for agent_name in available_agents:
            agent = self.agents[agent_name]
            description = getattr(agent, 'description', f"Agent: {agent_name}")
            keywords = getattr(agent, 'keywords', [])
            tools = list(agent.tools.keys()) if hasattr(agent, 'tools') and agent.tools else []
            agent_descriptions.append(f"- {agent_name}: {description} (specializes in: {', '.join(keywords)}, tools: {', '.join(tools)})")

        all_options = ["FINISH"] + available_agents

        system_prompt = f"""You are a team supervisor managing the following agents:

{chr(10).join(agent_descriptions)}

Your job is to route incoming tasks to the most appropriate agent in your team.
If the task is complete or no specific agent is needed, respond with "FINISH".

Choose from: {', '.join(all_options)}

Consider:
1. Which agent has the right expertise and tools for this task?
2. What specific capabilities are needed?
3. Can the task be handled by a specific agent or should all agents work on it?

Team: {self.name}
Team description: {self.description}
Team specialties: {', '.join(self.keywords)}"""

        try:
            # Create messages for LLM
            messages = [
                SystemMessage(content=system_prompt),  # type: ignore
                HumanMessage(content=f"Task: {message.content}")  # type: ignore
            ]

            # Get structured response from LLM
            if self.llm:
                structured_llm = self.llm.with_structured_output(TeamRoutingDecision)  # type: ignore
                response = await structured_llm.ainvoke(messages)
                target = response.next  # type: ignore
            else:
                available_agents = [name for name, agent in self.agents.items() if agent.is_available()]
                target = available_agents[0] if available_agents else "FINISH"

            # Return None for FINISH (broadcast to all)
            if target == "FINISH":
                return None

            # Validate the target exists and is available
            if target in available_agents:
                return target
            else:
                # Fallback to first available agent
                return available_agents[0] if available_agents else None

        except Exception as e:
            # Fallback to first available agent if LLM fails
            return available_agents[0] if available_agents else None

    async def _process_with_agent(self, message: AgentMessage, agent_name: str) -> Any:
        """Process message with a specific agent.

        Args:
            message: The message to process
            agent_name: Name of the agent to use

        Returns:
            Response from the agent
        """
        if agent_name not in self.agents:
            return AgentMessage(
                type=MessageType.ERROR,
                sender=self.name,
                content=f"Agent {agent_name} not found in team {self.name}",
            )

        agent = self.agents[agent_name]

        async with self._semaphore:
            # Create task for agent processing
            task = asyncio.create_task(agent.process_message(message))
            self.agent_tasks[agent_name] = task

            try:
                response = await task
                self.completion_order.append(agent_name)
                return response
            finally:
                if agent_name in self.agent_tasks:
                    del self.agent_tasks[agent_name]

    async def _process_with_all_agents(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process message with all available agents.

        Args:
            message: The message to process

        Returns:
            Aggregated response from all agents
        """
        available_agents = [
            agent for agent in self.agents.values()
            if agent.is_available()
        ]

        if not available_agents:
            return AgentMessage(
                type=MessageType.SYSTEM,
                sender=self.name,
                content=f"No available agents in team {self.name}",
            )

        # Process with all agents concurrently
        async def process_agent(agent: Agent) -> Optional[AgentMessage]:
            """Process message with a single agent."""
            async with self._semaphore:
                task = asyncio.create_task(agent.process_message(message))
                self.agent_tasks[agent.name] = task
                try:
                    response = await task
                    self.completion_order.append(agent.name)
                    return response
                except Exception as e:
                    return AgentMessage(
                        type=MessageType.ERROR,
                        sender=agent.name,
                        content=f"Error in agent {agent.name}: {str(e)}",
                    )
                finally:
                    if agent.name in self.agent_tasks:
                        del self.agent_tasks[agent.name]

        # Execute all agents concurrently
        tasks = [process_agent(agent) for agent in available_agents]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None responses and exceptions
        valid_responses = []
        for response in responses:
            if isinstance(response, AgentMessage):
                valid_responses.append(response)
            elif isinstance(response, Exception):
                error_response = AgentMessage(
                    type=MessageType.ERROR,
                    sender=self.name,
                    content=f"Error processing agent: {str(response)}",
                )
                valid_responses.append(error_response)

        # Aggregate responses
        if valid_responses:
            aggregated_content = "\n".join([
                f"{resp.sender}: {resp.content}" for resp in valid_responses
            ])
            return AgentMessage(
                type=MessageType.AGENT,
                sender=self.name,
                content=f"Team {self.name} responses:\n{aggregated_content}",
                metadata={"individual_responses": [resp.to_dict() for resp in valid_responses]},
            )

        return None

    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the supervisor and its agents.

        Returns:
            Dictionary with supervisor status information
        """
        agent_statuses = {}
        for name, agent in self.agents.items():
            agent_statuses[name] = await agent.get_status()

        return {
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "agents": agent_statuses,
            "active_tasks": len(self.agent_tasks),
            "completion_order": self.completion_order,
            "message_history_count": len(self.message_history),
            "is_stopped": self._stop_event.is_set(),
        }

    async def stop(self) -> None:
        """Stop the supervisor and all its agents."""
        self._stop_event.set()

        # Stop all agents
        stop_tasks = [agent.stop() for agent in self.agents.values()]

        # Cancel all active tasks
        for task in self.agent_tasks.values():
            if not task.done():
                task.cancel()

        # Wait for everything to stop
        all_tasks = stop_tasks + list(self.agent_tasks.values())
        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)

        self.agent_tasks.clear()

    async def reset(self) -> None:
        """Reset the supervisor and all its agents."""
        await self.stop()

        # Reset all agents
        reset_tasks = [agent.reset() for agent in self.agents.values()]
        if reset_tasks:
            await asyncio.gather(*reset_tasks, return_exceptions=True)

        # Reset supervisor state
        self.message_history.clear()
        self.completion_order.clear()
        self._stop_event.clear()

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names.

        Returns:
            List of agent names that are available
        """
        return [
            name for name, agent in self.agents.items()
            if agent.is_available()
        ]

    def get_agent_count(self) -> int:
        """Get the total number of agents in the team.

        Returns:
            Number of agents
        """
        return len(self.agents)

    async def broadcast_message(self, message: AgentMessage) -> List[AgentMessage]:
        """Broadcast a message to all agents and collect responses.

        Args:
            message: The message to broadcast

        Returns:
            List of responses from all agents
        """
        if self._stop_event.is_set():
            return []

        # Send to all agents
        tasks = []
        for agent_name, agent in self.agents.items():
            if agent.is_available():
                task = asyncio.create_task(agent.process_message(message))
                tasks.append((agent_name, task))

        # Collect responses
        responses = []
        for agent_name, task in tasks:
            try:
                response = await task
                if response:
                    responses.append(response)
            except Exception as e:
                error_response = AgentMessage(
                    type=MessageType.ERROR,
                    sender=agent_name,
                    content=f"Error in agent {agent_name}: {str(e)}",
                )
                responses.append(error_response)

        return responses

    def _create_supervisor_node(self):
        """Create LangGraph supervisor node for team-level routing.
        
        Returns:
            Function that can be used as a LangGraph node
        """
        if not HAS_LANGCHAIN:
            raise ImportError("LangChain is required for LangGraph integration")
        
        def team_supervisor_node(state: AgenticFlowState) -> Any:
            """LangGraph node for team-level routing."""
            try:
                available_agents = [
                    name for name, agent in self.agents.items()
                    if agent.is_available()
                ]

                if not available_agents:
                    return Command(goto=END, update={})  # type: ignore

                # If LLM is not initialized, use simple routing
                if not self.llm:
                    return Command(  # type: ignore
                        goto=f"{self.name}_{available_agents[0]}", 
                        update={"current_agent": available_agents[0]}
                    )

                # Build agent descriptions
                agent_descriptions = []
                for agent_name in available_agents:
                    agent = self.agents[agent_name]
                    description = getattr(agent, 'description', f"Agent: {agent_name}")
                    keywords = getattr(agent, 'keywords', [])
                    tools = list(agent.tools.keys()) if hasattr(agent, 'tools') and agent.tools else []
                    agent_descriptions.append(f"- {agent_name}: {description} (specializes in: {', '.join(keywords)}, tools: {', '.join(tools)})")

                all_options = ["FINISH"] + available_agents

                system_prompt = f"""You are a team supervisor managing the following agents:

{chr(10).join(agent_descriptions)}

Your job is to route incoming tasks to the most appropriate agent in your team.
If the task is complete or no specific agent is needed, respond with "FINISH".

Choose from: {', '.join(all_options)}

Consider:
1. Which agent has the right expertise and tools for this task?
2. What specific capabilities are needed?
3. Can the task be handled by a specific agent or should all agents work on it?

Team: {self.name}
Team description: {self.description}
Team specialties: {', '.join(self.keywords)}"""

                # Create messages for LLM
                messages = [
                    SystemMessage(content=system_prompt),  # type: ignore
                ] + state["messages"]

                # Get structured response from LLM
                if self.llm:
                    structured_llm = self.llm.with_structured_output(TeamRoutingDecision)  # type: ignore
                    response = structured_llm.invoke(messages)
                    target = response["next"]
                else:
                    target = available_agents[0] if available_agents else "FINISH"

                # Update execution path
                execution_path = state.get("execution_path", [])
                execution_path.append(f"{self.name}->{target}")

                # Return None for FINISH (broadcast to all)
                if target == "FINISH":
                    return Command(goto=END, update={"execution_path": execution_path})  # type: ignore

                # Validate the target exists and is available
                if target in available_agents:
                    return Command(  # type: ignore
                        goto=f"{self.name}_{target}", 
                        update={
                            "current_agent": target,
                            "execution_path": execution_path
                        }
                    )
                else:
                    # Fallback to first available agent
                    return Command(  # type: ignore
                        goto=f"{self.name}_{available_agents[0]}", 
                        update={
                            "current_agent": available_agents[0],
                            "execution_path": execution_path
                        }
                    )

            except Exception as e:
                # Fallback to first available agent if LLM fails
                available_agents = [
                    name for name, agent in self.agents.items()
                    if agent.is_available()
                ]
                if available_agents:
                    return Command(  # type: ignore
                        goto=f"{self.name}_{available_agents[0]}", 
                        update={"current_agent": available_agents[0]}
                    )
                return Command(goto=END, update={})  # type: ignore

        return team_supervisor_node