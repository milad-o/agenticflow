"""Rich console subscriber for beautiful terminal output."""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.live import Live
from rich.layout import Layout
from rich import box
from .events import Event


class RichConsoleSubscriber:
    """Rich console subscriber with beautiful terminal output."""
    
    def __init__(self, show_timestamps: bool = True, show_details: bool = True):
        self.console = Console()
        self.show_timestamps = show_timestamps
        self.show_details = show_details
        self._flow_tree = None
        self._current_flow_id = None
        self._agent_nodes = {}
        self._tool_nodes = {}
        self._team_nodes = {}
        self._progress_tracker = {}
        
    def handle_event_sync(self, event: Event) -> None:
        """Handle event synchronously for rich console display."""
        self._handle_event(event)
    
    async def handle_event(self, event: Event) -> None:
        """Handle event for rich console display."""
        self._handle_event(event)
    
    def _handle_event(self, event: Event) -> None:
        """Handle event with rich formatting."""
        if event.event_type == "flow_started":
            self._handle_flow_started(event)
        elif event.event_type == "flow_completed":
            self._handle_flow_completed(event)
        elif event.event_type == "agent_started":
            self._handle_agent_started(event)
        elif event.event_type == "agent_completed":
            self._handle_agent_completed(event)
        elif event.event_type == "agent_thinking":
            self._handle_agent_thinking(event)
        elif event.event_type == "agent_working":
            self._handle_agent_working(event)
        elif event.event_type == "tool_executed":
            self._handle_tool_executed(event)
        elif event.event_type == "tool_args":
            self._handle_tool_args(event)
        elif event.event_type == "tool_result":
            self._handle_tool_result(event)
        elif event.event_type == "tool_error":
            self._handle_tool_error(event)
        elif event.event_type == "team_supervisor_called":
            self._handle_team_supervisor_called(event)
        elif event.event_type == "team_agent_called":
            self._handle_team_agent_called(event)
    
    def _handle_flow_started(self, event: Event) -> None:
        """Handle flow started event."""
        flow_name = event.data.get("flow_name", "Unknown")
        message = event.data.get("message", "")

        # Create flow tree with clear role indicator
        self._flow_tree = Tree(f"🚀 [bold yellow]Orchestrator[/bold yellow] [bold blue]({flow_name})[/bold blue]", guide_style="blue")
        self._current_flow_id = event.flow_id

        # Add message if present
        if message:
            self._flow_tree.add(f"📝 [dim]{message[:100]}{'...' if len(message) > 100 else ''}[/dim]")

        self.console.print(self._flow_tree)
    
    def _handle_flow_completed(self, event: Event) -> None:
        """Handle flow completed event."""
        flow_name = event.data.get("flow_name", "Unknown")
        duration = event.data.get("duration_ms", 0)
        messages = event.data.get("total_messages", 0)
        
        # Update flow tree with completion
        if self._flow_tree:
            self._flow_tree.label = f"✅ [bold green]{flow_name}[/bold green] [dim]({duration:.1f}ms, {messages} messages)[/dim]"
            self.console.print(self._flow_tree)
        
        # Clear state
        self._flow_tree = None
        self._current_flow_id = None
        self._agent_nodes = {}
        self._tool_nodes = {}
        self._team_nodes = {}
    
    def _handle_agent_started(self, event: Event) -> None:
        """Handle agent started event."""
        agent_name = event.agent_name or "Unknown"
        agent_type = event.data.get("agent_type", "")
        tools = event.data.get("tools", [])
        team_name = event.team_name

        if self._flow_tree:
            # Determine parent node (team or flow)
            parent_node = self._flow_tree
            if team_name and team_name in self._team_nodes:
                parent_node = self._team_nodes[team_name]

            # Create agent node with clear role indicator
            if team_name:
                agent_node = parent_node.add(f"🤖 [bold magenta]Agent[/bold magenta] [bold cyan]({agent_name})[/bold cyan]")
            else:
                agent_node = parent_node.add(f"🤖 [bold green]Agent[/bold green] [bold cyan]({agent_name})[/bold cyan]")
            self._agent_nodes[agent_name] = agent_node

            # Add tools
            if tools and self.show_details:
                tools_text = ", ".join(tools[:3])
                if len(tools) > 3:
                    tools_text += "..."
                agent_node.add(f"🔧 [dim]Tools: {tools_text}[/dim]")
    
    def _handle_agent_completed(self, event: Event) -> None:
        """Handle agent completed event."""
        agent_name = event.agent_name or "Unknown"
        duration = event.data.get("duration_ms", 0)
        tools_used = event.data.get("tools_used", 0)
        team_name = event.team_name
        
        if agent_name in self._agent_nodes:
            # Update agent node with completion and role indicator
            agent_node = self._agent_nodes[agent_name]
            # Add role indicator to completed agent
            if team_name:
                agent_node.label = f"✅ [bold magenta]Agent[/bold magenta] [bold green]({agent_name})[/bold green] [dim]({duration:.1f}ms, {tools_used} tools)[/dim]"
            else:
                agent_node.label = f"✅ [bold green]Agent[/bold green] [bold green]({agent_name})[/bold green] [dim]({duration:.1f}ms, {tools_used} tools)[/dim]"
    
    def _handle_agent_thinking(self, event: Event) -> None:
        """Handle agent thinking event."""
        agent_name = event.agent_name or "Unknown"
        thinking = event.data.get("thinking_process", "")
        step = event.data.get("current_step", "")
        
        if agent_name in self._agent_nodes and self.show_details:
            agent_node = self._agent_nodes[agent_name]
            thinking_node = agent_node.add(f"🧠 [yellow]Thinking: {step}[/yellow]")
            if thinking:
                thinking_node.add(f"[dim]{thinking[:100]}{'...' if len(thinking) > 100 else ''}[/dim]")
    
    def _handle_agent_working(self, event: Event) -> None:
        """Handle agent working event."""
        agent_name = event.agent_name or "Unknown"
        task = event.data.get("task_description", "")
        
        if agent_name in self._agent_nodes:
            agent_node = self._agent_nodes[agent_name]
            # Show actual status instead of fake progress
            status = "🔄 Processing request and planning tool usage"
            agent_node.add(f"⚙️ [yellow]{status}[/yellow]")
    
    def _handle_tool_executed(self, event: Event) -> None:
        """Handle tool executed event."""
        tool_name = event.data.get("tool_name", "Unknown")
        agent_name = event.agent_name or "Unknown"
        
        if agent_name in self._agent_nodes:
            agent_node = self._agent_nodes[agent_name]
            tool_node = agent_node.add(f"🔧 [bold magenta]{tool_name}[/bold magenta] [dim](Tool Call)[/dim]")
            self._tool_nodes[f"{agent_name}_{tool_name}"] = tool_node
    
    def _handle_tool_args(self, event: Event) -> None:
        """Handle tool args event."""
        tool_name = event.data.get("tool_name", "Unknown")
        agent_name = event.agent_name or "Unknown"
        args = event.data.get("args", {})
        
        # Create tool node if it doesn't exist (tool_args comes before tool_executed)
        if agent_name in self._agent_nodes and f"{agent_name}_{tool_name}" not in self._tool_nodes:
            agent_node = self._agent_nodes[agent_name]
            tool_node = agent_node.add(f"🔧 [bold red]Tool[/bold red] [bold magenta]({tool_name})[/bold magenta]")
            self._tool_nodes[f"{agent_name}_{tool_name}"] = tool_node
        
        if f"{agent_name}_{tool_name}" in self._tool_nodes and self.show_details:
            tool_node = self._tool_nodes[f"{agent_name}_{tool_name}"]
            
            # Show status: tool called (this should come FIRST)
            tool_node.add(f"📞 [green]Tool Called[/green] - Preparing arguments...")
            
            # Filter out LangGraph internal metadata and show only meaningful args
            meaningful_args = self._filter_meaningful_args(args)
            
            if meaningful_args:
                # Create args table
                args_table = Table(show_header=False, box=box.SIMPLE)
                args_table.add_column("Key", style="cyan")
                args_table.add_column("Value", style="white")
                
                for key, value in meaningful_args.items():
                    value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    args_table.add_row(key, value_str)
                
                tool_node.add(Panel(args_table, title="📝 Arguments", border_style="blue"))
            else:
                tool_node.add(f"📝 [dim]No meaningful arguments to display[/dim]")
            
            # Add execution status after arguments
            tool_node.add(f"⚡ [yellow]Tool Executed[/yellow] - Running...")
    
    def _filter_meaningful_args(self, args: dict) -> dict:
        """Filter out LangGraph internal metadata and return meaningful arguments."""
        # Keys to exclude (LangGraph internal metadata)
        exclude_keys = {
            'callbacks', 'tags', 'metadata', 'run_name', 'run_id', 'parent_run_id',
            'run_type', 'run_tags', 'run_metadata', 'run_extra', 'run_parents',
            'run_children', 'run_sibling', 'run_order', 'run_sequence'
        }
        
        meaningful_args = {}
        for key, value in args.items():
            if key not in exclude_keys and value is not None:
                # Skip empty strings, empty lists, and None values
                if value != "" and value != [] and value != {}:
                    meaningful_args[key] = value
        
        return meaningful_args
    
    def _handle_tool_result(self, event: Event) -> None:
        """Handle tool result event."""
        tool_name = event.data.get("tool_name", "Unknown")
        agent_name = event.agent_name or "Unknown"
        result = event.data.get("result", "")
        duration = event.data.get("duration_ms", 0)
        success = event.data.get("success", True)
        
        if f"{agent_name}_{tool_name}" in self._tool_nodes:
            tool_node = self._tool_nodes[f"{agent_name}_{tool_name}"]
            
            # Show status: response received
            status_icon = "✅" if success else "❌"
            status_color = "green" if success else "red"
            status_text = "Response Received" if success else "Error Occurred"
            
            tool_node.add(f"📨 [{status_color}]{status_icon} {status_text}[/{status_color}] - Processing result...")
            
            # Parse and format result based on tool type
            formatted_result = self._format_tool_result(tool_name, result)
            
            result_panel = Panel(
                formatted_result,
                title=f"📤 Result ({duration:.1f}ms)",
                border_style=status_color,
                expand=False
            )
            tool_node.add(result_panel)
    
    def _format_tool_result(self, tool_name: str, result: str) -> str:
        """Format tool result based on tool type for better readability."""
        try:
            # Try to parse as JSON first
            import json
            if isinstance(result, str) and result.startswith('{'):
                result_dict = json.loads(result)
            else:
                result_dict = result
            
            if tool_name == "search_web":
                return self._format_search_web_result(result_dict)
            elif tool_name == "create_file":
                return self._format_create_file_result(result_dict)
            else:
                # Generic formatting
                result_str = str(result)
                if len(result_str) > 200:
                    return result_str[:200] + "..."
                return result_str
                
        except (json.JSONDecodeError, TypeError):
            # Fallback to string formatting
            result_str = str(result)
            if len(result_str) > 200:
                return result_str[:200] + "..."
            return result_str
    
    def _format_search_web_result(self, result) -> str:
        """Format search_web result for better readability."""
        result_str = str(result)
        
        # Try to extract query and results from the string
        import re
        
        # Extract query
        query_match = re.search(r"'query': '([^']+)'", result_str)
        query = query_match.group(1) if query_match else "Unknown query"
        
        # Extract results count
        results_match = re.search(r"'results': \[([^\]]+)\]", result_str)
        if results_match:
            results_content = results_match.group(1)
            # Count URLs in results
            url_count = len(re.findall(r"'url': '([^']+)'", results_content))
            
            formatted = f"🔍 Query: {query}\n📋 Found {url_count} results\n\n"
            
            # Extract first few URLs and titles
            urls = re.findall(r"'url': '([^']+)'", results_content)[:3]
            titles = re.findall(r"'title': '([^']+)'", results_content)[:3]
            
            for i, (url, title) in enumerate(zip(urls, titles), 1):
                formatted += f"{i}. {title[:50]}...\n   🔗 {url}\n"
            
            if url_count > 3:
                formatted += f"... and {url_count - 3} more results"
                
            return formatted
        
        return result_str[:200] + "..." if len(result_str) > 200 else result_str
    
    def _format_create_file_result(self, result) -> str:
        """Format create_file result for better readability."""
        result_str = str(result)
        
        # Extract file path from content if it's a success message
        if 'Created file' in result_str:
            import re
            file_path_match = re.search(r"'([^']+)'", result_str)
            if file_path_match:
                file_path = file_path_match.group(1)
                # Extract content preview
                content_match = re.search(r"with content: '([^']+)", result_str)
                if content_match:
                    content_preview = content_match.group(1)[:100] + "..."
                    return f"✅ File created: {file_path}\n📝 Content preview: {content_preview}"
                else:
                    return f"✅ File created: {file_path}"
        
        return result_str[:200] + "..." if len(result_str) > 200 else result_str
    
    def _handle_tool_error(self, event: Event) -> None:
        """Handle tool error event."""
        tool_name = event.data.get("tool_name", "Unknown")
        agent_name = event.agent_name or "Unknown"
        error_message = event.data.get("error_message", "")
        error_type = event.data.get("error_type", "")
        
        if f"{agent_name}_{tool_name}" in self._tool_nodes:
            tool_node = self._tool_nodes[f"{agent_name}_{tool_name}"]
            tool_node.add(f"❌ [bold red]Error: {error_type}[/bold red] [dim]{error_message}[/dim]")
    
    def print_summary(self, events: List[Event]) -> None:
        """Print a beautiful summary of all events."""
        if not events:
            return
        
        # Create summary table
        summary_table = Table(title="📊 Flow Summary", box=box.ROUNDED)
        summary_table.add_column("Event Type", style="cyan")
        summary_table.add_column("Count", style="magenta", justify="right")
        summary_table.add_column("Description", style="white")
        
        event_counts = {}
        for event in events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        event_descriptions = {
            "flow_started": "Flow initialization",
            "flow_completed": "Flow completion",
            "agent_started": "Agent activation",
            "agent_completed": "Agent completion",
            "agent_thinking": "Agent reasoning",
            "agent_working": "Agent execution",
            "tool_executed": "Tool execution",
            "tool_args": "Tool arguments",
            "tool_result": "Tool results",
            "tool_error": "Tool errors"
        }
        
        for event_type, count in sorted(event_counts.items()):
            description = event_descriptions.get(event_type, "Unknown event")
            summary_table.add_row(event_type, str(count), description)
        
        self.console.print(summary_table)
        
        # Print performance metrics
        flow_events = [e for e in events if e.event_type in ["flow_started", "flow_completed"]]
        if len(flow_events) >= 2:
            start_time = flow_events[0].timestamp
            end_time = flow_events[-1].timestamp
            total_duration = (end_time - start_time).total_seconds() * 1000
            
            metrics_panel = Panel(
                f"⏱️  Total Duration: {total_duration:.1f}ms\n"
                f"🔧 Tool Executions: {event_counts.get('tool_executed', 0)}\n"
                f"🤖 Agents Used: {len(set(e.agent_name for e in events if e.agent_name))}",
                title="Performance Metrics",
                border_style="green"
            )
            self.console.print(metrics_panel)
    
    def _handle_team_supervisor_called(self, event: Event) -> None:
        """Handle team supervisor called event."""
        team_name = event.team_name or "Unknown"
        team_agents = event.data.get("team_agents", [])

        if self._flow_tree:
            # Create team node with clear role indicator
            team_node = self._flow_tree.add(f"👥 [bold yellow]Supervisor[/bold yellow] [bold magenta]({team_name})[/bold magenta]")
            self._team_nodes[team_name] = team_node

            # Add team agents info
            if team_agents and self.show_details:
                agents_text = ", ".join(team_agents[:3])
                if len(team_agents) > 3:
                    agents_text += "..."
                team_node.add(f"👤 [dim]Agents: {agents_text}[/dim]")
    
    def _handle_team_agent_called(self, event: Event) -> None:
        """Handle team agent called event."""
        team_name = event.team_name or "Unknown"
        agent_name = event.agent_name or "Unknown"
        supervisor_decision = event.data.get("supervisor_decision", "")

        if team_name in self._team_nodes and self.show_details:
            team_node = self._team_nodes[team_name]
            decision_node = team_node.add(f"🎯 [bold cyan]Decision[/bold cyan] [yellow]({agent_name})[/yellow]")
            if supervisor_decision:
                decision_node.add(f"[dim]Decision: {supervisor_decision[:100]}{'...' if len(supervisor_decision) > 100 else ''}[/dim]")
