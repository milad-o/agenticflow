"""Working framework with simple team support."""

import os
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent

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
    
    def create_node(self):
        """Create agent node."""
        def agent_node(state: State) -> Command:
            if self._react_agent:
                # Use the ReAct agent with state directly
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
        return agent_node

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
            
            if "FINISH" in content.upper():
                return Command(goto=END, update={})
            
            # Route to appropriate agent
            for agent_name in agent_names:
                if agent_name.lower() in content.lower():
                    return Command(goto=agent_name, update={})
            
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
    
    def add_team(self, team: Team):
        """Add a team to the flow."""
        self.teams[team.name] = team
    
    def add_agent(self, agent: Agent):
        """Add an agent directly to the flow (no team)."""
        self.agents[agent.name] = agent
    
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
        
        result = await self._graph.ainvoke({
            "messages": [("user", message)]
        }, {"recursion_limit": recursion_limit})
        
        return result