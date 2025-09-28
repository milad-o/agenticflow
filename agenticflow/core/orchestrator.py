"""Orchestrator for top-level coordination of teams and agents."""

import asyncio
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union, Literal
from abc import ABC, abstractmethod
from pydantic import BaseModel

from .state import AgentMessage, AgentStatus, MessageType
from .langgraph_state import AgenticFlowState, RoutingDecision

if TYPE_CHECKING:
    from .flow import Flow
    from .agent import Agent
    from .supervisor import Supervisor

# LangGraph is required for the framework
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command
from langgraph.graph import START, END


class BaseOrchestrator(ABC):
    """Abstract base class for orchestrators."""

    def __init__(self, name: str):
        """Initialize the orchestrator.

        Args:
            name: Name of the orchestrator
        """
        self.name = name
        self.flow: Optional["Flow"] = None
        self.agents: Dict[str, "Agent"] = {}
        self.teams: Dict[str, "Supervisor"] = {}

    def set_flow(self, flow: "Flow") -> None:
        """Set the flow instance.

        Args:
            flow: The flow instance this orchestrator belongs to
        """
        self.flow = flow

        # Set workspace for all existing agents
        if flow.workspace:
            for agent in self.agents.values():
                agent.set_workspace(flow.workspace)

            # Set workspace for agents in teams
            for supervisor in self.teams.values():
                for agent in supervisor.agents.values():
                    agent.set_workspace(flow.workspace)

    @abstractmethod
    async def process(self, message: AgentMessage) -> None:
        """Process an incoming message.

        Args:
            message: The message to process
        """
        target = await self.route_message(message)

        if target:
            await self._route_to_target(message, target)
        else:
            await self._broadcast_message(message)

    @abstractmethod
    async def route_message(self, message: AgentMessage) -> Optional[str]:
        """Determine which agent or team should handle the message.

        Args:
            message: The message to route

        Returns:
            The name of the agent/team to route to, or None if no routing needed
        """
        pass


