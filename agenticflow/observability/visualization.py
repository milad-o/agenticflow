"""
Streamlit Visualization Module
=============================

Rich UI components for real-time AgenticFlow monitoring and visualization.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import time
from .observer import FlowObserver
from .event_tracker import EventTracker, EventType
from .metrics import MetricsCollector


def create_flow_visualizer(observer: FlowObserver) -> None:
    """Create the main Streamlit UI for flow visualization."""
    st.set_page_config(
        page_title="AgenticFlow Observatory",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .agent-card {
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #ffffff;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .event-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 0.25rem;
        border-left: 3px solid #ff7f0e;
    }
    .status-active { color: #2ca02c; }
    .status-idle { color: #d62728; }
    .status-running { color: #ff7f0e; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("🤖 AgenticFlow Observatory")
    st.markdown("**Real-time monitoring and visualization of multi-agent workflows**")

    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Observatory Controls")

        # Auto-refresh controls
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        refresh_interval = st.slider("Refresh Interval (seconds)", 1, 10, 3)

        # View options
        st.subheader("📊 View Options")
        show_events = st.checkbox("Show Event Stream", value=True)
        show_metrics = st.checkbox("Show Metrics", value=True)
        show_agents = st.checkbox("Show Agent Details", value=True)
        show_tools = st.checkbox("Show Tool Usage", value=True)

        # Export options
        st.subheader("📁 Export")
        if st.button("Export Events"):
            filename = observer.event_tracker.export_events()
            st.success(f"Events exported to {filename}")

        if st.button("Clear Events"):
            observer.event_tracker.clear_events()
            st.success("Events cleared")

    # Main content area
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

    # Get current status
    status = observer.get_real_time_status()
    analytics = observer.get_flow_analytics()

    # Overview metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Flow Status",
            status["flow_state"]["status"].title(),
            delta=None
        )

    with col2:
        st.metric(
            "Active Agents",
            len(status["active_agents"]),
            delta=None
        )

    with col3:
        st.metric(
            "Total Events",
            status["metrics"]["total_events"],
            delta=None
        )

    with col4:
        success_rate = analytics["performance"]["success_rate"]
        st.metric(
            "Success Rate",
            f"{success_rate:.1f}%",
            delta=None
        )

    # Flow state overview
    st.header("🌊 Flow State Overview")

    flow_state = status["flow_state"]
    if flow_state["status"] != "idle":
        with st.container():
            st.markdown(f"""
            <div class="metric-container">
            <h4>Current Task</h4>
            <p>{flow_state.get('current_task', 'No active task')}</p>
            <p><strong>Workers:</strong> {', '.join(flow_state.get('workers', []))}</p>
            <p><strong>Status:</strong> <span class="status-{flow_state['status']}">{flow_state['status'].title()}</span></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active flow - system is idle")

    # Agent details section
    if show_agents and status["active_agents"]:
        st.header("👥 Agent Activity")

        # Agent overview cards
        for agent_name, agent_data in status["active_agents"].items():
            with st.expander(f"🤖 {agent_name}", expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Tool Calls", agent_data.get("tool_calls", 0))

                with col2:
                    st.metric("Errors", agent_data.get("errors", 0))

                with col3:
                    status_val = agent_data.get("status", "unknown")
                    st.metric("Status", status_val.title())

                # Agent reflection
                if "reflection" in agent_data:
                    st.subheader("💭 Agent Reflection")
                    st.json(agent_data["reflection"])

                # Recent activities
                activities = agent_data.get("activities", [])
                if activities:
                    st.subheader("📋 Recent Activities")
                    for activity in activities[-5:]:  # Show last 5 activities
                        timestamp = activity["timestamp"].strftime("%H:%M:%S")
                        st.text(f"[{timestamp}] {activity['type']}: {activity.get('details', {})}")

    # Tool usage section
    if show_tools:
        st.header("🔧 Tool Usage Analytics")

        tool_usage = observer.event_tracker.get_tool_usage()
        if tool_usage:
            # Create tool usage chart
            tool_names = list(tool_usage.keys())
            call_counts = [tool_usage[tool]["call_count"] for tool in tool_names]
            success_counts = [tool_usage[tool]["success_count"] for tool in tool_names]
            error_counts = [tool_usage[tool]["error_count"] for tool in tool_names]

            fig = go.Figure(data=[
                go.Bar(name='Successful', x=tool_names, y=success_counts, marker_color='lightgreen'),
                go.Bar(name='Errors', x=tool_names, y=error_counts, marker_color='lightcoral')
            ])
            fig.update_layout(
                title="Tool Usage Statistics",
                xaxis_title="Tools",
                yaxis_title="Call Count",
                barmode='stack'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tool details table
            tool_df = pd.DataFrame([
                {
                    "Tool": tool,
                    "Total Calls": data["call_count"],
                    "Success": data["success_count"],
                    "Errors": data["error_count"],
                    "Success Rate": f"{(data['success_count']/data['call_count']*100):.1f}%" if data["call_count"] > 0 else "0%",
                    "Agents Using": ", ".join(data["agents_using"])
                }
                for tool, data in tool_usage.items()
            ])
            st.dataframe(tool_df, use_container_width=True)
        else:
            st.info("No tool usage data available")

    # Event stream section
    if show_events:
        st.header("📡 Live Event Stream")

        events = status["recent_events"]
        if events:
            # Event timeline
            event_df = pd.DataFrame(events)
            if not event_df.empty:
                # Convert timestamp to datetime
                event_df['timestamp'] = pd.to_datetime(event_df['timestamp'])

                # Create timeline chart
                fig = px.scatter(
                    event_df,
                    x='timestamp',
                    y='event_type',
                    color='source',
                    title="Event Timeline",
                    hover_data=['event_type', 'source']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            # Event details
            st.subheader("📋 Recent Events")
            for event in reversed(events[-10:]):  # Show last 10 events in reverse order
                timestamp = event.get("timestamp", "Unknown")
                event_type = event.get("event_type", "Unknown")
                source = event.get("source", "Unknown")

                with st.expander(f"[{timestamp}] {event_type} - {source}", expanded=False):
                    st.json(event)
        else:
            st.info("No events recorded yet")

    # Performance metrics section
    if show_metrics:
        st.header("📊 Performance Metrics")

        # Performance overview
        perf = analytics["performance"]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Tool Calls", perf["total_tool_calls"])

        with col2:
            st.metric("Total Errors", perf["total_errors"])

        with col3:
            st.metric("Success Rate", f"{perf['success_rate']:.1f}%")

        with col4:
            st.metric("Events Tracked", perf["events_tracked"])

        # Agent performance comparison
        if analytics["agent_summary"]:
            st.subheader("🏆 Agent Performance Comparison")

            agent_perf_df = pd.DataFrame([
                {
                    "Agent": agent_name,
                    "Tool Calls": data["tool_calls"],
                    "Errors": data["errors"],
                    "Success Rate": f"{((data['tool_calls'] - data['errors'])/data['tool_calls']*100):.1f}%" if data["tool_calls"] > 0 else "100%"
                }
                for agent_name, data in analytics["agent_summary"].items()
            ])

            st.dataframe(agent_perf_df, use_container_width=True)

            # Agent performance chart
            if len(agent_perf_df) > 0:
                fig = px.bar(
                    agent_perf_df,
                    x="Agent",
                    y="Tool Calls",
                    title="Agent Tool Call Activity"
                )
                st.plotly_chart(fig, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown("**AgenticFlow Observatory** - Real-time monitoring for multi-agent systems")


def create_agent_detail_view(observer: FlowObserver, agent_name: str) -> None:
    """Create detailed view for a specific agent."""
    st.header(f"🤖 Agent Details: {agent_name}")

    insights = observer.get_agent_insights(agent_name)

    # Agent overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Status", insights["status"].title())

    with col2:
        st.metric("Tool Calls", insights["stats"]["tool_calls"])

    with col3:
        st.metric("Errors", insights["stats"]["errors"])

    with col4:
        duration = insights["stats"]["active_duration"]
        st.metric("Active Duration", f"{duration:.1f}s")

    # Agent reflection
    if insights["reflection"]:
        st.subheader("💭 Agent Reflection")
        st.json(insights["reflection"])

    # Activity timeline
    if insights["timeline"]:
        st.subheader("📈 Activity Timeline")

        timeline_df = pd.DataFrame(insights["timeline"])
        if not timeline_df.empty:
            timeline_df['timestamp'] = pd.to_datetime(timeline_df['timestamp'])

            fig = px.timeline(
                timeline_df,
                x_start='timestamp',
                x_end='timestamp',
                y='event_type',
                title=f"Activity Timeline for {agent_name}"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Activities list
    if insights["activities"]:
        st.subheader("📋 Activity Log")
        for activity in reversed(insights["activities"][-20:]):  # Last 20 activities
            timestamp = activity["timestamp"].strftime("%H:%M:%S")
            activity_type = activity["type"]
            details = activity.get("details", {})

            with st.expander(f"[{timestamp}] {activity_type}", expanded=False):
                if details:
                    st.json(details)
                else:
                    st.text("No additional details")