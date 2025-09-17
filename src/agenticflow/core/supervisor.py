"""
SupervisorAgent for AgenticFlow with LangGraph integration.

Specialized Supervisor class with task decomposition, planning, routing capabilities
using LangGraph for workflow management and multi-agent coordination.
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Union, TypedDict, Annotated

import structlog
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# LangGraph imports with fallback for when not available
try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Fallback types
    class StateGraph:
        def __init__(self, *args, **kwargs):
            pass
    END = "END"
    def add_messages(*args):
        return []

from .agent import Agent
from .task_manager import Task, TaskManager, TaskPriority
# A2A communication components no longer needed here
from ..config.settings import SupervisorConfig

logger = structlog.get_logger(__name__)


class PlanningState(TypedDict):
    """State for the planning workflow."""
    messages: Annotated[List[BaseMessage], add_messages]
    original_task: str
    subtasks: List[Dict[str, Any]]
    completed_subtasks: List[str]
    failed_subtasks: List[str]
    current_step: str
    agent_assignments: Dict[str, str]  # subtask_id -> agent_id
    results: Dict[str, Any]
    reflection: Optional[str]


class SupervisorAgent(Agent):
    """Supervisor agent with task decomposition, planning, and coordination capabilities."""
    
    def __init__(self, config: SupervisorConfig) -> None:
        """Initialize supervisor agent."""
        super().__init__(config)
        self.supervisor_config = config
        
        # Sub-agent management
        self._sub_agents: Dict[str, Agent] = {}
        self._agent_capabilities: Dict[str, List[str]] = {}
        
        # Task management
        self._task_manager: Optional[TaskManager] = None
        
        # Planning workflow
        self._planning_graph = None
        if LANGGRAPH_AVAILABLE:
            self._setup_planning_workflow()
        
        self.logger.info(f"Supervisor agent {self.name} initialized")
    
    async def start(self) -> None:
        """Start supervisor agent and initialize task manager."""
        await super().start()
        
        # Initialize task manager
        from ..config.settings import get_config
        global_config = get_config()
        self._task_manager = TaskManager(global_config.task_config)
        
        # Register supervisor as task handler
        self._task_manager.register_handler("supervisor", self._handle_supervisor_task)
        self._task_manager.register_handler("coordination", self._handle_coordination_task)
        
        await self._task_manager.start()
        self.logger.info("Supervisor task manager started")
    
    async def stop(self) -> None:
        """Stop supervisor agent."""
        # Stop task manager
        if self._task_manager:
            await self._task_manager.stop()
        
        # Stop all sub-agents
        for agent in self._sub_agents.values():
            await agent.stop()
        
        await super().stop()
    
    def register_sub_agent(self, agent: Agent, capabilities: Optional[List[str]] = None) -> None:
        """Register a sub-agent with the supervisor."""
        self._sub_agents[agent.id] = agent
        self._agent_capabilities[agent.id] = capabilities or []
        self.logger.info(f"Registered sub-agent {agent.id} ({agent.name})")
    
    def unregister_sub_agent(self, agent_id: str) -> bool:
        """Unregister a sub-agent."""
        if agent_id in self._sub_agents:
            del self._sub_agents[agent_id]
            self._agent_capabilities.pop(agent_id, None)
            self.logger.info(f"Unregistered sub-agent {agent_id}")
            return True
        return False
    
    async def coordinate_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Coordinate a complex task across multiple agents."""
        self.logger.info(f"Starting task coordination: {task}")
        
        try:
            # Use LangGraph workflow if available, otherwise fall back to simple coordination
            if LANGGRAPH_AVAILABLE and self._planning_graph:
                return await self._coordinate_with_langgraph(task, context or {})
            else:
                return await self._coordinate_simple(task, context or {})
        
        except Exception as e:
            self.logger.error(f"Task coordination failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def _coordinate_with_langgraph(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate task using LangGraph workflow."""
        # Initialize planning state
        initial_state = PlanningState(
            messages=[HumanMessage(content=task)],
            original_task=task,
            subtasks=[],
            completed_subtasks=[],
            failed_subtasks=[],
            current_step="decompose",
            agent_assignments={},
            results={},
            reflection=None
        )
        
        try:
            # Run the planning workflow
            result = await self._planning_graph.ainvoke(initial_state)
            
            return {
                "success": len(result["failed_subtasks"]) == 0,
                "original_task": task,
                "subtasks": result["subtasks"],
                "completed_subtasks": result["completed_subtasks"],
                "failed_subtasks": result["failed_subtasks"],
                "results": result["results"],
                "reflection": result.get("reflection"),
                "agent_assignments": result["agent_assignments"]
            }
        
        except Exception as e:
            self.logger.error(f"LangGraph coordination failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def _coordinate_simple(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simple coordination without LangGraph."""
        # Decompose task
        subtasks = await self._decompose_task(task, context)
        
        # Assign agents
        assignments = await self._assign_agents_to_tasks(subtasks)
        
        # Execute tasks
        results = {}
        completed = []
        failed = []
        
        for subtask in subtasks:
            subtask_id = subtask["id"]
            agent_id = assignments.get(subtask_id)
            
            if not agent_id or agent_id not in self._sub_agents:
                failed.append(subtask_id)
                continue
            
            try:
                agent = self._sub_agents[agent_id]
                result = await agent.execute_task(subtask["description"], subtask.get("context", {}))
                results[subtask_id] = result
                completed.append(subtask_id)
            
            except Exception as e:
                failed.append(subtask_id)
                results[subtask_id] = {"error": str(e)}
        
        return {
            "success": len(failed) == 0,
            "original_task": task,
            "subtasks": subtasks,
            "completed_subtasks": completed,
            "failed_subtasks": failed,
            "results": results,
            "agent_assignments": assignments
        }
    
    def _setup_planning_workflow(self) -> None:
        """Setup LangGraph planning workflow."""
        if not LANGGRAPH_AVAILABLE:
            return
        
        # Create workflow graph
        workflow = StateGraph(PlanningState)
        
        # Add workflow nodes
        workflow.add_node("decompose", self._decompose_node)
        workflow.add_node("assign", self._assign_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("reflect", self._reflect_node)
        
        # Add edges
        workflow.add_edge("decompose", "assign")
        workflow.add_edge("assign", "execute")
        workflow.add_edge("execute", "reflect")
        workflow.add_edge("reflect", END)
        
        # Set entry point
        workflow.set_entry_point("decompose")
        
        # Compile the graph
        self._planning_graph = workflow.compile()
        self.logger.info("LangGraph planning workflow initialized")
    
    async def _decompose_node(self, state: PlanningState) -> PlanningState:
        """Decompose task into subtasks."""
        original_task = state["original_task"]
        
        # Use LLM to decompose task
        decomposition_prompt = f"""
        Break down this complex task into smaller, manageable subtasks:
        
        Task: {original_task}
        
        Available agents and their capabilities:
        {self._format_agent_capabilities()}
        
        Please provide a JSON list of subtasks with the following structure:
        {{
            "subtasks": [
                {{
                    "id": "unique_id",
                    "description": "Clear description of what needs to be done",
                    "dependencies": ["list_of_task_ids_this_depends_on"],
                    "estimated_duration": "estimated_time_in_minutes",
                    "required_capabilities": ["list_of_required_capabilities"]
                }}
            ]
        }}
        
        Make sure subtasks are:
        1. Specific and actionable
        2. Can be executed independently (except for dependencies)
        3. Have clear success criteria
        """
        
        messages = [HumanMessage(content=decomposition_prompt)]
        
        try:
            response = await self._get_llm_response(messages)
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response)
                subtasks = parsed_response.get("subtasks", [])
                
                # Add unique IDs if missing
                for i, subtask in enumerate(subtasks):
                    if "id" not in subtask:
                        subtask["id"] = f"subtask_{i + 1}"
                
                state["subtasks"] = subtasks
                state["current_step"] = "assign"
                
                self.logger.info(f"Decomposed task into {len(subtasks)} subtasks")
                
            except json.JSONDecodeError:
                # Fallback: create simple subtasks from response
                subtasks = [
                    {
                        "id": "subtask_1",
                        "description": response,
                        "dependencies": [],
                        "estimated_duration": "10 minutes",
                        "required_capabilities": []
                    }
                ]
                state["subtasks"] = subtasks
                state["current_step"] = "assign"
        
        except Exception as e:
            self.logger.error(f"Task decomposition failed: {e}")
            state["subtasks"] = []
            state["current_step"] = "reflect"
        
        return state
    
    async def _assign_node(self, state: PlanningState) -> PlanningState:
        """Assign agents to subtasks."""
        subtasks = state["subtasks"]
        assignments = {}
        
        for subtask in subtasks:
            # Find best agent for this subtask
            best_agent = self._find_best_agent_for_task(subtask)
            if best_agent:
                assignments[subtask["id"]] = best_agent
            else:
                self.logger.warning(f"No suitable agent found for subtask: {subtask['id']}")
        
        state["agent_assignments"] = assignments
        state["current_step"] = "execute"
        
        return state
    
    async def _execute_node(self, state: PlanningState) -> PlanningState:
        """Execute assigned subtasks."""
        subtasks = state["subtasks"]
        assignments = state["agent_assignments"]
        results = {}
        completed = []
        failed = []
        
        # Execute subtasks respecting dependencies
        remaining_tasks = {task["id"]: task for task in subtasks}
        
        while remaining_tasks:
            # Find tasks that can be executed (dependencies met)
            ready_tasks = []
            for task_id, task in remaining_tasks.items():
                dependencies = task.get("dependencies", [])
                if all(dep in completed for dep in dependencies):
                    ready_tasks.append((task_id, task))
            
            if not ready_tasks:
                # No more tasks can be executed, mark remaining as failed
                for task_id in remaining_tasks:
                    failed.append(task_id)
                break
            
            # Execute ready tasks in parallel
            execution_tasks = []
            for task_id, task in ready_tasks:
                agent_id = assignments.get(task_id)
                if agent_id and agent_id in self._sub_agents:
                    agent = self._sub_agents[agent_id]
                    execution_tasks.append(self._execute_subtask(task_id, task, agent))
                else:
                    failed.append(task_id)
            
            # Wait for completion
            task_results = await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # Process results
            for i, (task_id, task) in enumerate(ready_tasks):
                if task_id in failed:
                    continue
                
                result = task_results[i]
                if isinstance(result, Exception):
                    failed.append(task_id)
                    results[task_id] = {"error": str(result)}
                else:
                    completed.append(task_id)
                    results[task_id] = result
                
                # Remove from remaining tasks
                remaining_tasks.pop(task_id, None)
        
        state["completed_subtasks"] = completed
        state["failed_subtasks"] = failed
        state["results"] = results
        state["current_step"] = "reflect"
        
        return state
    
    async def _reflect_node(self, state: PlanningState) -> PlanningState:
        """Reflect on task execution results."""
        if not self.supervisor_config.enable_reflection:
            return state
        
        original_task = state["original_task"]
        completed = state["completed_subtasks"]
        failed = state["failed_subtasks"]
        results = state["results"]
        
        reflection_prompt = f"""
        Reflect on the execution of this task:
        
        Original Task: {original_task}
        
        Completed Subtasks ({len(completed)}): {completed}
        Failed Subtasks ({len(failed)}): {failed}
        
        Results Summary:
        {json.dumps(results, indent=2)}
        
        Please provide:
        1. Overall success assessment
        2. Key insights from the execution
        3. Recommendations for improvement
        4. Final consolidated result/answer for the original task
        
        Format as JSON:
        {{
            "success": true/false,
            "insights": "key insights",
            "recommendations": "improvement suggestions", 
            "final_result": "consolidated answer to original task"
        }}
        """
        
        try:
            messages = [HumanMessage(content=reflection_prompt)]
            reflection_response = await self._get_llm_response(messages)
            
            try:
                reflection_data = json.loads(reflection_response)
                state["reflection"] = reflection_data
            except json.JSONDecodeError:
                state["reflection"] = {"raw_response": reflection_response}
        
        except Exception as e:
            self.logger.error(f"Reflection failed: {e}")
            state["reflection"] = {"error": str(e)}
        
        return state
    
    async def _execute_subtask(self, task_id: str, task: Dict[str, Any], agent: Agent) -> Dict[str, Any]:
        """Execute a single subtask with an agent."""
        try:
            result = await agent.execute_task(
                task["description"],
                context=task.get("context", {})
            )
            return result
        
        except Exception as e:
            raise Exception(f"Subtask {task_id} failed: {e}")
    
    def _find_best_agent_for_task(self, subtask: Dict[str, Any]) -> Optional[str]:
        """Find the best agent for a given subtask."""
        required_capabilities = subtask.get("required_capabilities", [])
        
        # If no specific capabilities required, use any available agent
        if not required_capabilities:
            available_agents = list(self._sub_agents.keys())
            return available_agents[0] if available_agents else None
        
        # Find agent with best capability match
        best_agent = None
        best_score = -1
        
        for agent_id, capabilities in self._agent_capabilities.items():
            if agent_id not in self._sub_agents:
                continue
            
            # Calculate capability match score
            matches = len(set(required_capabilities) & set(capabilities))
            coverage = matches / len(required_capabilities) if required_capabilities else 0
            
            if coverage > best_score:
                best_score = coverage
                best_agent = agent_id
        
        return best_agent
    
    def _format_agent_capabilities(self) -> str:
        """Format agent capabilities for prompts."""
        if not self._sub_agents:
            return "No agents available"
        
        formatted = []
        for agent_id, agent in self._sub_agents.items():
            capabilities = self._agent_capabilities.get(agent_id, [])
            formatted.append(f"- {agent.name} ({agent_id}): {', '.join(capabilities) if capabilities else 'General purpose'}")
        
        return "\n".join(formatted)
    
    async def _decompose_task(self, task: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simple task decomposition without LangGraph."""
        prompt = f"""
        Break down this task into 2-4 smaller subtasks:
        
        Task: {task}
        Context: {json.dumps(context, indent=2)}
        
        Provide subtasks as a simple numbered list.
        """
        
        messages = [HumanMessage(content=prompt)]
        response = await self._get_llm_response(messages)
        
        # Simple parsing of numbered list
        lines = response.strip().split('\n')
        subtasks = []
        
        for i, line in enumerate(lines):
            if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-')):
                # Clean up the line
                description = line.strip()
                if description[0].isdigit():
                    description = description[2:].strip()  # Remove "1. "
                elif description.startswith('-'):
                    description = description[1:].strip()  # Remove "- "
                
                subtasks.append({
                    "id": f"subtask_{i + 1}",
                    "description": description,
                    "dependencies": [],
                    "required_capabilities": []
                })
        
        return subtasks if subtasks else [{"id": "subtask_1", "description": task, "dependencies": [], "required_capabilities": []}]
    
    async def _assign_agents_to_tasks(self, subtasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """Simple agent assignment."""
        assignments = {}
        available_agents = list(self._sub_agents.keys())
        
        for i, subtask in enumerate(subtasks):
            if available_agents:
                # Round-robin assignment
                agent_id = available_agents[i % len(available_agents)]
                assignments[subtask["id"]] = agent_id
        
        return assignments
    
    async def _handle_supervisor_task(self, task: Task) -> Any:
        """Handle supervisor-specific tasks."""
        task_type = task.payload.get("type", "coordinate")
        
        if task_type == "coordinate":
            return await self.coordinate_task(task.name, task.context)
        elif task_type == "decompose":
            return await self._decompose_task(task.name, task.context)
        else:
            return {"error": f"Unknown supervisor task type: {task_type}"}
    
    async def _handle_coordination_task(self, task: Task) -> Any:
        """Handle coordination tasks."""
        return await self.coordinate_task(task.name, task.context)
    
    def get_supervisor_status(self) -> Dict[str, Any]:
        """Get supervisor-specific status."""
        base_status = self.get_status()
        
        supervisor_status = {
            **base_status,
            "supervisor_type": "supervisor",
            "sub_agents": len(self._sub_agents),
            "agent_capabilities": self._agent_capabilities,
            "task_manager_running": self._task_manager._running if self._task_manager else False,
            "langgraph_available": LANGGRAPH_AVAILABLE,
        }
        
        if self._task_manager:
            supervisor_status["task_statistics"] = self._task_manager.get_statistics()
        
        return supervisor_status