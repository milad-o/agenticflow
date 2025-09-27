"""
Enterprise Super Agent - Interactive Chat Interface
==================================================

Real-time chat interface with multiple specialized agents for enterprise tasks.
No hardcoded assumptions - fully configurable and intelligent routing.
"""

import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agenticflow import ObservableFlow
from agenticflow.agents.python_repl_agent import PythonREPLAgent
from agenticflow.agents.sql_agent import SQLAgent
from agenticflow.agents.filesystem_enhanced_agent import FileSystemEnhancedAgent
from agenticflow.agents.data_format_agent import DataFormatAgent
from agenticflow.agents.etl_agent import ETLAgent
from agenticflow.agents.web_scraping_agent import WebScrapingAgent

import time
import json
from datetime import datetime
import threading
import queue


def load_env():
    """Load environment variables."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return True
    except ImportError:
        return False


def initialize_enterprise_flow():
    """Initialize the enterprise super agent flow with all specialized agents."""
    if 'enterprise_flow' not in st.session_state:
        flow = ObservableFlow()

        # Add all enterprise agents
        flow.add_worker("python_repl", PythonREPLAgent())
        flow.add_worker("sql_database", SQLAgent())
        flow.add_worker("filesystem", FileSystemEnhancedAgent())
        flow.add_worker("data_format", DataFormatAgent())
        flow.add_worker("etl_pipeline", ETLAgent())
        flow.add_worker("web_scraping", WebScrapingAgent())

        st.session_state.enterprise_flow = flow
        st.session_state.chat_history = []
        st.session_state.agent_status = {}
        st.session_state.system_events = []


def get_agent_capabilities():
    """Get all agent capabilities for display."""
    if 'enterprise_flow' not in st.session_state:
        return {}

    capabilities = {}
    flow = st.session_state.enterprise_flow

    for worker_name, worker in flow.workers.items():
        if hasattr(worker, 'capabilities'):
            capabilities[worker_name] = worker.capabilities
        else:
            capabilities[worker_name] = ["general_tasks"]

    return capabilities


def process_user_input(user_input: str):
    """Process user input and route to appropriate agents."""
    if not user_input.strip():
        return

    # Add user message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })

    # Show thinking indicator
    thinking_placeholder = st.empty()
    thinking_placeholder.markdown("🤔 **Analyzing your request and routing to appropriate agents...**")

    try:
        # Execute the task using the enterprise flow
        flow = st.session_state.enterprise_flow

        # Register a callback to capture real-time events
        events_captured = []

        def capture_event(event_data):
            events_captured.append(event_data)
            st.session_state.system_events.append({
                **event_data,
                "captured_at": datetime.now().isoformat()
            })

        observer = flow.get_observer()
        observer.register_callback(capture_event)

        # Execute the task
        result = flow.run(user_input)

        # Clear thinking indicator
        thinking_placeholder.empty()

        # Add assistant response to chat history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result,
            "timestamp": datetime.now().isoformat(),
            "events": events_captured,
            "workers_used": result.get('workers_used', []),
            "success": result.get('success', False)
        })

        # Update agent status
        for worker_name in result.get('workers_used', []):
            st.session_state.agent_status[worker_name] = {
                "last_used": datetime.now().isoformat(),
                "status": "active"
            }

    except Exception as e:
        thinking_placeholder.empty()
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"❌ Error processing request: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "error": True
        })


def render_chat_message(message, index):
    """Render a chat message with styling."""
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
            st.caption(f"📅 {message['timestamp']}")

    else:  # assistant
        with st.chat_message("assistant"):
            if message.get("error"):
                st.error(message["content"])
            else:
                # Main response
                result = message["content"]
                if isinstance(result, dict):
                    st.success(f"✅ Task completed: {result.get('success', False)}")

                    # Show workers used
                    if result.get('workers_used'):
                        st.markdown("**🤖 Agents Used:**")
                        for worker in result['workers_used']:
                            st.badge(worker, type="secondary")

                    # Show result details
                    if 'result' in result:
                        with st.expander("📊 Detailed Results"):
                            st.json(result['result'])

                    # Show supervisor messages (the main conversation)
                    if result.get('messages'):
                        st.markdown("**💬 Conversation:**")
                        for msg in result['messages']:
                            if isinstance(msg, dict) and msg.get('role') == 'supervisor':
                                st.markdown(f"🤖 **Assistant**: {msg.get('content', '')}")
                            elif isinstance(msg, str) and 'supervisor' in msg.lower():
                                st.markdown(f"🤖 **Assistant**: {msg}")

                else:
                    st.markdown(str(result))

            # Show events in expandable section
            if message.get("events"):
                with st.expander(f"🔍 System Events ({len(message['events'])})"):
                    for event in message["events"]:
                        event_type = event.get("type", "unknown")
                        if event_type == "agent_activity":
                            st.markdown(f"⚡ **{event.get('agent_name')}**: {event.get('activity_type')}")
                        elif event_type == "flow_start":
                            st.markdown(f"🚀 **Flow Started**: {event.get('task')}")
                        elif event_type == "flow_end":
                            st.markdown(f"🏁 **Flow Completed**: {event.get('success')}")
                        else:
                            st.markdown(f"📝 **{event_type}**: {event}")

            st.caption(f"📅 {message['timestamp']}")


def main():
    """Main enterprise chat interface."""
    st.set_page_config(
        page_title="🏢 AgenticFlow Enterprise Super Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Load environment
    load_env()

    # Initialize flow
    initialize_enterprise_flow()

    # Header
    st.title("🏢 AgenticFlow Enterprise Super Agent")
    st.markdown("**Intelligent multi-agent system for enterprise tasks** • Python • SQL • Files • Data • ETL • Web")

    # Sidebar - Agent Status and Capabilities
    with st.sidebar:
        st.header("🤖 Agent Dashboard")

        # Agent capabilities
        st.subheader("Available Agents")
        capabilities = get_agent_capabilities()

        for agent_name, agent_caps in capabilities.items():
            with st.expander(f"🔧 {agent_name.replace('_', ' ').title()}"):
                for cap in agent_caps[:5]:  # Show first 5 capabilities
                    st.markdown(f"• {cap.replace('_', ' ').title()}")
                if len(agent_caps) > 5:
                    st.markdown(f"• ... and {len(agent_caps) - 5} more")

        # Agent Status
        st.subheader("Agent Status")
        for agent_name, status in st.session_state.agent_status.items():
            status_color = "🟢" if status.get("status") == "active" else "⚪"
            st.markdown(f"{status_color} **{agent_name.replace('_', ' ').title()}**")
            st.caption(f"Last used: {status.get('last_used', 'Never')}")

        # System Events
        st.subheader("📡 Recent Events")
        recent_events = st.session_state.system_events[-5:] if st.session_state.system_events else []
        for event in reversed(recent_events):
            event_type = event.get("type", "unknown")
            st.markdown(f"• {event_type}")

        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.agent_status = {}
            st.session_state.system_events = []
            st.rerun()

    # Main chat interface
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("💬 Chat with Enterprise Agents")

        # Chat history
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.chat_history):
                render_chat_message(message, i)

        # Chat input
        user_input = st.chat_input("Ask me to do anything: create files, run code, query databases, process data, scrape web...")

        if user_input:
            process_user_input(user_input)
            st.rerun()

    with col2:
        st.subheader("🎯 Quick Actions")

        # Predefined example tasks
        examples = [
            "Create a folder called 'project_data'",
            "Execute Python: print('Hello Enterprise!')",
            "Create a SQLite database with a users table",
            "Convert this JSON to CSV: {'name': 'test', 'value': 123}",
            "Extract links from https://example.com",
            "List all files in the current directory",
            "Generate sample customer data in JSON format",
            "Create a data pipeline to process CSV files"
        ]

        for example in examples:
            if st.button(example, key=f"example_{hash(example)}", use_container_width=True):
                process_user_input(example)
                st.rerun()

        # System info
        st.subheader("📊 System Info")
        flow = st.session_state.enterprise_flow
        st.metric("Active Agents", len(flow.workers))
        st.metric("Chat Messages", len(st.session_state.chat_history))
        st.metric("System Events", len(st.session_state.system_events))

        # Export chat
        if st.button("💾 Export Chat History"):
            chat_export = {
                "chat_history": st.session_state.chat_history,
                "system_events": st.session_state.system_events,
                "exported_at": datetime.now().isoformat()
            }

            st.download_button(
                label="📥 Download Chat Export",
                data=json.dumps(chat_export, indent=2),
                file_name=f"enterprise_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    # Footer
    st.markdown("---")
    st.markdown("""
    **💡 What can you do?**
    • **File Operations**: Create, read, search, organize files and folders
    • **Code Execution**: Run Python code, install packages, analyze data
    • **Database Tasks**: Create databases, run SQL queries, import/export data
    • **Data Processing**: Convert formats (JSON/XML/CSV), clean and transform data
    • **ETL Pipelines**: Extract, transform, and load data from multiple sources
    • **Web Operations**: Scrape websites, extract data, download content

    **🚀 Examples**: Try natural language like "Create a CSV file with sample sales data" or "Run Python code to calculate fibonacci numbers"
    """)


if __name__ == "__main__":
    main()