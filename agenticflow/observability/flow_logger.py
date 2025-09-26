"""
Comprehensive Colorful Logging System for AgenticFlow

This module provides detailed, timestamped, colorful logging for all flow entities
including tasks, subtasks, reflections, decisions, and DAG structures.
"""

import sys
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import json


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Standard colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class FlowLogger:
    """
    Comprehensive logging system with colorful, timestamped output
    for all AgenticFlow entities and operations.
    """
    
    def __init__(self, enable_colors: bool = True, min_level: LogLevel = LogLevel.INFO):
        self.enable_colors = enable_colors
        self.min_level = min_level
        self.session_start = datetime.now()
        self.log_entries: List[Dict[str, Any]] = []
        
        # Entity-specific color schemes
        self.entity_colors = {
            'flow': Colors.BRIGHT_BLUE,
            'orchestrator': Colors.BRIGHT_MAGENTA,
            'planner': Colors.BRIGHT_CYAN,
            'agent': Colors.BRIGHT_GREEN,
            'task': Colors.YELLOW,
            'subtask': Colors.BRIGHT_YELLOW,
            'tool': Colors.CYAN,
            'dag': Colors.MAGENTA,
            'reflection': Colors.BRIGHT_WHITE,
            'decision': Colors.BRIGHT_RED,
            'event': Colors.BRIGHT_BLACK
        }
        
        # Level-specific formatting
        self.level_formats = {
            LogLevel.DEBUG: (Colors.BRIGHT_BLACK, "🔍"),
            LogLevel.INFO: (Colors.BLUE, "ℹ️"),
            LogLevel.SUCCESS: (Colors.BRIGHT_GREEN, "✅"),
            LogLevel.WARNING: (Colors.YELLOW, "⚠️"),
            LogLevel.ERROR: (Colors.RED, "❌"),
            LogLevel.CRITICAL: (Colors.BRIGHT_RED + Colors.BOLD, "🚨")
        }
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if log level meets minimum threshold."""
        level_order = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.SUCCESS, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        return level_order.index(level) >= level_order.index(self.min_level)
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color if colors are enabled."""
        if not self.enable_colors:
            return text
        return f"{color}{text}{Colors.RESET}"
    
    def _format_timestamp(self) -> str:
        """Format current timestamp with session duration."""
        now = datetime.now()
        duration = (now - self.session_start).total_seconds()
        return f"{now.strftime('%H:%M:%S.%f')[:-3]} (+{duration:06.2f}s)"
    
    def _log_entry(self, entity: str, level: LogLevel, message: str, **kwargs):
        """Core logging method with structured output."""
        if not self._should_log(level):
            return
        
        timestamp = self._format_timestamp()
        level_color, level_icon = self.level_formats[level]
        entity_color = self.entity_colors.get(entity.lower(), Colors.WHITE)
        
        # Create log entry for storage
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'entity': entity,
            'level': level.value,
            'message': message,
            'data': kwargs
        }
        self.log_entries.append(log_entry)
        
        # Format console output
        entity_tag = self._colorize(f"[{entity.upper()}]", entity_color + Colors.BOLD)
        level_tag = self._colorize(f"{level_icon} {level.value}", level_color)
        timestamp_tag = self._colorize(timestamp, Colors.BRIGHT_BLACK)
        
        # Main message with action attribution
        action_separator = " 🔹 " if "DEBUG" not in level.value else " 🔸 "
        main_line = f"{timestamp_tag} {level_tag} {entity_tag}{action_separator}{message}"
        print(main_line)
        
        # Additional data formatting
        if kwargs:
            for key, value in kwargs.items():
                if key in ['dag_structure', 'reflection_result', 'decision_tree']:
                    self._format_structured_data(key, value, indent="    ")
                else:
                    formatted_value = self._format_value(value)
                    data_line = f"    └─ {self._colorize(key, Colors.CYAN)}: {formatted_value}"
                    print(data_line)
    
    def _format_value(self, value: Any) -> str:
        """Format values for display."""
        if isinstance(value, (dict, list)):
            if len(str(value)) > 100:
                return f"{str(value)[:97]}..."
            return str(value)
        elif isinstance(value, str) and len(value) > 80:
            return f"{value[:77]}..."
        return str(value)
    
    def _format_structured_data(self, key: str, data: Any, indent: str = ""):
        """Format complex structured data like DAGs, reflections, etc."""
        header = f"{indent}┌─ {self._colorize(key.upper(), Colors.BOLD + Colors.YELLOW)}"
        print(header)
        
        if key == 'dag_structure' and isinstance(data, dict):
            self._format_dag_structure(data, indent + "│  ")
        elif key == 'reflection_result' and isinstance(data, dict):
            self._format_reflection(data, indent + "│  ")
        elif key == 'decision_tree' and isinstance(data, dict):
            self._format_decision_tree(data, indent + "│  ")
        else:
            # Generic structured data
            try:
                formatted = json.dumps(data, indent=2, default=str)
                for line in formatted.split('\n')[:10]:  # Limit lines
                    print(f"{indent}│  {line}")
            except:
                print(f"{indent}│  {str(data)}")
        
        print(f"{indent}└─")
    
    def _format_dag_structure(self, dag_data: Dict[str, Any], indent: str):
        """Format DAG structure visualization."""
        nodes = dag_data.get('nodes', [])
        edges = dag_data.get('edges', [])
        
        print(f"{indent}Nodes: {len(nodes)}")
        for i, node in enumerate(nodes):
            status_icon = "✅" if node.get('status') == 'completed' else "⏳" if node.get('status') == 'running' else "⏸️"
            print(f"{indent}  {i+1}. {status_icon} {node.get('name', 'Unknown')} ({node.get('tool', 'No tool')})")
        
        if edges:
            print(f"{indent}Dependencies:")
            for edge in edges:
                print(f"{indent}  {edge.get('from', '?')} → {edge.get('to', '?')}")
    
    def _format_reflection(self, reflection_data: Dict[str, Any], indent: str):
        """Format reflection results."""
        print(f"{indent}Input: {reflection_data.get('input', 'Unknown')[:60]}...")
        print(f"{indent}Analysis: {reflection_data.get('analysis', 'None')}")
        print(f"{indent}Confidence: {reflection_data.get('confidence', 'Unknown')}")
        if 'reasoning' in reflection_data:
            print(f"{indent}Reasoning: {reflection_data['reasoning'][:80]}...")
    
    def _format_decision_tree(self, decision_data: Dict[str, Any], indent: str):
        """Format decision tree."""
        print(f"{indent}Options Considered: {len(decision_data.get('options', []))}")
        chosen = decision_data.get('chosen')
        if chosen:
            print(f"{indent}Chosen: {self._colorize(chosen, Colors.BRIGHT_GREEN)}")
        if 'reasoning' in decision_data:
            print(f"{indent}Reasoning: {decision_data['reasoning']}")
    
    # Entity-specific logging methods
    def flow(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Log flow-level events."""
        self._log_entry("flow", level, message, **kwargs)
    
    def orchestrator(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Log orchestrator events."""
        self._log_entry("orchestrator", level, message, **kwargs)
    
    def planner(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Log planner events with DAG visualization."""
        self._log_entry("planner", level, message, **kwargs)
    
    def agent(self, message: str, agent_name: str = "unknown", level: LogLevel = LogLevel.INFO, **kwargs):
        """Log agent events."""
        self._log_entry(f"agent:{agent_name}", level, message, **kwargs)
    
    def task(self, message: str, task_id: str = "unknown", level: LogLevel = LogLevel.INFO, **kwargs):
        """Log task lifecycle events with timestamps."""
        kwargs['task_id'] = task_id
        kwargs['timestamp'] = datetime.now().isoformat()
        self._log_entry("task", level, message, **kwargs)
    
    def subtask(self, message: str, subtask_id: str = "unknown", parent_task: str = "unknown", level: LogLevel = LogLevel.INFO, **kwargs):
        """Log subtask events with parent relationship."""
        kwargs['subtask_id'] = subtask_id
        kwargs['parent_task'] = parent_task
        kwargs['timestamp'] = datetime.now().isoformat()
        self._log_entry("subtask", level, message, **kwargs)
    
    def tool(self, message: str, tool_name: str = "unknown", level: LogLevel = LogLevel.INFO, **kwargs):
        """Log tool execution."""
        self._log_entry(f"tool:{tool_name}", level, message, **kwargs)
    
    def reflection(self, message: str, entity: str = "unknown", level: LogLevel = LogLevel.INFO, **kwargs):
        """Log reflection processes."""
        self._log_entry(f"reflection:{entity}", level, message, **kwargs)
    
    def decision(self, message: str, entity: str = "unknown", level: LogLevel = LogLevel.INFO, **kwargs):
        """Log decision making."""
        self._log_entry(f"decision:{entity}", level, message, **kwargs)
    
    def event(self, message: str, event_type: str = "unknown", level: LogLevel = LogLevel.DEBUG, **kwargs):
        """Log event bus events."""
        self._log_entry(f"event:{event_type}", level, message, **kwargs)
    
    def separator(self, title: str = ""):
        """Print a visual separator."""
        width = 80
        if title:
            title_formatted = f" {title} "
            padding = (width - len(title_formatted)) // 2
            line = "═" * padding + title_formatted + "═" * (width - padding - len(title_formatted))
        else:
            line = "═" * width
        
        print(self._colorize(line, Colors.BRIGHT_BLUE + Colors.BOLD))
    
    def session_summary(self):
        """Print session summary."""
        duration = (datetime.now() - self.session_start).total_seconds()
        
        self.separator("SESSION SUMMARY")
        self.flow(f"Session Duration: {duration:.2f}s", level=LogLevel.SUCCESS)
        self.flow(f"Total Log Entries: {len(self.log_entries)}", level=LogLevel.SUCCESS)
        
        # Count by entity
        entity_counts = {}
        for entry in self.log_entries:
            entity = entry['entity'].split(':')[0]
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
        
        for entity, count in sorted(entity_counts.items()):
            self.flow(f"{entity.title()} Events: {count}", level=LogLevel.INFO)
        
        self.separator()
    
    def export_log(self, file_path: Optional[str] = None) -> str:
        """Export complete log to JSON file."""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"flow_log_{timestamp}.json"
        
        export_data = {
            'metadata': {
                'session_start': self.session_start.isoformat(),
                'export_timestamp': datetime.now().isoformat(),
                'total_entries': len(self.log_entries),
                'session_duration': (datetime.now() - self.session_start).total_seconds()
            },
            'log_entries': self.log_entries
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            self.flow(f"Log exported to: {file_path}", level=LogLevel.SUCCESS)
            return file_path
        except Exception as e:
            self.flow(f"Failed to export log: {e}", level=LogLevel.ERROR)
            return ""


# Global logger instance
_global_flow_logger = None


def get_flow_logger() -> FlowLogger:
    """Get the global flow logger instance."""
    global _global_flow_logger
    if _global_flow_logger is None:
        _global_flow_logger = FlowLogger()
    return _global_flow_logger


def set_flow_logger(logger: FlowLogger):
    """Set the global flow logger instance."""
    global _global_flow_logger
    _global_flow_logger = logger