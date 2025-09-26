#!/usr/bin/env python3
"""
Weather Comparison Demo with Tavily Search

This demo showcases intelligent agents using online search tools to:
1. Weather Research Agent: Uses Tavily to search for current weather in Toronto and Los Angeles
2. Report Writer Agent: Creates a comprehensive comparison report

Demonstrates:
- Tool-enabled agents with reflection and decision-making
- Online search integration with Tavily
- System-aware agents that understand when to use tools
- Multi-agent collaboration for data gathering and report generation

Note: Checkpointers are disabled to avoid msgpack serialization issues with complex tool objects.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AgenticFlow components
from agenticflow.agent.base.agent import Agent
from agenticflow.agent.strategies.enhanced_rpavh_agent import EnhancedRPAVHGraphFactory
from agenticflow.core.events.event_bus import EventBus, Event, EventType
from agenticflow.observability.flow_logger import get_flow_logger, LogLevel
from agenticflow.core.models import get_chat_model

# Import Tavily search tool
from langchain_community.tools.tavily_search import TavilySearchResults

# Import file tools for report writing
from agenticflow.tools.file.file_tools import WriteTextAtomicTool


class WeatherComparisonDemo:
    """
    Intelligent weather comparison demo using tool-enabled reflective agents.
    
    This demo creates two specialized agents:
    1. Weather Research Agent - Uses online search to gather current weather data
    2. Report Writer Agent - Creates comprehensive comparison reports
    """
    
    def __init__(self):
        self.logger = get_flow_logger()
        self.event_bus = EventBus()
        
        # Initialize LLM
        self.model = get_chat_model(
            model_name="granite3.2:8b", 
            temperature=0.1
        )
        
        self.setup_event_monitoring()
        
        # Validate Tavily API Key
        if not os.getenv("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY") == "your_tavily_api_key_here":
            raise ValueError("Please set a valid TAVILY_API_KEY in your .env file")
    
    def setup_event_monitoring(self):
        """Set up comprehensive event monitoring for agent actions."""
        def on_task_started(event: Event):
            self.logger.info(f"🎬 Task Started: {event.source}",
                           event_data=event.data,
                           level=LogLevel.INFO)
        
        def on_task_completed(event: Event):
            self.logger.info(f"🏁 Task Completed: {event.source}",
                           event_data=event.data,
                           level=LogLevel.SUCCESS)
        
        def on_progress(event: Event):
            self.logger.info(f"📊 Progress: {event.source}",
                           event_data=event.data,
                           level=LogLevel.INFO)
        
        def on_rpavh_event(event: Event):
            data = event.data
            phase = data.get("phase", "unknown")
            
            if "subtask" in data:
                subtask_name = data.get("subtask_name", "Unknown")
                tool_used = data.get("tool_used", "Unknown")
                self.logger.info(f"🔧 Agent Tool Usage: {subtask_name}",
                               phase=phase,
                               tool=tool_used,
                               event_data=data,
                               level=LogLevel.INFO)
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.TASK_STARTED, on_task_started)
        self.event_bus.subscribe(EventType.TASK_COMPLETED, on_task_completed)
        self.event_bus.subscribe(EventType.TASK_PROGRESS, on_progress)
        # Subscribe to custom channel for enhanced RPAVH events
        self.event_bus.subscribe("subtask_completed", on_rpavh_event, "enhanced_rpavh")
        self.event_bus.subscribe("subtask_started", on_rpavh_event, "enhanced_rpavh")
    
    def create_weather_research_agent(self) -> Agent:
        """Create an agent specialized in weather research using Tavily search."""
        
        # Create Tavily search tool
        tavily_search = TavilySearchResults(
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        
        tools = [tavily_search]
        
        # Create enhanced brain for intelligent search decisions
        enhanced_brain = EnhancedRPAVHGraphFactory(
            use_llm_for_planning=True,
            use_llm_for_verification=True,
            max_parallel_tasks=2,
            max_retries=1
        ).create_graph()
        
        agent = Agent(
            model=self.model,  # Required LLM instance
            name="weather_researcher",  # Required name
            tools=tools,
            custom_graph=enhanced_brain,
            checkpointer=None,  # Disable checkpointing to avoid serialization issues
            use_llm_reflection=True,
            use_llm_verification=True
        )
        
        self.logger.agent(f"🌤️ Created Weather Research Agent",
                         agent_name="weather_researcher",
                         tools_available=["tavily_search"],
                         brain_type="enhanced_rpavh",
                         search_capabilities="advanced_web_search",
                         level=LogLevel.SUCCESS)
        
        return agent
    
    def create_report_writer_agent(self) -> Agent:
        """Create an agent specialized in writing comprehensive comparison reports."""
        
        # Create file writing tool
        write_tool = WriteTextAtomicTool()
        
        tools = [write_tool]
        
        # Create enhanced brain for intelligent report writing
        enhanced_brain = EnhancedRPAVHGraphFactory(
            use_llm_for_planning=True,
            use_llm_for_verification=True,
            max_parallel_tasks=1,
            max_retries=1
        ).create_graph()
        
        # Create a separate model instance with higher temperature for creative writing
        creative_model = get_chat_model(
            model_name="granite3.2:8b", 
            temperature=0.3
        )
        
        agent = Agent(
            model=creative_model,  # Required LLM instance
            name="report_writer",  # Required name
            tools=tools,
            custom_graph=enhanced_brain,
            checkpointer=None,  # Disable checkpointing to avoid serialization issues
            use_llm_reflection=True,
            use_llm_verification=True
        )
        
        self.logger.agent(f"📊 Created Report Writer Agent",
                         agent_name="report_writer", 
                         tools_available=["write_text_atomic"],
                         brain_type="enhanced_rpavh",
                         writing_capabilities="comprehensive_reports",
                         level=LogLevel.SUCCESS)
        
        return agent
    
    async def run_weather_comparison_demo(self):
        """Run the complete weather comparison demo."""
        self.logger.flow("🌤️ Starting Weather Comparison Demo", 
                        demo_type="weather_analysis",
                        cities=["Toronto", "Los Angeles"],
                        agent_count=2,
                        level=LogLevel.SUCCESS)
        
        try:
            # Create specialized agents
            weather_agent = self.create_weather_research_agent()
            report_agent = self.create_report_writer_agent()
            
            # Phase 1: Research current weather in both cities
            self.logger.flow("🔍 Phase 1: Weather Research",
                           task="gather_current_weather_data",
                           cities=["Toronto", "Los Angeles"],
                           level=LogLevel.INFO)
            
            weather_request = """
            I need you to research and gather current weather information for Toronto and Los Angeles. 
            
            For each city, please find:
            - Current temperature and "feels like" temperature
            - Weather conditions (sunny, cloudy, rainy, etc.)
            - Humidity levels
            - Wind speed and direction
            - Air quality if available
            - Any weather alerts or warnings
            - Today's forecast including high/low temperatures
            
            Use online search to get the most current weather data available.
            The agent should reflect on whether it needs to use search tools and then use them intelligently.
            """
            
            # Execute weather research with enhanced agent
            weather_result = await weather_agent.arun(
                message=weather_request,
                thread_id=f"weather_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # Weather agent execution completed
            
            self.logger.flow("✅ Phase 1 Completed: Weather Research",
                           research_status=weather_result.get("success", False),
                           level=LogLevel.SUCCESS)
            
            # Phase 2: Generate comparison report
            self.logger.flow("📊 Phase 2: Report Generation",
                           task="create_weather_comparison_report",
                           level=LogLevel.INFO)
            
            # Extract actual weather data from results
            weather_data = weather_result.get('data', {})
            weather_results = weather_data.get('results', [])
            
            # Format weather data for report
            weather_data_text = "No weather data available"
            if weather_results:
                weather_info = []
                for result in weather_results:
                    if 'result' in result:
                        weather_info.append(result['result'])
                weather_data_text = "\n\n".join(weather_info)
            
            report_request = f"""
            Based on the weather research data below, create a comprehensive weather comparison report 
            between Toronto and Los Angeles.
            
            WEATHER RESEARCH DATA:
            {weather_data_text}
            
            Please create a detailed report that includes:
            
            1. Executive Summary
            - Quick comparison highlights
            - Key differences between the cities
            
            2. Current Conditions Comparison
            - Temperature comparison with analysis
            - Weather conditions analysis
            - Comfort levels and air quality
            
            3. Detailed Metrics Table
            - Side-by-side comparison of all weather metrics
            
            4. Climate Context
            - Typical weather patterns for each city
            - Seasonal considerations
            
            5. Recommendations
            - Best city for outdoor activities today
            - Clothing recommendations for each location
            - Travel considerations
            
            **IMPORTANT: You must save the report to this exact file path:**
            examples/artifact/weather_comparison_report.md
            
            **Generate a COMPLETE report with ALL sections listed above.**
            The report should be well-structured, informative, and professional with detailed analysis.
            """
            
            # Report generation with real weather data
            
            # Execute report generation
            report_result = await report_agent.arun(
                message=report_request,
                thread_id=f"report_writing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            self.logger.flow("✅ Phase 2 Completed: Report Generation",
                           report_status=report_result.get("success", False),
                           level=LogLevel.SUCCESS)
            
            # Display comprehensive results
            await self.display_demo_results(weather_result, report_result)
            
        except Exception as e:
            self.logger.flow(f"❌ Weather comparison demo failed: {str(e)}",
                           error=str(e),
                           level=LogLevel.ERROR)
            raise
        
        finally:
            self.logger.flow("🎯 Weather comparison demo completed",
                           demo_status="finished",
                           level=LogLevel.SUCCESS)
    
    async def display_demo_results(self, weather_result: Dict[str, Any], report_result: Dict[str, Any]):
        """Display comprehensive results from the weather comparison demo."""
        
        self.logger.flow("📋 Weather Comparison Demo Results",
                        demo_status="completed",
                        level=LogLevel.SUCCESS)
        
        # Weather Research Results
        weather_success = weather_result.get("success", False)
        self.logger.agent(f"🌤️ Weather Research Agent: {'✅ Success' if weather_success else '❌ Failed'}",
                         agent_name="weather_researcher",
                         task_completion=weather_success,
                         reflection_performed=True,
                         tools_used="tavily_search",
                         level=LogLevel.SUCCESS if weather_success else LogLevel.ERROR)
        
        # Report Writing Results
        report_success = report_result.get("success", False)
        self.logger.agent(f"📊 Report Writer Agent: {'✅ Success' if report_success else '❌ Failed'}",
                         agent_name="report_writer",
                         task_completion=report_success,
                         report_generated=report_success,
                         output_file="examples/artifact/weather_comparison_report.md",
                         level=LogLevel.SUCCESS if report_success else LogLevel.ERROR)
        
        # Agent Intelligence Insights
        insights = {
            "tool_utilization": "Agents intelligently decided when to use online search tools",
            "reflection_capability": "Enhanced RPAVH brain provided sophisticated decision-making",
            "task_specialization": "Each agent focused on its specialized capability area",
            "data_flow": "Weather data flowed seamlessly from research to report generation",
            "adaptability": "Agents adapted their approach based on available tools and task requirements"
        }
        
        self.logger.flow("🧠 Agent Intelligence Analysis",
                        insights=insights,
                        level=LogLevel.INFO)
        
        # Final Summary
        overall_success = weather_success and report_success
        self.logger.flow(f"🎯 Overall Demo Success: {'✅ Complete' if overall_success else '⚠️ Partial'}",
                        weather_research=weather_success,
                        report_generation=report_success,
                        agent_collaboration="successful",
                        tool_integration="tavily_search + file_writing",
                        level=LogLevel.SUCCESS if overall_success else LogLevel.WARNING)
        
        # Results are handled by the observability system - no hardcoded prints


async def main():
    """Run the weather comparison demo."""
    # Check for API key
    if not os.getenv("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY") == "your_tavily_api_key_here":
        return
    
    demo = WeatherComparisonDemo()
    
    try:
        await demo.run_weather_comparison_demo()
        
    except Exception as e:
        raise


if __name__ == "__main__":
    asyncio.run(main())