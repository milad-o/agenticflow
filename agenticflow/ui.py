#!/usr/bin/env python3
"""
AgenticFlow UI - Main Unified Monitoring Interface
=================================================

The primary Streamlit interface for AgenticFlow multi-agent workflow monitoring.
Combines the best features from all specialized UIs into one comprehensive dashboard.
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to path
sys.path.insert(0, os.getcwd())

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from agenticflow import ObservableFlow
from agenticflow.agents import FileSystemWorker, AnalysisWorker, ReportingWorker


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value


load_env()

# Enhanced CSS for the unified interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .main { font-family: 'Inter', sans-serif; }

    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }

    /* Status cards */
    .status-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        border-left: 4px solid;
        transition: all 0.3s ease;
    }

    .status-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 25px rgba(0,0,0,0.15);
    }

    .card-flow { border-left-color: #007bff; }
    .card-agent { border-left-color: #28a745; }
    .card-tool { border-left-color: #17a2b8; }
    .card-performance { border-left-color: #ffc107; }

    /* Progress elements */
    .progress-container {
        background: #e9ecef;
        border-radius: 10px;
        height: 8px;
        margin: 0.5rem 0;
        overflow: hidden;
    }

    .progress-bar {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        height: 100%;
        transition: width 0.5s ease;
        border-radius: 10px;
    }

    /* Status indicators */
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }

    .status-active { background: #28a745; animation: pulse 2s infinite; }
    .status-idle { background: #6c757d; }
    .status-error { background: #dc3545; }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    /* Event stream */
    .event-stream {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #dee2e6;
    }

    .event-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        background: white;
        border-radius: 5px;
        border-left: 3px solid #007bff;
        font-size: 0.9em;
    }

    /* Chat messages */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 80%;
    }

    .user-message {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
        margin-left: auto;
        border-radius: 15px 15px 5px 15px;
    }

    .agent-message {
        background: linear-gradient(135deg, #28a745, #1e7e34);
        color: white;
        border-radius: 15px 15px 15px 5px;
    }

    .system-message {
        background: #6c757d;
        color: white;
        text-align: center;
        border-radius: 15px;
        margin: 0.5rem auto;
        max-width: 60%;
    }

    /* Metrics grid */
    .metrics-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #007bff;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        color: #6c757d;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="AgenticFlow Observatory",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'flow' not in st.session_state:
    st.session_state.flow = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def create_main_flow():
    """Create the main observable flow."""
    flow = ObservableFlow()
    flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
    flow.add_worker("analysis", AnalysisWorker())
    flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))
    return flow

def format_timestamp(timestamp):
    """Format timestamp for display."""
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        except:
            return timestamp[:8]
    return datetime.now().strftime("%H:%M:%S")

def render_status_card(title, icon, content, card_type="flow"):
    """Render a beautiful status card."""
    st.markdown(f"""
    <div class="status-card card-{card_type}">
        <h4>{icon} {title}</h4>
        {content}
    </div>
    """, unsafe_allow_html=True)

def render_chat_message(message, sender, timestamp):
    """Render a chat message bubble."""
    time_str = format_timestamp(timestamp)

    if sender == "User":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 You</strong> <small style="opacity: 0.8;">• {time_str}</small><br>
            {message}
        </div>
        """, unsafe_allow_html=True)
    elif sender == "System":
        st.markdown(f"""
        <div class="chat-message system-message">
            <strong>⚙️ System</strong> • {time_str} • {message}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message agent-message">
            <strong>🤖 {sender}</strong> <small style="opacity: 0.8;">• {time_str}</small><br>
            {message}
        </div>
        """, unsafe_allow_html=True)

# Main interface
st.markdown("""
<div class="main-header">
    <h1>🤖 AgenticFlow Observatory</h1>
    <p>Comprehensive real-time monitoring for multi-agent workflows</p>
</div>
""", unsafe_allow_html=True)

# Initialize flow
if st.session_state.flow is None:
    st.session_state.flow = create_main_flow()

flow = st.session_state.flow
observer = flow.get_observer()

