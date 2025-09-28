#!/usr/bin/env python3
"""Method Chaining example for AgenticFlow.

This example demonstrates the beautiful method chaining API that makes
AgenticFlow easy to use and configure.
"""

import asyncio
from agenticflow import Flow, Orchestrator, Supervisor, ReActAgent
from agenticflow.tools import WriteFileTool, ReadFileTool


async def method_chaining_example():
    """Run a method chaining example."""
    print("🔗 AgenticFlow Method Chaining Example")
    print("=" * 45)
    
    # Create a flow using method chaining
    flow = (Flow("chaining_flow")
            .add_orchestrator(Orchestrator("main_orchestrator", initialize_llm=False)))
    
    # Create teams using method chaining
    research_team = (Supervisor("research_team", description="Research specialists", initialize_llm=False)
                    .add_agent(ReActAgent("researcher", description="Web researcher", initialize_llm=False)
                              .add_tool(WriteFileTool())
                              .add_tool(ReadFileTool())))
    
    writing_team = (Supervisor("writing_team", description="Writing specialists", initialize_llm=False)
                   .add_agent(ReActAgent("writer", description="Content writer", initialize_llm=False)
                             .add_tool(WriteFileTool())))
    
    # Add teams to orchestrator using method chaining
    orchestrator = flow.orchestrator
    (orchestrator
     .add_team(research_team)
     .add_team(writing_team))
    
    print("✅ Flow setup complete using method chaining!")
    print(f"   - Flow: {flow.name}")
    print(f"   - Orchestrator: {orchestrator.name}")
    print(f"   - Teams: {list(orchestrator.teams.keys())}")
    print(f"   - Research team agents: {list(research_team.agents.keys())}")
    print(f"   - Writing team agents: {list(writing_team.agents.keys())}")
    
    # Show the beautiful API structure
    print("\n🎨 Beautiful API Structure:")
    print("   Flow()")
    print("   └── .add_orchestrator(Orchestrator())")
    print("       ├── .add_team(Supervisor()")
    print("       │   └── .add_agent(ReActAgent()")
    print("       │       └── .add_tool(WriteFileTool()))")
    print("       └── .add_team(Supervisor()")
    print("           └── .add_agent(ReActAgent()")
    print("               └── .add_tool(WriteFileTool()))")
    
    # Run the flow
    print("\n🎯 Running the flow...")
    await flow.start("Demonstrate the beautiful method chaining API!")
    
    # Get the results
    messages = await flow.get_messages()
    print(f"\n📝 Generated {len(messages)} messages:")
    for i, msg in enumerate(messages, 1):
        print(f"   {i}. [{msg.sender}]: {msg.content}")
    
    print("\n🎉 Method chaining example completed!")
    print("   - Your beautiful OOP API is preserved!")
    print("   - LangGraph integration works seamlessly!")


if __name__ == "__main__":
    asyncio.run(method_chaining_example())
