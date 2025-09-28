#!/usr/bin/env python3
"""Hello World example for AgenticFlow.

This is the simplest possible example showing how to create and run a basic flow.
"""

import asyncio
from agenticflow import Flow, Orchestrator, Supervisor, SimpleAgent


async def hello_world_example():
    """Run a simple hello world example."""
    print("🚀 AgenticFlow Hello World Example")
    print("=" * 40)
    
    # Create a flow
    flow = Flow("hello_world_flow")
    
    # Add an orchestrator
    orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
    flow.add_orchestrator(orchestrator)
    
    # Create a simple team
    team = Supervisor("greeting_team", description="Handles greetings", initialize_llm=False)
    
    # Add a simple agent
    agent = SimpleAgent("greeter", description="A friendly greeting agent")
    team.add_agent(agent)
    
    # Add team to orchestrator
    orchestrator.add_team(team)
    
    print("✅ Flow setup complete!")
    print(f"   - Flow: {flow.name}")
    print(f"   - Orchestrator: {orchestrator.name}")
    print(f"   - Team: {team.name}")
    print(f"   - Agent: {agent.name}")
    
    # Run the flow
    print("\n🎯 Running the flow...")
    await flow.start("Hello, AgenticFlow!")
    
    # Get the results
    messages = await flow.get_messages()
    print(f"\n📝 Generated {len(messages)} messages:")
    for i, msg in enumerate(messages, 1):
        print(f"   {i}. [{msg.sender}]: {msg.content}")
    
    print("\n🎉 Hello World example completed!")


if __name__ == "__main__":
    asyncio.run(hello_world_example())
