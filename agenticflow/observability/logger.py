"""Event logger for observability."""

import json
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from .events import Event
from .event_bus import EventBus, get_global_event_bus


class EventLogger:
    """Event logger with in-memory and persistent storage options."""
    
    def __init__(self, persistent: bool = False, backend: str = "sqlite3", db_path: Optional[str] = None):
        self.persistent = persistent
        self.backend = backend
        self.db_path = db_path or "examples/artifacts/agenticflow_events.db"
        
        # In-memory storage
        self._events: List[Event] = []
        self._event_bus = get_global_event_bus()
        
        # Persistent storage setup
        if self.persistent:
            self._setup_persistent_storage()
    
    def _setup_persistent_storage(self) -> None:
        """Setup persistent storage backend."""
        if self.backend == "sqlite3":
            self._setup_sqlite()
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")
    
    def _setup_sqlite(self) -> None:
        """Setup SQLite database."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
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
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_flow_id ON events(flow_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_name ON events(agent_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)")
            
            conn.commit()
    
    async def log_event(self, event: Event) -> None:
        """Log an event."""
        # Store in memory
        self._events.append(event)
        
        # Emit to event bus
        await self._event_bus.emit_event(event)
        
        # Store persistently if enabled
        if self.persistent:
            await self._store_event_persistent(event)
    
    async def _store_event_persistent(self, event: Event) -> None:
        """Store event in persistent storage."""
        if self.backend == "sqlite3":
            await self._store_event_sqlite(event)
    
    async def _store_event_sqlite(self, event: Event) -> None:
        """Store event in SQLite database."""
        try:
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
        except Exception as e:
            print(f"Error storing event to database: {e}")
    
    def get_events(self, event_type: Optional[str] = None, 
                  flow_id: Optional[str] = None,
                  agent_name: Optional[str] = None,
                  limit: Optional[int] = None) -> List[Event]:
        """Get events from memory."""
        events = self._events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if flow_id:
            events = [e for e in events if e.flow_id == flow_id]
        
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_events_persistent(self, event_type: Optional[str] = None,
                            flow_id: Optional[str] = None,
                            agent_name: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get events from persistent storage."""
        if not self.persistent:
            return []
        
        if self.backend == "sqlite3":
            return self._query_events_sqlite(event_type, flow_id, agent_name, limit)
        
        return []
    
    def _query_events_sqlite(self, event_type: Optional[str] = None,
                            flow_id: Optional[str] = None,
                            agent_name: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Query events from SQLite database."""
        try:
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
        except Exception as e:
            print(f"Error querying events from database: {e}")
            return []
    
    def get_flow_summary(self, flow_id: str) -> Dict[str, Any]:
        """Get summary for a specific flow."""
        flow_events = self.get_events(flow_id=flow_id)
        
        if not flow_events:
            return {"error": "Flow not found"}
        
        # Find flow start and end events
        start_events = [e for e in flow_events if e.event_type == "flow_started"]
        end_events = [e for e in flow_events if e.event_type == "flow_completed"]
        
        summary = {
            "flow_id": flow_id,
            "total_events": len(flow_events),
            "started": len(start_events) > 0,
            "completed": len(end_events) > 0,
            "start_time": start_events[0].timestamp if start_events else None,
            "end_time": end_events[0].timestamp if end_events else None,
            "duration_ms": 0,
            "agents": {},
            "tools": {},
            "errors": []
        }
        
        # Calculate duration
        if start_events and end_events:
            duration = (end_events[0].timestamp - start_events[0].timestamp).total_seconds() * 1000
            summary["duration_ms"] = duration
        
        # Analyze agent events
        agent_events = [e for e in flow_events if e.agent_name]
        for event in agent_events:
            agent_name = event.agent_name
            if agent_name not in summary["agents"]:
                summary["agents"][agent_name] = {
                    "events": 0,
                    "tools_used": 0,
                    "duration_ms": 0
                }
            
            summary["agents"][agent_name]["events"] += 1
            
            if event.event_type == "agent_completed":
                duration = event.data.get("duration_ms", 0)
                summary["agents"][agent_name]["duration_ms"] = duration
                summary["agents"][agent_name]["tools_used"] = event.data.get("tools_used", 0)
        
        # Analyze tool events
        tool_events = [e for e in flow_events if e.event_type in ["tool_executed", "tool_result"]]
        for event in tool_events:
            tool_name = event.data.get("tool_name", "Unknown")
            if tool_name not in summary["tools"]:
                summary["tools"][tool_name] = {"count": 0, "total_duration_ms": 0}
            
            summary["tools"][tool_name]["count"] += 1
            
            if event.event_type == "tool_result":
                duration = event.data.get("duration_ms", 0)
                summary["tools"][tool_name]["total_duration_ms"] += duration
        
        # Find errors
        error_events = [e for e in flow_events if "error" in e.event_type]
        summary["errors"] = [e.to_dict() for e in error_events]
        
        return summary
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get overall metrics."""
        if not self._events:
            return {"total_events": 0}
        
        # Count events by type
        event_counts = {}
        for event in self._events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Get unique flows, agents, tools
        flows = set(e.flow_id for e in self._events if e.flow_id)
        agents = set(e.agent_name for e in self._events if e.agent_name)
        tools = set()
        
        for event in self._events:
            if "tool" in event.event_type and "tool_name" in event.data:
                tools.add(event.data["tool_name"])
        
        return {
            "total_events": len(self._events),
            "unique_flows": len(flows),
            "unique_agents": len(agents),
            "unique_tools": len(tools),
            "event_counts": event_counts,
            "flows": list(flows),
            "agents": list(agents),
            "tools": list(tools)
        }
    
    def clear_events(self) -> None:
        """Clear all events from memory."""
        self._events.clear()
    
    def export_events(self, filepath: str, format: str = "json") -> None:
        """Export events to file."""
        file_path = Path(filepath)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([event.to_dict() for event in self._events], f, indent=2, ensure_ascii=False)
        elif format == "csv":
            import csv
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                if self._events:
                    writer = csv.DictWriter(f, fieldnames=self._events[0].to_dict().keys())
                    writer.writeheader()
                    writer.writerows(event.to_dict() for event in self._events)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_event_bus(self) -> EventBus:
        """Get the event bus instance."""
        return self._event_bus
