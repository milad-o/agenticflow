"""Observability example demonstrating real-time flow monitoring."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agenticflow import (
    Flow, Agent, Team, 
    FilesystemAgent, PythonAgent,
    create_file, search_web
)


async def basic_observability_example():
    """Basic observability example with console output."""
    print("🔍 Basic Observability Example")
    print("=" * 40)
    
    # Create flow with observability enabled
    flow = Flow("observability_demo")
    flow.enable_observability(
        console_output=True,  # Real-time console output
        file_logging=False,   # No file logging for this example
        persistent=False      # In-memory only
    )
    
    # Create agents
    researcher = Agent(
        name="researcher",
        tools=[search_web],
        description="Researches topics using web search"
    )
    
    writer = Agent(
        name="writer", 
        tools=[create_file],
        description="Writes reports and documents"
    )
    
    # Add agents to flow
    flow.add_agent(researcher)
    flow.add_agent(writer)
    
    print(f"✅ Created flow with {len(flow.agents)} agents")
    print("🎯 Running workflow with real-time observability...")
    print()
    
    # Run workflow - you'll see real-time events in console
    result = await flow.run("Research the latest trends in AI and create a brief report")
    
    print()
    print("✅ Workflow completed!")
    print(f"📝 Total messages: {len(result['messages'])}")
    
    # Get metrics
    metrics = flow.get_metrics()
    print(f"📊 Total events logged: {metrics['total_events']}")
    print(f"🤖 Agents involved: {metrics['unique_agents']}")
    print(f"🔧 Tools used: {metrics['unique_tools']}")


async def team_observability_example():
    """Team-based observability example."""
    print("\n🏢 Team Observability Example")
    print("=" * 40)
    
    # Create flow with observability
    flow = Flow("team_observability_demo")
    flow.enable_observability(
        console_output=True,
        file_logging=True,  # Enable file logging
        log_file="examples/artifacts/team_events.log"
    )
    
    # Create research team
    research_team = Team("research_team")
    research_team.add_agent(Agent(
        name="web_researcher",
        tools=[search_web],
        description="Web research specialist"
    ))
    
    # Create writing team  
    writing_team = Team("writing_team")
    writing_team.add_agent(Agent(
        name="technical_writer",
        tools=[create_file],
        description="Technical writing specialist"
    ))
    
    # Add teams to flow
    flow.add_team(research_team)
    flow.add_team(writing_team)
    
    print(f"✅ Created flow with {len(flow.teams)} teams")
    print("🎯 Running team workflow with observability...")
    print()
    
    # Run workflow
    result = await flow.run("Research machine learning frameworks and write a technical comparison")
    
    print()
    print("✅ Team workflow completed!")
    
    # Get flow summary
    summary = flow.get_flow_summary()
    if "error" not in summary:
        print(f"⏱️ Total duration: {summary['duration_ms']:.1f}ms")
        print(f"🤖 Agents used: {list(summary['agents'].keys())}")
        print(f"🔧 Tools used: {list(summary['tools'].keys())}")


async def specialized_agent_observability_example():
    """Specialized agent observability example."""
    print("\n🛠️ Specialized Agent Observability Example")
    print("=" * 50)
    
    # Create flow with observability
    flow = Flow("specialized_agent_demo")
    flow.enable_observability(
        console_output=True,
        file_logging=True,
        log_file="examples/artifacts/specialized_events.log"
    )
    
    # Create specialized agents
    fs_agent = FilesystemAgent("file_manager")
    py_agent = PythonAgent("code_analyst")
    
    # Add agents to flow
    flow.add_agent(fs_agent)
    flow.add_agent(py_agent)
    
    print(f"✅ Created flow with {len(flow.agents)} specialized agents")
    print("🎯 Running specialized agent workflow...")
    print()
    
    # Run workflow
    result = await flow.run("Create a Python script that calculates prime numbers and save it to a file")
    
    print()
    print("✅ Specialized agent workflow completed!")
    
    # Show detailed metrics
    metrics = flow.get_metrics()
    print(f"📊 Detailed metrics:")
    print(f"   Total events: {metrics['total_events']}")
    print(f"   Event types: {list(metrics['event_counts'].keys())}")
    print(f"   Agents: {metrics['agents']}")
    print(f"   Tools: {metrics['tools']}")


async def custom_events_example():
    """Custom events example."""
    print("\n⭐ Custom Events Example")
    print("=" * 30)
    
    # Create flow with observability
    flow = Flow("custom_events_demo")
    flow.enable_observability(console_output=True)
    
    # Create agent
    agent = Agent("custom_agent", tools=[create_file])
    flow.add_agent(agent)
    
    print("🎯 Running workflow with custom events...")
    print()
    
    # Emit custom events during workflow
    flow.emit_custom_event("workflow_started", {"phase": "initialization"})
    
    result = await flow.run("Create a simple text file")
    
    flow.emit_custom_event("workflow_completed", {"phase": "completion", "files_created": 1})
    
    print()
    print("✅ Custom events workflow completed!")
    
    # Show custom events
    events = flow._event_logger.get_events(event_type="custom_event")
    print(f"📊 Custom events emitted: {len(events)}")
    for event in events:
        print(f"   - {event.data['custom_type']}: {event.data['custom_data']}")


async def persistent_logging_example():
    """Persistent logging example."""
    print("\n💾 Persistent Logging Example")
    print("=" * 35)
    
    # Create flow with persistent logging
    flow = Flow("persistent_demo")
    flow.enable_observability(
        console_output=False,  # No console output for this example
        file_logging=True,
        log_file="examples/artifacts/persistent_events.log",
        persistent=True,  # Enable persistent storage
        backend="sqlite3"
    )
    
    # Create agent
    agent = Agent("persistent_agent", tools=[create_file])
    flow.add_agent(agent)
    
    print("🎯 Running workflow with persistent logging...")
    
    # Run workflow
    result = await flow.run("Create a data file with sample content")
    
    print("✅ Persistent logging workflow completed!")
    
    # Query persistent events
    persistent_events = flow._event_logger.get_events_persistent(limit=10)
    print(f"📊 Events stored persistently: {len(persistent_events)}")
    
    # Export events
    flow._event_logger.export_events("examples/artifacts/exported_events.json", format="json")
    print("📁 Events exported to examples/artifacts/exported_events.json")


async def main():
    """Run all observability examples."""
    print("🚀 AgenticFlow Observability Examples")
    print("=" * 50)
    
    # Ensure artifacts directory exists
    os.makedirs("examples/artifacts", exist_ok=True)
    
    try:
        # Run examples
        await basic_observability_example()
        await team_observability_example()
        await specialized_agent_observability_example()
        await custom_events_example()
        await persistent_logging_example()
        
        print("\n🎉 All observability examples completed!")
        print("\n📁 Check the following files for detailed logs:")
        print("   - examples/artifacts/team_events.log")
        print("   - examples/artifacts/specialized_events.log")
        print("   - examples/artifacts/persistent_events.log")
        print("   - examples/artifacts/exported_events.json")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
