"""Observable ReAct agent with basic observability."""

import time
from typing import Any, Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool
from .events import (
    Event, AgentStarted, AgentCompleted, AgentError, AgentThinking, AgentWorking
)
from .tool_instrumentation import instrument_tool


class ObservableReActAgent:
    """ReAct agent with basic observability."""
    
    def __init__(self, llm: ChatOpenAI, tools: List[BaseTool], flow_id: str, agent_name: str, event_logger):
        self.llm = llm
        self.tools = tools
        self.flow_id = flow_id
        self.agent_name = agent_name
        self.event_logger = event_logger
        
        # Instrument tools with observability
        self._observable_tools = [
            instrument_tool(tool, flow_id, agent_name, event_logger)
            for tool in tools
        ]
        
        # Create the base ReAct agent with observable tools
        self._react_agent = create_react_agent(llm, tools=self._observable_tools)
    
    def _emit_event(self, event: Event) -> None:
        """Emit an event to both logger storage and console."""
        if self.event_logger:
            # Store in logger's memory
            self.event_logger._events.append(event)
            # Emit to console via event bus
            self.event_logger.get_event_bus().emit_event_sync(event)
    
    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the agent with basic observability."""
        # Emit agent started event
        if self.event_logger:
            agent_started = AgentStarted(
                flow_id=self.flow_id,
                agent_name=self.agent_name,
                agent_type="ReActAgent",
                tools=self.tools
            )
            self._emit_event(agent_started)
        
        # Emit agent thinking event
        if self.event_logger:
            agent_thinking = AgentThinking(
                flow_id=self.flow_id,
                agent_name=self.agent_name,
                thinking_process="Analyzing request and planning tool usage",
                current_step="Initial reasoning"
            )
            self._emit_event(agent_thinking)
        
        # Emit agent working event
        if self.event_logger:
            agent_working = AgentWorking(
                flow_id=self.flow_id,
                agent_name=self.agent_name,
                task_description="Executing ReAct reasoning loop with tools",
                progress=0.0
            )
            self._emit_event(agent_working)
        
        start_time = time.time()
        
        try:
            # Execute the ReAct agent
            result = self._react_agent.invoke(state)
            
            # Emit agent completed event
            if self.event_logger:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Count tools used from the result
                tools_used = 0
                if "messages" in result:
                    for msg in result["messages"]:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            tools_used += len(msg.tool_calls)
                
                agent_completed = AgentCompleted(
                    flow_id=self.flow_id,
                    agent_name=self.agent_name,
                    agent_type="ReActAgent",
                    duration_ms=duration_ms,
                    tools_used=tools_used
                )
                self._emit_event(agent_completed)
            
            return result
            
        except Exception as e:
            # Emit agent error event
            if self.event_logger:
                agent_error = AgentError(
                    flow_id=self.flow_id,
                    agent_name=self.agent_name,
                    agent_type="ReActAgent",
                    error_message=str(e),
                    error_type=type(e).__name__,
                    stack_trace=str(e.__traceback__) if hasattr(e, '__traceback__') else None
                )
                self._emit_event(agent_error)
            
            raise
    
    async def ainvoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Async invoke the agent with basic observability."""
        # Emit agent started event
        if self.event_logger:
            agent_started = AgentStarted(
                flow_id=self.flow_id,
                agent_name=self.agent_name,
                agent_type="ReActAgent",
                tools=self.tools
            )
            self._emit_event(agent_started)
        
        # Emit agent thinking event
        if self.event_logger:
            agent_thinking = AgentThinking(
                flow_id=self.flow_id,
                agent_name=self.agent_name,
                thinking_process="Analyzing request and planning tool usage",
                current_step="Initial reasoning"
            )
            self._emit_event(agent_thinking)
        
        # Emit agent working event
        if self.event_logger:
            agent_working = AgentWorking(
                flow_id=self.flow_id,
                agent_name=self.agent_name,
                task_description="Executing ReAct reasoning loop with tools",
                progress=0.0
            )
            self._emit_event(agent_working)
        
        start_time = time.time()
        
        try:
            # Execute the ReAct agent
            result = await self._react_agent.ainvoke(state)
            
            # Emit agent completed event
            if self.event_logger:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Count tools used from the result
                tools_used = 0
                if "messages" in result:
                    for msg in result["messages"]:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            tools_used += len(msg.tool_calls)
                
                agent_completed = AgentCompleted(
                    flow_id=self.flow_id,
                    agent_name=self.agent_name,
                    agent_type="ReActAgent",
                    duration_ms=duration_ms,
                    tools_used=tools_used
                )
                self._emit_event(agent_completed)
            
            return result
            
        except Exception as e:
            # Emit agent error event
            if self.event_logger:
                agent_error = AgentError(
                    flow_id=self.flow_id,
                    agent_name=self.agent_name,
                    agent_type="ReActAgent",
                    error_message=str(e),
                    error_type=type(e).__name__,
                    stack_trace=str(e.__traceback__) if hasattr(e, '__traceback__') else None
                )
                self._emit_event(agent_error)
            
            raise