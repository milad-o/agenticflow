"""Working framework with simple team support."""

import os
import time
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from ..observability import (
    EventLogger, ConsoleSubscriber, FileSubscriber, MetricsCollector, RichConsoleSubscriber,
    FlowStarted, FlowCompleted, FlowError, AgentStarted, AgentCompleted,
    AgentReasoning, AgentError, ToolExecuted, ToolArgs, ToolResult, ToolError,
    MessageRouted, MessageReceived, TeamSupervisorCalled, TeamAgentCalled,
    CustomEvent
)
from ..observability.observable_agent import ObservableReActAgent

class State(MessagesState):
    """Simple state."""
    pass

class Agent:
    """Agent that performs tool-calling tasks."""
    
    def __init__(self, name: str, tools: List[Any] = None, description: str = ""):
        self.name = name
        self.tools = tools or []
        self.description = description
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self._react_agent = None
        if self.tools:
            self._react_agent = create_react_agent(self.llm, tools=self.tools)
        
        # Observability
        self._flow_id: Optional[str] = None
        self._event_logger: Optional[EventLogger] = None
    
    def create_node(self):
        """Create agent node."""
        def agent_node(state: State) -> Command:
            try:
                if self._react_agent:
                    # Use the ReAct agent with state directly (it handles observability)
                    result = self._react_agent.invoke(state)
                    content = result["messages"][-1].content if "messages" in result and result["messages"] else str(result)
                else:
                    # Fallback to direct LLM call
                    response = self.llm.invoke([
                        SystemMessage(content=f"You are {self.name}. {self.description}"),
                        *state["messages"]
                    ])
                    content = response.content
                
                return Command(
                    update={
                        "messages": [AIMessage(content=content, name=self.name)]
                    },
                    goto=END
                )
            
            except Exception as e:
                # Emit agent error event
                if self._event_logger:
                    agent_error = AgentError(
                        flow_id=self._flow_id,
                        agent_name=self.name,
                        agent_type=self.__class__.__name__,
                        error_message=str(e),
                        error_type=type(e).__name__,
                        stack_trace=str(e.__traceback__) if hasattr(e, '__traceback__') else None
                    )
                    self._event_logger.get_event_bus().emit_event_sync(agent_error)
                
                raise
        
        return agent_node
    
    def set_observability(self, flow_id: str, event_logger: EventLogger) -> None:
        """Set observability context for this agent."""
        self._flow_id = flow_id
        self._event_logger = event_logger
        
        # Create observable ReAct agent if tools are available
        if self.tools and self._event_logger:
            self._react_agent = ObservableReActAgent(
                self.llm, self.tools, flow_id, self.name, event_logger
            )

