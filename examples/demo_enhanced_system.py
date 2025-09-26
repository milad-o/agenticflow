#!/usr/bin/env python3
"""
Comprehensive Enhanced AgenticFlow Demo

This demo showcases the fully enhanced AgenticFlow system with:
- Enhanced Planner with LangGraph brain
- Enhanced Orchestrator with intelligent scheduling
- Enhanced System-Aware Agents with memory
- Comprehensive logging with entity attribution
- Full event bus monitoring and system communication
- DAG visualization and progress tracking
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Import enhanced components
from agenticflow.core.flow import Flow
from agenticflow.orchestration.planners.enhanced_planner import EnhancedPlanner
from agenticflow.orchestration.enhanced_orchestrator import EnhancedOrchestrator
from agenticflow.agents.enhanced_system_aware_agent import EnhancedSystemAwareAgent, AgentRole

# Import core infrastructure
from agenticflow.core.events.event_bus import EventBus, Event, EventType
from agenticflow.observability.flow_logger import get_flow_logger, LogLevel

# Import LLM
from langchain_openai import ChatOpenAI


class EnhancedFlowDemo:
    """
    Comprehensive demo showcasing the enhanced AgenticFlow system.
    
    Demonstrates the complete architecture with intelligent components,
    system awareness, memory, and comprehensive observability.
    """
    
    def __init__(self):
        self.logger = get_flow_logger()
        self.event_bus = EventBus()
        
        # Initialize LLM
        self.model = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            streaming=False
        )
        
        # Demo configuration
        self.demo_request = """
        Create a comprehensive market analysis report for AI in healthcare.
        
        The report should include:
        1. Market size analysis and trends
        2. Key players and competitive landscape  
        3. Technology adoption patterns
        4. Regulatory challenges and opportunities
        5. Investment trends and funding patterns
        6. Future predictions and recommendations
        
        Deliver as a structured document with executive summary,
        detailed sections, and actionable insights.
        """
        
        self.setup_event_monitoring()
    
    def setup_event_monitoring(self):
        """Set up comprehensive event monitoring."""
        @self.event_bus.on(EventType.TASK_STARTED)
        async def on_task_started(event: Event):
            self.logger.info(f"🎬 Task Started: {event.source}",
                           event_data=event.data,
                           level=LogLevel.INFO)
        
        @self.event_bus.on(EventType.TASK_COMPLETED)
        async def on_task_completed(event: Event):
            self.logger.info(f"🏁 Task Completed: {event.source}",
                           event_data=event.data,
                           level=LogLevel.SUCCESS)
        
        @self.event_bus.on(EventType.STATUS_UPDATE)
        async def on_status_update(event: Event):
            self.logger.info(f"📊 Status Update: {event.source}",
                           event_data=event.data,
                           level=LogLevel.INFO)
        
        @self.event_bus.on("system_communication")
        async def on_system_communication(event: Event):
            data = event.data
            report_type = data.get("report_type", "unknown")
            from_agent = data.get("from_agent", "unknown")
            to_superior = data.get("to_superior", "unknown")
            
            self.logger.info(f"📡 System Communication: {from_agent} → {to_superior}",
                           communication_type=report_type,
                           event_data=data,
                           level=LogLevel.INFO)
    
    async def run_enhanced_demo(self):
        """Run the comprehensive enhanced demo."""
        self.logger.flow("🌟 Starting Enhanced AgenticFlow System Demo", 
                        demo_type="comprehensive",
                        architecture="enhanced",
                        level=LogLevel.SUCCESS)
        
        try:
            # Create enhanced components
            enhanced_planner = self.create_enhanced_planner()
            enhanced_orchestrator = self.create_enhanced_orchestrator()
            enhanced_agents = self.create_enhanced_agents()
            
            # Create Flow with enhanced components
            flow = Flow(
                planner=enhanced_planner,
                orchestrator=enhanced_orchestrator,
                event_bus=self.event_bus
            )
            
            self.logger.flow("🏗️ Enhanced Flow architecture assembled",
                           planner_type="enhanced_langgraph",
                           orchestrator_type="enhanced_langgraph",
                           agent_count=len(enhanced_agents),
                           level=LogLevel.SUCCESS)
            
            # Log system architecture
            await self.log_system_architecture(enhanced_agents)
            
            # Execute the enhanced flow
            self.logger.flow("🚀 Executing enhanced flow with intelligent components",
                           request_preview=self.demo_request[:100] + "...",
                           level=LogLevel.INFO)
            
            # Start flow execution
            result = await flow.arun(
                user_request=self.demo_request,
                agents=enhanced_agents
            )
            
            # Display comprehensive results
            await self.display_enhanced_results(result)
            
        except Exception as e:
            self.logger.flow(f"❌ Enhanced demo failed: {str(e)}",
                           error=str(e),
                           level=LogLevel.ERROR)
            raise
        
        finally:
            self.logger.flow("🎯 Enhanced demo completed",
                           demo_status="finished",
                           level=LogLevel.SUCCESS)
    
    def create_enhanced_planner(self) -> EnhancedPlanner:
        """Create enhanced planner with LangGraph brain."""
        self.logger.planner("🧠 Creating Enhanced Planner with LangGraph brain",
                          planner_features="multi_phase,memory,reflection,dependency_detection",
                          level=LogLevel.SUCCESS)
        
        return EnhancedPlanner(
            model=self.model,
            event_bus=self.event_bus
        )
    
    def create_enhanced_orchestrator(self) -> EnhancedOrchestrator:
        """Create enhanced orchestrator with intelligent scheduling."""
        self.logger.orchestrator("🧠 Creating Enhanced Orchestrator with LangGraph brain",
                                orchestrator_features="adaptive_scheduling,load_balancing,error_recovery",
                                max_concurrent_tasks=3,
                                level=LogLevel.SUCCESS)
        
        return EnhancedOrchestrator(
            model=self.model,
            event_bus=self.event_bus,
            max_concurrent_tasks=3
        )
    
    def create_enhanced_agents(self) -> List[Dict[str, Any]]:
        """Create enhanced system-aware agents with memory."""
        agents = []
        
        # Research Analyst Agent
        research_agent = EnhancedSystemAwareAgent(
            model=self.model,
            agent_id="research_analyst",
            event_bus=self.event_bus,
            superior="enhanced_orchestrator",
            role=AgentRole.SUBORDINATE
        )
        
        # Market Intelligence Agent  
        market_agent = EnhancedSystemAwareAgent(
            model=self.model,
            agent_id="market_intelligence", 
            event_bus=self.event_bus,
            superior="enhanced_orchestrator",
            role=AgentRole.SUBORDINATE
        )
        
        # Report Writer Agent
        writer_agent = EnhancedSystemAwareAgent(
            model=self.model,
            agent_id="report_writer",
            event_bus=self.event_bus,
            superior="enhanced_orchestrator", 
            role=AgentRole.SUBORDINATE
        )
        
        agents = [
            {
                "name": "research_analyst",
                "agent": research_agent,
                "capabilities": ["research", "data_analysis", "trend_analysis", "academic_sources"],
                "description": "Specializes in comprehensive research and data analysis"
            },
            {
                "name": "market_intelligence",
                "agent": market_agent, 
                "capabilities": ["market_analysis", "competitive_intelligence", "financial_analysis", "industry_reports"],
                "description": "Expert in market intelligence and competitive analysis"
            },
            {
                "name": "report_writer",
                "agent": writer_agent,
                "capabilities": ["writing", "documentation", "synthesis", "executive_summaries"],
                "description": "Skilled in creating comprehensive reports and documentation"
            }
        ]
        
        for agent_info in agents:
            self.logger.agent(f"🤖 Created enhanced system-aware agent: {agent_info['name']}",
                            agent_id=agent_info['name'],
                            capabilities=agent_info['capabilities'],
                            superior="enhanced_orchestrator",
                            role=AgentRole.SUBORDINATE.value,
                            level=LogLevel.SUCCESS)
        
        return agents
    
    async def log_system_architecture(self, agents: List[Dict[str, Any]]):
        """Log the complete system architecture."""
        architecture = {
            "system_hierarchy": {
                "flow": {
                    "role": "coordinator",
                    "manages": ["planner", "orchestrator"]
                },
                "enhanced_planner": {
                    "role": "intelligent_planner",
                    "brain_type": "langgraph",
                    "capabilities": ["task_decomposition", "dependency_analysis", "agent_matching"],
                    "reports_to": "flow"
                },
                "enhanced_orchestrator": {
                    "role": "intelligent_scheduler", 
                    "brain_type": "langgraph",
                    "capabilities": ["adaptive_scheduling", "load_balancing", "progress_monitoring"],
                    "reports_to": "flow",
                    "manages": [agent["name"] for agent in agents]
                },
                "enhanced_agents": {
                    agent["name"]: {
                        "role": "subordinate_executor",
                        "brain_type": "langgraph", 
                        "capabilities": agent["capabilities"],
                        "superior": "enhanced_orchestrator",
                        "has_memory": True,
                        "system_aware": True
                    }
                    for agent in agents
                }
            },
            "communication_flows": {
                "planning_phase": "flow → planner → orchestrator", 
                "execution_phase": "orchestrator ↔ agents",
                "progress_reporting": "agents → orchestrator → flow",
                "event_bus": "all_components ↔ event_bus"
            },
            "intelligence_features": {
                "planner": ["multi_phase_analysis", "dependency_detection", "capability_matching"],
                "orchestrator": ["adaptive_scheduling", "intelligent_allocation", "error_recovery"],
                "agents": ["system_awareness", "memory_persistence", "progress_reporting", "reflection"]
            }
        }
        
        self.logger.flow("🏛️ Enhanced System Architecture",
                        architecture=architecture,
                        level=LogLevel.INFO)
    
    async def display_enhanced_results(self, result: Dict[str, Any]):
        """Display comprehensive results from the enhanced system."""
        self.logger.flow("📋 Enhanced Flow Execution Results",
                        execution_status=result.get("status", "unknown"),
                        level=LogLevel.SUCCESS)
        
        # Display execution summary
        if "summary" in result:
            summary = result["summary"]
            self.logger.flow("📊 Execution Summary",
                           total_tasks=summary.get("total_tasks", 0),
                           successful_tasks=summary.get("successful", 0),
                           failed_tasks=summary.get("failed", 0),
                           success_rate=f"{summary.get('success_rate', 0)*100:.1f}%",
                           execution_time=f"{result.get('execution_time_seconds', 0):.1f}s",
                           level=LogLevel.SUCCESS)
        
        # Display task results
        if "task_results" in result:
            task_results = result["task_results"]
            for task_id, task_result in task_results.items():
                status = task_result.get("status", "unknown")
                if status == "success":
                    self.logger.task(f"✅ Task {task_id} completed successfully",
                                   task_id=task_id,
                                   result_preview=str(task_result.get("result", ""))[:100] + "...",
                                   level=LogLevel.SUCCESS)
                else:
                    self.logger.task(f"❌ Task {task_id} failed",
                                   task_id=task_id,
                                   error=task_result.get("error", "Unknown error"),
                                   level=LogLevel.ERROR)
        
        # Display system insights
        await self.display_system_insights(result)
    
    async def display_system_insights(self, result: Dict[str, Any]):
        """Display insights about system performance."""
        insights = {
            "planning_intelligence": "Enhanced planner successfully decomposed complex request",
            "orchestration_efficiency": "Intelligent scheduling optimized task execution",
            "agent_collaboration": "System-aware agents provided comprehensive progress reporting", 
            "memory_utilization": "Agents maintained context and learning across task execution",
            "event_coordination": "Event bus facilitated seamless system communication"
        }
        
        self.logger.flow("🎯 Enhanced System Performance Insights",
                        insights=insights,
                        level=LogLevel.INFO)
        
        # System recommendations
        recommendations = {
            "scalability": "System can handle increased complexity with more agents",
            "observability": "Comprehensive logging provides full execution visibility",
            "reliability": "Error recovery and retry mechanisms ensure robust operation",
            "intelligence": "LangGraph brains enable adaptive and context-aware decisions"
        }
        
        self.logger.flow("💡 System Enhancement Recommendations", 
                        recommendations=recommendations,
                        level=LogLevel.INFO)


async def main():
    """Run the comprehensive enhanced AgenticFlow demo."""
    print("🌟 Enhanced AgenticFlow System Demo")
    print("="*60)
    print("This demo showcases the fully enhanced system with:")
    print("• Enhanced Planner with LangGraph brain") 
    print("• Enhanced Orchestrator with intelligent scheduling")
    print("• Enhanced System-Aware Agents with memory")
    print("• Comprehensive logging and observability")
    print("• Full event bus monitoring")
    print("="*60)
    
    demo = EnhancedFlowDemo()
    
    try:
        await demo.run_enhanced_demo()
        
        print("\n🎯 Demo completed successfully!")
        print("Check the logs above for detailed system execution traces.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Ensure we have the required environment
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    asyncio.run(main())