# Sidebar - Control Panel
with st.sidebar:
    st.markdown("### 🎮 Control Center")

    # Task execution
    st.markdown("#### 🚀 Execute Tasks")
    task_input = st.text_area("Enter your task:", placeholder="e.g., 'Analyze Q3 data and create business report'")

    if st.button("Execute Task", key="main_execute") and task_input:
        # Add to messages
        st.session_state.messages.append({
            "message": task_input,
            "sender": "User",
            "timestamp": datetime.now().isoformat()
        })

        with st.spinner("Executing task..."):
            result = flow.run(task_input)

        # Add result message
        success_msg = "✅ Task completed successfully!" if result["success"] else "❌ Task failed"
        details = f"Workers: {', '.join(result.get('workers_used', []))} | Time: {result.get('execution_time_ms', 0):.2f}ms"

        st.session_state.messages.append({
            "message": f"{success_msg} - {details}",
            "sender": "System",
            "timestamp": datetime.now().isoformat()
        })

        st.rerun()

    # Quick actions
    st.markdown("#### ⚡ Quick Actions")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Find Files", key="quick_files"):
            with st.spinner("Finding files..."):
                result = flow.run("Find all data files and list their contents")
            st.session_state.messages.append({
                "message": f"Found {len(result.get('results', {}).get('filesystem', {}).get('files', []))} files",
                "sender": "System",
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()

    with col2:
        if st.button("📊 Analyze", key="quick_analyze"):
            with st.spinner("Analyzing..."):
                result = flow.run("Perform comprehensive data analysis")
            st.session_state.messages.append({
                "message": f"Analysis complete - {', '.join(result.get('workers_used', []))} workers used",
                "sender": "System",
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()

    if st.button("📋 Generate Report", key="quick_report"):
        with st.spinner("Generating report..."):
            result = flow.run("Generate comprehensive business report")
        report_path = result.get('results', {}).get('reporting', {}).get('filepath', 'Report generated')
        st.session_state.messages.append({
            "message": f"Report ready: {report_path}",
            "sender": "System",
            "timestamp": datetime.now().isoformat()
        })
        st.rerun()

    st.markdown("---")

    # Settings
    st.markdown("#### ⚙️ Settings")
    auto_refresh = st.checkbox("Auto Refresh", value=True)
    if auto_refresh:
        refresh_interval = st.slider("Refresh Rate (seconds)", 1, 10, 3)

    # Data management
    st.markdown("#### 📁 Data")
    if st.button("Export Events"):
        filename = flow.export_observability_data()
        st.success(f"Exported: {filename}")

    if st.button("Clear History"):
        st.session_state.messages = []
        flow.get_event_tracker().clear_events()
        st.success("History cleared")

# Main content - Three column layout
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown("### 📊 System Overview")

    if observer:
        status = observer.get_real_time_status()
        analytics = observer.get_flow_analytics()

        # Flow status card
        flow_state = status["flow_state"]
        flow_status = flow_state.get("status", "idle")
        current_task = flow_state.get("current_task", "No active task")

        render_status_card(
            "Flow Status",
            "🌊",
            f"""
            <p><span class="status-dot status-{flow_status}"></span><strong>Status:</strong> {flow_status.title()}</p>
            <p><strong>Current Task:</strong> {current_task[:50]}{'...' if len(current_task) > 50 else ''}</p>
            <p><strong>Workers:</strong> {len(flow_state.get('workers', []))}</p>
            """,
            "flow"
        )

        # Performance metrics
        performance = analytics["performance"]
        render_status_card(
            "Performance",
            "⚡",
            f"""
            <div class="metrics-container">
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 600; color: #28a745;">{performance['success_rate']:.1f}%</div>
                    <div style="font-size: 0.8rem; color: #6c757d;">SUCCESS RATE</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 600; color: #007bff;">{performance['total_tool_calls']}</div>
                    <div style="font-size: 0.8rem; color: #6c757d;">TOOL CALLS</div>
                </div>
            </div>
            """,
            "performance"
        )

with col2:
    st.markdown("### 🤖 Agent Monitor")

    if observer:
        status = observer.get_real_time_status()

        # Agent status cards
        active_agents = status["active_agents"]
        if active_agents:
            for agent_name, agent_data in active_agents.items():
                agent_status = agent_data.get("status", "idle")
                tool_calls = agent_data.get("tool_calls", 0)
                errors = agent_data.get("errors", 0)

                # Calculate success rate
                success_rate = ((tool_calls - errors) / tool_calls * 100) if tool_calls > 0 else 100

                agent_emoji = {
                    "filesystem": "📁",
                    "analysis": "📊",
                    "reporting": "📋"
                }.get(agent_name.lower(), "🤖")

                render_status_card(
                    f"{agent_name}",
                    agent_emoji,
                    f"""
                    <p><span class="status-dot status-{agent_status}"></span><strong>Status:</strong> {agent_status.title()}</p>
                    <div style="margin: 0.5rem 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>Tool Calls: {tool_calls}</span>
                            <span>Errors: {errors}</span>
                        </div>
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {success_rate}%;"></div>
                        </div>
                        <small>Success Rate: {success_rate:.1f}%</small>
                    </div>
                    """,
                    "agent"
                )

                # Show recent activities
                activities = agent_data.get("activities", [])
                if activities:
                    st.markdown("**Recent Activities:**")
                    for activity in activities[-3:]:
                        timestamp = format_timestamp(activity.get("timestamp", ""))
                        activity_type = activity.get("type", "unknown")
                        st.text(f"[{timestamp}] {activity_type}")
        else:
            st.info("No active agents - execute a task to see agent activity")

with col3:
    st.markdown("### 🔧 Tools & Events")

    if observer:
        # Tool usage
        tool_usage = observer.event_tracker.get_tool_usage()
        if tool_usage:
            render_status_card(
                "Tool Usage",
                "🔧",
                f"""
                <div style="max-height: 200px; overflow-y: auto;">
                    {''.join([
                        f'''
                        <div style="margin: 0.5rem 0;">
                            <div style="display: flex; justify-content: space-between;">
                                <strong>{tool}</strong>
                                <span>{data["call_count"]} calls</span>
                            </div>
                            <div class="progress-container">
                                <div class="progress-bar" style="width: {(data['success_count']/data['call_count']*100) if data['call_count'] > 0 else 0}%;"></div>
                            </div>
                            <small>Success: {(data['success_count']/data['call_count']*100) if data['call_count'] > 0 else 0:.1f}%</small>
                        </div>
                        '''
                        for tool, data in tool_usage.items()
                    ])}
                </div>
                """,
                "tool"
            )

        # Recent events
        events = observer.event_tracker.get_events(limit=8)
        if events:
            st.markdown("**📡 Recent Events**")
            st.markdown('<div class="event-stream">', unsafe_allow_html=True)

            for event in reversed(events):
                event_data = event.to_dict()
                timestamp = format_timestamp(event_data.get("timestamp", ""))
                event_type = event_data.get("event_type", "unknown").replace('_', ' ').title()
                source = event_data.get("source", "system")

                st.markdown(f"""
                <div class="event-item">
                    <strong>[{timestamp}]</strong> {event_type}<br>
                    <small style="color: #666;">Source: {source}</small>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

# Chat section at the bottom
st.markdown("### 💬 Conversation History")

if st.session_state.messages:
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages[-10:]:  # Show last 10 messages
            render_chat_message(
                msg["message"],
                msg["sender"],
                msg["timestamp"]
            )
else:
    st.info("💡 Execute a task above to start a conversation with your agents!")

# Tool usage chart
if observer:
    tool_usage = observer.event_tracker.get_tool_usage()
    if tool_usage:
        st.markdown("### 📈 Tool Usage Analytics")

        # Create tool usage chart
        tools = list(tool_usage.keys())
        calls = [tool_usage[tool]["call_count"] for tool in tools]
        success_rates = [(tool_usage[tool]["success_count"]/tool_usage[tool]["call_count"]*100) if tool_usage[tool]["call_count"] > 0 else 0 for tool in tools]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Tool Calls',
            x=tools,
            y=calls,
            marker_color='lightblue'
        ))

        fig.update_layout(
            title="Tool Usage Overview",
            xaxis_title="Tools",
            yaxis_title="Call Count",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666;">
    <strong>🤖 AgenticFlow Observatory</strong> - Real-time multi-agent workflow monitoring<br>
    <small>Built with Streamlit • Powered by LangGraph • Enhanced with Observability</small>
</div>
""", unsafe_allow_html=True)