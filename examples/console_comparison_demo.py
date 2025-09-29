"""Compare regular vs rich console output."""

import asyncio
from agenticflow import Flow, Agent, create_file, search_web


async def demo_regular_console():
    """Demo regular console output."""
    print("\n🔧 REGULAR CONSOLE OUTPUT")
    print("=" * 50)
    
    flow = Flow('regular_demo')
    flow.enable_observability(console_output=True, rich_console=False)
    
    researcher = Agent('researcher', tools=[search_web], description='Web researcher')
    flow.add_agent(researcher)
    
    result = await flow.run('Search for AI trends')
    return result


async def demo_rich_console():
    """Demo rich console output."""
    print("\n🎨 RICH CONSOLE OUTPUT")
    print("=" * 50)
    
    flow = Flow('rich_demo')
    flow.enable_observability(console_output=True, rich_console=True)
    
    researcher = Agent('researcher', tools=[search_web], description='Web researcher')
    flow.add_agent(researcher)
    
    result = await flow.run('Search for AI trends')
    
    # Print summary
    events = flow._event_logger.get_events()
    if hasattr(flow._event_logger.get_event_bus()._subscribers[0], 'print_summary'):
        flow._event_logger.get_event_bus()._subscribers[0].print_summary(events)
    
    return result


async def main():
    """Run both demos."""
    print("🔄 CONSOLE OUTPUT COMPARISON")
    print("=" * 60)
    
    # Regular console
    await demo_regular_console()
    
    # Rich console
    await demo_rich_console()
    
    print("\n✨ Notice the difference:")
    print("  - Regular: Plain text with emojis")
    print("  - Rich: Tree structure, colors, tables, and beautiful formatting!")


if __name__ == "__main__":
    asyncio.run(main())
