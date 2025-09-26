#!/usr/bin/env python3
"""
Proper AgenticFlow Architecture Demo

This demo showcases the CORRECT AgenticFlow architecture:
Flow → Orchestrator → Planner → Agent(s)

With comprehensive observability showing:
- Flow initialization and startup
- Planner creating task decomposition  
- Orchestrator coordinating agent execution
- Agent executing with Enhanced RPAVH brain
- Full event bus and logging integration
"""

import asyncio
import logging
from pathlib import Path

from agenticflow import Flow, FlowConfig
from agenticflow.agent import Agent
from agenticflow.agent.strategies.enhanced_rpavh_agent import EnhancedRPAVHGraphFactory
from agenticflow.core.config import AgentConfig
from agenticflow.agent.roles import AgentRole
from agenticflow.orchestration.planners import Planner
from agenticflow.orchestration.orchestrators import Orchestrator
from agenticflow.observability.flow_logger import FlowLogger, LogLevel
from agenticflow.observability.event_monitor import EventMonitor
from langchain_ollama import ChatOllama


def _pick_ollama_models():
    """Pick the best available Ollama model."""
    import subprocess
    prefer = ('qwen2.5:7b', 'granite3.2:8b', 'llama3.2:3b')
    names = []
    try:
        p = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=False)
        for line in p.stdout.splitlines()[1:]:
            parts = line.split()
            if parts:
                names.append(parts[0])
    except Exception:
        names = []
    chat = next((m for m in prefer if any(n.startswith(m) for n in names)), names[0] if names else None)
    if not chat:
        raise RuntimeError('No Ollama model found')
    return chat, None


