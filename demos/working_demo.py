#!/usr/bin/env python3
"""Working demo using the tutorial pattern."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from typing import Annotated

# Define state
class State(MessagesState):
    pass

# Create tools
@tool
def create_file(
    content: Annotated[str, "Content to write to the file"],
    filename: Annotated[str, "Name of the file to create"]
) -> str:
    """Create a file with the given content."""
    try:
        with open(filename, "w") as f:
            f.write(content)
        return f"✅ Created file '{filename}' with content: '{content}'"
    except Exception as e:
        return f"❌ Error creating file: {e}"

@tool
def search_web(
    query: Annotated[str, "Search query for the web"]
) -> str:
    """Search the web for information."""
    try:
        from langchain_tavily import TavilySearch
        search = TavilySearch(max_results=3)
        results = search.invoke(query)
        return f"🔍 Web search results for '{query}':\n{results}"
    except Exception as e:
        return f"❌ Error searching web: {e}"

async def main():
    """Working demo using tutorial pattern."""
    print("🚀 AgenticFlow - Working Demo")
    print("=" * 35)
    
    # Create LLM
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create agents
    researcher_agent = create_react_agent(llm, tools=[search_web])
    writer_agent = create_react_agent(llm, tools=[create_file])
    
    def researcher_node(state: State) -> Command:
        """Researcher node."""
        result = researcher_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="researcher")
                ]
            },
            goto="supervisor"
        )
    
    def writer_node(state: State) -> Command:
        """Writer node."""
        result = writer_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="writer")
                ]
            },
            goto="supervisor"
        )
    
    def supervisor_node(state: State) -> Command:
        """Supervisor node."""
        system_prompt = (
            "You are a supervisor managing these agents: researcher, writer. "
            "Given the user request, respond with the agent to act next. "
            "When finished, respond with FINISH."
        )
        
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = llm.invoke(messages)
        content = response.content
        
        if "FINISH" in content.upper():
            return Command(goto=END, update={})
        elif "researcher" in content.lower():
            return Command(goto="researcher", update={})
        elif "writer" in content.lower():
            return Command(goto="writer", update={})
        else:
            return Command(goto=END, update={})
    
    # Create graph
    builder = StateGraph(State)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    
    builder.add_edge(START, "supervisor")
    graph = builder.compile()
    
    print("✅ Graph created with supervisor and 2 agents")
    
    # Run workflow
    print("\n🎯 Running workflow...")
    result = await graph.ainvoke({
        "messages": [("user", "Research AI trends and create a simple report")]
    }, {"recursion_limit": 10})
    
    print("✅ Workflow completed!")
    print(f"📝 Messages: {len(result['messages'])}")
    
    for i, msg in enumerate(result["messages"], 1):
        sender = getattr(msg, 'name', 'user')
        print(f"   {i}. [{sender}]: {msg.content[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())