class Orchestrator(BaseOrchestrator):
    """LLM-powered top-level orchestrator for coordinating teams and individual agents.

    The orchestrator uses an LLM to intelligently decide which teams or agents
    should handle incoming messages based on their capabilities and the task requirements.
    """

    def __init__(
        self,
        name: str = "main_orchestrator",
        llm_model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        initialize_llm: bool = True,
    ):
        """Initialize the LLM-powered orchestrator.

        Args:
            name: Name of the orchestrator
            llm_model: LLM model to use for routing decisions
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if None)
            initialize_llm: Whether to initialize the LLM immediately (set to False for testing)
        """
        super().__init__(name)

        # LangGraph is required for the framework

        self.llm = None
        if initialize_llm:
            self.llm = ChatOpenAI(  # type: ignore
                model=llm_model,
                api_key=api_key or os.getenv("OPENAI_API_KEY"),  # type: ignore
                temperature=0.1
            )

        # Registry of teams and agents
        self.teams: Dict[str, "Supervisor"] = {}
        self.agents: Dict[str, "Agent"] = {}

        # Execution tracking
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completion_order: List[str] = []
        self.routing_strategy: str = "llm_based"

    def __repr__(self) -> str:
        return f"Orchestrator(name='{self.name}')"

    def add_team(self, supervisor: "Supervisor") -> "Orchestrator":
        """Add a team (supervisor) to the orchestrator.

        Args:
            supervisor: The supervisor managing the team

        Returns:
            Self for method chaining
        """
        self.teams[supervisor.name] = supervisor
        supervisor.set_orchestrator(self)

        # Set workspace for all agents in the team if available
        if self.flow and self.flow.workspace:
            for agent in supervisor.agents.values():
                agent.set_workspace(self.flow.workspace)
        
        # Rebuild graph if flow is set
        if hasattr(self, 'flow') and self.flow:
            self.flow._build_langgraph()

        return self

    def add_agent(self, agent: "Agent") -> "Orchestrator":
        """Add an individual agent to the orchestrator.

        Args:
            agent: The agent to add

        Returns:
            Self for method chaining
        """
        self.agents[agent.name] = agent
        agent.set_orchestrator(self)

        # Set workspace if available
        if self.flow and self.flow.workspace:
            agent.set_workspace(self.flow.workspace)
        
        # Rebuild graph if flow is set
        if hasattr(self, 'flow') and self.flow:
            self.flow._build_langgraph()

        return self

    async def process(self, message: AgentMessage) -> None:
        """Process an incoming message and route it appropriately.

        Args:
            message: The message to process
        """
        if not self.flow:
            raise RuntimeError("Orchestrator not attached to a flow")

        # Route the message
        target = await self.route_message(message)

        if target is None:
            # No specific target, broadcast to all available agents/teams
            await self._broadcast_message(message)
        else:
            # Route to specific target
            await self._route_to_target(message, target)

        # Note: Original message is already added by flow.start() or flow.send_message()

        if self.flow.observer:
            await self.flow.observer.message_processed(
                message.id, self.name, target or "broadcast"
            )

    async def route_message(self, message: AgentMessage) -> Optional[str]:
        """Use LLM to intelligently determine which agent or team should handle the message.

        Args:
            message: The message to route

        Returns:
            The name of the agent/team to route to, or None for broadcast
        """
        # Get available options
        available_teams = list(self.teams.keys())
        available_agents = list(self.agents.keys())
        all_options = ["FINISH"] + available_teams + available_agents

        if not available_teams and not available_agents:
            return None

        # Build system prompt with team/agent descriptions
        team_descriptions = []
        for team_name, supervisor in self.teams.items():
            description = getattr(supervisor, 'description', f"Team: {team_name}")
            keywords = getattr(supervisor, 'keywords', [])
            team_descriptions.append(f"- {team_name}: {description} (specializes in: {', '.join(keywords)})")

        agent_descriptions = []
        for agent_name, agent in self.agents.items():
            description = getattr(agent, 'description', f"Agent: {agent_name}")
            keywords = getattr(agent, 'keywords', [])
            agent_descriptions.append(f"- {agent_name}: {description} (specializes in: {', '.join(keywords)})")

        system_prompt = f"""You are a master supervisor coordinating a multi-agent system.
Your job is to route incoming tasks to the most appropriate team or agent.

Available teams:
{chr(10).join(team_descriptions) if team_descriptions else "No teams available"}

Available individual agents:
{chr(10).join(agent_descriptions) if agent_descriptions else "No individual agents available"}

Given the user's request, decide which team or agent should handle it next.
IMPORTANT: You should ALWAYS route to a team or agent unless the task is completely unrelated to any available capabilities.
Only return "FINISH" if the task is impossible to handle with the available teams/agents.

Choose from: {', '.join(all_options)}

Consider:
1. Which team/agent has the right expertise for this task?
2. What tools and capabilities are needed?
3. Is this a research task, writing task, analysis task, etc.?

Respond with just the team/agent name and your reasoning."""

        try:
            # Create messages for LLM
            messages = [
                SystemMessage(content=system_prompt),  # type: ignore
                HumanMessage(content=f"Task: {message.content}")  # type: ignore
            ]

            # Get structured response from LLM
            if self.llm:
                structured_llm = self.llm.with_structured_output(RoutingDecision)  # type: ignore
                response = await structured_llm.ainvoke(messages)
                target = response.next  # type: ignore
                reasoning = response.reasoning  # type: ignore
            else:
                available_teams = list(self.teams.keys())
                available_agents = list(self.agents.keys())
                target = available_teams[0] if available_teams else (available_agents[0] if available_agents else "FINISH")
                reasoning = "Fallback routing"

            # Log the reasoning if we have an observer
            if self.flow and self.flow.observer:
                await self.flow.observer.message_processed(
                    message.id, self.name, f"{target} (reasoning: {reasoning})"
                )

            # Return None for FINISH or broadcast
            if target == "FINISH":
                return None

            # Validate the target exists
            if target in self.teams or target in self.agents:
                return target
            else:
                # Fallback to first available option
                if available_teams:
                    return available_teams[0]
                elif available_agents:
                    return available_agents[0]
                return None

        except Exception as e:
            # Fallback to simple routing if LLM fails
            if self.flow and self.flow.observer:
                await self.flow.observer.routing_error(message.id, f"LLM routing failed: {str(e)}")

            # Simple fallback
            if available_teams:
                return available_teams[0]
            elif available_agents:
                return available_agents[0]
            return None

    def _get_next_sequential_target(self) -> Optional[str]:
        """Get the next target in sequential routing."""
        all_targets = list(self.teams.keys()) + list(self.agents.keys())

        if not all_targets:
            return None

        # Simple round-robin
        if not self.completion_order:
            return all_targets[0]

        last_used = self.completion_order[-1]
        try:
            current_index = all_targets.index(last_used)
            next_index = (current_index + 1) % len(all_targets)
            return all_targets[next_index]
        except ValueError:
            return all_targets[0]

    async def _broadcast_message(self, message: AgentMessage) -> None:
        """Broadcast message to all teams and agents.

        Args:
            message: The message to broadcast
        """
        tasks = []

        # Send to all teams
        for supervisor in self.teams.values():
            task = asyncio.create_task(supervisor.process_message(message))
            tasks.append(task)

        # Send to all individual agents
        for agent in self.agents.values():
            task = asyncio.create_task(agent.process_message(message))
            tasks.append(task)

        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Add valid responses to flow state
            if self.flow:
                for response in responses:
                    if response and not isinstance(response, Exception) and isinstance(response, AgentMessage):
                        await self.flow.state.add_message(response)

    async def _route_to_target(self, message: AgentMessage, target: str) -> None:
        """Route message to a specific target.

        Args:
            message: The message to route
            target: The target name (team or agent)
        """
        response = None

        # Check if target is a team
        if target in self.teams:
            response = await self.teams[target].process_message(message)
        # Check if target is an individual agent
        elif target in self.agents:
            response = await self.agents[target].process_message(message)
        else:
            # Target not found
            if self.flow and self.flow.observer:
                await self.flow.observer.routing_error(
                    message.id, f"Target not found: {target}"
                )
            return

        # Add response to flow state if available
        if response and self.flow:
            await self.flow.state.add_message(response)

    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the orchestrator.

        Returns:
            Dictionary with orchestrator status information
        """
        team_statuses = {}
        for name, supervisor in self.teams.items():
            team_statuses[name] = await supervisor.get_status()

        agent_statuses = {}
        for name, agent in self.agents.items():
            agent_statuses[name] = await agent.get_status()

        return {
            "name": self.name,
            "routing_strategy": self.routing_strategy,
            "teams": team_statuses,
            "agents": agent_statuses,
            "active_tasks": len(self.active_tasks),
            "completion_order": self.completion_order,
        }

    async def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all active tasks to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if all tasks completed, False if timeout
        """
        if not self.active_tasks:
            return True

        try:
            await asyncio.wait_for(
                asyncio.gather(*self.active_tasks.values(), return_exceptions=True),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            return False

    async def stop_all(self) -> None:
        """Stop all teams and agents."""
        # Stop all teams
        team_tasks = [supervisor.stop() for supervisor in self.teams.values()]

        # Stop all agents
        agent_tasks = [agent.stop() for agent in self.agents.values()]

        # Wait for all to stop
        all_tasks = team_tasks + agent_tasks
        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)

        # Clear active tasks
        for task in self.active_tasks.values():
            if not task.done():
                task.cancel()

        self.active_tasks.clear()

    def get_available_targets(self) -> List[str]:
        """Get list of all available routing targets.

        Returns:
            List of team and agent names
        """
        return list(self.teams.keys()) + list(self.agents.keys())

    def _create_supervisor_node(self):
        """Create LangGraph supervisor node for orchestrator-level routing.
        
        Returns:
            Function that can be used as a LangGraph node
        """
        # LangGraph is required for the framework
        
        def orchestrator_node(state: AgenticFlowState) -> Any:
            """LangGraph node for orchestrator-level routing."""
            try:
                # Get available options
                available_teams = list(self.teams.keys())
                available_agents = list(self.agents.keys())
                all_options = ["FINISH"] + available_teams + available_agents

                if not available_teams and not available_agents:
                    return Command(goto=END, update={})  # type: ignore

                # If LLM is not initialized, use simple routing
                if not self.llm:
                    # Check if we've already processed this message (avoid infinite loop)
                    execution_path = state.get("execution_path", [])
                    if f"orchestrator_{self.name}_processed" in execution_path:
                        return Command(goto=END, update={})  # type: ignore
                    
                    if available_teams:
                        return Command(
                            goto=available_teams[0], 
                            update={
                                "current_team": available_teams[0],
                                "execution_path": [f"orchestrator_{self.name}_processed"]
                            }
                        )  # type: ignore
                    elif available_agents:
                        return Command(
                            goto=available_agents[0], 
                            update={
                                "current_agent": available_agents[0],
                                "execution_path": [f"orchestrator_{self.name}_processed"]
                            }
                        )  # type: ignore
                    return Command(goto=END, update={})  # type: ignore

                # Build system prompt with team/agent descriptions
                team_descriptions = []
                for team_name, supervisor in self.teams.items():
                    description = getattr(supervisor, 'description', f"Team: {team_name}")
                    keywords = getattr(supervisor, 'keywords', [])
                    team_descriptions.append(f"- {team_name}: {description} (specializes in: {', '.join(keywords)})")

                agent_descriptions = []
                for agent_name, agent in self.agents.items():
                    description = getattr(agent, 'description', f"Agent: {agent_name}")
                    keywords = getattr(agent, 'keywords', [])
                    agent_descriptions.append(f"- {agent_name}: {description} (specializes in: {', '.join(keywords)})")

                system_prompt = f"""You are a master supervisor coordinating a multi-agent system.
Your job is to route incoming tasks to the most appropriate team or agent.

Available teams:
{chr(10).join(team_descriptions) if team_descriptions else "No teams available"}

Available individual agents:
{chr(10).join(agent_descriptions) if agent_descriptions else "No individual agents available"}

Given the user's request, decide which team or agent should handle it next.
IMPORTANT: You should ALWAYS route to a team or agent unless the task is completely unrelated to any available capabilities.
Only return "FINISH" if the task is impossible to handle with the available teams/agents.

Choose from: {', '.join(all_options)}

Consider:
1. Which team/agent has the right expertise for this task?
2. What tools and capabilities are needed?
3. Is this a research task, writing task, analysis task, etc.?

Respond with just the team/agent name and your reasoning."""

                # Create messages for LLM
                messages = [
                    SystemMessage(content=system_prompt),  # type: ignore
                ] + state["messages"]

                # Get structured response from LLM
                if self.llm:
                    structured_llm = self.llm.with_structured_output(RoutingDecision)  # type: ignore
                    response = structured_llm.invoke(messages)
                    target = response["next"]
                else:
                    target = available_teams[0] if available_teams else (available_agents[0] if available_agents else "FINISH")

                # Update execution path
                execution_path = state.get("execution_path", [])
                execution_path.append(f"orchestrator->{target}")

                # Return None for FINISH or broadcast
                if target == "FINISH":
                    return Command(goto=END, update={"execution_path": execution_path})  # type: ignore

                # Validate the target exists
                if target in self.teams or target in self.agents:
                    return Command(  # type: ignore
                        goto=target, 
                        update={
                            "current_team": target if target in self.teams else None,
                            "current_agent": target if target in self.agents else None,
                            "execution_path": execution_path
                        }
                    )
                else:
                    # Fallback to first available option
                    if available_teams:
                        return Command(  # type: ignore
                            goto=available_teams[0], 
                            update={
                                "current_team": available_teams[0],
                                "execution_path": execution_path
                            }
                        )
                    elif available_agents:
                        return Command(  # type: ignore
                            goto=available_agents[0], 
                            update={
                                "current_agent": available_agents[0],
                                "execution_path": execution_path
                            }
                        )
                    return Command(goto=END, update={"execution_path": execution_path})  # type: ignore

            except Exception as e:
                # Fallback to simple routing if LLM fails
                available_teams = list(self.teams.keys())
                available_agents = list(self.agents.keys())
                
                if available_teams:
                    return Command(goto=available_teams[0], update={"current_team": available_teams[0]})  # type: ignore
                elif available_agents:
                    return Command(goto=available_agents[0], update={"current_agent": available_agents[0]})  # type: ignore
                return Command(goto=END, update={})  # type: ignore

        return orchestrator_node