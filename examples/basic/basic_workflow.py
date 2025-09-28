"""Basic workflow example for AgenticFlow framework.

This example demonstrates how to create a simple hierarchical agent workflow
inspired by the LangGraph hierarchical agent teams pattern.
"""

import asyncio
import os
from agenticflow import Flow, Orchestrator, Supervisor
from agenticflow.core.agent import SimpleAgent, Tool
from agenticflow.agents.research_agents import SearchAgent, WebScraperAgent
from agenticflow.agents.document_agents import DocumentWriterAgent, NoteWriterAgent


def create_echo_tool():
    """Create a simple echo tool for demonstration."""
    def echo_func(message: str) -> str:
        return f"Echo: {message}"

    return Tool(
        name="echo",
        description="Echo the input message",
        func=echo_func,
        parameters={"message": {"type": "string", "description": "Message to echo"}},
    )


async def basic_agent_example():
    """Demonstrate basic agent functionality."""
    print("=== Basic Agent Example ===")

    # Create a simple agent with a tool
    agent = SimpleAgent("demo_agent", description="A demonstration agent")
    agent.add_tool(create_echo_tool())

    # Process a message
    from agenticflow.core.state import AgentMessage
    message = AgentMessage(sender="user", content="Hello, agent!")

    response = await agent.process_message(message)
    print(f"Agent response: {response.content}")

    # Use a tool
    echo_result = await agent.use_tool("echo", message="Testing tool usage")
    print(f"Tool result: {echo_result}")


async def team_workflow_example():
    """Demonstrate team-based workflow with supervisor."""
    print("\n=== Team Workflow Example ===")

    # Create specialized agents
    researcher = SimpleAgent("researcher", keywords=["research", "search"])
    writer = SimpleAgent("writer", keywords=["write", "document"])
    analyst = SimpleAgent("analyst", keywords=["analyze", "data"])

    # Create a team supervisor
    team = Supervisor("analysis_team", keywords=["team", "analyze"])
    team.add_agent(researcher).add_agent(writer).add_agent(analyst)

    # Process a team message
    from agenticflow.core.state import AgentMessage
    message = AgentMessage(sender="user", content="Analyze market trends and create a report")

    response = await team.process_message(message)
    print(f"Team response: {response.content}")

    # Get team status
    status = await team.get_status()
    print(f"Team completed agents: {status['completion_order']}")


async def hierarchical_flow_example():
    """Demonstrate full hierarchical flow with multiple teams."""
    print("\n=== Hierarchical Flow Example ===")

    # Create workspace
    import tempfile
    temp_dir = tempfile.mkdtemp()

    try:
        # Create flow
        flow = Flow("demo_flow", workspace_path=temp_dir)

        # Create research team
        research_team = Supervisor("research_team", keywords=["research"])
        search_agent = SimpleAgent("searcher", keywords=["search"])
        scraper_agent = SimpleAgent("scraper", keywords=["scrape"])
        research_team.add_agent(search_agent).add_agent(scraper_agent)

        # Create document team
        doc_team = Supervisor("document_team", keywords=["write", "document"])
        writer_agent = SimpleAgent("writer", keywords=["write"])
        editor_agent = SimpleAgent("editor", keywords=["edit"])
        doc_team.add_agent(writer_agent).add_agent(editor_agent)

        # Create standalone coordinator
        coordinator = SimpleAgent("coordinator", keywords=["coordinate", "manage"])

        # Create top-level orchestrator
        orchestrator = Orchestrator("main_orchestrator")
        orchestrator.add_team(research_team)
        orchestrator.add_team(doc_team)
        orchestrator.add_agent(coordinator)

        # Setup flow
        flow.add_orchestrator(orchestrator)

        # Start flow
        start_task = asyncio.create_task(
            flow.start("Research AI agents and create a comprehensive report")
        )

        # Let it process
        await asyncio.sleep(0.5)

        # Send additional messages (only if flow is running)
        if flow.is_running():
            await flow.send_message("Focus on recent developments in 2024")
            await flow.send_message("Include performance benchmarks")

        # Let it process more
        await asyncio.sleep(0.5)

        # Get results
        messages = await flow.get_messages()
        print(f"Total messages processed: {len(messages)}")

        # Get orchestrator status
        status = await orchestrator.get_status()
        print(f"Active teams: {list(status['teams'].keys())}")
        print(f"Individual agents: {list(status['agents'].keys())}")

        # Get workspace files
        files = await flow.get_workspace_files()
        print(f"Workspace files created: {files}")

        # Get metrics
        metrics = await flow.get_metrics()
        print(f"Flow metrics: {metrics.get('total_flow_events', 0)} events")

        # Stop flow
        await flow.stop()
        try:
            await start_task
        except:
            pass

    finally:
        import shutil
        shutil.rmtree(temp_dir)


