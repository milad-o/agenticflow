"""Tool wrapper for observability."""

import time
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool
from .events import ToolExecuted, ToolArgs, ToolResult, ToolError


class ObservableTool(BaseTool):
    """Tool wrapper that emits observability events."""
    
    def _filter_serializable_args(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out non-serializable objects from kwargs."""
        serializable_kwargs = {}
        for key, value in kwargs.items():
            try:
                import json
                json.dumps(value)
                serializable_kwargs[key] = value
            except (TypeError, ValueError):
                serializable_kwargs[key] = str(type(value).__name__)
        return serializable_kwargs
    
    def __init__(self, tool: BaseTool, flow_id: str, agent_name: str, event_logger):
        # Initialize BaseTool with original tool properties first
        super().__init__(
            name=tool.name,
            description=tool.description,
            args_schema=tool.args_schema
        )
        
        # Store attributes in __dict__ to avoid Pydantic restrictions
        self.__dict__['_original_tool'] = tool
        self.__dict__['_flow_id'] = flow_id
        self.__dict__['_agent_name'] = agent_name
        self.__dict__['_event_logger'] = event_logger
    
    def _run(self, *args, **kwargs) -> Any:
        """Execute tool with observability events."""
        return self._execute_with_observability(lambda: self.__dict__['_original_tool'].run(*args, **kwargs), kwargs)
    
    async def _arun(self, *args, **kwargs) -> Any:
        """Execute tool asynchronously with observability events."""
        return await self._execute_with_observability_async(lambda: self.__dict__['_original_tool'].arun(*args, **kwargs), kwargs)
    
    def run(self, *args, **kwargs) -> Any:
        """Execute tool with observability events (public interface)."""
        try:
            return self._execute_with_observability(lambda: self.__dict__['_original_tool'].run(*args, **kwargs), kwargs)
        except Exception as e:
            # Fallback to original tool
            return self.__dict__['_original_tool'].run(*args, **kwargs)
    
    async def arun(self, *args, **kwargs) -> Any:
        """Execute tool asynchronously with observability events (public interface)."""
        return await self._execute_with_observability_async(lambda: self.__dict__['_original_tool'].arun(*args, **kwargs), kwargs)
    
    def _execute_with_observability(self, tool_func, kwargs: Dict[str, Any]) -> Any:
        """Execute tool with observability events."""
        event_logger = self.__dict__.get('_event_logger')
        
        # Emit tool args event
        if event_logger:
            tool_args_event = ToolArgs(
                flow_id=self.__dict__['_flow_id'],
                agent_name=self.__dict__['_agent_name'],
                tool_name=self.name,
                args=self._filter_serializable_args(kwargs)
            )
            event_logger._events.append(tool_args_event)
            event_logger.get_event_bus().emit_event_sync(tool_args_event)
        
        # Emit tool executed event
        if event_logger:
            tool_executed_event = ToolExecuted(
                flow_id=self.__dict__['_flow_id'],
                agent_name=self.__dict__['_agent_name'],
                tool_name=self.name,
                tool_type="function"
            )
            event_logger._events.append(tool_executed_event)
            event_logger.get_event_bus().emit_event_sync(tool_executed_event)
        
        start_time = time.time()
        try:
            # Execute the tool
            result = tool_func()
            
            # Emit tool result event
            if event_logger:
                duration_ms = (time.time() - start_time) * 1000
                tool_result_event = ToolResult(
                    flow_id=self.__dict__['_flow_id'],
                    agent_name=self.__dict__['_agent_name'],
                    tool_name=self.name,
                    result=str(result)[:500],  # Truncate long results
                    duration_ms=duration_ms
                )
                event_logger._events.append(tool_result_event)
                event_logger.get_event_bus().emit_event_sync(tool_result_event)
            
            return result
            
        except Exception as e:
            # Emit tool error event
            if event_logger:
                tool_error_event = ToolError(
                    flow_id=self.__dict__['_flow_id'],
                    agent_name=self.__dict__['_agent_name'],
                    tool_name=self.name,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                event_logger._events.append(tool_error_event)
                event_logger.get_event_bus().emit_event_sync(tool_error_event)
            raise
    
    async def _execute_with_observability_async(self, tool_func, kwargs: Dict[str, Any]) -> Any:
        """Execute tool asynchronously with observability events."""
        # Emit tool args event
        if event_logger:
            tool_args_event = ToolArgs(
                flow_id=self.__dict__['_flow_id'],
                agent_name=self.__dict__['_agent_name'],
                tool_name=self.name,
                args=self._filter_serializable_args(kwargs)
            )
            event_logger._events.append(tool_args_event)
            event_logger.get_event_bus().emit_event_sync(tool_args_event)
        
        # Emit tool executed event
        if event_logger:
            tool_executed_event = ToolExecuted(
                flow_id=self.__dict__['_flow_id'],
                agent_name=self.__dict__['_agent_name'],
                tool_name=self.name,
                tool_type="function"
            )
            event_logger._events.append(tool_executed_event)
            event_logger.get_event_bus().emit_event_sync(tool_executed_event)
        
        start_time = time.time()
        try:
            # Execute the tool
            result = await tool_func()
            
            # Emit tool result event
            if event_logger:
                duration_ms = (time.time() - start_time) * 1000
                tool_result_event = ToolResult(
                    flow_id=self.__dict__['_flow_id'],
                    agent_name=self.__dict__['_agent_name'],
                    tool_name=self.name,
                    result=str(result)[:500],  # Truncate long results
                    duration_ms=duration_ms
                )
                event_logger._events.append(tool_result_event)
                event_logger.get_event_bus().emit_event_sync(tool_result_event)
            
            return result
            
        except Exception as e:
            # Emit tool error event
            if event_logger:
                tool_error_event = ToolError(
                    flow_id=self.__dict__['_flow_id'],
                    agent_name=self.__dict__['_agent_name'],
                    tool_name=self.name,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                event_logger._events.append(tool_error_event)
                event_logger.get_event_bus().emit_event_sync(tool_error_event)
            raise