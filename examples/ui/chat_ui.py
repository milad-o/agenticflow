#!/usr/bin/env python3
"""
AgenticFlow Chat UI - Beautiful Interactive Chat Interface
=========================================================

A beautiful chat-style interface for monitoring AgenticFlow executions
with dedicated panes for agents, supervisor, and tools.
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
from plotly.subplots import make_subplots
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

# Custom CSS for beautiful styling
st.markdown("""
<style>
    /* Main app styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Chat container */
    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #007bff;
    }

    /* Agent panes */
    .agent-pane {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }

    .supervisor-pane {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }

    .tool-pane {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }

    /* Message bubbles */
    .user-message {
        background: #007bff;
        color: white;
        padding: 1rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        margin-left: 20%;
    }

    .agent-message {
        background: #28a745;
        color: white;
        padding: 1rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        margin-right: 20%;
    }

    .supervisor-message {
        background: #6f42c1;
        color: white;
        padding: 1rem;
        border-radius: 18px;
        margin: 0.5rem 0;
        margin-left: 10%;
        margin-right: 10%;
    }

    .system-message {
        background: #6c757d;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        margin: 0.3rem 0;
        font-size: 0.9em;
        text-align: center;
    }

    /* Status indicators */
    .status-running {
        color: #28a745;
        animation: pulse 2s infinite;
    }

    .status-idle { color: #6c757d; }
    .status-error { color: #dc3545; }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    /* Tool usage bars */
    .tool-bar {
        background: #e9ecef;
        height: 20px;
        border-radius: 10px;
        margin: 0.2rem 0;
        overflow: hidden;
    }

    .tool-progress {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        height: 100%;
        transition: width 0.3s ease;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="AgenticFlow Chat Observatory",
    page_icon="🤖💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'flow' not in st.session_state:
    st.session_state.flow = None
if 'execution_active' not in st.session_state:
    st.session_state.execution_active = False
if 'last_events_count' not in st.session_state:
    st.session_state.last_events_count = 0

@st.cache_resource
def create_observable_flow():
    """Create and cache the observable flow."""
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

def render_message_bubble(content, sender, timestamp=None, message_type="normal"):
    """Render a beautiful message bubble."""
    time_str = format_timestamp(timestamp) if timestamp else datetime.now().strftime("%H:%M:%S")

    if sender == "User":
        st.markdown(f"""
        <div class="user-message">
            <strong>👤 You</strong> <small style="opacity: 0.8;">• {time_str}</small><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    elif sender == "Supervisor":
        st.markdown(f"""
        <div class="supervisor-message">
            <strong>🎯 Supervisor</strong> <small style="opacity: 0.8;">• {time_str}</small><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    elif "Worker" in sender or "Agent" in sender:
        st.markdown(f"""
        <div class="agent-message">
            <strong>🤖 {sender}</strong> <small style="opacity: 0.8;">• {time_str}</small><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="system-message">
            <strong>⚙️ {sender}</strong> • {time_str} • {content}
        </div>
        """, unsafe_allow_html=True)

def render_agent_pane(agent_name, agent_data, expanded=True):
    """Render a beautiful agent status pane."""
    status = agent_data.get("status", "idle")
    tool_calls = agent_data.get("tool_calls", 0)
    errors = agent_data.get("errors", 0)

    status_class = f"status-{status}" if status in ["running", "idle", "error"] else "status-idle"

    with st.expander(f"🤖 Agent: {agent_name}", expanded=expanded):
        st.markdown(f"""
        <div class="agent-pane">
            <h4>🤖 {agent_name}</h4>
            <p><strong>Status:</strong> <span class="{status_class}">●</span> {status.title()}</p>
            <p><strong>Tool Calls:</strong> {tool_calls} | <strong>Errors:</strong> {errors}</p>
        </div>
        """, unsafe_allow_html=True)

        # Recent activities
        activities = agent_data.get("activities", [])
        if activities:
            st.write("**Recent Activities:**")
            for activity in activities[-3:]:  # Show last 3
                activity_time = format_timestamp(activity.get("timestamp", ""))
                activity_type = activity.get("type", "unknown")
                st.text(f"[{activity_time}] {activity_type}")

        # Agent reflection
        reflection = agent_data.get("reflection", {})
        if reflection:
            st.write("**💭 Agent Reflection:**")
            st.json(reflection, expanded=False)

def render_tool_usage_pane(tool_usage):
    """Render beautiful tool usage visualization."""
    st.markdown("""
    <div class="tool-pane">
        <h4>🔧 Tool Usage Analytics</h4>
    </div>
    """, unsafe_allow_html=True)

    if tool_usage:
        # Create tool usage chart
        tools = list(tool_usage.keys())
        calls = [tool_usage[tool]["call_count"] for tool in tools]
        success_rates = [
            (tool_usage[tool]["success_count"] / tool_usage[tool]["call_count"] * 100)
            if tool_usage[tool]["call_count"] > 0 else 0
            for tool in tools
        ]

        # Bar chart for tool calls
        fig = go.Figure(data=[
            go.Bar(name='Tool Calls', x=tools, y=calls, marker_color='lightblue'),
        ])
        fig.update_layout(
            title="Tool Usage Count",
            xaxis_title="Tools",
            yaxis_title="Call Count",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

        # Success rate indicators
        st.write("**Success Rates:**")
        for tool, rate in zip(tools, success_rates):
            st.markdown(f"""
            <div style="margin: 0.5rem 0;">
                <strong>{tool}:</strong> {rate:.1f}%
                <div class="tool-bar">
                    <div class="tool-progress" style="width: {rate}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No tool usage data available yet")

def render_supervisor_pane(flow_state):
    """Render supervisor status pane."""
    st.markdown(f"""
    <div class="supervisor-pane">
        <h4>🎯 Supervisor Status</h4>
        <p><strong>Current Task:</strong> {flow_state.get('current_task', 'No active task')[:50]}...</p>
        <p><strong>Workers:</strong> {len(flow_state.get('workers', []))} active</p>
        <p><strong>Status:</strong> {flow_state.get('status', 'idle').title()}</p>
    </div>
    """, unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🤖💬 AgenticFlow Chat Observatory</h1>
    <p>Interactive chat interface for real-time multi-agent monitoring</p>
</div>
""", unsafe_allow_html=True)

# Initialize flow
if st.session_state.flow is None:
    st.session_state.flow = create_observable_flow()

flow = st.session_state.flow
observer = flow.get_observer()

# Sidebar - Control Panel
with st.sidebar:
    st.markdown("### 🎮 Control Panel")

    # Quick actions
    st.markdown("#### Quick Tasks")

    if st.button("🔍 Find Data Files", key="find_files"):
        task = "Find and list all CSV files in the data directory"
        st.session_state.messages.append({
            "content": task,
            "sender": "User",
            "timestamp": datetime.now().isoformat()
        })

        with st.spinner("Executing..."):
            result = flow.run(task)

        st.session_state.messages.append({
            "content": f"Found {len(result.get('results', {}).get('filesystem', {}).get('files', []))} files. Task completed in {result.get('execution_time_ms', 0):.2f}ms",
            "sender": "System",
            "timestamp": datetime.now().isoformat()
        })
        st.rerun()

    if st.button("📊 Analyze Data", key="analyze_data"):
        task = "Analyze all CSV files and identify patterns and trends"
        st.session_state.messages.append({
            "content": task,
            "sender": "User",
            "timestamp": datetime.now().isoformat()
        })

        with st.spinner("Analyzing..."):
            result = flow.run(task)

        st.session_state.messages.append({
            "content": f"Analysis complete! Workers used: {', '.join(result.get('workers_used', []))}. Execution time: {result.get('execution_time_ms', 0):.2f}ms",
            "sender": "System",
            "timestamp": datetime.now().isoformat()
        })
        st.rerun()

    if st.button("📋 Generate Report", key="generate_report"):
        task = "Generate comprehensive business report with insights from all available data"
        st.session_state.messages.append({
            "content": task,
            "sender": "User",
            "timestamp": datetime.now().isoformat()
        })

        with st.spinner("Generating report..."):
            result = flow.run(task)

        report_path = result.get('results', {}).get('reporting', {}).get('filepath', 'Unknown')
        st.session_state.messages.append({
            "content": f"Report generated successfully! File: {report_path}. Task completed in {result.get('execution_time_ms', 0):.2f}ms",
            "sender": "System",
            "timestamp": datetime.now().isoformat()
        })
        st.rerun()

    st.markdown("---")

    # Settings
    st.markdown("#### ⚙️ Settings")
    auto_refresh = st.checkbox("Auto Refresh", value=True)
    refresh_interval = st.slider("Refresh Rate (seconds)", 1, 10, 3)

    # Stats
    st.markdown("#### 📊 Live Stats")
    if observer:
        status = observer.get_real_time_status()
        st.metric("Events", status["metrics"]["total_events"])
        st.metric("Active Agents", len(status["active_agents"]))

        analytics = observer.get_flow_analytics()
        st.metric("Success Rate", f"{analytics['performance']['success_rate']:.1f}%")

# Main content area - 3 columns
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.markdown("### 💬 Chat & Messages")

    # Chat input
    user_input = st.text_input("Enter your task:", placeholder="e.g., 'Analyze sales data and create report'")

    if st.button("Send", key="send_task") and user_input:
        # Add user message
        st.session_state.messages.append({
            "content": user_input,
            "sender": "User",
            "timestamp": datetime.now().isoformat()
        })

        # Execute task
        with st.spinner("Processing..."):
            result = flow.run(user_input)

        # Add system response
        success_msg = "✅ Task completed successfully!" if result["success"] else "❌ Task failed"
        details = f"Workers: {', '.join(result.get('workers_used', []))} | Time: {result.get('execution_time_ms', 0):.2f}ms"

        st.session_state.messages.append({
            "content": f"{success_msg}<br><small>{details}</small>",
            "sender": "System",
            "timestamp": datetime.now().isoformat()
        })

        st.rerun()

    # Display chat messages
    st.markdown("#### Message History")
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages[-10:]:  # Show last 10 messages
            render_message_bubble(
                message["content"],
                message["sender"],
                message["timestamp"]
            )

with col2:
    st.markdown("### 🤖 Agent Monitor")

    if observer:
        status = observer.get_real_time_status()

        # Supervisor pane
        render_supervisor_pane(status["flow_state"])

        # Agent panes
        for agent_name, agent_data in status["active_agents"].items():
            render_agent_pane(agent_name, agent_data, expanded=False)

        if not status["active_agents"]:
            st.info("No active agents - start a task to see agent activity")

with col3:
    st.markdown("### 🔧 Tools & Analytics")

    if observer:
        tool_usage = observer.event_tracker.get_tool_usage()
        render_tool_usage_pane(tool_usage)

        # Recent events
        st.markdown("#### 📡 Recent Events")
        events = observer.event_tracker.get_events(limit=5)

        for event in reversed(events):
            event_data = event.to_dict()
            event_time = format_timestamp(event_data.get("timestamp", ""))
            event_type = event_data.get("event_type", "unknown")
            source = event_data.get("source", "system")

            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 0.5rem; margin: 0.2rem 0; border-radius: 5px; font-size: 0.8em;">
                <strong>{event_time}</strong><br>
                {event_type} • {source}
            </div>
            """, unsafe_allow_html=True)

# Auto-refresh functionality
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("**AgenticFlow Chat Observatory** - Real-time multi-agent workflow monitoring with beautiful UI")