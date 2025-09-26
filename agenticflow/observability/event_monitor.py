"""
Comprehensive Event Monitor for AgenticFlow Observability

This module provides real-time monitoring of all system events through the event bus,
creating a complete audit trail of agent activities, task execution, and system state changes.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from agenticflow.core.events.event_bus import EventBus, Event, EventType
from agenticflow.observability.reporter import Reporter


class EventMonitor:
    """
    Comprehensive event monitor that subscribes to all event types
    and provides detailed observability into system execution.
    """
    
    def __init__(self, event_bus: EventBus, reporter: Optional[Reporter] = None):
        self.event_bus = event_bus
        self.reporter = reporter
        self.events_log: List[Dict[str, Any]] = []
        self.state_tracker: Dict[str, Any] = {
            'active_tasks': {},
            'agent_status': {},
            'flow_status': 'initialized',
            'execution_timeline': []
        }
        
        # Subscribe to all event types
        self._setup_subscriptions()
        
    def _setup_subscriptions(self):
        """Subscribe to all event types for comprehensive monitoring."""
        
        # Task lifecycle events
        self.event_bus.subscribe(EventType.TASK_STARTED, self._on_task_started, "monitor")
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed, "monitor")
        self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed, "monitor")
        self.event_bus.subscribe(EventType.TASK_PROGRESS, self._on_task_progress, "monitor")
        
        # Data flow events
        self.event_bus.subscribe(EventType.DATA_AVAILABLE, self._on_data_available, "monitor")
        self.event_bus.subscribe(EventType.DATA_PROCESSED, self._on_data_processed, "monitor")
        self.event_bus.subscribe(EventType.DATA_ERROR, self._on_data_error, "monitor")
        
        # Agent events
        self.event_bus.subscribe(EventType.AGENT_READY, self._on_agent_ready, "monitor")
        self.event_bus.subscribe(EventType.AGENT_BUSY, self._on_agent_busy, "monitor")
        self.event_bus.subscribe(EventType.AGENT_ERROR, self._on_agent_error, "monitor")
        
        # Flow events
        self.event_bus.subscribe(EventType.FLOW_STARTED, self._on_flow_started, "monitor")
        self.event_bus.subscribe(EventType.FLOW_COMPLETED, self._on_flow_completed, "monitor")
        self.event_bus.subscribe(EventType.FLOW_ERROR, self._on_flow_error, "monitor")
        
        print("🔍 [EVENT_MONITOR] Subscribed to all event types - monitoring active")
        
    def _log_event(self, event: Event, event_description: str):
        """Log event with full context and update state tracker."""
        timestamp = datetime.now()
        
        # Create comprehensive log entry
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'event_id': event.event_id,
            'event_type': event.event_type.value,
            'source': event.source,
            'target': event.target,
            'channel': event.channel,
            'description': event_description,
            'data': event.data,
            'state_snapshot': self._create_state_snapshot()
        }
        
        self.events_log.append(log_entry)
        
        # Update execution timeline
        self.state_tracker['execution_timeline'].append({
            'timestamp': timestamp.isoformat(),
            'event': event.event_type.value,
            'source': event.source,
            'description': event_description
        })
        
        # Console output with structured logging
        print(f"📊 [MONITOR] {timestamp.strftime('%H:%M:%S')} | {event.source} | {event.event_type.value}")
        print(f"    └─ {event_description}")
        if event.data:
            key_data = {k: v for k, v in event.data.items() if k in ['task_id', 'subtask_name', 'tool_used', 'phase', 'status']}
            if key_data:
                print(f"    └─ Data: {key_data}")
        
        # Log via reporter if available
        if self.reporter:
            self.reporter.log("event_monitored", 
                             event_type=event.event_type.value,
                             source=event.source,
                             description=event_description,
                             **event.data)
    
    def _create_state_snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of current system state."""
        return {
            'active_tasks_count': len(self.state_tracker['active_tasks']),
            'agent_count': len(self.state_tracker['agent_status']),
            'flow_status': self.state_tracker['flow_status'],
            'total_events': len(self.events_log)
        }
    
    # Task lifecycle event handlers
    def _on_task_started(self, event: Event):
        task_id = event.data.get('task_id', 'unknown')
        phase = event.data.get('phase', 'unknown')
        
        self.state_tracker['active_tasks'][task_id] = {
            'status': 'running',
            'agent': event.source,
            'phase': phase,
            'started_at': datetime.now().isoformat(),
            'subtasks': {}
        }
        
        self._log_event(event, f"Task started in {phase} phase")
        
    def _on_task_completed(self, event: Event):
        task_id = event.data.get('task_id', 'unknown')
        
        if task_id in self.state_tracker['active_tasks']:
            self.state_tracker['active_tasks'][task_id]['status'] = 'completed'
            self.state_tracker['active_tasks'][task_id]['completed_at'] = datetime.now().isoformat()
        
        self._log_event(event, "Task completed successfully")
        
    def _on_task_failed(self, event: Event):
        task_id = event.data.get('task_id', 'unknown')
        error = event.data.get('error', 'Unknown error')
        
        if task_id in self.state_tracker['active_tasks']:
            self.state_tracker['active_tasks'][task_id]['status'] = 'failed'
            self.state_tracker['active_tasks'][task_id]['error'] = error
        
        self._log_event(event, f"Task failed: {error}")
        
    def _on_task_progress(self, event: Event):
        task_id = event.data.get('task_id', 'unknown')
        phase = event.data.get('phase', 'unknown')
        subtask_name = event.data.get('subtask_name')
        tool_used = event.data.get('tool_used')
        
        # Update task progress
        if task_id in self.state_tracker['active_tasks']:
            task = self.state_tracker['active_tasks'][task_id]
            task['phase'] = phase
            
            if subtask_name:
                subtask_id = event.data.get('subtask_id', subtask_name)
                task['subtasks'][subtask_id] = {
                    'name': subtask_name,
                    'tool': tool_used,
                    'status': event.data.get('status', 'running'),
                    'timestamp': datetime.now().isoformat()
                }
        
        # Create descriptive message
        if subtask_name and tool_used:
            desc = f"Subtask progress: {subtask_name} using {tool_used}"
        else:
            desc = f"Task progress in {phase} phase"
            
        self._log_event(event, desc)
    
    # Data flow event handlers
    def _on_data_available(self, event: Event):
        self._log_event(event, "Data available for processing")
        
    def _on_data_processed(self, event: Event):
        self._log_event(event, "Data processed successfully")
        
    def _on_data_error(self, event: Event):
        error = event.data.get('error', 'Data processing error')
        self._log_event(event, f"Data error: {error}")
    
    # Agent event handlers
    def _on_agent_ready(self, event: Event):
        self.state_tracker['agent_status'][event.source] = 'ready'
        self._log_event(event, "Agent ready for tasks")
        
    def _on_agent_busy(self, event: Event):
        self.state_tracker['agent_status'][event.source] = 'busy'
        self._log_event(event, "Agent busy with task")
        
    def _on_agent_error(self, event: Event):
        self.state_tracker['agent_status'][event.source] = 'error'
        error = event.data.get('error', 'Agent error')
        self._log_event(event, f"Agent error: {error}")
    
    # Flow event handlers
    def _on_flow_started(self, event: Event):
        self.state_tracker['flow_status'] = 'running'
        self._log_event(event, "Flow execution started")
        
    def _on_flow_completed(self, event: Event):
        self.state_tracker['flow_status'] = 'completed'
        self._log_event(event, "Flow execution completed")
        
    def _on_flow_error(self, event: Event):
        self.state_tracker['flow_status'] = 'error'
        error = event.data.get('error', 'Flow error')
        self._log_event(event, f"Flow error: {error}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'timestamp': datetime.now().isoformat(),
            'flow_status': self.state_tracker['flow_status'],
            'active_tasks': len([t for t in self.state_tracker['active_tasks'].values() if t['status'] == 'running']),
            'completed_tasks': len([t for t in self.state_tracker['active_tasks'].values() if t['status'] == 'completed']),
            'failed_tasks': len([t for t in self.state_tracker['active_tasks'].values() if t['status'] == 'failed']),
            'agent_status': self.state_tracker['agent_status'],
            'total_events': len(self.events_log),
            'recent_events': self.events_log[-5:] if self.events_log else []
        }
    
    def export_execution_log(self, file_path: Optional[str] = None) -> str:
        """Export complete execution log to JSON file."""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"execution_log_{timestamp}.json"
        
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_events': len(self.events_log),
                'execution_duration': self._calculate_execution_duration()
            },
            'final_state': self.state_tracker,
            'events': self.events_log
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"📄 [MONITOR] Execution log exported to: {file_path}")
            return file_path
        except Exception as e:
            print(f"❌ [MONITOR] Failed to export log: {e}")
            return ""
    
    def _calculate_execution_duration(self) -> str:
        """Calculate total execution duration."""
        if not self.events_log:
            return "0s"
        
        try:
            first_event = datetime.fromisoformat(self.events_log[0]['timestamp'])
            last_event = datetime.fromisoformat(self.events_log[-1]['timestamp'])
            duration = last_event - first_event
            return f"{duration.total_seconds():.2f}s"
        except Exception:
            return "unknown"
    
    def print_execution_summary(self):
        """Print a comprehensive execution summary."""
        status = self.get_system_status()
        
        print("\n" + "="*60)
        print("📊 EXECUTION SUMMARY")
        print("="*60)
        print(f"⏱️  Duration: {self._calculate_execution_duration()}")
        print(f"🔄 Flow Status: {status['flow_status']}")
        print(f"✅ Completed Tasks: {status['completed_tasks']}")
        print(f"❌ Failed Tasks: {status['failed_tasks']}")
        print(f"🏃 Active Tasks: {status['active_tasks']}")
        print(f"📨 Total Events: {status['total_events']}")
        
        if status['agent_status']:
            print(f"\n🤖 Agent Status:")
            for agent, stat in status['agent_status'].items():
                print(f"   - {agent}: {stat}")
        
        print(f"\n📋 Recent Activity:")
        for event in status['recent_events']:
            time_str = event['timestamp'][11:19]  # Extract HH:MM:SS
            print(f"   {time_str} | {event['source']} | {event['description']}")
        
        print("="*60)