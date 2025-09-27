#!/usr/bin/env python3
"""
AgenticFlow Progress UI - Real-time Flow Progress Monitoring
==========================================================

Advanced UI showing real-time progress of multi-agent workflow execution
with live progress bars, step tracking, and agent coordination visualization.
"""

import os
import sys
import time
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import queue

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

# Progress-focused CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .main { font-family: 'Inter', sans-serif; }

    /* Progress header */
    .progress-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }

    /* Flow progress container */
    .flow-progress {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border-left: 5px solid #007bff;
    }

    /* Progress bar */
    .progress-container {
        background: #e9ecef;
        border-radius: 10px;
        height: 30px;
        margin: 1rem 0;
        overflow: hidden;
        position: relative;
    }

    .progress-bar {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        height: 100%;
        transition: width 0.5s ease;
        border-radius: 10px;
        position: relative;
    }

    .progress-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: white;
        font-weight: 600;
        font-size: 0.9em;
    }

    /* Step indicators */
    .step-container {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 0 1rem;
    }

    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        flex: 1;
    }

    .step-circle {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 2;
    }

    .step-pending { background: #6c757d; }
    .step-active {
        background: linear-gradient(135deg, #007bff, #0056b3);
        animation: pulse 2s infinite;
    }
    .step-completed { background: #28a745; }

    .step-line {
        position: absolute;
        top: 25px;
        left: 50%;
        width: 100%;
        height: 3px;
        background: #dee2e6;
        z-index: 1;
    }

    .step-line.completed { background: #28a745; }
    .step-line.active {
        background: linear-gradient(90deg, #28a745 0%, #007bff 100%);
        animation: shimmer 2s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0,123,255,0.7); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(0,123,255,0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0,123,255,0); }
    }

    @keyframes shimmer {
        0% { background-position: -200px 0; }
        100% { background-position: 200px 0; }
    }

    /* Agent status cards */
    .agent-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        border-left: 4px solid;
        transition: all 0.3s ease;
    }

    .agent-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 25px rgba(0,0,0,0.15);
    }

    .agent-filesystem { border-left-color: #fd7e14; }
    .agent-analysis { border-left-color: #20c997; }
    .agent-reporting { border-left-color: #6f42c1; }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-waiting { background: #f8f9fa; color: #6c757d; }
    .status-running { background: #fff3cd; color: #856404; }
    .status-completed { background: #d1edff; color: #0c5460; }

    /* Real-time logs */
    .log-container {
        background: #1a1a1a;
        color: #00ff00;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        max-height: 300px;
        overflow-y: auto;
    }

    .log-entry {
        padding: 0.2rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    .log-timestamp { color: #888; }
    .log-agent { color: #00bfff; }
    .log-action { color: #ffff00; }
    .log-success { color: #00ff00; }
    .log-error { color: #ff4444; }

    /* Metrics dashboard */
    .metrics-grid {
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
        font-size: 2.5rem;
        font-weight: 700;
        color: #007bff;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        color: #6c757d;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="AgenticFlow Progress Monitor",
    page_icon="📊⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for progress tracking
if 'flow' not in st.session_state:
    st.session_state.flow = None
if 'execution_progress' not in st.session_state:
    st.session_state.execution_progress = {
        'active': False,
        'steps': [],
        'current_step': 0,
        'overall_progress': 0,
        'start_time': None,
        'logs': [],
        'agent_status': {}
    }
if 'progress_queue' not in st.session_state:
    st.session_state.progress_queue = queue.Queue()

@st.cache_resource
def create_progress_flow():
    """Create flow with progress monitoring."""
    flow = ObservableFlow()
    flow.add_worker("filesystem", FileSystemWorker(search_root="examples/data"))
    flow.add_worker("analysis", AnalysisWorker())
    flow.add_worker("reporting", ReportingWorker(output_dir="examples/artifact"))

    # Register progress callback
    def progress_callback(event_data):
        timestamp = datetime.now().strftime("%H:%M:%S")

        if event_data["type"] == "flow_start":
            update_progress("flow_started", "Flow execution started", 10)
            add_log(timestamp, "SYSTEM", "Flow started", "success")

        elif event_data["type"] == "agent_activity":
            agent = event_data.get("agent_name", "Unknown")
            activity = event_data.get("activity_type", "unknown")

            if activity == "execution_start":
                update_progress(f"{agent}_started", f"{agent} worker started", None)
                add_log(timestamp, agent.upper(), f"Worker started", "action")

            elif activity == "execution_complete":
                update_progress(f"{agent}_completed", f"{agent} worker completed", None)
                add_log(timestamp, agent.upper(), f"Worker completed", "success")

        elif event_data["type"] == "flow_end":
            success = event_data.get("success", False)
            update_progress("flow_completed", "Flow execution completed", 100)
            status = "success" if success else "error"
            add_log(timestamp, "SYSTEM", f"Flow {'completed' if success else 'failed'}", status)

    observer = flow.get_observer()
    if observer:
        observer.register_callback(progress_callback)

    return flow

def update_progress(step_id, description, progress_pct):
    """Update execution progress."""
    progress = st.session_state.execution_progress

    if not progress['active']:
        progress['active'] = True
        progress['start_time'] = datetime.now()
        progress['steps'] = [
            {"id": "flow_started", "name": "Initialize", "status": "pending"},
            {"id": "filesystem_started", "name": "Filesystem", "status": "pending"},
            {"id": "analysis_started", "name": "Analysis", "status": "pending"},
            {"id": "reporting_started", "name": "Reporting", "status": "pending"},
            {"id": "flow_completed", "name": "Complete", "status": "pending"}
        ]

    # Update step status
    for i, step in enumerate(progress['steps']):
        if step_id.startswith(step['id'].split('_')[0]):
            if step_id.endswith('_started'):
                step['status'] = 'active'
                progress['current_step'] = i
            elif step_id.endswith('_completed') or step_id == 'flow_completed':
                step['status'] = 'completed'
                if i < len(progress['steps']) - 1:
                    progress['current_step'] = i + 1

    if progress_pct is not None:
        progress['overall_progress'] = progress_pct

def add_log(timestamp, agent, action, log_type="normal"):
    """Add log entry."""
    progress = st.session_state.execution_progress
    log_entry = {
        "timestamp": timestamp,
        "agent": agent,
        "action": action,
        "type": log_type
    }
    progress['logs'].append(log_entry)

    # Keep only last 50 logs
    if len(progress['logs']) > 50:
        progress['logs'] = progress['logs'][-50:]

def render_progress_bar(progress_pct):
    """Render beautiful progress bar."""
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {progress_pct}%;">
            <div class="progress-text">{progress_pct:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_step_indicators(steps, current_step):
    """Render step indicators."""
    st.markdown('<div class="step-container">', unsafe_allow_html=True)

    for i, step in enumerate(steps):
        status_class = "step-pending"
        if step['status'] == 'active':
            status_class = "step-active"
        elif step['status'] == 'completed':
            status_class = "step-completed"

        # Step circle
        st.markdown(f"""
        <div class="step">
            <div class="step-circle {status_class}">
                {i + 1}
            </div>
            <div style="text-align: center; font-size: 0.9em; font-weight: 500;">
                {step['name']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Connecting line (except for last step)
        if i < len(steps) - 1:
            line_class = ""
            if i < current_step:
                line_class = "completed"
            elif i == current_step:
                line_class = "active"

            st.markdown(f'<div class="step-line {line_class}"></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def render_agent_progress_card(agent_name, status):
    """Render agent progress card."""
    agent_classes = {
        "filesystem": "agent-filesystem",
        "analysis": "agent-analysis",
        "reporting": "agent-reporting"
    }

    agent_emojis = {
        "filesystem": "📁",
        "analysis": "📊",
        "reporting": "📋"
    }

    status_classes = {
        "pending": "status-waiting",
        "active": "status-running",
        "completed": "status-completed"
    }

    card_class = agent_classes.get(agent_name.lower(), "agent-card")
    emoji = agent_emojis.get(agent_name.lower(), "🤖")
    status_class = status_classes.get(status, "status-waiting")

    st.markdown(f"""
    <div class="agent-card {card_class}">
        <h4>{emoji} {agent_name} Worker</h4>
        <span class="status-badge {status_class}">{status}</span>
        <p style="margin-top: 1rem; color: #6c757d;">
            {agent_name} agent handling specialized tasks
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_live_logs(logs):
    """Render live execution logs."""
    st.markdown('<div class="log-container">', unsafe_allow_html=True)

    for log in logs[-20:]:  # Show last 20 logs
        timestamp = log["timestamp"]
        agent = log["agent"]
        action = log["action"]
        log_type = log["type"]

        type_class = f"log-{log_type}"

        st.markdown(f"""
        <div class="log-entry">
            <span class="log-timestamp">[{timestamp}]</span>
            <span class="log-agent">{agent}:</span>
            <span class="{type_class}">{action}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def execute_with_progress(task):
    """Execute task with progress monitoring."""
    # Reset progress
    st.session_state.execution_progress = {
        'active': True,
        'steps': [],
        'current_step': 0,
        'overall_progress': 0,
        'start_time': datetime.now(),
        'logs': [],
        'agent_status': {}
    }

    # Execute the task
    result = st.session_state.flow.run(task)

    # Mark as completed
    update_progress("flow_completed", "Flow execution completed", 100)

    return result

# Main interface
st.markdown("""
<div class="progress-header">
    <h1>📊⚡ AgenticFlow Progress Monitor</h1>
    <p>Real-time visualization of multi-agent workflow execution progress</p>
</div>
""", unsafe_allow_html=True)

# Initialize flow
if st.session_state.flow is None:
    st.session_state.flow = create_progress_flow()

flow = st.session_state.flow
progress = st.session_state.execution_progress

# Sidebar - Progress Control
with st.sidebar:
    st.markdown("### 🎮 Progress Control")

    # Task input
    task = st.text_area("Enter task:", value="Analyze Q3 2024 business data and generate comprehensive report with insights")

    if st.button("🚀 Execute with Progress Monitoring", key="execute_progress"):
        if task:
            # Execute in thread to allow UI updates
            def run_task():
                return execute_with_progress(task)

            with st.spinner("Executing task with progress monitoring..."):
                result = run_task()

            st.success(f"Task completed! Execution time: {result.get('execution_time_ms', 0):.2f}ms")
            st.rerun()

    # Quick tasks
    st.markdown("#### ⚡ Quick Tasks")

    if st.button("📁 Data Discovery", key="quick_discovery"):
        with st.spinner("Discovering data..."):
            result = execute_with_progress("Find and catalog all available data files")
        st.rerun()

    if st.button("📊 Analytics Run", key="quick_analytics"):
        with st.spinner("Running analytics..."):
            result = execute_with_progress("Perform comprehensive data analysis")
        st.rerun()

    st.markdown("---")

    # Live metrics
    st.markdown("#### 📊 Live Metrics")
    if flow.get_observer():
        status = flow.get_observer().get_real_time_status()

        st.metric("Events", status["metrics"]["total_events"])
        st.metric("Agents", len(status["active_agents"]))

        if progress['active'] and progress['start_time']:
            elapsed = (datetime.now() - progress['start_time']).total_seconds()
            st.metric("Elapsed", f"{elapsed:.1f}s")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📈 Execution Progress")

    if progress['active']:
        # Overall progress bar
        render_progress_bar(progress['overall_progress'])

        # Step indicators
        if progress['steps']:
            render_step_indicators(progress['steps'], progress['current_step'])

        # Execution details
        if progress['start_time']:
            elapsed = (datetime.now() - progress['start_time']).total_seconds()
            st.markdown(f"""
            <div class="flow-progress">
                <h4>🔄 Flow Execution Details</h4>
                <p><strong>Status:</strong> {'In Progress' if progress['overall_progress'] < 100 else 'Completed'}</p>
                <p><strong>Elapsed Time:</strong> {elapsed:.1f} seconds</p>
                <p><strong>Current Step:</strong> {progress['current_step'] + 1} of {len(progress['steps'])}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🚀 Ready to execute tasks with real-time progress monitoring!")
        st.markdown("""
        **Features:**
        - Real-time progress visualization
        - Step-by-step execution tracking
        - Agent status monitoring
        - Live execution logs
        - Performance metrics
        """)

    # Agent progress cards
    st.markdown("### 🤖 Agent Progress")

    if progress['active'] and progress['steps']:
        agents = ["FileSystem", "Analysis", "Reporting"]

        cols = st.columns(3)
        for i, agent in enumerate(agents):
            with cols[i]:
                # Determine agent status from steps
                agent_status = "pending"
                for step in progress['steps']:
                    if agent.lower() in step['id']:
                        agent_status = step['status']
                        break

                render_agent_progress_card(agent, agent_status)

with col2:
    st.markdown("### 📋 Live Execution Logs")

    if progress['logs']:
        render_live_logs(progress['logs'])
    else:
        st.info("Execution logs will appear here during task execution")

    # Real-time metrics
    st.markdown("### 📊 Performance Metrics")

    if flow.get_observer():
        analytics = flow.get_observer().get_flow_analytics()
        performance = analytics['performance']

        st.markdown(f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{performance['total_tool_calls']}</div>
                <div class="metric-label">Tool Calls</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{performance['success_rate']:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tool usage chart
        tool_usage = flow.get_observer().event_tracker.get_tool_usage()
        if tool_usage:
            st.markdown("#### 🔧 Tool Usage")

            tools = list(tool_usage.keys())
            calls = [tool_usage[tool]["call_count"] for tool in tools]

            fig = go.Figure(data=[
                go.Bar(x=tools, y=calls, marker_color='lightblue')
            ])
            fig.update_layout(
                title="Tool Usage Count",
                height=250,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

# Auto-refresh for progress updates
if progress['active']:
    time.sleep(1)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666;">
    <strong>📊⚡ AgenticFlow Progress Monitor</strong><br>
    Real-time multi-agent workflow progress visualization and monitoring
</div>
""", unsafe_allow_html=True)