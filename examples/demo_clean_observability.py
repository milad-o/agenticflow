#!/usr/bin/env python3
"""
Clean Enhanced RPAVH Demo with Full Observability

This demo showcases the Enhanced RPAVH agent with:
- Comprehensive colorful logging
- Full DAG visualization  
- Task/subtask lifecycle tracking
- Reflection and decision transcription
- Event bus monitoring
- Clean, uncluttered output
"""

import asyncio
import logging
from pathlib import Path

from agenticflow import Flow, FlowConfig
from agenticflow.agent import Agent
from agenticflow.agent.strategies.enhanced_rpavh_agent import EnhancedRPAVHGraphFactory
from agenticflow.core.config import AgentConfig
from agenticflow.agent.roles import AgentRole
from agenticflow.observability.flow_logger import FlowLogger, LogLevel, get_flow_logger
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


async def demo_clean_observability():
    """Demo enhanced RPAVH with comprehensive observability."""
    
    # Initialize comprehensive logging
    logger = FlowLogger(enable_colors=True, min_level=LogLevel.INFO)
    
    logger.separator("ENHANCED RPAVH WITH FULL OBSERVABILITY")
    logger.flow("Starting clean demo with comprehensive logging", level=LogLevel.SUCCESS)
    
    # Setup workspace
    workspace = Path(__file__).parent / "examples"
    artifact_dir = workspace / "artifact"
    artifact_dir.mkdir(exist_ok=True)
    data_dir = workspace / "data" / "csv"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.flow(f"Workspace configured", workspace=str(workspace))
    
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
    
    # Create flow with event bus
    logger.separator("FLOW INITIALIZATION")
    flow = Flow(FlowConfig(
        flow_name="CleanObservabilityDemo",
        workspace_path=str(workspace),
        max_parallel_tasks=2,
        recursion_limit=15
    ))
    
    # Setup event monitoring
    monitor = EventMonitor(flow.event_bus, flow.reporter)
    logger.flow("Event monitoring activated - capturing all system events")
    
    # Install tools
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast", 
        "write_text_atomic",
        "file_stat"
    ])
    
    logger.flow(f"Tools installed", tool_count=len(flow.tool_registry.get_all_tools()))
    
    # Get LLM
    chat_model, _ = _pick_ollama_models()
    llm = ChatOllama(model=chat_model, temperature=0.1)
    logger.flow(f"LLM configured: {chat_model}")
    
    # Create Enhanced RPAVH Brain
    logger.separator("ENHANCED BRAIN CREATION")
    factory = EnhancedRPAVHGraphFactory(
        use_llm_for_planning=True,
        use_llm_for_verification=True,
        max_parallel_tasks=3,
        max_retries=2
    )
    enhanced_graph = factory.create_graph()
    
    logger.planner("Enhanced RPAVH Graph created", 
                  llm_planning=factory.use_llm_for_planning,
                  llm_verification=factory.use_llm_for_verification,
                  max_parallel_tasks=factory.max_parallel_tasks)
    
    # Create Agent Body
    logger.separator("AGENT BODY CREATION")
    agent_config = AgentConfig(
        name="enhanced_csv_agent",
        model=chat_model,
        temperature=0.1,
        role=AgentRole.FILE_MANAGER
    )
    
    enhanced_agent = Agent(
        config=agent_config,
        model=llm,
        tools=flow.tool_registry.get_all_tools(),
        max_attempts=2,
        custom_graph=enhanced_graph
    )
    
    # Connect agent to observability systems
    enhanced_agent._flow_ref = flow
    enhanced_agent.event_bus = flow.event_bus
    enhanced_agent.reporter = flow.reporter
    # Don't override agent's logger - it has different interface
    
    logger.agent("Agent body created and connected", 
                agent_name=enhanced_agent.name,
                tool_count=len(enhanced_agent.tools),
                role=str(agent_config.role))
    
    # Test execution with comprehensive logging
    logger.separator("TASK EXECUTION")
    
    request = """Find CSV files in examples/data/csv directory, read their content to understand the structure, 
    and write a comprehensive analysis report to examples/artifact/clean_enhanced_report.md"""
    
    logger.task(f"Task received: {request[:80]}...", task_id="clean_demo_001")
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        logger.agent("Starting enhanced agent execution", 
                    agent_name=enhanced_agent.name, 
                    level=LogLevel.SUCCESS)
        
        # Execute the enhanced agent
        result = await enhanced_agent.arun(request, thread_id="clean_demo_001")
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        logger.separator("EXECUTION RESULTS")
        
        logger.agent(f"Execution completed in {execution_time:.2f}s", 
                    agent_name=enhanced_agent.name,
                    success=result.get('success', False),
                    level=LogLevel.SUCCESS if result.get('success') else LogLevel.ERROR)
        
        if result.get('data'):
            data = result['data']
            exec_summary = data.get('execution_summary', {})
            
            logger.task("Task execution summary",
                       task_id="clean_demo_001",
                       total_subtasks=exec_summary.get('total_subtasks', 0),
                       completed_subtasks=exec_summary.get('completed_subtasks', 0),
                       success_rate=f"{exec_summary.get('success_rate', 0):.0%}")
            
            # Show subtask details
            results = data.get('results', [])
            if results:
                logger.task("Subtask execution details", task_id="clean_demo_001")
                for i, subtask_result in enumerate(results, 1):
                    logger.subtask(f"Subtask {i}: {subtask_result.get('subtask', 'Unknown')}",
                                 subtask_id=f"subtask_{i}",
                                 parent_task="clean_demo_001",
                                 tool=subtask_result.get('tool', 'Unknown'),
                                 status=subtask_result.get('status', 'Unknown'))
        
        # Check for report creation
        report_path = workspace / "artifact" / "clean_enhanced_report.md"
        if report_path.exists():
            logger.flow(f"Report successfully created", 
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
        logger.agent(f"Execution failed: {str(e)}", 
                    agent_name=enhanced_agent.name,
                    error=str(e), 
                    level=LogLevel.ERROR)
        import traceback
        traceback.print_exc()
    
    # Final observability summary
    logger.separator("OBSERVABILITY SUMMARY")
    
    # Event monitoring summary  
    monitor.print_execution_summary()
    
    # Export logs
    event_log_file = monitor.export_execution_log()
    flow_log_file = logger.export_log()
    
    logger.flow("Comprehensive logs exported", 
               event_log=event_log_file,
               flow_log=flow_log_file,
               level=LogLevel.SUCCESS)
    
    # Session summary
    logger.session_summary()


if __name__ == "__main__":
    asyncio.run(demo_clean_observability())