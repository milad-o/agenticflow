"""
Core Agent class for AgenticFlow.

Implements the base Agent with async execution, tool integration, memory management,
error recovery with retries, and self-verification capabilities.
"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Union

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..communication.a2a_handler import A2AHandler, MessageType
from ..config.settings import AgentConfig, ExecutionMode, ErrorRecoveryStrategy
from ..llm_providers import LLMProviderFactory, get_llm_manager
from ..memory import AsyncMemory, MemoryFactory
from ..tools.base_tool import AsyncTool, ToolRegistry, ToolResult, get_tool_registry
from ..orchestration import ToolSelector, RuleBasedToolSelector, ParameterExtractor
from ..mcp.manager import MCPServerManager
from ..visualization.mixins import AgentVisualizationMixin

logger = structlog.get_logger(__name__)


class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass


class AgentState:
    """Agent state management."""
    
    def __init__(self) -> None:
        """Initialize agent state."""
        self.status = "idle"  # idle, thinking, executing, waiting, error
        self.current_task: Optional[str] = None
        self.last_action: Optional[str] = None
        self.error_count = 0
        self.total_tasks = 0
        self.successful_tasks = 0
        self.start_time = time.time()
        self.context: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "status": self.status,
            "current_task": self.current_task,
            "last_action": self.last_action,
            "error_count": self.error_count,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "uptime": time.time() - self.start_time,
            "success_rate": self.successful_tasks / max(self.total_tasks, 1),
            "context": self.context,
        }


class Agent(AgentVisualizationMixin):
    """Base Agent class with async functionality and tool integration."""
    
    def __init__(self, config: AgentConfig) -> None:
        """Initialize the agent."""
        self.config = config
        self.name = config.name
        self.id = f"{config.name}_{str(uuid.uuid4())[:8]}"
        self.logger = logger.bind(agent_id=self.id, agent_name=self.name)
        
        # State management
        self.state = AgentState()
        self._running = False
        
        # Core components
        self._llm_provider = None
        self._memory: Optional[AsyncMemory] = None
        self._tool_registry: Optional[ToolRegistry] = None
        self._a2a_handler: Optional[A2AHandler] = None
        self._mcp_manager: Optional[MCPServerManager] = None
        
        # Execution control
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._execution_lock = asyncio.Lock()
        
        self.logger.info(f"Agent {self.name} initialized")
    
    async def start(self) -> None:
        """Start the agent."""
        if self._running:
            return
        
        self._running = True
        
        try:
            # Initialize LLM provider
            await self._initialize_llm()
            
            # Initialize memory
            await self._initialize_memory()
            
            # Initialize tool registry
            await self._initialize_tools()
            
            # Initialize MCP servers if configured
            if self.config.mcp_config:
                await self._initialize_mcp()
            
            # Initialize A2A communication if enabled
            if self.config.enable_a2a_communication:
                await self._initialize_a2a()
            
            self.state.status = "idle"
            self.logger.info(f"Agent {self.name} started successfully")
            
        except Exception as e:
            self.state.status = "error"
            self.logger.error(f"Failed to start agent: {e}")
            await self.stop()
            raise AgentError(f"Failed to start agent: {e}")
    
    async def stop(self) -> None:
        """Stop the agent."""
        if not self._running:
            return
        
        self._running = False
        self.state.status = "stopped"
        
        # Stop MCP servers
        if self._mcp_manager:
            await self._mcp_manager.stop()
        
        # Stop A2A handler
        if self._a2a_handler:
            await self._a2a_handler.stop()
        
        # Save memory if configured
        if self._memory and self.config.memory.vector_store_path:
            try:
                await self._memory.save()
                self.logger.info("Memory saved successfully")
            except Exception as e:
                self.logger.warning(f"Failed to save memory: {e}")
        
        self.logger.info(f"Agent {self.name} stopped")
    
    async def execute_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task with full error recovery and self-verification."""
        if not self._running:
            raise AgentError("Agent is not running")
        
        task_id = str(uuid.uuid4())
        self.state.current_task = task_id
        self.state.status = "thinking"
        self.state.total_tasks += 1
        
        if context:
            self.state.context.update(context)
        
        # Add system message if configured
        messages = []
        system_content = self.config.instructions or ""
        
        # Add tool usage instructions if tools are available
        if self._tool_registry and self._tool_registry.list_tools():
            tool_info = self._get_tool_usage_instructions()
            system_content += f"\n\n{tool_info}"
        
        if system_content:
            messages.append(SystemMessage(content=system_content))
        
        # Add task message
        messages.append(HumanMessage(content=task))
        
        # Add recent context from memory
        if self._memory:
            recent_messages = await self._memory.get_messages(limit=5)
            messages.extend(recent_messages[-3:])  # Add last 3 messages for context
        
        try:
            async with self._execution_lock:
                # Execute based on configured mode
                if self.config.execution_mode == ExecutionMode.SEQUENTIAL:
                    result = await self._execute_sequential(messages, task_id)
                elif self.config.execution_mode == ExecutionMode.PARALLEL:
                    result = await self._execute_parallel(messages, task_id)
                elif self.config.execution_mode == ExecutionMode.GRAPH:
                    result = await self._execute_graph(messages, task_id)
                elif self.config.execution_mode == ExecutionMode.CONTROLLED:
                    result = await self._execute_controlled(task, task_id)
                else:
                    result = await self._execute_sequential(messages, task_id)
                
                # Self-verification if enabled
                if self.config.enable_self_verification:
                    result = await self._verify_result(task, result, task_id)
                
                # Store in memory
                if self._memory:
                    await self._memory.add_message(
                        HumanMessage(content=task),
                        metadata={"task_id": task_id, "timestamp": time.time()}
                    )
                    await self._memory.add_message(
                        AIMessage(content=str(result.get("response", ""))),
                        metadata={"task_id": task_id, "timestamp": time.time()}
                    )
                
                self.state.successful_tasks += 1
                self.state.status = "idle"
                self.state.current_task = None
                
                self.logger.info(f"Task {task_id} completed successfully")
                return result
        
        except Exception as e:
            self.state.error_count += 1
            self.state.status = "error"
            self.logger.error(f"Task {task_id} failed: {e}")
            
            # Apply error recovery strategy
            if self.config.error_recovery == ErrorRecoveryStrategy.RETRY:
                return await self._retry_task(task, context, task_id, e)
            elif self.config.error_recovery == ErrorRecoveryStrategy.REPHRASE:
                return await self._rephrase_and_retry(task, context, task_id, e)
            elif self.config.error_recovery == ErrorRecoveryStrategy.ESCALATE:
                return await self._escalate_task(task, context, task_id, e)
            else:
                raise AgentExecutionError(f"Task execution failed: {e}")
        
        finally:
            self.state.current_task = None
    
    async def _execute_sequential(self, messages: List[BaseMessage], task_id: str) -> Dict[str, Any]:
        """Execute task sequentially."""
        self.state.status = "executing"
        
        # Get LLM response
        response = await self._get_llm_response(messages)
        
        # Parse and execute any tool calls
        tool_results = await self._parse_and_execute_tools(response, task_id)
        
        # Generate final response incorporating tool results
        if tool_results:
            final_messages = messages + [
                AIMessage(content=response),
                HumanMessage(content=f"Tool results: {tool_results}. Please provide a final response.")
            ]
            final_response = await self._get_llm_response(final_messages)
        else:
            final_response = response
        
        return {
            "response": final_response,
            "tool_results": tool_results,
            "task_id": task_id,
            "execution_mode": "sequential"
        }
    
    async def _execute_parallel(self, messages: List[BaseMessage], task_id: str) -> Dict[str, Any]:
        """Execute task with parallel tool calls."""
        self.state.status = "executing"
        
        # Get LLM response
        response = await self._get_llm_response(messages)
        
        # Parse tool calls
        tool_calls = self._parse_tool_calls(response)
        
        # Execute tools in parallel
        if tool_calls:
            tool_tasks = [
                self._execute_single_tool(tool_name, tool_params) 
                for tool_name, tool_params in tool_calls
            ]
            tool_results = await asyncio.gather(*tool_tasks, return_exceptions=True)
        else:
            tool_results = []
        
        # Generate final response
        if tool_results:
            final_messages = messages + [
                AIMessage(content=response),
                HumanMessage(content=f"Tool results: {tool_results}. Please provide a final response.")
            ]
            final_response = await self._get_llm_response(final_messages)
        else:
            final_response = response
        
        return {
            "response": final_response,
            "tool_results": tool_results,
            "task_id": task_id,
            "execution_mode": "parallel"
        }
    
    async def _execute_graph(self, messages: List[BaseMessage], task_id: str) -> Dict[str, Any]:
        """Execute task using LangGraph (placeholder for now)."""
        # This would integrate with LangGraph for complex workflows
        # For now, fall back to sequential execution
        self.logger.info("Graph execution not yet implemented, falling back to sequential")
        return await self._execute_sequential(messages, task_id)
    
    async def _execute_controlled(self, task: str, task_id: str) -> Dict[str, Any]:
        """Execute task using agent-controlled orchestration."""
        self.state.status = "executing"
        
        # Initialize tool selector and parameter extractor
        tool_selector = getattr(self, '_tool_selector', None)
        if not tool_selector:
            tool_selector = RuleBasedToolSelector(self._tool_registry)
        
        parameter_extractor = ParameterExtractor(self._llm_provider)
        
        # Step 1: Agent selects which tools to use
        selected_tools = tool_selector.select_tools(task, self.state.context)
        self.logger.debug(f"Selected tools for controlled execution: {selected_tools}")
        
        if not selected_tools:
            # No tools needed, generate direct response
            messages = [HumanMessage(content=task)]
            if self.config.instructions:
                messages.insert(0, SystemMessage(content=self.config.instructions))
            response = await self._get_llm_response(messages)
            
            return {
                "response": response,
                "tool_results": [],
                "task_id": task_id,
                "execution_mode": "controlled",
                "selected_tools": []
            }
        
        # Step 2: For each selected tool, extract parameters and execute
        tool_results = []
        execution_context = {}
        
        for tool_name in selected_tools:
            if not self._tool_registry.has_tool(tool_name):
                self.logger.warning(f"Tool '{tool_name}' not available in registry")
                continue
            
            try:
                # Get tool schema for parameter extraction
                tool_schema = self._get_tool_param_schema(tool_name)
                if not tool_schema:
                    self.logger.warning(f"No parameter schema for tool '{tool_name}'")
                    continue
                
                # Step 3: Extract parameters using LLM
                parameters = await parameter_extractor.extract_parameters(
                    task, tool_name, tool_schema, execution_context
                )
                
                if not parameters:
                    tool_results.append({
                        "tool": tool_name,
                        "success": False,
                        "error": "Failed to extract parameters",
                        "parameters": {}
                    })
                    continue
                
                # Step 4: Execute tool
                result = await self._execute_single_tool(tool_name, parameters)
                tool_result = {
                    "tool": tool_name,
                    "parameters": parameters,
                    "result": result.result if result.success else None,
                    "error": result.error if not result.success else None,
                    "success": result.success
                }
                tool_results.append(tool_result)
                
                # Add successful results to context for next tools
                if result.success:
                    execution_context[f"{tool_name}_result"] = result.result
                
            except Exception as e:
                self.logger.error(f"Error executing tool '{tool_name}': {e}")
                tool_results.append({
                    "tool": tool_name,
                    "parameters": {},
                    "result": None,
                    "error": str(e),
                    "success": False
                })
        
        # Step 5: Generate final response based on tool results
        if tool_results:
            final_prompt = f"""
Original task: {task}

Tool execution results:
{self._format_tool_results_for_response(tool_results)}

Please provide a final response that addresses the original task using these results."""
            
            messages = [HumanMessage(content=final_prompt)]
            if self.config.instructions:
                messages.insert(0, SystemMessage(content=self.config.instructions))
            
            final_response = await self._get_llm_response(messages)
        else:
            final_response = "No tools were successfully executed for this task."
        
        return {
            "response": final_response,
            "tool_results": tool_results,
            "task_id": task_id,
            "execution_mode": "controlled",
            "selected_tools": selected_tools
        }
    
    async def _get_llm_response(self, messages: List[BaseMessage]) -> str:
        """Get response from LLM with retries."""
        if not self._llm_provider:
            raise AgentError("LLM provider not initialized")
        
        retry_config = AsyncRetrying(
            stop=stop_after_attempt(self.config.max_retries + 1),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            retry=retry_if_exception_type(Exception),
        )
        
        async for attempt in retry_config:
            with attempt:
                try:
                    return await self._llm_provider.agenerate(messages)
                except Exception as e:
                    self.logger.warning(f"LLM request attempt failed: {e}")
                    raise
    
    async def _parse_and_execute_tools(self, response: str, task_id: str) -> List[Dict[str, Any]]:
        """Parse response for tool calls and execute them."""
        tool_calls = self._parse_tool_calls(response)
        results = []
        
        for tool_name, tool_params in tool_calls:
            try:
                result = await self._execute_single_tool(tool_name, tool_params)
                results.append({
                    "tool": tool_name,
                    "parameters": tool_params,
                    "result": result.result if result.success else None,
                    "error": result.error if not result.success else None,
                    "success": result.success
                })
            except Exception as e:
                results.append({
                    "tool": tool_name,
                    "parameters": tool_params,
                    "result": None,
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    def _parse_tool_calls(self, response: str) -> List[tuple]:
        """Parse tool calls from LLM response."""
        import json
        import re
        
        tool_calls = []
        
        # Debug logging
        self.logger.debug(f"Parsing tool calls from response: {response[:200]}...")
        
        # Improved Pattern 1: Look for JSON code blocks with or without json label
        # Handle multi-line JSON with proper whitespace handling
        json_pattern1 = r'```(?:json)?\s*(\{[\s\S]*?"tool"\s*:\s*"[^"]*?"[\s\S]*?\})\s*```'
        json_matches1 = re.findall(json_pattern1, response, re.IGNORECASE)
        
        # Improved Pattern 2: Look for JSON objects with tool key (outside code blocks)
        # More flexible to capture tool calls in various formats
        json_pattern2 = r'(?<!`)\{[\s\S]*?"tool"\s*:\s*"[^"]*?"[\s\S]*?\}(?!`)'
        json_matches2 = re.findall(json_pattern2, response, re.IGNORECASE)
        
        # Pattern 3: Specific for simpler JSON tool calls
        json_pattern3 = r'\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"parameters"\s*:\s*(\{[^}]*\})\s*\}'
        json_matches3 = re.findall(json_pattern3, response, re.IGNORECASE)
        
        # Pattern 4: Granite format - <tool_call>[{...}] (closing tag optional)
        granite_pattern = r'<tool_call>\s*\[\s*(\{[\s\S]*?\})\s*\](?:\s*</tool_call>)?'
        granite_matches = re.findall(granite_pattern, response, re.IGNORECASE)
        
        # Process matches from patterns 1, 2, and granite
        json_matches = json_matches1 + json_matches2 + granite_matches
        
        self.logger.debug(f"Found {len(json_matches)} JSON matches: {[m[:100] + '...' if len(m) > 100 else m for m in json_matches]}")
        
        # Remove duplicates by converting to set and back
        seen_json = set()
        for match in json_matches:
            clean_match = match.strip()
            if clean_match not in seen_json:
                seen_json.add(clean_match)
                try:
                    # First try to parse as single object
                    tool_call = json.loads(clean_match)
                    
                    # Handle standard format: {"tool": "name", "parameters": {...}}
                    if "tool" in tool_call and "parameters" in tool_call:
                        tool_calls.append((tool_call["tool"], tool_call["parameters"]))
                    # Handle Granite format: {"name": "tool_name", "arguments": {...}}
                    elif "name" in tool_call and "arguments" in tool_call:
                        tool_calls.append((tool_call["name"], tool_call["arguments"]))
                        
                except json.JSONDecodeError as e:
                    # If single object parsing fails, try parsing as array of objects
                    # This handles Granite's format: [{...}, {...}, {...}]
                    try:
                        # Add brackets if missing to make it a proper array
                        array_match = f"[{clean_match}]" if not clean_match.strip().startswith('[') else clean_match
                        tool_array = json.loads(array_match)
                        
                        if isinstance(tool_array, list):
                            for tool_item in tool_array:
                                if isinstance(tool_item, dict):
                                    # Handle standard format
                                    if "tool" in tool_item and "parameters" in tool_item:
                                        tool_calls.append((tool_item["tool"], tool_item["parameters"]))
                                    # Handle Granite format
                                    elif "name" in tool_item and "arguments" in tool_item:
                                        tool_calls.append((tool_item["name"], tool_item["arguments"]))
                    except json.JSONDecodeError:
                        self.logger.debug(f"JSON decode error (both single and array): {e} in: {clean_match[:50]}...")
                        continue
        
        # Process matches from pattern 3 (direct extraction)
        for tool_name, params_str in json_matches3:
            try:
                params = json.loads(params_str)
                tool_calls.append((tool_name, params))
            except json.JSONDecodeError:
                continue
        
        # Look for function call patterns
        # Pattern: tool_name(param1="value1", param2="value2")
        func_pattern = r'(\w+)\(([^)]+)\)'
        func_matches = re.findall(func_pattern, response)
        
        for tool_name, params_str in func_matches:
            # Skip if it's not a registered tool
            if not self._tool_registry or not self._tool_registry.has_tool(tool_name):
                continue
            
            # Parse parameters
            params = {}
            param_pattern = r'(\w+)\s*=\s*(["\']?)([^,"\']*)\2'
            param_matches = re.findall(param_pattern, params_str)
            
            for param_name, quote, value in param_matches:
                # Try to convert to appropriate type
                try:
                    if value.lower() in ['true', 'false']:
                        params[param_name] = value.lower() == 'true'
                    elif value.isdigit():
                        params[param_name] = int(value)
                    elif '.' in value and value.replace('.', '').isdigit():
                        params[param_name] = float(value)
                    else:
                        params[param_name] = value
                except ValueError:
                    params[param_name] = value
            
            tool_calls.append((tool_name, params))
        
        # Look for natural language tool requests and convert them
        if not tool_calls and self._tool_registry:
            tool_calls = self._extract_implicit_tool_calls(response)
        
        self.logger.debug(f"Total tool calls parsed: {len(tool_calls)}")
        for i, (tool_name, params) in enumerate(tool_calls):
            self.logger.debug(f"Tool call {i+1}: {tool_name} with params {params}")
        
        return tool_calls
    
    async def _execute_single_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a single tool."""
        if not self._tool_registry:
            return ToolResult.error_result("Tool registry not initialized")
        
        return await self._tool_registry.execute_tool(tool_name, parameters)
    
    async def _verify_result(self, original_task: str, result: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Self-verify the result."""
        if not self.config.enable_self_verification:
            return result
        
        verification_prompt = f"""
        Original task: {original_task}
        
        My response: {result.get('response', '')}
        Tool results: {result.get('tool_results', [])}
        
        Please verify:
        1. Does this response fully address the original task?
        2. Are there any errors or inconsistencies?
        3. Should any additional actions be taken?
        
        Respond with 'VERIFIED' if the response is complete and correct, or explain what needs to be improved.
        """
        
        verification_messages = [HumanMessage(content=verification_prompt)]
        verification_response = await self._get_llm_response(verification_messages)
        
        result["verification"] = {
            "response": verification_response,
            "verified": "VERIFIED" in verification_response.upper()
        }
        
        return result
    
    async def _retry_task(self, task: str, context: Optional[Dict[str, Any]], task_id: str, error: Exception) -> Dict[str, Any]:
        """Retry task execution."""
        retry_count = self.state.context.get(f"{task_id}_retry_count", 0)
        if retry_count >= self.config.max_retries:
            raise AgentExecutionError(f"Task failed after {retry_count} retries: {error}")
        
        self.state.context[f"{task_id}_retry_count"] = retry_count + 1
        self.logger.info(f"Retrying task {task_id} (attempt {retry_count + 2})")
        
        # Wait before retry
        await asyncio.sleep(2 ** retry_count)
        return await self.execute_task(task, context)
    
    async def _rephrase_and_retry(self, task: str, context: Optional[Dict[str, Any]], task_id: str, error: Exception) -> Dict[str, Any]:
        """Rephrase task and retry."""
        rephrase_prompt = f"""
        The following task failed with error: {error}
        
        Original task: {task}
        
        Please rephrase this task to be clearer and more specific, avoiding the issue that caused the failure.
        """
        
        messages = [HumanMessage(content=rephrase_prompt)]
        rephrased_task = await self._get_llm_response(messages)
        
        self.logger.info(f"Rephrased task: {rephrased_task}")
        return await self.execute_task(rephrased_task, context)
    
    async def _escalate_task(self, task: str, context: Optional[Dict[str, Any]], task_id: str, error: Exception) -> Dict[str, Any]:
        """Escalate task (placeholder for supervisor communication)."""
        # This would communicate with a supervisor agent
        self.logger.warning(f"Escalating failed task {task_id}: {error}")
        
        return {
            "response": f"Task escalated due to error: {error}",
            "task_id": task_id,
            "escalated": True,
            "error": str(error)
        }
    
    async def _initialize_llm(self) -> None:
        """Initialize LLM provider."""
        try:
            # Add to LLM manager or create provider directly
            llm_manager = get_llm_manager()
            llm_manager.add_provider(f"{self.name}_llm", self.config.llm, is_default=True)
            self._llm_provider = llm_manager.get_provider(f"{self.name}_llm")
            
            self.logger.info(f"Initialized LLM provider: {self.config.llm.provider.value}")
        except Exception as e:
            raise AgentError(f"Failed to initialize LLM: {e}")
    
    async def _initialize_memory(self) -> None:
        """Initialize memory system."""
        try:
            self._memory = await MemoryFactory.create_memory(self.config.memory)
            self.logger.info(f"Initialized memory: {self.config.memory.type}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize memory: {e}")
            # Memory is optional, so we continue without it
    
    
    def _extract_implicit_tool_calls(self, response: str) -> List[tuple]:
        """Extract implicit tool calls from natural language."""
        tool_calls = []
        response_lower = response.lower()
        
        if not self._tool_registry:
            return tool_calls
        
        # Get all available tools
        available_tools = self._tool_registry.list_tools()
        
        # Generic tool detection - look for explicit tool mentions
        import re
        for tool_name in available_tools:
            # Pattern 1: "I will use the {tool_name} tool" or "use {tool_name}"
            tool_mention_patterns = [
                rf'(?:will\s+use\s+(?:the\s+)?`?{re.escape(tool_name)}`?(?:\s+tool)?)',
                rf'(?:using\s+(?:the\s+)?`?{re.escape(tool_name)}`?(?:\s+tool)?)',
                rf'(?:use\s+(?:the\s+)?`?{re.escape(tool_name)}`?(?:\s+tool)?)',
                rf'(?:call\s+(?:the\s+)?`?{re.escape(tool_name)}`?(?:\s+tool)?)',
                rf'(?:execute\s+(?:the\s+)?`?{re.escape(tool_name)}`?(?:\s+tool)?)',
                rf'`{re.escape(tool_name)}`\s*(?:tool)?\s*(?:to|will|should)',
            ]
            
            for pattern in tool_mention_patterns:
                if re.search(pattern, response_lower):
                    self.logger.debug(f"Detected implicit tool call: {tool_name}")
                    tool_calls.append((tool_name, {}))
                    break  # Only add once per tool
        
        # Specific tool detection with parameter extraction
        
        # Time-related requests
        if any(tool in available_tools for tool in ['get_time', 'time', 'current_time']):
            time_patterns = [
                r'what\s+time\s+is\s+it',
                r'current\s+time',
                r'what\s*[\'\"]?s\s+the\s+time',
                r'time\s+right\s+now',
                r'what\s+is\s+the\s+current\s+time',
            ]
            
            for pattern in time_patterns:
                if re.search(pattern, response_lower):
                    # Find the appropriate tool name
                    for tool_name in ['get_time', 'time', 'current_time']:
                        if tool_name in available_tools:
                            tool_calls.append((tool_name, {}))
                            break
                    break
        
        # System information requests
        if any(tool in available_tools for tool in ['system_info', 'system', 'platform']):
            system_patterns = [
                r'system\s+information',
                r'what\s+system\s+am\s+i\s+(?:running\s+)?on',
                r'platform\s+information',
                r'system\s+details',
                r'operating\s+system',
            ]
            
            for pattern in system_patterns:
                if re.search(pattern, response_lower):
                    for tool_name in ['system_info', 'system', 'platform']:
                        if tool_name in available_tools:
                            tool_calls.append((tool_name, {}))
                            break
                    break
        
        # Math/calculation requests
        if any(tool in available_tools for tool in ['math', 'precise_math', 'calculator', 'calculate']):
            # Look for mathematical expressions
            math_patterns = [
                r'calculate\s+([0-9+\-*/\s().]+)',
                r'what\s+is\s+([0-9+\-*/\s().]+)',
                r'compute\s+([0-9+\-*/\s().]+)',
                r'([0-9]+(?:\.[0-9]+)?\s*[+\-*/]\s*[0-9]+(?:\.[0-9]+)?(?:\s*[+\-*/]\s*[0-9]+(?:\.[0-9]+)?)*)',
            ]
            
            for pattern in math_patterns:
                matches = re.findall(pattern, response_lower)
                for match in matches:
                    if match.strip():
                        expression = match.strip()
                        # Find the appropriate tool name
                        for tool_name in ['precise_math', 'math', 'calculator', 'calculate']:
                            if tool_name in available_tools:
                                tool_calls.append((tool_name, {'expression': expression}))
                                break
                        break  # Only take first match
        
        # Legacy specific tool patterns (backward compatibility)
        
        # Check for calculator usage (legacy)
        if self._tool_registry.has_tool("calculator"):
            calc_patterns = [
                r'what\s+is\s+(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)',
                r'calculate\s+(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)',
            ]
            
            for pattern in calc_patterns:
                matches = re.findall(pattern, response_lower)
                for match in matches:
                    if len(match) == 3:
                        a, operation, b = match
                        op_map = {'+': 'add', '-': 'subtract', '*': 'multiply', '/': 'divide'}
                        if operation in op_map:
                            tool_calls.append(('calculator', {
                                'operation': op_map[operation],
                                'a': float(a),
                                'b': float(b)
                            }))
                            break  # Only take the first match
        
        # Check for weather requests (legacy)
        if self._tool_registry.has_tool("weather"):
            weather_patterns = [
                r'weather\s+(?:in\s+)?([a-zA-Z\s]+)',
                r'what\s*[\'\"]?s\s+the\s+weather\s+(?:like\s+)?(?:in\s+)?([a-zA-Z\s]+)',
                r'forecast\s+(?:for\s+)?([a-zA-Z\s]+)'
            ]
            
            for pattern in weather_patterns:
                matches = re.findall(pattern, response_lower, re.IGNORECASE)
                for city in matches:
                    city = city.strip().title()
                    if city:
                        tool_calls.append(('weather', {'city': city}))
                        break  # Only take the first match
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tool_calls = []
        for tool_name, params in tool_calls:
            tool_key = (tool_name, frozenset(params.items()) if params else frozenset())
            if tool_key not in seen:
                seen.add(tool_key)
                unique_tool_calls.append((tool_name, params))
        
        return unique_tool_calls
    
    def _get_tool_usage_instructions(self) -> str:
        """Generate tool usage instructions for the system prompt."""
        if not self._tool_registry:
            return ""
        
        tools_info = self._tool_registry.get_tools_info()
        if not tools_info:
            return ""
        
        instructions = "\n## Available Tools\n\n"
        instructions += "You have access to the following tools. Use them when appropriate to complete tasks:\n\n"
        
        for tool in tools_info:
            instructions += f"**{tool['name']}**: {tool['description']}\n"
            
            # Add parameter information
            if 'parameters' in tool and isinstance(tool['parameters'], dict):
                params = tool['parameters']
                if 'properties' in params:
                    instructions += "  Parameters:\n"
                    for param_name, param_info in params['properties'].items():
                        param_type = param_info.get('type', 'string')
                        param_desc = param_info.get('description', '')
                        required = param_name in params.get('required', [])
                        req_marker = ' (required)' if required else ' (optional)'
                        instructions += f"    - {param_name} ({param_type}){req_marker}: {param_desc}\n"
            instructions += "\n"
        
        instructions += """## Tool Usage Format

To use a tool, you can:

1. **Function call style**: tool_name(parameter1="value1", parameter2="value2")
2. **JSON format**:
```json
{
  "tool": "tool_name",
  "parameters": {
    "parameter1": "value1",
    "parameter2": "value2"
  }
}
```
3. **Natural language**: Just ask naturally, e.g., "What's 15 + 27?" or "What's the weather in Tokyo?"

Use tools whenever they can help you provide more accurate or current information."""
        
        return instructions
    
    
    
    async def _initialize_tools(self) -> None:
        """Initialize tools."""
        try:
            # Create a new tool registry for this agent if one doesn't exist
            if not self._tool_registry:
                self._tool_registry = ToolRegistry()
            
            # Import the global tool registry to get registered tools
            from ..tools.base_tool import get_tool_registry
            global_registry = get_tool_registry()
            
            # Register configured tools from global registry
            for tool_name in self.config.tools:
                if global_registry.has_tool(tool_name):
                    # Get the tool from global registry
                    global_tool = global_registry.get_tool(tool_name)
                    if global_tool:
                        # Add to agent's local registry
                        self._tool_registry.register_tool(global_tool)
                        self.logger.info(f"Loaded tool: {tool_name}")
                    else:
                        self.logger.warning(f"Tool {tool_name} not found in global registry")
                else:
                    self.logger.warning(f"Tool {tool_name} not available in global registry")
            
            # Get actual tool count from registry
            actual_tools_count = len(self._tool_registry.list_tools())
            self.logger.info(f"Initialized {actual_tools_count} tools")
        except Exception as e:
            self.logger.warning(f"Failed to initialize tools: {e}")
    
    async def _initialize_mcp(self) -> None:
        """Initialize MCP server connections."""
        try:
            self._mcp_manager = MCPServerManager(self.config.mcp_config)
            await self._mcp_manager.start()
            
            # Register MCP tools with the agent's tool registry
            if self.config.mcp_config.auto_register_tools:
                mcp_tools = self._mcp_manager.get_tools()
                for tool in mcp_tools:
                    # Use namespaced names if configured
                    tool_name = tool.name
                    if self.config.mcp_config.tool_namespace:
                        tool_name = f"{tool.mcp_client.name}.{tool.name}"
                    
                    # Register with a unique name to avoid conflicts
                    self._tool_registry.register_tool(tool)
                    self.logger.info(f"Registered MCP tool: {tool_name}")
            
            self.logger.info("MCP integration initialized", 
                           servers=self._mcp_manager.list_active_servers(),
                           total_tools=len(self._mcp_manager.get_tools()))
        except Exception as e:
            self.logger.warning(f"Failed to initialize MCP integration: {e}")
    
    async def _initialize_a2a(self) -> None:
        """Initialize A2A communication."""
        try:
            from ..config.settings import get_config
            config = get_config()
            
            self._a2a_handler = A2AHandler(
                agent_id=self.id,
                message_timeout=config.a2a_config.message_timeout,
                max_message_size=config.a2a_config.max_message_size,
                max_retries=config.a2a_config.max_retries
            )
            await self._a2a_handler.start()
            
            self.logger.info("A2A communication initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize A2A communication: {e}")
    
    async def send_message_to_agent(self, recipient_id: str, content: Dict[str, Any]) -> bool:
        """Send a message to another agent via A2A."""
        if not self._a2a_handler:
            self.logger.warning("A2A handler not initialized")
            return False
        
        try:
            await self._a2a_handler.send_direct_message(recipient_id, content)
            return True
        except Exception as e:
            self.logger.error(f"Failed to send A2A message: {e}")
            return False
    
    async def request_task_from_agent(self, recipient_id: str, task_content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Request a task from another agent."""
        if not self._a2a_handler:
            self.logger.warning("A2A handler not initialized")
            return None
        
        try:
            response_message = await self._a2a_handler.send_request(recipient_id, task_content)
            return response_message.content if response_message else None
        except Exception as e:
            self.logger.error(f"Failed to request task from agent: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        status = self.state.to_dict()
        status.update({
            "agent_id": self.id,
            "agent_name": self.name,
            "running": self._running,
            "llm_provider": self.config.llm.provider.value if self.config.llm else None,
            "memory_type": self.config.memory.type,
            "tools_count": len(self.config.tools),
            "a2a_enabled": self.config.enable_a2a_communication,
        })
        return status
    
    async def get_memory_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search agent memory."""
        if not self._memory:
            return []
        
        results = await self._memory.search(query, limit)
        return [doc.to_dict() for doc in results]
    
    def register_tool(self, tool_func: callable) -> None:
        """Register a tool function for this agent."""
        if not self._tool_registry:
            self._tool_registry = ToolRegistry()
        
        from ..tools.registry import generate_schema_from_function
        
        # Generate schema from function
        schema = generate_schema_from_function(tool_func)
        tool_name = tool_func.__name__
        description = tool_func.__doc__ or f"Tool: {tool_name}"
        
        # Register the function as a tool
        self._tool_registry.register_function(
            name=tool_name,
            description=description,
            func=tool_func,
            parameters_schema=schema
        )
        
        # Store reference for easy access
        if not hasattr(self, '_tools'):
            self._tools = {}
        self._tools[tool_name] = tool_func
        
        self.logger.info(f"Registered tool: {tool_name}")
    
    def register_langchain_tool(self, langchain_tool: Any) -> None:
        """Register a LangChain tool for this agent."""
        if not self._tool_registry:
            self._tool_registry = ToolRegistry()
        
        self._tool_registry.register_langchain_tool(langchain_tool)
        
        # Store reference for easy access
        if not hasattr(self, '_tools'):
            self._tools = {}
        self._tools[langchain_tool.name] = langchain_tool
        
        self.logger.info(f"Registered LangChain tool: {langchain_tool.name}")
    
    def register_async_tool(self, async_tool: 'AsyncTool') -> None:
        """Register an AsyncTool object for this agent."""
        if not self._tool_registry:
            self._tool_registry = ToolRegistry()
        
        self._tool_registry.register_tool(async_tool)
        
        # Store reference for easy access
        if not hasattr(self, '_tools'):
            self._tools = {}
        self._tools[async_tool.name] = async_tool
        
        self.logger.info(f"Registered AsyncTool: {async_tool.name}")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools for this agent."""
        if not self._tool_registry:
            return []
        return self._tool_registry.list_tools()
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if agent has a specific tool."""
        if not self._tool_registry:
            return False
        return self._tool_registry.has_tool(tool_name)
    
    def _get_tool_param_schema(self, tool_name: str) -> Optional[Dict[str, type]]:
        """Get parameter schema for a tool."""
        if not self._tool_registry or not self._tool_registry.has_tool(tool_name):
            return None
        
        # Get the tool object directly
        tool = self._tool_registry.get_tool(tool_name)
        if not tool:
            return None
        
        # Get tool info from the tool's to_dict method
        tool_info = tool.to_dict()
        if not tool_info or 'parameters' not in tool_info:
            return None
        
        # Convert JSON schema to type mapping
        param_schema = {}
        parameters = tool_info['parameters']
        
        if 'properties' in parameters:
            for param_name, param_info in parameters['properties'].items():
                param_type_str = param_info.get('type', 'string')
                # Map JSON schema types to Python types
                type_mapping = {
                    'string': str,
                    'integer': int,
                    'number': float,
                    'boolean': bool,
                    'array': list,
                    'object': dict
                }
                param_schema[param_name] = type_mapping.get(param_type_str, str)
        
        return param_schema
    
    def _format_tool_results_for_response(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results for inclusion in final response."""
        if not tool_results:
            return "No tools were executed."
        
        formatted_results = []
        for result in tool_results:
            tool_name = result.get('tool', 'Unknown')
            success = result.get('success', False)
            
            if success:
                tool_result = result.get('result', 'No result')
                params = result.get('parameters', {})
                param_str = ', '.join([f"{k}={v}" for k, v in params.items()])
                formatted_results.append(f"- {tool_name}({param_str}) → {tool_result}")
            else:
                error = result.get('error', 'Unknown error')
                formatted_results.append(f"- {tool_name}: FAILED - {error}")
        
        return "\n".join(formatted_results)
    
    def set_tool_selector(self, tool_selector: ToolSelector) -> None:
        """Set a custom tool selector for controlled execution."""
        self._tool_selector = tool_selector
        self.logger.info(f"Set custom tool selector: {tool_selector.__class__.__name__}")
    
    def as_tool(
        self, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None
    ) -> 'AsyncTool':
        """Convert this agent into a tool for delegation patterns.
        
        Args:
            name: Tool name (defaults to agent_{agent_name})
            description: Tool description (defaults to delegation description)
            parameters_schema: Custom parameters schema (defaults to task parameter)
            
        Returns:
            AsyncTool that delegates to this agent
        """
        from ..tools.base_tool import AsyncTool, ToolResult, ToolType
        
        # Default values
        tool_name = name or f"agent_{self.name.lower().replace(' ', '_')}"
        tool_description = description or f"Delegate tasks to {self.name} agent"
        
        # Default parameters schema - simple task parameter
        if parameters_schema is None:
            parameters_schema = {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Task to delegate to the agent"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context for the task",
                        "default": {}
                    }
                },
                "required": ["task"]
            }
        
        # Create the agent tool
        class AgentTool(AsyncTool):
            def __init__(self, agent_instance):
                super().__init__(tool_name, tool_description, ToolType.CUSTOM)
                self.agent = agent_instance
                self._parameters = parameters_schema
            
            @property
            def parameters(self) -> Dict[str, Any]:
                return self._parameters
            
            async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
                """Execute by delegating to the agent."""
                import time
                start_time = time.time()
                
                try:
                    await self.validate_parameters(parameters)
                    
                    task = parameters.get("task")
                    context = parameters.get("context", {})
                    
                    # Execute task via agent
                    result = await self.agent.execute_task(task, context)
                    
                    execution_time = time.time() - start_time
                    self.logger.info(f"Agent tool '{self.name}' executed successfully in {execution_time:.2f}s")
                    
                    return ToolResult.success_result(
                        result=result,
                        metadata={
                            "tool_type": "agent",
                            "agent_id": self.agent.id,
                            "agent_name": self.agent.name
                        },
                        execution_time=execution_time
                    )
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    error_msg = f"Agent tool execution failed: {e}"
                    self.logger.error(error_msg)
                    
                    return ToolResult.error_result(
                        error=error_msg,
                        metadata={
                            "tool_type": "agent",
                            "agent_id": self.agent.id,
                            "agent_name": self.agent.name,
                            "exception": str(type(e).__name__)
                        },
                        execution_time=execution_time
                    )
        
        return AgentTool(self)
