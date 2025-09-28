"""
AgenticFlow - A simple, clean multi-agent framework.

Usage:
    from agenticflow import Flow, Agent, create_file, search_web
    
    # Create flow
    flow = Flow("my_workflow")
    
    # Create agents
    agent1 = Agent("researcher", tools=[search_web])
    agent2 = Agent("writer", tools=[create_file])
    
    # Add agents to flow
    flow.add_agent(agent1)
    flow.add_agent(agent2)
    
    # Run workflow
    result = await flow.run("Research and write a report")
"""

from .core import Flow, Agent, Team
from .tools import create_file, search_web

__version__ = "1.0.0"
__all__ = ["Flow", "Agent", "Team", "create_file", "search_web"]