async def specialized_agents_example():
    """Demonstrate specialized agents with tools."""
    print("\n=== Specialized Agents Example ===")

    import tempfile
    temp_dir = tempfile.mkdtemp()

    try:
        from agenticflow.workspace.workspace import Workspace
        workspace = Workspace(temp_dir)

        # Test document writer
        doc_agent = DocumentWriterAgent()
        doc_agent.workspace = workspace

        from agenticflow.core.state import AgentMessage
        write_message = AgentMessage(
            sender="user",
            content="Write a document about AI safety to ai_safety.txt"
        )

        doc_response = await doc_agent.process_message(write_message)
        print(f"Document agent: {doc_response.content}")

        # Test note writer
        note_agent = NoteWriterAgent()
        note_agent.workspace = workspace

        note_message = AgentMessage(
            sender="user",
            content="""Create an outline for these key points:
            • AI alignment is crucial for safety
            • Interpretability helps understand AI decisions
            • Robustness ensures reliable performance
            • Value learning aligns AI with human values
            """
        )

        note_response = await note_agent.process_message(note_message)
        print(f"Note agent: {note_response.content}")

        # Check created files
        files = await workspace.list_files()
        print(f"Created files: {files}")

    finally:
        import shutil
        shutil.rmtree(temp_dir)


async def observability_example():
    """Demonstrate observability features."""
    print("\n=== Observability Example ===")

    import tempfile
    temp_dir = tempfile.mkdtemp()

    try:
        # Create flow with observability
        flow = Flow("observability_demo", workspace_path=temp_dir, enable_observability=True)

        # Create agents with different execution patterns
        fast_agent = SimpleAgent("fast_agent")
        slow_agent = SimpleAgent("slow_agent", response_template="Slow response: {content}")

        # Create orchestrator
        orchestrator = Orchestrator()
        orchestrator.add_agent(fast_agent).add_agent(slow_agent)
        flow.add_orchestrator(orchestrator)

        # Start flow
        start_task = asyncio.create_task(flow.start("Test observability"))
        await asyncio.sleep(0.2)

        # Send multiple messages
        for i in range(5):
            await flow.send_message(f"Message {i}")
            await asyncio.sleep(0.1)

        # Get metrics
        metrics = await flow.get_metrics()
        print(f"Flow metrics: {metrics}")

        # Get recent events
        if flow.observer:
            events = flow.observer.get_recent_events(limit=5)
            print(f"Recent events: {len(events)}")
            for event in events[-3:]:  # Show last 3 events
                print(f"  - {event['event_type']} at {event['timestamp']}")

            # Get error summary
            error_summary = flow.observer.get_error_summary()
            print(f"Error summary: {error_summary}")

        await flow.stop()
        try:
            await start_task
        except:
            pass

    finally:
        import shutil
        shutil.rmtree(temp_dir)


async def main():
    """Run all examples."""
    print("AgenticFlow Framework Examples")
    print("=" * 50)

    await basic_agent_example()
    await team_workflow_example()
    await hierarchical_flow_example()
    await specialized_agents_example()
    await observability_example()

    print("\n" + "=" * 50)
    print("All examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())