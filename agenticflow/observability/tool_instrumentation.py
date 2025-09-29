"""Tool instrumentation to capture actual tool arguments."""

import functools
from typing import Any, Dict, List
from langchain_core.tools import BaseTool
from .events import ToolArgs, ToolExecuted, ToolResult, ToolError
from .tool_wrapper import ObservableTool


def instrument_tool(tool: BaseTool, flow_id: str, agent_name: str, event_logger) -> BaseTool:
    """Instrument a tool to capture actual arguments and emit events."""
    
    # Get the original run method
    original_run = tool.run
    original_arun = tool.arun
    
    # Track processed tool calls to avoid duplicates
    processed_calls = set()
    last_call_time = {}
    
    def instrumented_run(*args, **kwargs):
        """Instrumented run method that captures actual arguments."""
        
        import time
        current_time = time.time()
        
        # Check if this tool was called recently (within 1 second)
        if tool.name in last_call_time and (current_time - last_call_time[tool.name]) < 1.0:
            return original_run(*args, **kwargs)
        
        # Update last call time
        last_call_time[tool.name] = current_time
        
        # Extract meaningful arguments from args and kwargs
        meaningful_args = {}
        
        # Get the tool's input schema to understand parameter names
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema_fields = tool.args_schema.model_fields
            param_names = list(schema_fields.keys())
            
            # Map positional args to parameter names
            for i, arg in enumerate(args):
                if i < len(param_names):
                    meaningful_args[param_names[i]] = arg
            
            # Add keyword arguments
            for key, value in kwargs.items():
                if key in param_names:
                    meaningful_args[key] = value
        
        # If we have nested dictionaries (from LangGraph), flatten them
        flattened_args = {}
        for key, value in meaningful_args.items():
            if isinstance(value, dict):
                # This is a nested dict from LangGraph, extract all inner values
                for inner_key, inner_value in value.items():
                    flattened_args[inner_key] = inner_value
            else:
                flattened_args[key] = value
        
        meaningful_args = flattened_args
        
        # Emit tool args event with actual arguments
        if event_logger:
            # Check if we've already emitted this event recently
            recent_events = [e for e in event_logger._events[-10:] if e.event_type == 'tool_args' and e.tool_name == tool.name]
            if not recent_events:
                tool_args_event = ToolArgs(
                    flow_id=flow_id,
                    agent_name=agent_name,
                    tool_name=tool.name,
                    args=meaningful_args
                )
                event_logger._events.append(tool_args_event)
                event_logger.get_event_bus().emit_event_sync(tool_args_event)
        
        # Emit tool executed event
        if event_logger:
            # Check if we've already emitted this event recently
            recent_events = [e for e in event_logger._events[-10:] if e.event_type == 'tool_executed' and e.tool_name == tool.name]
            if not recent_events:
                tool_executed_event = ToolExecuted(
                    flow_id=flow_id,
                    agent_name=agent_name,
                    tool_name=tool.name,
                    tool_type="function"
                )
                event_logger._events.append(tool_executed_event)
                event_logger.get_event_bus().emit_event_sync(tool_executed_event)
        
        # Execute the original tool
        try:
            result = original_run(*args, **kwargs)
            
            # Emit tool result event
            if event_logger:
                # Check if we've already emitted this event recently
                recent_events = [e for e in event_logger._events[-10:] if e.event_type == 'tool_result' and e.tool_name == tool.name]
                if not recent_events:
                    tool_result_event = ToolResult(
                        flow_id=flow_id,
                        agent_name=agent_name,
                        tool_name=tool.name,
                        result=str(result)[:500],
                        duration_ms=0,  # We don't have timing here
                        success=True
                    )
                    event_logger._events.append(tool_result_event)
                    event_logger.get_event_bus().emit_event_sync(tool_result_event)
            
            return result
            
        except Exception as e:
            # Emit tool error event
            if event_logger:
                tool_error_event = ToolError(
                    flow_id=flow_id,
                    agent_name=agent_name,
                    tool_name=tool.name,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                event_logger._events.append(tool_error_event)
                event_logger.get_event_bus().emit_event_sync(tool_error_event)
            raise
    
    async def instrumented_arun(*args, **kwargs):
        """Instrumented async run method that captures actual arguments."""
        
        import time
        current_time = time.time()
        
        # Check if this tool was called recently (within 1 second)
        if tool.name in last_call_time and (current_time - last_call_time[tool.name]) < 1.0:
            return await original_arun(*args, **kwargs)
        
        # Update last call time
        last_call_time[tool.name] = current_time
        
        # Extract meaningful arguments from args and kwargs
        meaningful_args = {}
        
        # Get the tool's input schema to understand parameter names
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema_fields = tool.args_schema.model_fields
            param_names = list(schema_fields.keys())
            
            # Map positional args to parameter names
            for i, arg in enumerate(args):
                if i < len(param_names):
                    meaningful_args[param_names[i]] = arg
            
            # Add keyword arguments
            for key, value in kwargs.items():
                if key in param_names:
                    meaningful_args[key] = value
        
        # If we have nested dictionaries (from LangGraph), flatten them
        flattened_args = {}
        for key, value in meaningful_args.items():
            if isinstance(value, dict):
                # This is a nested dict from LangGraph, extract all inner values
                for inner_key, inner_value in value.items():
                    flattened_args[inner_key] = inner_value
            else:
                flattened_args[key] = value
        
        meaningful_args = flattened_args
        
        # Emit tool args event with actual arguments
        if event_logger:
            # Check if we've already emitted this event recently
            recent_events = [e for e in event_logger._events[-10:] if e.event_type == 'tool_args' and e.tool_name == tool.name]
            if not recent_events:
                tool_args_event = ToolArgs(
                    flow_id=flow_id,
                    agent_name=agent_name,
                    tool_name=tool.name,
                    args=meaningful_args
                )
                event_logger._events.append(tool_args_event)
                event_logger.get_event_bus().emit_event_sync(tool_args_event)
        
        # Emit tool executed event
        if event_logger:
            # Check if we've already emitted this event recently
            recent_events = [e for e in event_logger._events[-10:] if e.event_type == 'tool_executed' and e.tool_name == tool.name]
            if not recent_events:
                tool_executed_event = ToolExecuted(
                    flow_id=flow_id,
                    agent_name=agent_name,
                    tool_name=tool.name,
                    tool_type="function"
                )
                event_logger._events.append(tool_executed_event)
                event_logger.get_event_bus().emit_event_sync(tool_executed_event)
        
        # Execute the original tool
        try:
            result = await original_arun(*args, **kwargs)
            
            # Emit tool result event
            if event_logger:
                # Check if we've already emitted this event recently
                recent_events = [e for e in event_logger._events[-10:] if e.event_type == 'tool_result' and e.tool_name == tool.name]
                if not recent_events:
                    tool_result_event = ToolResult(
                        flow_id=flow_id,
                        agent_name=agent_name,
                        tool_name=tool.name,
                        result=str(result)[:500],
                        duration_ms=0,  # We don't have timing here
                        success=True
                    )
                    event_logger._events.append(tool_result_event)
                    event_logger.get_event_bus().emit_event_sync(tool_result_event)
            
            return result
            
        except Exception as e:
            # Emit tool error event
            if event_logger:
                tool_error_event = ToolError(
                    flow_id=flow_id,
                    agent_name=agent_name,
                    tool_name=tool.name,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                event_logger._events.append(tool_error_event)
                event_logger.get_event_bus().emit_event_sync(tool_error_event)
            raise
    
    # Create a new tool instance with instrumented methods
    # Use the original tool class but monkey patch the methods
    instrumented_tool = tool
    
    # Store original methods
    instrumented_tool._original_run = original_run
    instrumented_tool._original_arun = original_arun
    
    # Replace the methods using __dict__ to bypass Pydantic restrictions
    instrumented_tool.__dict__['run'] = instrumented_run
    instrumented_tool.__dict__['arun'] = instrumented_arun
    
    return instrumented_tool
