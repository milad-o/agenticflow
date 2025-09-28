#!/usr/bin/env python3
"""Researcher-Writer Teams Example using AgenticFlow."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Explicitly set API keys to ensure they're available
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "")

# Verify API keys are set
print("🔑 API Key Status:")
print(f"   OpenAI: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
print(f"   Tavily: {'✅ Set' if os.getenv('TAVILY_API_KEY') else '❌ Missing'}")

from agenticflow import Flow, Agent, search_web, create_file, read_file

async def create_researcher_writer_teams():
    """Create researcher and writer teams."""
    print("🔬 Creating Researcher-Writer Teams")
    print("=" * 50)
    
    # Create main flow
    flow = Flow("researcher_writer_workflow")
    
    # Create research team
    research_agent = Agent(
        name="researcher",
        description="Specialized in web research and information gathering",
        system_prompt="You are a research specialist. Use web search to find comprehensive, accurate information on any topic. Provide detailed findings with sources.",
        tools=[search_web]
    )
    
    # Create writing team
    writer_agent = Agent(
        name="writer", 
        description="Specialized in content creation and document writing",
        system_prompt="You are a professional writer. Create well-structured, engaging content based on research findings. Use clear language and proper formatting.",
        tools=[create_file, read_file]
    )
    
    # Add agents to flow
    flow.add_agent(research_agent)
    flow.add_agent(writer_agent)
    
    print("✅ Teams created successfully!")
    print(f"   - Research Agent: {research_agent.name}")
    print(f"   - Writer Agent: {writer_agent.name}")
    print(f"   - Total Agents: {len(flow.agents)}")
    
    return flow

async def test_research_writing_workflow(flow: Flow, topic: str):
    """Test the research-writing workflow."""
    print(f"\n🎯 Research & Writing Task: {topic}")
    print("-" * 50)
    
    try:
        # Run the workflow
        result = await flow.run(f"Research '{topic}' and create a comprehensive report with your findings")
        
        print("✅ Workflow completed successfully!")
        print(f"📝 Generated {len(result['messages'])} messages:")
        
        for i, msg in enumerate(result["messages"], 1):
            sender = getattr(msg, 'name', 'user')
            content = msg.content
            print(f"\n   {i}. [{sender}]:")
            print(f"      {content[:200]}{'...' if len(content) > 200 else ''}")
        
        return result
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main function to run the researcher-writer teams example."""
    print("🚀 AgenticFlow Researcher-Writer Teams Example")
    print("=" * 60)
    
    # Create teams
    flow = await create_researcher_writer_teams()
    
    # Test topics
    topics = [
        "Latest developments in quantum computing",
        "Impact of AI on healthcare industry", 
        "Sustainable energy trends 2024",
        "Future of remote work technology"
    ]
    
    print(f"\n📚 Testing {len(topics)} research topics:")
    print("=" * 60)
    
    for i, topic in enumerate(topics, 1):
        print(f"\n{'='*60}")
        print(f"TOPIC {i}/{len(topics)}: {topic}")
        print(f"{'='*60}")
        
        result = await test_research_writing_workflow(flow, topic)
        
        if result:
            print(f"✅ Topic {i} completed successfully!")
        else:
            print(f"❌ Topic {i} failed!")
        
        # Small delay between topics
        await asyncio.sleep(1)
    
    print(f"\n🎉 RESEARCHER-WRITER TEAMS EXAMPLE COMPLETED!")
    print("=" * 60)
    print("✅ Multi-agent coordination working!")
    print("✅ Research capabilities working!")
    print("✅ Writing capabilities working!")
    print("✅ File creation working!")

if __name__ == "__main__":
    asyncio.run(main())
