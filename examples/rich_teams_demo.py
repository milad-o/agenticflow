"""Demo rich console output with teams."""

import asyncio
from agenticflow import Flow, Agent, Team, create_file, search_web


async def demo_rich_teams():
    """Demonstrate rich console output with teams."""
    print("🎨 Rich Console Output with Teams")
    print("=" * 50)
    
    # Create flow with rich console
    flow = Flow('teams_demo')
    flow.enable_observability(console_output=True, rich_console=True)
    
    # Create a research team
    research_team = Team('research_team')
    researcher = Agent('researcher', tools=[search_web], description='Web researcher')
    analyst = Agent('analyst', tools=[create_file], description='Data analyst')
    
    research_team.add_agent(researcher)
    research_team.add_agent(analyst)
    
    # Create a writing team
    writing_team = Team('writing_team')
    writer = Agent('writer', tools=[create_file], description='Content writer')
    editor = Agent('editor', tools=[create_file], description='Content editor')
    
    writing_team.add_agent(writer)
    writing_team.add_agent(editor)
    
    # Add teams to flow
    flow.add_team(research_team)
    flow.add_team(writing_team)
    
    # Run workflow
    result = await flow.run('Research AI trends and create a comprehensive report with analysis')
    
    # Print summary
    events = flow._event_logger.get_events()
    if hasattr(flow._event_logger.get_event_bus()._subscribers[0], 'print_summary'):
        flow._event_logger.get_event_bus()._subscribers[0].print_summary(events)
    
    return result


if __name__ == "__main__":
    asyncio.run(demo_rich_teams())
