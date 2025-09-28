#!/usr/bin/env python3
"""Simple LangGraph pattern following the tutorial exactly."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent
from langchain import hub
from langchain_tavily import TavilySearch
from typing import Literal
from typing_extensions import TypedDict

# Define state exactly like the tutorial
class State(MessagesState):
    next: str

# Create tools
tavily_tool = TavilySearch(max_results=5)

# Create LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

# Create agents
prompt = hub.pull("hwchase17/react")
search_agent = create_react_agent(llm, tools=[tavily_tool], prompt=prompt)

async def search_node(state: State) -> Command[Literal["supervisor"]]:
    """Search node that always returns to supervisor."""
    print("🔍 Search node called!")
    
    # Provide intermediate_steps expected by ReAct agent
    last_message = state["messages"][-1]
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message)

    result = search_agent.invoke({
        "input": user_input,
        "intermediate_steps": []
    })

    if hasattr(result, "return_values") and "output" in result.return_values:
        content = result.return_values["output"]
    else:
        content = str(result)

    return Command(
        update={
            "messages": [
                HumanMessage(content=content, name="search")
            ]
        },
        goto="supervisor",
    )

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

    def supervisor_node(state: State) -> Command[str]:
        messages = [
            SystemMessage(content=system_prompt),
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]

        if goto == "FINISH":
            return Command(goto=END, update={"next": goto})

        return Command(goto=goto, update={"next": goto})
    
    return supervisor_node

# Create the graph exactly like the tutorial
research_supervisor_node = make_supervisor_node(llm, ["search"])

research_builder = StateGraph(State)
research_builder.add_node("supervisor", research_supervisor_node)
research_builder.add_node("search", search_node)

research_builder.add_edge(START, "supervisor")
research_graph = research_builder.compile()

async def test_simple_pattern():
    """Test the simple LangGraph pattern."""
    print("🔍 Testing Simple LangGraph Pattern")
    print("=" * 40)
    
    # Test the graph using async API
    result = await research_graph.ainvoke({
        "messages": [HumanMessage(content="What is the latest news about AI?")]
    })
    
    print(f"✅ Graph executed successfully!")
    print(f"📝 Generated {len(result['messages'])} messages:")
    
    for i, msg in enumerate(result["messages"], 1):
        print(f"\n{i}. [{getattr(msg, 'name', 'user')}]:")
        print(f"   Content: {msg.content[:200]}...")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_simple_pattern())
