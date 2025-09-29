"""Demo of rich console output for AgenticFlow observability."""

import asyncio
from agenticflow import Flow, Agent, create_file, search_web


async def demo_rich_console():
    """Demonstrate rich console output."""
    print("🎨 Rich Console Output Demo")
    print("=" * 50)
    
    # Create flow with rich console output
    flow = Flow('rich_demo')
    flow.enable_observability(
        console_output=True, 
        rich_console=True,  # Enable rich console
        file_logging=False
    )

    # Create agents
    researcher = Agent('researcher', tools=[search_web], description='Web researcher')
    writer = Agent('writer', tools=[create_file], description='Content writer')
    
    flow.add_agent(researcher)
    flow.add_agent(writer)
    
    # Run workflow
    result = await flow.run('Research AI trends and create a comprehensive report')
    
    # Print summary
    events = flow._event_logger.get_events()
    if hasattr(flow._event_logger.get_event_bus()._subscribers[0], 'print_summary'):
        flow._event_logger.get_event_bus()._subscribers[0].print_summary(events)
    
    return result


if __name__ == "__main__":
    asyncio.run(demo_rich_console())
