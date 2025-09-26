#!/usr/bin/env python3
"""
Enhanced RPAVH Agent Demo

This demo showcases the new Enhanced RPAVH agent that implements your vision:
- True LLM-driven reflection and planning
- DAG-based subtask decomposition with proper dependencies
- Real-time Event Bus integration for orchestrator communication
- Smart verification using both tools and LLM
- Proper completion detection and handoff

Comparison with original RPAVH:
- ✅ Fixed infinite loop issues
- ✅ True DAG planning vs simple keyword matching
- ✅ Event Bus integration for real-time status
- ✅ Smart verification that actually works
- ✅ Comprehensive task handoff with full context
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agenticflow import Flow, FlowConfig
from agenticflow.agent import Agent
from agenticflow.agent.strategies.enhanced_rpavh_agent import EnhancedRPAVHGraphFactory
from agenticflow.core.config import AgentConfig
from agenticflow.agent.roles import AgentRole
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


async def demo_enhanced_rpavh():
    """Demo the Enhanced RPAVH agent."""
    print("=" * 60)
    print("🚀 ENHANCED RPAVH AGENT DEMO")
    print("=" * 60)

    workspace = Path(__file__).parent
    print(f"Workspace: {workspace}")

    # Suppress noisy logs
    try:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("ollama").setLevel(logging.WARNING)
        logging.getLogger().setLevel(logging.WARNING)
    except Exception:
        pass

    # Create flow
    flow = Flow(
        FlowConfig(
            flow_name="EnhancedRPAVHDemo",
            workspace_path=str(workspace),
            max_parallel_tasks=2,
            recursion_limit=15,  # Lower limit to test proper termination
        )
    )
    
    # Setup comprehensive event monitoring
    monitor = EventMonitor(flow.event_bus, flow.reporter)
    print(f"🔍 [SETUP] Event monitoring activated - all system events will be tracked")

    # Install tools
    flow.install_tools_from_repo([
        "find_files",
        "read_text_fast",
        "write_text_atomic",
        "file_stat"
    ])

    # Get LLM
    chat_model, _ = _pick_ollama_models()
    llm = ChatOllama(model=chat_model, temperature=0.1)
    print(f"🤖 Using LLM: {chat_model}")

    # Create Enhanced RPAVH agent using new Brain + Body pattern
    agent_config = AgentConfig(
        name="enhanced_csv_agent",
        model=chat_model,
        temperature=0.1,
        role=AgentRole.FILE_MANAGER  # CSV file analysis role
    )

    # Create enhanced brain (graph) using factory
    factory = EnhancedRPAVHGraphFactory(
        use_llm_for_planning=True,
        use_llm_for_verification=True,
        max_parallel_tasks=3,
        max_retries=2
    )
    enhanced_graph = factory.create_graph()
    
    # Create agent with enhanced brain
    enhanced_agent = Agent(
        config=agent_config,
        model=llm,
        tools=flow.tool_registry.get_all_tools(),
        max_attempts=2,
        custom_graph=enhanced_graph
    )
    
    # Connect agent to flow's event bus and reporter
    enhanced_agent._flow_ref = flow
    enhanced_agent.event_bus = flow.event_bus
    enhanced_agent.reporter = flow.reporter

    print(f"✅ Enhanced RPAVH Agent created with {len(enhanced_agent.tools)} tools")
    print(f"🧠 Brain: Enhanced RPAVH Graph (DAG-based execution)")
    print(f"🤖 Body: File Manager Agent with specialized tools")
    print(f"🔗 Integration: Brain plugged into Body via custom_graph")

    # Create sample data if not exists
    print("\n📁 Preparing sample data...")
    data_dir = workspace / "data" / "csv"
    data_dir.mkdir(parents=True, exist_ok=True)
    
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
            print(f"💾 Created: {filename}")
        else:
            print(f"✅ Exists: {filename}")
    
    # Ensure artifact directory exists
    artifact_dir = workspace / "artifact"
    artifact_dir.mkdir(exist_ok=True)

    # Test the enhanced agent directly
    request = """Find CSV files in data/csv directory, read their content to understand the structure,
    and write a comprehensive analysis report to artifact/enhanced_analysis_report.md"""

    print(f"\n📋 Request: {request}")
    print("\n🎆 BRAIN + BODY ARCHITECTURE DEMONSTRATION")
    print("🧠 Brain (Enhanced RPAVH): Will decompose this into DAG subtasks")
    print("🤖 Body (File Manager): Will execute with file operation tools")
    print("🔗 Integration: Brain controls flow, Body provides capabilities")
    print("\n🔄 Executing Enhanced Agent...")

    try:
        start_time = asyncio.get_event_loop().time()

        # Execute the enhanced agent
        print(f"🔍 Debug: Enhanced agent tools: {[t.name for t in enhanced_agent.tools]}")
        print(f"🔍 Debug: Graph type: {type(enhanced_agent.compiled_graph)}")
        
        result = await enhanced_agent.arun(request)
        
        print(f"🔍 Debug: Full result structure: {result.keys()}")
        for key, value in result.items():
            if key != 'message':  # Don't repeat the message
                print(f"   {key}: {type(value)} = {str(value)[:100]}...")

        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time

        # Display results
        print("\n" + "=" * 60)
        print("📊 ENHANCED RPAVH RESULTS")
        print("=" * 60)

        print(f"✅ Success: {result.get('success', False)}")
        print(f"⏱️ Execution Time: {execution_time:.2f}s")
        print(f"📝 Final Response: {result.get('message', 'No message')}")
        print(f"🤖 Agent Name: {result.get('agent_name', 'Unknown')}")
        
        # Get metadata if available
        metadata = result.get('metadata', {})
        if metadata:
            print(f"🔄 Execution Metadata:")
            for key, value in metadata.items():
                print(f"   - {key}: {value}")

        # Show execution summary
        if result.get('data', {}).get('execution_summary'):
            summary = result['data']['execution_summary']
            print(f"📈 Execution Summary:")
            print(f"   - Total Subtasks: {summary.get('total_subtasks', 0)}")
            print(f"   - Completed: {summary.get('completed_subtasks', 0)}")
            print(f"   - Success Rate: {summary.get('success_rate', 0):.0%}")

        # Show subtask results
        if result.get('data', {}).get('results'):
            print(f"\n🔧 Subtask Results:")
            for i, task_result in enumerate(result['data']['results'], 1):
                print(f"   {i}. {task_result.get('subtask', 'Unknown')}")
                print(f"      Tool: {task_result.get('tool', 'Unknown')}")
                exec_time = task_result.get('execution_time')
                if exec_time:
                    print(f"      Time: {exec_time:.2f}s")

        # Check if report was created
        report_path = workspace / "artifact" / "enhanced_analysis_report.md"
        if report_path.exists():
            print(f"\n📄 Report created: {report_path}")
            with open(report_path, 'r') as f:
                content = f.read()
                preview = content[:300] + "..." if len(content) > 300 else content
                print(f"\n📖 Report Preview:")
                print("-" * 40)
                print(preview)
                print("-" * 40)
        else:
            print(f"\n⚠️ Report not found at: {report_path}")

        # Show verification details
        if result.get('data', {}).get('verification'):
            verification = result['data']['verification']
            print(f"\n🔍 Verification Details:")
            if 'heuristic_check' in verification:
                print(f"   - Heuristic Check: {'✅ PASSED' if verification['heuristic_check'] else '❌ FAILED'}")
            if 'llm_check' in verification:
                llm_check = verification['llm_check']
                if llm_check.get('passed') is not None:
                    status = '✅ PASSED' if llm_check['passed'] else '❌ FAILED'
                    print(f"   - LLM Check: {status}")
                    if llm_check.get('response'):
                        print(f"   - LLM Response: {llm_check['response'][:100]}...")

    except Exception as e:
        print(f"\n❌ Enhanced RPAVH execution failed: {e}")
        import traceback
        traceback.print_exc()

    # Print comprehensive execution summary from event monitor
    monitor.print_execution_summary()
    
    # Export detailed execution log
    log_file = monitor.export_execution_log()
    if log_file:
        print(f"📄 Detailed execution log saved: {log_file}")
    
    print("\n" + "=" * 60)
    print("🎯 ENHANCED RPAVH DEMO COMPLETE")
    print("=" * 60)

    # Show key improvements
    print("\n🔥 Key Improvements Over Original RPAVH:")
    print("✅ True LLM-driven reflection and planning")
    print("✅ DAG-based subtask decomposition with dependencies")
    print("✅ Real-time Event Bus integration")
    print("✅ Smart verification with both heuristics and LLM")
    print("✅ Fixed infinite loop issues")
    print("✅ Comprehensive task handoff with full context")
    print("✅ Proper completion detection")


if __name__ == "__main__":
    asyncio.run(demo_enhanced_rpavh())