class Team:
    """Team with supervisor and agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.agents = {}
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def add_agent(self, agent: Agent):
        """Add an agent to this team."""
        self.agents[agent.name] = agent
    
    def create_supervisor_node(self):
        """Create supervisor node for this team."""
        def supervisor_node(state: State) -> Command:
            if not self.agents:
                return Command(goto=END, update={})
            
            agent_names = list(self.agents.keys())
            system_prompt = (
                f"You are supervisor of {self.name} team. "
                f"Manage these agents: {agent_names}. "
                f"Given the user request, respond with the agent to act next. "
                f"When finished, respond with FINISH."
            )
            
            messages = [SystemMessage(content=system_prompt), *state["messages"]]
            response = self.llm.invoke(messages)
            content = response.content
            
            # Emit team supervisor called event
            if hasattr(self, '_flow_id') and hasattr(self, '_event_logger') and self._event_logger:
                team_event = TeamSupervisorCalled(
                    flow_id=self._flow_id,
                    team_name=self.name,
                    team_agents=agent_names
                )
                self._event_logger.get_event_bus().emit_event_sync(team_event)
            
            if "FINISH" in content.upper():
                return Command(goto=END, update={})
            
            # Route to appropriate agent (use full node name with team prefix)
            for agent_name in agent_names:
                if agent_name.lower() in content.lower():
                    # Emit team agent called event
                    if hasattr(self, '_flow_id') and hasattr(self, '_event_logger') and self._event_logger:
                        agent_event = TeamAgentCalled(
                            flow_id=self._flow_id,
                            team_name=self.name,
                            agent_name=agent_name,
                            supervisor_decision=content
                        )
                        self._event_logger.get_event_bus().emit_event_sync(agent_event)
                    
                    # Use the full node name: team_name_agent_name
                    full_node_name = f"{self.name}_{agent_name}"
                    return Command(goto=full_node_name, update={})
            
            return Command(goto=END, update={})
        
        return supervisor_node

class Flow:
    """Flow that manages teams and agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.teams = {}
        self.agents = {}  # Direct agents (no team)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self._graph = None
        
        # Observability
        self._observability_enabled = False
        self._event_logger: Optional[EventLogger] = None
        self._flow_id: Optional[str] = None
    
    def add_team(self, team: Team):
        """Add a team to the flow."""
        self.teams[team.name] = team
        
        # Set observability for team and team agents if enabled
        if self._observability_enabled and self._event_logger:
            flow_id = self._flow_id or "temp-flow-id"
            # Set team observability context
            team._flow_id = flow_id
            team._event_logger = self._event_logger
            # Set observability for team agents
            for agent in team.agents.values():
                if hasattr(agent, 'set_observability'):
                    agent.set_observability(flow_id, self._event_logger)
    
    def add_agent(self, agent: Agent):
        """Add an agent directly to the flow (no team)."""
        self.agents[agent.name] = agent
        
        # Set observability if enabled
        if self._observability_enabled and self._event_logger and hasattr(agent, 'set_observability'):
            # Use a temporary flow_id if not set yet
            flow_id = self._flow_id or "temp-flow-id"
            agent.set_observability(flow_id, self._event_logger)
    
    def enable_observability(self, persistent: bool = False, backend: str = "sqlite3", 
                           console_output: bool = True, file_logging: bool = False,
                           log_file: str = "examples/artifacts/flow_events.log",
                           rich_console: bool = False) -> None:
        """Enable observability for this flow."""
        self._observability_enabled = True
        self._event_logger = EventLogger(persistent=persistent, backend=backend)
        
        # Add subscribers
        if console_output:
            if rich_console:
                console_sub = RichConsoleSubscriber(show_timestamps=True, show_details=True)
            else:
                console_sub = ConsoleSubscriber(show_timestamps=True, show_details=True)
            self._event_logger.get_event_bus().add_subscriber(console_sub)
        
        if file_logging:
            file_sub = FileSubscriber(log_file, format="json")
            self._event_logger.get_event_bus().add_subscriber(file_sub)
        
        # Always add metrics collector
        metrics_sub = MetricsCollector()
        self._event_logger.get_event_bus().add_subscriber(metrics_sub)
        
        # Set observability context for all agents
        self._set_agents_observability()
    
    def disable_observability(self) -> None:
        """Disable observability for this flow."""
        self._observability_enabled = False
        self._event_logger = None
    
    def emit_custom_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit a custom event."""
        if not self._observability_enabled or not self._event_logger:
            return
        
        event = CustomEvent(
            flow_id=self._flow_id,
            custom_type=event_type,
            custom_data=data
        )
        
        # Emit synchronously for immediate processing
        self._event_logger.get_event_bus().emit_event_sync(event)
        
        # Also log the event directly to the logger
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, schedule the coroutine
                asyncio.create_task(self._event_logger.log_event(event))
            else:
                # If we're not in an async context, run it
                loop.run_until_complete(self._event_logger.log_event(event))
        except RuntimeError:
            # No event loop, create a new one
            asyncio.run(self._event_logger.log_event(event))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get flow metrics."""
        if not self._observability_enabled or not self._event_logger:
            return {"error": "Observability not enabled"}
        
        return self._event_logger.get_metrics()
    
    def get_flow_summary(self) -> Dict[str, Any]:
        """Get summary for this flow."""
        if not self._observability_enabled or not self._event_logger or not self._flow_id:
            return {"error": "Observability not enabled or flow not started"}
        
        return self._event_logger.get_flow_summary(self._flow_id)
    
    def _set_agents_observability(self) -> None:
        """Set observability context for all agents."""
        if not self._observability_enabled or not self._event_logger:
            return
        
        # Set for direct agents
        for agent in self.agents.values():
            if hasattr(agent, 'set_observability'):
                agent.set_observability(self._flow_id, self._event_logger)
        
        # Set for team agents
        for team in self.teams.values():
            for agent in team.agents.values():
                if hasattr(agent, 'set_observability'):
                    agent.set_observability(self._flow_id, self._event_logger)
    
    def build_graph(self):
        """Build the LangGraph with simple hierarchy."""
        if not self.teams and not self.agents:
            raise ValueError("No teams or agents added to flow")
        
        # Create supervisor
        def supervisor_node(state: State) -> Command:
            all_entities = []
            for team_name in self.teams.keys():
                all_entities.append(f"{team_name}_supervisor")
            all_entities.extend(self.agents.keys())
            
            system_prompt = (
                f"You are a supervisor managing these entities: {all_entities}. "
                f"Given the user request, respond with the entity to act next. "
                f"When finished, respond with FINISH."
            )
            
            messages = [SystemMessage(content=system_prompt), *state["messages"]]
            response = self.llm.invoke(messages)
            content = response.content
            
            if "FINISH" in content.upper():
                return Command(goto=END, update={})
            
            # Route to appropriate entity
            for entity in all_entities:
                if entity.lower() in content.lower():
                    return Command(goto=entity, update={})
            
            return Command(goto=END, update={})
        
        # Build graph
        builder = StateGraph(State)
        builder.add_node("supervisor", supervisor_node)
        
        # Add team nodes (supervisor + agents)
        for team_name, team in self.teams.items():
            # Add team supervisor
            builder.add_node(f"{team_name}_supervisor", team.create_supervisor_node())
            
            # Add team agents
            for agent_name, agent in team.agents.items():
                builder.add_node(f"{team_name}_{agent_name}", agent.create_node())
        
        # Add direct agent nodes
        for agent_name, agent in self.agents.items():
            builder.add_node(agent_name, agent.create_node())
        
        # Add edges
        builder.add_edge(START, "supervisor")
        
        # Add team edges (supervisor -> team_supervisor -> team_agents)
        for team_name, team in self.teams.items():
            builder.add_edge("supervisor", f"{team_name}_supervisor")
            for agent_name in team.agents.keys():
                builder.add_edge(f"{team_name}_supervisor", f"{team_name}_{agent_name}")
        
        # Add direct agent edges
        for agent_name in self.agents.keys():
            builder.add_edge("supervisor", agent_name)
        
        self._graph = builder.compile()
        return self._graph
    
    async def run(self, message: str, recursion_limit: int = 10):
        """Run the flow."""
        if not self._graph:
            self.build_graph()
        
        # Generate flow ID for this execution
        import uuid
        self._flow_id = str(uuid.uuid4())
        
        # Set observability context for all agents
        if self._observability_enabled and self._event_logger:
            self._set_agents_observability()
        
        # Emit flow started event
        if self._observability_enabled and self._event_logger:
            start_time = time.time()
            flow_started = FlowStarted(
                flow_id=self._flow_id,
                flow_name=self.name,
                message=message
            )
            await self._event_logger.log_event(flow_started)
        
        try:
            result = await self._graph.ainvoke({
                "messages": [("user", message)]
            }, {"recursion_limit": recursion_limit})
            
            # Emit flow completed event
            if self._observability_enabled and self._event_logger:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                total_messages = len(result.get("messages", []))
                
                flow_completed = FlowCompleted(
                    flow_id=self._flow_id,
                    flow_name=self.name,
                    duration_ms=duration_ms,
                    total_messages=total_messages
                )
                await self._event_logger.log_event(flow_completed)
            
            return result
            
        except Exception as e:
            # Emit flow error event
            if self._observability_enabled and self._event_logger:
                flow_error = FlowError(
                    flow_id=self._flow_id,
                    flow_name=self.name,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    stack_trace=str(e.__traceback__) if hasattr(e, '__traceback__') else None
                )
                await self._event_logger.log_event(flow_error)
            
            raise