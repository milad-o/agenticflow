"""Simplified Agent class following the tutorial pattern."""

import os
from typing import Dict, List, Optional, Any, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langgraph.graph import StateGraph, MessagesState, START, END
from typing_extensions import TypedDict

class State(MessagesState):
    """Simple state following tutorial pattern."""
    next: str

class SimpleAgent:
    """Simplified agent following the tutorial pattern."""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        system_prompt: str = "",
        tools: Optional[List[Any]] = None,
        model: str = "gpt-4o-mini"
    ):
        """Initialize a simple agent.
        
        Args:
            name: Agent name
            description: Agent description
            system_prompt: System prompt for the agent
            tools: List of tools for the agent
            model: OpenAI model to use
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt or f"You are {name}. {description}"
        self.tools = tools or []
        self.model = model
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create ReAct agent
        self._react_agent = None
        if self.tools:
            self._create_react_agent()
    
    def _create_react_agent(self):
        """Create the ReAct agent with tools."""
        if not self.tools:
            return
            
        # Convert our tools to LangChain tools if needed
        langchain_tools = []
        for tool in self.tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                # It's already a LangChain tool
                langchain_tools.append(tool)
            else:
                # Convert our custom tool to LangChain tool
                langchain_tools.append(tool)
        
        self._react_agent = create_react_agent(
            self.llm,
            tools=langchain_tools
        )
    
    def add_tool(self, tool: Any):
        """Add a tool to the agent."""
        self.tools.append(tool)
        self._create_react_agent()
    
    def create_node(self) -> callable:
        """Create a node function for this agent following tutorial pattern."""
        def agent_node(state: State) -> Command[Literal["supervisor"]]:
            """Agent node that always returns to supervisor."""
            if not self._react_agent:
                # Simple agent without tools
                response = self.llm.invoke([
                    SystemMessage(content=self.system_prompt),
                    *state["messages"]
                ])
                content = response.content
            else:
                # ReAct agent with tools
                result = self._react_agent.invoke(state)
                content = result["messages"][-1].content
            
            return Command(
                update={
                    "messages": [
                        HumanMessage(content=content, name=self.name)
                    ]
                },
                # Always return to supervisor
                goto="supervisor",
            )
        
        return agent_node

def make_supervisor_node(llm, members: list[str]):
    """Create supervisor node exactly like tutorial."""
    options = ["FINISH"] + members
    
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )
    
    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""
        next: Literal[*options]

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
        """An LLM-based router."""
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})
    
    return supervisor_node

class SimpleFlow:
    """Simplified flow following tutorial pattern."""
    
    def __init__(self, name: str):
        self.name = name
        self.agents = {}
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self._graph = None
    
    def add_agent(self, agent: SimpleAgent):
        """Add an agent to the flow."""
        self.agents[agent.name] = agent
    
    def build_graph(self):
        """Build the graph following tutorial pattern."""
        if not self.agents:
            raise ValueError("No agents added to flow")
        
        # Create supervisor
        supervisor_node = make_supervisor_node(self.llm, list(self.agents.keys()))
        
        # Create graph
        builder = StateGraph(State)
        builder.add_node("supervisor", supervisor_node)
        
        # Add agent nodes
        for name, agent in self.agents.items():
            builder.add_node(name, agent.create_node())
        
        # Add edges
        builder.add_edge(START, "supervisor")
        
        # Compile graph
        self._graph = builder.compile()
        return self._graph
    
    async def run(self, message: str, recursion_limit: int = 10):
        """Run the flow with a message."""
        if not self._graph:
            self.build_graph()
        
        result = await self._graph.ainvoke({
            "messages": [("user", message)]
        }, {"recursion_limit": recursion_limit})
        
        return result