async def demo_proper_architecture():
    """Demo the proper AgenticFlow architecture with full observability."""
    
    # Initialize comprehensive logging
    logger = FlowLogger(enable_colors=True, min_level=LogLevel.INFO)
    
    logger.separator("PROPER AGENTICFLOW ARCHITECTURE")
    logger.flow("Flow → Orchestrator → Planner → Agent(s)", level=LogLevel.SUCCESS)
    
    # Setup workspace
    workspace = Path(__file__).parent / "examples"
    artifact_dir = workspace / "artifact"  
    artifact_dir.mkdir(exist_ok=True)
    data_dir = workspace / "data" / "csv"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.flow("Workspace configured", workspace=str(workspace))
    
    # Create sample data
    sample_data = {
        "sales_data.csv": "date,product,sales,region\n2024-01-01,Widget A,1000,North\n2024-01-02,Widget B,1500,South\n2024-01-03,Widget A,1200,East",
        "customer_data.csv": "id,name,email,segment\n1,John Doe,john@example.com,Premium\n2,Jane Smith,jane@example.com,Standard\n3,Bob Johnson,bob@example.com,Premium",
        "inventory_data.csv": "sku,name,quantity,price\nW001,Widget A,100,25.99\nW002,Widget B,75,39.99\nW003,Widget C,50,19.99"
    }
    
    for filename, content in sample_data.items():
        filepath = data_dir / filename
        if not filepath.exists():
            with open(filepath, 'w') as f:
                f.write(content)
            logger.flow(f"Created sample data: {filename}")
        else:
            logger.flow(f"Sample data exists: {filename}")
    
    # Suppress noisy logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("ollama").setLevel(logging.WARNING)
    
    # === STEP 1: CREATE FLOW ===
    logger.separator("STEP 1: FLOW CREATION")
    
    flow = Flow(FlowConfig(
        flow_name="ProperArchitectureDemo",
        workspace_path=str(workspace),
        max_parallel_tasks=2,
        recursion_limit=15
    ))
    
    logger.flow("Flow created with event bus and registries")
    
    # Setup comprehensive event monitoring
    monitor = EventMonitor(flow.event_bus, flow.reporter)
    logger.flow("Event monitoring activated")
    
    # Install tools
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast",
        "write_text_atomic", 
        "file_stat"
    ])
    
    logger.flow("Tools installed", tool_count=len(flow.tool_registry.get_all_tools()))
    
    # Get LLM
    chat_model, _ = _pick_ollama_models()
    llm = ChatOllama(model=chat_model, temperature=0.1)
    logger.flow(f"LLM configured: {chat_model}")
    
    # === STEP 2: CREATE PLANNER ===
    logger.separator("STEP 2: PLANNER CREATION")
    
    # Create planner - this is what was missing!
    flow.planner = Planner(
        model_name=chat_model,
        temperature=0.1
    )
    
    logger.planner("Planner created and attached to flow", 
                  model_name=chat_model,
                  temperature=0.1)
    
    # === STEP 3: CREATE ENHANCED AGENT ===
    logger.separator("STEP 3: ENHANCED AGENT CREATION")
    
    # Create Enhanced RPAVH Brain
    factory = EnhancedRPAVHGraphFactory(
        use_llm_for_planning=True,
        use_llm_for_verification=True,
        max_parallel_tasks=3,
        max_retries=2
    )
    enhanced_graph = factory.create_graph()
    
    logger.agent("Enhanced RPAVH brain created", 
                agent_name="csv_agent",
                llm_planning=True,
                llm_verification=True)
    
    # Create Agent with Enhanced Brain
    agent_config = AgentConfig(
        name="enhanced_csv_agent",
        model=chat_model,
        temperature=0.1,
        role=AgentRole.FILE_MANAGER,
        tools=["find_files", "read_text_fast", "write_text_atomic", "file_stat"]
    )
    
    enhanced_agent = Agent(
        config=agent_config,
        model=llm,
        tools=flow.tool_registry.get_all_tools(),
        max_attempts=2,
        custom_graph=enhanced_graph
    )
    
    logger.agent("Enhanced agent created with brain + body", 
                agent_name=enhanced_agent.name,
                tool_count=len(enhanced_agent.tools),
                role=str(agent_config.role))
    
    # === STEP 4: ADD AGENT TO FLOW ===
    logger.separator("STEP 4: AGENT REGISTRATION")
    
    # Add agent to flow - this connects it to the orchestrator
    flow.add_agent("csv_agent", enhanced_agent)
    
    logger.flow("Agent registered with flow", 
               agent_name="csv_agent",
               agents_count=len(flow.agents))
    
    # === STEP 5: START FLOW (Creates Orchestrator) ===
    logger.separator("STEP 5: FLOW STARTUP")
    
    # This is where Orchestrator gets created with Planner + Agents
    flow.start()
    
    logger.orchestrator("Orchestrator created and linked", 
                       planner_available=flow.planner is not None,
                       agent_count=len(flow.agents),
                       level=LogLevel.SUCCESS)
    
    logger.flow("Flow started - complete architecture ready", 
               orchestrator_ready=flow.orchestrator is not None,
               level=LogLevel.SUCCESS)
    
    # === STEP 6: EXECUTE REQUEST THROUGH PROPER FLOW ===
    logger.separator("STEP 6: PROPER FLOW EXECUTION")
    
    request = """Find CSV files in examples/data/csv directory, read their content to understand the structure, 
    and write a comprehensive analysis report to examples/artifact/proper_architecture_report.md"""
    
    logger.task("Task submitted to Flow", 
               task_id="proper_demo_001",
               request_preview=request[:80] + "...")
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        # THIS IS THE PROPER WAY: Flow → Orchestrator → Planner → Agent
        result = await flow.arun(request, thread_id="proper_demo_001")
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        logger.separator("EXECUTION RESULTS")
        
        logger.flow(f"Flow execution completed in {execution_time:.2f}s",
                   success=result.get('success', False),
                   level=LogLevel.SUCCESS if result.get('success', False) else LogLevel.ERROR)
        
        # Show detailed results
        if result:
            logger.flow("Flow execution result", 
                       result_keys=list(result.keys()),
                       message_preview=str(result.get('message', ''))[:100] + "...")
            
            # Check for comprehensive execution data
            if 'data' in result:
                data = result['data']
                logger.orchestrator("Orchestrator execution data",
                                   data_keys=list(data.keys()) if isinstance(data, dict) else "Non-dict data")
        
        # Check for report creation  
        report_path = workspace / "artifact" / "proper_architecture_report.md"
        if report_path.exists():
            logger.flow("Report successfully created", 
                       report_path=str(report_path),
                       level=LogLevel.SUCCESS)
            
            with open(report_path, 'r') as f:
                content = f.read()
                logger.flow(f"Report content preview: {content[:200]}...")
        else:
            logger.flow("Report not found", 
                       expected_path=str(report_path),
                       level=LogLevel.WARNING)
        
    except Exception as e:
        logger.flow(f"Flow execution failed: {str(e)}", 
                   error=str(e),
                   level=LogLevel.ERROR)
        import traceback
        traceback.print_exc()
    
    # === FINAL: COMPREHENSIVE OBSERVABILITY ===
    logger.separator("ARCHITECTURE VERIFICATION")
    
    # Verify all components exist and are connected
    architecture_status = {
        "Flow": flow is not None,
        "EventBus": flow.event_bus is not None,
        "ToolRegistry": flow.tool_registry is not None,
        "Planner": flow.planner is not None,
        "Orchestrator": flow.orchestrator is not None,
        "Agents": len(flow.agents) > 0,
        "Enhanced_Agent": "csv_agent" in flow.agents,
        "Agent_Brain": hasattr(flow.agents.get("csv_agent", {}), "compiled_graph")
    }
    
    for component, status in architecture_status.items():
        status_icon = "✅" if status else "❌"
        logger.flow(f"{component}: {status_icon}",
                   component=component,
                   status=status,
                   level=LogLevel.SUCCESS if status else LogLevel.ERROR)
    
    # Event monitoring summary
    monitor.print_execution_summary()
    
    # Export comprehensive logs
    event_log_file = monitor.export_execution_log()
    flow_log_file = logger.export_log()
    
    logger.flow("Comprehensive logs exported",
               event_log=event_log_file,
               flow_log=flow_log_file,
               level=LogLevel.SUCCESS)
    
    # Final session summary
    logger.session_summary()
    
    logger.separator("ARCHITECTURE DEMONSTRATION COMPLETE")
    logger.flow("Proper AgenticFlow architecture validated", level=LogLevel.SUCCESS)


if __name__ == "__main__":
    asyncio.run(demo_proper_architecture())