"""Event subscribers for observability."""

import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from .events import Event


class BaseSubscriber(ABC):
    """Base class for event subscribers."""
    
    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Handle an event."""
        pass
    
    def handle_event_sync(self, event: Event) -> None:
        """Handle an event synchronously (optional)."""
        pass


class ConsoleSubscriber(BaseSubscriber):
    """Console subscriber for real-time event display."""
    
    def __init__(self, show_timestamps: bool = True, show_details: bool = True):
        self.show_timestamps = show_timestamps
        self.show_details = show_details
        self._indent_level = 0
        self._flow_stack = []
    
    async def handle_event(self, event: Event) -> None:
        """Handle event for console display."""
        self._update_indent(event)
        self._print_event(event)
    
    def handle_event_sync(self, event: Event) -> None:
        """Handle event synchronously for console display."""
        self._update_indent(event)
        self._print_event(event)
    
    def _update_indent(self, event: Event) -> None:
        """Update indentation based on event type."""
        if event.event_type == "flow_started":
            self._flow_stack.append(event.flow_id)
            self._indent_level = 0
        elif event.event_type == "flow_completed":
            if self._flow_stack:
                self._flow_stack.pop()
            self._indent_level = 0
        elif event.event_type == "agent_started":
            self._indent_level = 1
        elif event.event_type == "agent_completed":
            self._indent_level = 1
        elif event.event_type in ["tool_executed", "tool_args", "tool_result"]:
            self._indent_level = 2
    
    def _print_event(self, event: Event) -> None:
        """Print event to console."""
        indent = "  " * self._indent_level
        timestamp = f"[{event.timestamp.strftime('%H:%M:%S.%f')[:-3]}] " if self.show_timestamps else ""
        
        # Event type emoji mapping
        emoji_map = {
            "flow_started": "🚀",
            "flow_completed": "✅",
            "flow_error": "❌",
            "agent_started": "🤖",
            "agent_completed": "✅",
            "agent_reasoning": "🤔",
            "agent_error": "❌",
            "tool_executed": "🔧",
            "tool_args": "📝",
            "tool_result": "📤",
            "tool_error": "❌",
            "message_routed": "📨",
            "message_received": "📥",
            "team_supervisor_called": "👥",
            "team_agent_called": "👤",
            "custom_event": "⭐"
        }
        
        emoji = emoji_map.get(event.event_type, "📋")
        
        # Format event display
        if event.event_type == "flow_started":
            flow_name = event.data.get("flow_name", "Unknown")
            message = event.data.get("message", "")
            print(f"{timestamp}{emoji} Flow Started: \"{flow_name}\"")
            if message:
                print(f"{indent}  📝 Message: {message[:100]}{'...' if len(message) > 100 else ''}")
        
        elif event.event_type == "flow_completed":
            flow_name = event.data.get("flow_name", "Unknown")
            duration = event.data.get("duration_ms", 0)
            messages = event.data.get("total_messages", 0)
            print(f"{timestamp}{emoji} Flow Completed: \"{flow_name}\" ({duration:.1f}ms, {messages} messages)")
        
        elif event.event_type == "agent_started":
            agent_name = event.agent_name or "Unknown"
            agent_type = event.data.get("agent_type", "")
            tools = event.data.get("tools", [])
            print(f"{indent}{emoji} Agent Started: \"{agent_name}\" ({agent_type})")
            if tools and self.show_details:
                print(f"{indent}  🔧 Tools: {', '.join(tools[:3])}{'...' if len(tools) > 3 else ''}")
        
        elif event.event_type == "agent_completed":
            agent_name = event.agent_name or "Unknown"
            duration = event.data.get("duration_ms", 0)
            tools_used = event.data.get("tools_used", 0)
            print(f"{indent}{emoji} Agent Completed: \"{agent_name}\" ({duration:.1f}ms, {tools_used} tools)")
        
        elif event.event_type == "agent_reasoning":
            reasoning = event.data.get("reasoning", "")
            decision = event.data.get("decision", "")
            print(f"{indent}{emoji} Reasoning: {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}")
            if decision:
                print(f"{indent}  💡 Decision: {decision}")
        
        elif event.event_type == "agent_thinking":
            agent_name = event.agent_name or "Unknown"
            thinking = event.data.get("thinking_process", "")
            step = event.data.get("current_step", "")
            print(f"{indent}🧠 Agent Thinking: \"{agent_name}\" - {step}")
            if self.show_details and thinking:
                print(f"{indent}  Process: {thinking}")
        
        elif event.event_type == "agent_working":
            agent_name = event.agent_name or "Unknown"
            task = event.data.get("task_description", "")
            progress = event.data.get("progress")
            progress_str = f" ({progress*100:.0f}%)" if progress is not None else ""
            print(f"{indent}⚙️  Agent Working: \"{agent_name}\" - {task}{progress_str}")
        
        elif event.event_type == "tool_executed":
            tool_name = event.data.get("tool_name", "Unknown")
            print(f"{indent}{emoji} Tool Executed: \"{tool_name}\"")
        
        elif event.event_type == "tool_args":
            tool_name = event.data.get("tool_name", "Unknown")
            args = event.data.get("args", {})
            print(f"{indent}  {emoji} Args: {json.dumps(args, indent=2)[:200]}{'...' if len(str(args)) > 200 else ''}")
        
        elif event.event_type == "tool_result":
            tool_name = event.data.get("tool_name", "Unknown")
            result = event.data.get("result", "")
            duration = event.data.get("duration_ms", 0)
            success = event.data.get("success", True)
            status = "✅" if success else "❌"
            print(f"{indent}  {emoji} Result: {status} {str(result)[:100]}{'...' if len(str(result)) > 100 else ''} ({duration:.1f}ms)")
        
        elif event.event_type == "message_routed":
            from_comp = event.data.get("from_component", "Unknown")
            to_comp = event.data.get("to_component", "Unknown")
            reason = event.data.get("routing_reason", "")
            print(f"{indent}{emoji} Message Routed: {from_comp} → {to_comp}")
            if reason:
                print(f"{indent}  💭 Reason: {reason}")
        
        elif event.event_type == "team_supervisor_called":
            supervisor = event.data.get("supervisor_name", "Unknown")
            decision = event.data.get("decision", "")
            print(f"{indent}{emoji} Supervisor Called: \"{supervisor}\"")
            if decision:
                print(f"{indent}  🎯 Decision: {decision}")
        
        elif event.event_type == "custom_event":
            custom_type = event.data.get("custom_type", "Unknown")
            custom_data = event.data.get("custom_data", {})
            print(f"{indent}{emoji} Custom Event: \"{custom_type}\"")
            if custom_data and self.show_details:
                print(f"{indent}  📊 Data: {json.dumps(custom_data, indent=2)[:200]}{'...' if len(str(custom_data)) > 200 else ''}")
        
        else:
            # Generic event display
            print(f"{indent}{emoji} {event.event_type.replace('_', ' ').title()}")


class FileSubscriber(BaseSubscriber):
    """File subscriber for persistent event logging."""
    
    def __init__(self, filepath: str, format: str = "json"):
        self.filepath = Path(filepath)
        self.format = format
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    async def handle_event(self, event: Event) -> None:
        """Handle event for file logging."""
        with open(self.filepath, "a", encoding="utf-8") as f:
            if self.format == "json":
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
            else:
                # Plain text format
                timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                f.write(f"[{timestamp}] {event.event_type}: {event.agent_name or 'N/A'}\n")


class MetricsCollector(BaseSubscriber):
    """Metrics collector for performance tracking."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "flow_count": 0,
            "agent_count": 0,
            "tool_count": 0,
            "total_duration_ms": 0.0,
            "error_count": 0,
            "flows": {},
            "agents": {},
            "tools": {}
        }
    
    async def handle_event(self, event: Event) -> None:
        """Collect metrics from events."""
        if event.event_type == "flow_started":
            self.metrics["flow_count"] += 1
            self.metrics["flows"][event.flow_id] = {
                "start_time": event.timestamp,
                "name": event.data.get("flow_name", "Unknown")
            }
        
        elif event.event_type == "flow_completed":
            if event.flow_id in self.metrics["flows"]:
                flow_data = self.metrics["flows"][event.flow_id]
                duration = event.data.get("duration_ms", 0)
                flow_data["duration_ms"] = duration
                flow_data["end_time"] = event.timestamp
                self.metrics["total_duration_ms"] += duration
        
        elif event.event_type == "agent_started":
            self.metrics["agent_count"] += 1
            agent_name = event.agent_name or "Unknown"
            self.metrics["agents"][agent_name] = {
                "start_time": event.timestamp,
                "type": event.data.get("agent_type", "Unknown"),
                "tools": event.data.get("tools", [])
            }
        
        elif event.event_type == "agent_completed":
            agent_name = event.agent_name or "Unknown"
            if agent_name in self.metrics["agents"]:
                agent_data = self.metrics["agents"][agent_name]
                duration = event.data.get("duration_ms", 0)
                agent_data["duration_ms"] = duration
                agent_data["tools_used"] = event.data.get("tools_used", 0)
                agent_data["end_time"] = event.timestamp
        
        elif event.event_type == "tool_executed":
            self.metrics["tool_count"] += 1
            tool_name = event.data.get("tool_name", "Unknown")
            if tool_name not in self.metrics["tools"]:
                self.metrics["tools"][tool_name] = {"count": 0, "total_duration_ms": 0.0}
            self.metrics["tools"][tool_name]["count"] += 1
        
        elif event.event_type == "tool_result":
            tool_name = event.data.get("tool_name", "Unknown")
            duration = event.data.get("duration_ms", 0)
            if tool_name in self.metrics["tools"]:
                self.metrics["tools"][tool_name]["total_duration_ms"] += duration
        
        elif "error" in event.event_type:
            self.metrics["error_count"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "flow_count": 0,
            "agent_count": 0,
            "tool_count": 0,
            "total_duration_ms": 0.0,
            "error_count": 0,
            "flows": {},
            "agents": {},
            "tools": {}
        }


class DatabaseSubscriber(BaseSubscriber):
    """Database subscriber for persistent storage."""
    
    def __init__(self, db_path: str = "agenticflow_events.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    flow_id TEXT,
                    agent_name TEXT,
                    team_name TEXT,
                    data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    async def handle_event(self, event: Event) -> None:
        """Store event in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO events 
                (event_id, timestamp, event_type, flow_id, agent_name, team_name, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.timestamp.isoformat(),
                event.event_type,
                event.flow_id,
                event.agent_name,
                event.team_name,
                json.dumps(event.data)
            ))
            conn.commit()
    
    def query_events(self, event_type: Optional[str] = None, 
                    flow_id: Optional[str] = None,
                    agent_name: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """Query events from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if flow_id:
                query += " AND flow_id = ?"
                params.append(flow_id)
            
            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
