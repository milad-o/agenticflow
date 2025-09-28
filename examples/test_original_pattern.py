#!/usr/bin/env python3
"""Filesystem agent using the original tutorial pattern exactly."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import Annotated, List, Literal
from typing_extensions import TypedDict

# Define state exactly like the tutorial
class State(MessagesState):
    next: str

# Create LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

# Create filesystem tools exactly like the tutorial
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
def list_directory(
    path: Annotated[str, "Directory path to list (use '.' for current directory)"]
) -> str:
    """List the contents of a directory."""
    try:
        if path == ".":
            path = os.getcwd()
        files = os.listdir(path)
        files_str = "\n".join(f"  - {f}" for f in files[:10])  # Limit to 10 files
        return f"📁 Directory contents of '{path}':\n{files_str}"
    except Exception as e:
        return f"❌ Error listing directory: {e}"

@tool
def create_folder(
    folder_name: Annotated[str, "Name of the folder to create"]
) -> str:
    """Create a folder."""
    try:
        os.makedirs(folder_name, exist_ok=True)
        return f"✅ Created folder '{folder_name}'"
    except Exception as e:
        return f"❌ Error creating folder: {e}"

# Create filesystem agent exactly like the tutorial
from langgraph.prebuilt import create_react_agent

filesystem_agent = create_react_agent(llm, tools=[create_file, list_directory, create_folder])

def filesystem_node(state: State) -> Command[Literal["supervisor"]]:
    """Filesystem node exactly like tutorial pattern."""
    result = filesystem_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="filesystem")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
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

# Create the graph exactly like the tutorial
filesystem_supervisor_node = make_supervisor_node(llm, ["filesystem"])

filesystem_builder = StateGraph(State)
filesystem_builder.add_node("supervisor", filesystem_supervisor_node)
filesystem_builder.add_node("filesystem", filesystem_node)

filesystem_builder.add_edge(START, "supervisor")
filesystem_graph = filesystem_builder.compile()

async def test_filesystem_agent():
    """Test the filesystem agent using the original tutorial pattern."""
    print("🗂️  Testing Filesystem Agent (Original Tutorial Pattern)")
    print("=" * 60)
    
    # Test 1: Create a file
    print("\n🎯 Test 1: Create a file")
    print("-" * 40)
    result1 = await filesystem_graph.ainvoke({
        "messages": [("user", "Create a file called 'hello.txt' with the content 'Hello from AgenticFlow!'")]
    })
    
    print(f"✅ Test 1 completed!")
    print(f"📝 Generated {len(result1['messages'])} messages:")
    for i, msg in enumerate(result1["messages"], 1):
        print(f"   {i}. [{getattr(msg, 'name', 'user')}]: {msg.content}")
    
    # Test 2: List directory
    print("\n🎯 Test 2: List directory")
    print("-" * 40)
    result2 = await filesystem_graph.ainvoke({
        "messages": [("user", "List the contents of the current directory")]
    })
    
    print(f"✅ Test 2 completed!")
    print(f"📝 Generated {len(result2['messages'])} messages:")
    for i, msg in enumerate(result2["messages"], 1):
        print(f"   {i}. [{getattr(msg, 'name', 'user')}]: {msg.content}")
    
    # Test 3: Create a folder
    print("\n🎯 Test 3: Create a folder")
    print("-" * 40)
    result3 = await filesystem_graph.ainvoke({
        "messages": [("user", "Create a folder called 'test_project' and then create a file called 'README.md' inside it with project information")]
    })
    
    print(f"✅ Test 3 completed!")
    print(f"📝 Generated {len(result3['messages'])} messages:")
    for i, msg in enumerate(result3["messages"], 1):
        print(f"   {i}. [{getattr(msg, 'name', 'user')}]: {msg.content}")
    
    print("\n🎉 Filesystem agent testing completed successfully!")
    print("=" * 60)
    
    # Show what files were actually created
    print("\n📁 Files created during testing:")
    test_files = ["hello.txt", "test_project"]
    for item in test_files:
        if os.path.exists(item):
            if os.path.isfile(item):
                print(f"   ✅ File: {item}")
                with open(item, "r") as f:
                    print(f"      Content: {f.read()}")
            else:
                print(f"   ✅ Folder: {item}/")
                # Check for README.md inside
                readme_path = os.path.join(item, "README.md")
                if os.path.exists(readme_path):
                    print(f"      📄 Contains README.md")
                    with open(readme_path, "r") as f:
                        print(f"         Content: {f.read()[:100]}...")
        else:
            print(f"   ❌ {item}")

if __name__ == "__main__":
    asyncio.run(test_filesystem_agent())

