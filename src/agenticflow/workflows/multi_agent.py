"""
MultiAgentSystem for AgenticFlow.

Implements the main system class that orchestrates multiple agents with 
star-shaped hierarchy and supervisor-based coordination.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union

import structlog

from ..core.agent import Agent
from ..core.supervisor import SupervisorAgent
from ..core.task_manager import TaskManager, TaskPriority
from ..config.settings import AgenticFlowConfig, get_config
from ..communication.a2a_handler import A2AHandler, MessageType
from .topologies import (
    BaseTopology, StarTopology, PeerToPeerTopology, 
    HierarchicalTopology, PipelineTopology, CustomTopology,
    TopologyType, create_topology
)

logger = structlog.get_logger(__name__)


class MultiAgentSystemError(Exception):
    """Base exception for multi-agent system errors."""
    pass


class AgentRegistrationError(MultiAgentSystemError):
    """Raised when agent registration fails."""
    pass


class MultiAgentSystem:
    """Multi-agent system with star topology and supervisor coordination."""
    
    def __init__(
        self,
        supervisor: Optional[SupervisorAgent] = None,
        agents: Optional[List[Agent]] = None,
        config: Optional[AgenticFlowConfig] = None,
        topology: Optional[Union[BaseTopology, TopologyType, str]] = None,
        topology_name: str = "default_topology"
    ) -> None:
        """Initialize multi-agent system with flexible topology support."""
        self.config = config or get_config()
        self.logger = logger.bind(component="multi_agent_system")
        
        # System components
        self._supervisor = supervisor
        self._agents: Dict[str, Agent] = {}
        self._agent_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Topology management
        self._setup_topology(topology, topology_name, supervisor)
        
        # System state
        self._running = False
        self._start_time: Optional[float] = None
        
        # Task management
        self._global_task_manager: Optional[TaskManager] = None
        
        # Communication
        self._communication_hub: Optional[A2AHandler] = None
        
        # Statistics
        self._stats = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "agent_utilization": {},
        }
        
        # Register initial agents if provided
        if agents:
            for agent in agents:
                self._register_agent_sync(agent)
        
        self.logger.info(f"Multi-agent system initialized with {self.topology.topology_type.value} topology")
    
    async def start(self) -> None:
        """Start the multi-agent system."""
        if self._running:
            self.logger.warning("System is already running")
            return
        
        self.logger.info("Starting multi-agent system...")
        
        try:
            # Initialize global task manager
            await self._initialize_task_manager()
            
            # Start supervisor if available
            if self._supervisor:
                await self._supervisor.start()
                self.logger.info("Supervisor started")
            
            # Start all registered agents
            start_tasks = []
            for agent in self._agents.values():
                start_tasks.append(agent.start())
            
            if start_tasks:
                await asyncio.gather(*start_tasks)
                self.logger.info(f"Started {len(start_tasks)} agents")
            
            # Initialize communication hub if A2A is enabled
            if self.config.a2a_config.enable_a2a:
                await self._initialize_communication_hub()
            
            # Set system as running
            self._running = True
            self._start_time = time.time()
            
            self.logger.info("Multi-agent system started successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to start multi-agent system: {e}")
            await self.stop()  # Cleanup on failure
            raise MultiAgentSystemError(f"System startup failed: {e}")
    
    async def stop(self) -> None:
        """Stop the multi-agent system."""
        if not self._running:
            return
        
        self.logger.info("Stopping multi-agent system...")
        
        # Stop communication hub
        if self._communication_hub:
            await self._communication_hub.stop()
        
        # Stop all agents
        stop_tasks = []
        for agent in self._agents.values():
            stop_tasks.append(agent.stop())
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        # Stop supervisor
        if self._supervisor:
            await self._supervisor.stop()
        
        # Stop global task manager
        if self._global_task_manager:
            await self._global_task_manager.stop()
        
        self._running = False
        self.logger.info("Multi-agent system stopped")
    
    def register_agent(
        self,
        agent: Agent,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register an agent with the system."""
        if self._running:
            raise AgentRegistrationError("Cannot register agents while system is running")
        
        self._register_agent_sync(agent, capabilities, metadata)
    
    def _register_agent_sync(
        self,
        agent: Agent,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Synchronously register an agent."""
        if agent.id in self._agents:
            raise AgentRegistrationError(f"Agent {agent.id} is already registered")
        
        # Register with system
        self._agents[agent.id] = agent
        self._agent_metadata[agent.id] = {
            "capabilities": capabilities or [],
            "metadata": metadata or {},
            "registered_at": time.time(),
            "tasks_processed": 0,
            "last_task_time": None,
        }
        
        # Register with supervisor if available
        if self._supervisor:
            self._supervisor.register_sub_agent(agent, capabilities)
        
        # Register with topology unless it already exists (e.g., preconfigured topology)
        try:
            existing = getattr(self.topology, 'agents', {})
            if agent.id not in existing:
                self.topology.add_agent(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    capabilities=capabilities or [],
                    metadata=metadata or {},
                    role=metadata.get('role', 'worker') if metadata else 'worker'
                )
                self.logger.info(f"Registered agent {agent.id} ({agent.name}) with topology")
            else:
                self.logger.debug(f"Agent {agent.id} already present in topology; skipping add")
        except Exception:
            # Fallback safe add
            self.topology.add_agent(
                agent_id=agent.id,
                agent_name=agent.name,
                capabilities=capabilities or [],
                metadata=metadata or {},
                role=metadata.get('role', 'worker') if metadata else 'worker'
            )
            self.logger.info(f"Registered agent {agent.id} ({agent.name}) with topology")
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the system."""
        if self._running:
            raise AgentRegistrationError("Cannot unregister agents while system is running")
        
        if agent_id not in self._agents:
            return False
        
        # Unregister from supervisor
        if self._supervisor:
            self._supervisor.unregister_sub_agent(agent_id)
        
        # Remove from system
        del self._agents[agent_id]
        self._agent_metadata.pop(agent_id, None)
        
        self.logger.info(f"Unregistered agent {agent_id}")
        return True
    
    def _setup_topology(
        self, 
        topology: Optional[Union[BaseTopology, TopologyType, str]], 
        topology_name: str,
        supervisor: Optional[SupervisorAgent]
    ) -> None:
        """Setup the communication topology for the multi-agent system."""
        if isinstance(topology, BaseTopology):
            # Use provided topology instance
            self.topology = topology
        elif topology is not None:
            # Create topology from type
            if isinstance(topology, str):
                topology = TopologyType(topology)
            
            if topology == TopologyType.STAR:
                supervisor_id = supervisor.id if supervisor else None
                self.topology = StarTopology(topology_name, supervisor_id)
            else:
                self.topology = create_topology(topology, topology_name)
        else:
            # Default to star topology if supervisor is provided, otherwise peer-to-peer
            if supervisor:
                self.topology = StarTopology(topology_name, supervisor.id)
            else:
                self.topology = PeerToPeerTopology(topology_name)
        
        self.logger.info(f"Using {self.topology.topology_type.value} topology: {self.topology.name}")
    
    def add_communication_route(self, from_agent_id: str, to_agent_id: str, **route_kwargs) -> None:
        """Add a custom communication route between agents."""
        from .topologies import CommunicationRoute, MessageRouting
        
        route = CommunicationRoute(
            from_agent=from_agent_id,
            to_agent=to_agent_id,
            route_type=route_kwargs.get('route_type', MessageRouting.DIRECT),
            bidirectional=route_kwargs.get('bidirectional', True),
            filters=route_kwargs.get('filters', []),
            priority=route_kwargs.get('priority', 1)
        )
        
        self.topology.add_route(route)
        self.logger.info(f"Added communication route: {from_agent_id} -> {to_agent_id}")
    
    def add_agent_group(self, group_name: str, agent_ids: List[str]) -> None:
        """Create an agent group for broadcasting."""
        self.topology.add_group(group_name, agent_ids)
        self.logger.info(f"Created agent group '{group_name}' with {len(agent_ids)} agents")
    
    def get_communication_topology(self) -> BaseTopology:
        """Get the current communication topology."""
        return self.topology
    
    def find_communication_path(self, from_agent_id: str, to_agent_id: str) -> Optional[List[str]]:
        """Find communication path between two agents."""
        return self.topology.find_path(from_agent_id, to_agent_id)
    
    def get_agent_neighbors(self, agent_id: str) -> List[str]:
        """Get agents that can directly communicate with the specified agent."""
        return self.topology.get_agent_neighbors(agent_id)
    
    async def execute_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute a task using the multi-agent system."""
        if not self._running:
            raise MultiAgentSystemError("System is not running")
        
        self.logger.info(f"Executing task: {task}")
        start_time = time.time()
        
        try:
            # If we have a supervisor, use it for coordination
            if self._supervisor:
                result = await self._execute_with_supervisor(task, context, timeout)
            else:
                # Fallback to simple execution with first available agent
                result = await self._execute_simple(task, context, timeout)
            
            # Update statistics
            execution_time = time.time() - start_time
            self._update_task_statistics(True, execution_time)
            
            result["execution_time"] = execution_time
            result["system_stats"] = self.get_statistics()
            
            self.logger.info(f"Task completed in {execution_time:.2f}s")
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_task_statistics(False, execution_time)
            
            error_result = {
                "success": False,
                "error": str(e),
                "task": task,
                "execution_time": execution_time,
            }
            
            self.logger.error(f"Task execution failed after {execution_time:.2f}s: {e}")
            return error_result
    
    async def _execute_with_supervisor(
        self,
        task: str,
        context: Optional[Dict[str, Any]],
        timeout: Optional[float]
    ) -> Dict[str, Any]:
        """Execute task using supervisor coordination."""
        try:
            if timeout:
                result = await asyncio.wait_for(
                    self._supervisor.coordinate_task(task, context),
                    timeout=timeout
                )
            else:
                result = await self._supervisor.coordinate_task(task, context)
            
            return result
        
        except asyncio.TimeoutError:
            raise MultiAgentSystemError(f"Task execution timed out after {timeout}s")
        except Exception as e:
            raise MultiAgentSystemError(f"Supervisor coordination failed: {e}")
    
    async def _execute_simple(
        self,
        task: str,
        context: Optional[Dict[str, Any]],
        timeout: Optional[float]
    ) -> Dict[str, Any]:
        """Simple task execution without supervisor."""
        if not self._agents:
            raise MultiAgentSystemError("No agents available for task execution")
        
        # Use the first available agent
        agent = next(iter(self._agents.values()))
        
        try:
            if timeout:
                result = await asyncio.wait_for(
                    agent.execute_task(task, context),
                    timeout=timeout
                )
            else:
                result = await agent.execute_task(task, context)
            
            # Update agent utilization
            self._update_agent_utilization(agent.id)
            
            return {
                "success": True,
                "result": result,
                "executed_by": agent.id,
                "agent_name": agent.name,
            }
        
        except asyncio.TimeoutError:
            raise MultiAgentSystemError(f"Task execution timed out after {timeout}s")
        except Exception as e:
            raise MultiAgentSystemError(f"Agent execution failed: {e}")
    
    async def execute_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel."""
        if not self._running:
            raise MultiAgentSystemError("System is not running")
        
        max_concurrent = max_concurrent or len(self._agents)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single_task(task_info: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.execute_task(
                    task=task_info["task"],
                    context=task_info.get("context"),
                    priority=task_info.get("priority", TaskPriority.NORMAL),
                    timeout=task_info.get("timeout")
                )
        
        self.logger.info(f"Executing {len(tasks)} tasks in parallel (max_concurrent={max_concurrent})")
        
        # Execute all tasks
        results = await asyncio.gather(
            *[execute_single_task(task_info) for task_info in tasks],
            return_exceptions=True
        )
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "task_index": i,
                    "task": tasks[i]["task"]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _initialize_task_manager(self) -> None:
        """Initialize global task manager."""
        self._global_task_manager = TaskManager(self.config.task_config)
        await self._global_task_manager.start()
        self.logger.info("Global task manager initialized")
    
    async def _initialize_communication_hub(self) -> None:
        """Initialize communication hub for A2A messaging."""
        self._communication_hub = A2AHandler(
            agent_id="multi_agent_system",
            message_timeout=self.config.a2a_config.message_timeout,
            max_message_size=self.config.a2a_config.max_message_size,
            max_retries=self.config.a2a_config.max_retries
        )
        
        # Register message handlers
        self._communication_hub.register_handler(
            MessageType.REQUEST,
            self._handle_task_request
        )
        
        await self._communication_hub.start()
        self.logger.info("Communication hub initialized")
    
    async def _handle_task_request(self, message) -> None:
        """Handle incoming task requests via A2A."""
        try:
            task_data = message.content
            
            # Extract task information
            task = task_data.get("description", "")
            context = task_data.get("parameters", {})
            
            # Execute task
            result = await self.execute_task(task, context)
            
            # Send response back
            if self._communication_hub:
                response_content = {
                    "task_id": task_data.get("task_id"),
                    "result": result,
                    "status": "completed" if result.get("success") else "failed"
                }
                
                await self._communication_hub.send_direct_message(
                    message.sender_id,
                    response_content
                )
        
        except Exception as e:
            self.logger.error(f"Failed to handle task request: {e}")
    
    def _update_task_statistics(self, success: bool, execution_time: float) -> None:
        """Update system task statistics."""
        self._stats["total_tasks_processed"] += 1
        
        if success:
            self._stats["successful_tasks"] += 1
        else:
            self._stats["failed_tasks"] += 1
    
    def _update_agent_utilization(self, agent_id: str) -> None:
        """Update agent utilization statistics."""
        if agent_id in self._agent_metadata:
            self._agent_metadata[agent_id]["tasks_processed"] += 1
            self._agent_metadata[agent_id]["last_task_time"] = time.time()
        
        # Update global utilization stats
        if agent_id not in self._stats["agent_utilization"]:
            self._stats["agent_utilization"][agent_id] = 0
        self._stats["agent_utilization"][agent_id] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        uptime = time.time() - self._start_time if self._start_time else 0
        
        base_stats = {
            "system_running": self._running,
            "uptime_seconds": uptime,
            "total_agents": len(self._agents),
            "has_supervisor": self._supervisor is not None,
            **self._stats,
        }
        
        # Add success rate
        total_tasks = self._stats["total_tasks_processed"]
        if total_tasks > 0:
            base_stats["success_rate"] = self._stats["successful_tasks"] / total_tasks
        else:
            base_stats["success_rate"] = 0.0
        
        # Add agent information
        agent_info = {}
        for agent_id, agent in self._agents.items():
            metadata = self._agent_metadata.get(agent_id, {})
            agent_info[agent_id] = {
                "name": agent.name,
                "status": agent.get_status(),
                "capabilities": metadata.get("capabilities", []),
                "tasks_processed": metadata.get("tasks_processed", 0),
                "last_task_time": metadata.get("last_task_time"),
            }
        
        base_stats["agents"] = agent_info
        
        # Add supervisor statistics if available
        if self._supervisor:
            base_stats["supervisor_stats"] = self._supervisor.get_supervisor_status()
        
        # Add task manager statistics if available
        if self._global_task_manager:
            base_stats["task_manager_stats"] = self._global_task_manager.get_statistics()
        
        # Add topology statistics
        if hasattr(self, 'topology'):
            base_stats["topology_stats"] = self.topology.get_topology_stats()
        
        return base_stats
    
    def get_agent_status(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of specific agent or all agents."""
        if agent_id:
            if agent_id not in self._agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self._agents[agent_id]
            metadata = self._agent_metadata.get(agent_id, {})
            
            return {
                "agent_id": agent_id,
                "name": agent.name,
                "status": agent.get_status(),
                "capabilities": metadata.get("capabilities", []),
                "tasks_processed": metadata.get("tasks_processed", 0),
                "registered_at": metadata.get("registered_at"),
                "last_task_time": metadata.get("last_task_time"),
            }
        else:
            # Return all agents
            return {
                agent_id: self.get_agent_status(agent_id)
                for agent_id in self._agents.keys()
            }
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents with basic information."""
        return [
            {
                "id": agent_id,
                "name": agent.name,
                "capabilities": self._agent_metadata.get(agent_id, {}).get("capabilities", []),
                "tasks_processed": self._agent_metadata.get(agent_id, {}).get("tasks_processed", 0),
            }
            for agent_id, agent in self._agents.items()
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health_status = {
            "system_healthy": True,
            "timestamp": time.time(),
            "issues": [],
        }
        
        # Check if system is running
        if not self._running:
            health_status["system_healthy"] = False
            health_status["issues"].append("System is not running")
        
        # Check supervisor health
        if self._supervisor:
            supervisor_status = self._supervisor.get_status()
            if supervisor_status["status"] == "error":
                health_status["system_healthy"] = False
                health_status["issues"].append("Supervisor is in error state")
        
        # Check agent health
        unhealthy_agents = []
        for agent_id, agent in self._agents.items():
            agent_status = agent.get_status()
            if agent_status["status"] == "error":
                unhealthy_agents.append(agent_id)
        
        if unhealthy_agents:
            health_status["system_healthy"] = False
            health_status["issues"].append(f"Unhealthy agents: {unhealthy_agents}")
        
        # Check task manager health
        if self._global_task_manager and not self._global_task_manager._running:
            health_status["system_healthy"] = False
            health_status["issues"].append("Global task manager is not running")
        
        health_status["component_status"] = {
            "supervisor": self._supervisor.get_status() if self._supervisor else None,
            "agents": {agent_id: agent.get_status() for agent_id, agent in self._agents.items()},
            "task_manager": self._global_task_manager.get_statistics() if self._global_task_manager else None,
            "communication_hub": self._communication_hub.get_statistics() if self._communication_hub else None,
        }
        
        return health_status
    
    def __repr__(self) -> str:
        """String representation of the system."""
        supervisor_info = f" with supervisor ({self._supervisor.name})" if self._supervisor else ""
        return f"MultiAgentSystem({len(self._agents)} agents{supervisor_info}, running={self._running})"