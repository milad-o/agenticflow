"""
Multi-Agent Topology System for AgenticFlow.

Provides flexible topology patterns for multi-agent communication and coordination:
- StarTopology (supervisor-based)
- PeerToPeerTopology (fully connected)
- HierarchicalTopology (tree-like structure)  
- PipelineTopology (sequential processing)
- MeshTopology (partial connectivity)
- CustomTopology (user-defined patterns)
"""

import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


class TopologyType(str, Enum):
    """Types of supported topologies."""
    STAR = "star"
    PEER_TO_PEER = "peer_to_peer"
    HIERARCHICAL = "hierarchical"
    PIPELINE = "pipeline"
    MESH = "mesh"
    CUSTOM = "custom"


class MessageRouting(str, Enum):
    """Message routing strategies."""
    DIRECT = "direct"          # Point-to-point
    BROADCAST = "broadcast"    # One-to-many
    MULTICAST = "multicast"    # One-to-some
    PUBLISH_SUBSCRIBE = "pubsub"  # Topic-based


@dataclass
class CommunicationRoute:
    """Defines a communication route between agents."""
    from_agent: str
    to_agent: str
    route_type: MessageRouting = MessageRouting.DIRECT
    bidirectional: bool = True
    filters: Optional[List[str]] = None  # Message type filters
    middleware: Optional[List[Callable]] = None  # Message transformations
    priority: int = 1  # Route priority (higher = more preferred)
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = []
        if self.middleware is None:
            self.middleware = []


@dataclass
class AgentNode:
    """Represents an agent in the topology."""
    agent_id: str
    agent_name: str
    capabilities: List[str] = field(default_factory=list)
    role: Optional[str] = None  # e.g., "supervisor", "worker", "coordinator"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Communication settings
    max_concurrent_messages: int = 10
    message_queue_size: int = 100
    timeout_seconds: int = 30


class BaseTopology(ABC):
    """Abstract base class for multi-agent topologies."""
    
    def __init__(self, name: str, topology_type: TopologyType):
        self.name = name
        self.topology_type = topology_type
        self.logger = logger.bind(component="topology", name=name, type=topology_type.value)
        
        # Topology structure
        self.agents: Dict[str, AgentNode] = {}
        self.routes: List[CommunicationRoute] = []
        self.groups: Dict[str, List[str]] = {}  # Agent groups for broadcasting
        
        # Runtime state
        self._running = False
        self._message_stats: Dict[str, int] = {}
    
    @abstractmethod
    def add_agent(self, agent_id: str, agent_name: str, **kwargs) -> AgentNode:
        """Add an agent to the topology."""
        pass
    
    @abstractmethod
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the topology."""
        pass
    
    @abstractmethod
    def get_communication_routes(self, from_agent: str, to_agent: Optional[str] = None) -> List[CommunicationRoute]:
        """Get communication routes from an agent."""
        pass
    
    def add_route(self, route: CommunicationRoute) -> None:
        """Add a custom communication route."""
        self.routes.append(route)
        self.logger.debug(f"Added route: {route.from_agent} -> {route.to_agent}")
    
    def add_group(self, group_name: str, agent_ids: List[str]) -> None:
        """Create an agent group for broadcasting."""
        self.groups[group_name] = agent_ids
        self.logger.debug(f"Created group {group_name} with {len(agent_ids)} agents")
    
    def get_agent_neighbors(self, agent_id: str) -> List[str]:
        """Get directly connected agents."""
        neighbors = set()
        for route in self.routes:
            if route.from_agent == agent_id:
                neighbors.add(route.to_agent)
            elif route.bidirectional and route.to_agent == agent_id:
                neighbors.add(route.from_agent)
        return list(neighbors)
    
    def find_path(self, from_agent: str, to_agent: str, max_hops: int = 10) -> Optional[List[str]]:
        """Find communication path between agents using BFS."""
        if from_agent == to_agent:
            return [from_agent]
        
        queue = [(from_agent, [from_agent])]
        visited = {from_agent}
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_hops:
                continue
            
            for neighbor in self.get_agent_neighbors(current):
                if neighbor == to_agent:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None  # No path found
    
    def get_topology_stats(self) -> Dict[str, Any]:
        """Get topology statistics."""
        return {
            "name": self.name,
            "type": self.topology_type.value,
            "agents_count": len(self.agents),
            "routes_count": len(self.routes),
            "groups_count": len(self.groups),
            "running": self._running,
            "message_stats": self._message_stats.copy(),
            "connectivity": self._calculate_connectivity()
        }
    
    def _calculate_connectivity(self) -> Dict[str, float]:
        """Calculate connectivity metrics."""
        n = len(self.agents)
        if n < 2:
            return {"density": 0.0, "diameter": 0}
        
        # Calculate network density
        max_edges = n * (n - 1)  # For directed graph
        actual_edges = len(self.routes)
        density = actual_edges / max_edges if max_edges > 0 else 0.0
        
        # Calculate network diameter (longest shortest path)
        max_distance = 0
        for agent1 in self.agents:
            for agent2 in self.agents:
                if agent1 != agent2:
                    path = self.find_path(agent1, agent2)
                    if path:
                        max_distance = max(max_distance, len(path) - 1)
        
        return {
            "density": density,
            "diameter": max_distance
        }


class StarTopology(BaseTopology):
    """Star topology with central supervisor and worker agents."""
    
    def __init__(self, name: str, supervisor_id: Optional[str] = None):
        super().__init__(name, TopologyType.STAR)
        self.supervisor_id = supervisor_id
        self.worker_agents: Set[str] = set()
    
    def add_agent(self, agent_id: str, agent_name: str, **kwargs) -> AgentNode:
        """Add agent as either supervisor or worker."""
        role = kwargs.get('role', 'worker')
        
        if role == 'supervisor':
            if self.supervisor_id and self.supervisor_id != agent_id:
                raise ValueError("Star topology can only have one supervisor")
            self.supervisor_id = agent_id
        elif role == 'worker':
            self.worker_agents.add(agent_id)
        
        node = AgentNode(
            agent_id=agent_id,
            agent_name=agent_name,
            role=role,
            capabilities=kwargs.get('capabilities', []),
            metadata=kwargs.get('metadata', {})
        )
        
        self.agents[agent_id] = node
        self._create_star_routes()
        
        return node
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent and update routes."""
        if agent_id not in self.agents:
            return False
        
        if agent_id == self.supervisor_id:
            self.supervisor_id = None
        else:
            self.worker_agents.discard(agent_id)
        
        del self.agents[agent_id]
        self._create_star_routes()
        return True
    
    def get_communication_routes(self, from_agent: str, to_agent: Optional[str] = None) -> List[CommunicationRoute]:
        """Get routes in star pattern (all through supervisor)."""
        routes = []
        
        if from_agent == self.supervisor_id:
            # Supervisor can communicate with all workers
            for worker_id in self.worker_agents:
                if not to_agent or worker_id == to_agent:
                    routes.append(CommunicationRoute(
                        from_agent=from_agent,
                        to_agent=worker_id,
                        route_type=MessageRouting.DIRECT
                    ))
        else:
            # Workers communicate through supervisor
            if not to_agent or to_agent == self.supervisor_id:
                routes.append(CommunicationRoute(
                    from_agent=from_agent,
                    to_agent=self.supervisor_id,
                    route_type=MessageRouting.DIRECT
                ))
        
        return routes
    
    def _create_star_routes(self):
        """Create star topology routes."""
        self.routes.clear()
        
        if not self.supervisor_id:
            return
        
        # Create bidirectional routes between supervisor and all workers
        for worker_id in self.worker_agents:
            route = CommunicationRoute(
                from_agent=self.supervisor_id,
                to_agent=worker_id,
                route_type=MessageRouting.DIRECT,
                bidirectional=True
            )
            self.routes.append(route)


class PeerToPeerTopology(BaseTopology):
    """Fully connected peer-to-peer topology."""
    
    def __init__(self, name: str):
        super().__init__(name, TopologyType.PEER_TO_PEER)
    
    def add_agent(self, agent_id: str, agent_name: str, **kwargs) -> AgentNode:
        """Add agent and create connections to all existing agents."""
        node = AgentNode(
            agent_id=agent_id,
            agent_name=agent_name,
            capabilities=kwargs.get('capabilities', []),
            metadata=kwargs.get('metadata', {})
        )
        
        self.agents[agent_id] = node
        self._create_full_mesh()
        
        return node
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent and update connections."""
        if agent_id not in self.agents:
            return False
        
        del self.agents[agent_id]
        self._create_full_mesh()
        return True
    
    def get_communication_routes(self, from_agent: str, to_agent: Optional[str] = None) -> List[CommunicationRoute]:
        """Get all peer-to-peer routes."""
        routes = []
        
        for agent_id in self.agents:
            if agent_id != from_agent and (not to_agent or agent_id == to_agent):
                routes.append(CommunicationRoute(
                    from_agent=from_agent,
                    to_agent=agent_id,
                    route_type=MessageRouting.DIRECT
                ))
        
        return routes
    
    def _create_full_mesh(self):
        """Create full mesh connectivity."""
        self.routes.clear()
        
        agent_ids = list(self.agents.keys())
        for i, agent1 in enumerate(agent_ids):
            for j, agent2 in enumerate(agent_ids):
                if i < j:  # Avoid duplicates in bidirectional
                    route = CommunicationRoute(
                        from_agent=agent1,
                        to_agent=agent2,
                        route_type=MessageRouting.DIRECT,
                        bidirectional=True
                    )
                    self.routes.append(route)


class HierarchicalTopology(BaseTopology):
    """Hierarchical tree topology with multiple levels."""
    
    def __init__(self, name: str):
        super().__init__(name, TopologyType.HIERARCHICAL)
        self.hierarchy: Dict[str, str] = {}  # child -> parent mapping
        self.root_agent: Optional[str] = None
    
    def add_agent(self, agent_id: str, agent_name: str, **kwargs) -> AgentNode:
        """Add agent to hierarchy."""
        parent_id = kwargs.get('parent_id')
        level = kwargs.get('level', 0)
        
        node = AgentNode(
            agent_id=agent_id,
            agent_name=agent_name,
            role=kwargs.get('role', f'level_{level}'),
            capabilities=kwargs.get('capabilities', []),
            metadata=kwargs.get('metadata', {'level': level})
        )
        
        self.agents[agent_id] = node
        
        if parent_id:
            if parent_id not in self.agents:
                raise ValueError(f"Parent agent {parent_id} must be added first")
            self.hierarchy[agent_id] = parent_id
        else:
            if self.root_agent:
                raise ValueError("Hierarchy can only have one root agent")
            self.root_agent = agent_id
        
        self._create_hierarchical_routes()
        
        return node
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent and handle children."""
        if agent_id not in self.agents:
            return False
        
        # Handle children (they become orphaned or need reassignment)
        children = [child for child, parent in self.hierarchy.items() if parent == agent_id]
        for child in children:
            del self.hierarchy[child]  # Remove orphaned children for now
        
        # Remove from hierarchy
        if agent_id in self.hierarchy:
            del self.hierarchy[agent_id]
        
        if agent_id == self.root_agent:
            self.root_agent = None
        
        del self.agents[agent_id]
        self._create_hierarchical_routes()
        
        return True
    
    def get_communication_routes(self, from_agent: str, to_agent: Optional[str] = None) -> List[CommunicationRoute]:
        """Get hierarchical communication routes."""
        routes = []
        
        # Can communicate with parent
        if from_agent in self.hierarchy:
            parent_id = self.hierarchy[from_agent]
            if not to_agent or parent_id == to_agent:
                routes.append(CommunicationRoute(
                    from_agent=from_agent,
                    to_agent=parent_id,
                    route_type=MessageRouting.DIRECT
                ))
        
        # Can communicate with direct children
        children = [child for child, parent in self.hierarchy.items() if parent == from_agent]
        for child in children:
            if not to_agent or child == to_agent:
                routes.append(CommunicationRoute(
                    from_agent=from_agent,
                    to_agent=child,
                    route_type=MessageRouting.DIRECT
                ))
        
        return routes
    
    def _create_hierarchical_routes(self):
        """Create hierarchical routes."""
        self.routes.clear()
        
        # Create bidirectional parent-child routes
        for child, parent in self.hierarchy.items():
            route = CommunicationRoute(
                from_agent=parent,
                to_agent=child,
                route_type=MessageRouting.DIRECT,
                bidirectional=True
            )
            self.routes.append(route)
    
    def get_hierarchy_tree(self) -> Dict[str, Any]:
        """Get hierarchy as nested dict."""
        def build_tree(agent_id):
            children = [child for child, parent in self.hierarchy.items() if parent == agent_id]
            return {
                "agent_id": agent_id,
                "agent_name": self.agents[agent_id].agent_name,
                "children": [build_tree(child) for child in children]
            }
        
        return build_tree(self.root_agent) if self.root_agent else {}


class PipelineTopology(BaseTopology):
    """Pipeline topology for sequential processing."""
    
    def __init__(self, name: str):
        super().__init__(name, TopologyType.PIPELINE)
        self.pipeline_order: List[str] = []
    
    def add_agent(self, agent_id: str, agent_name: str, **kwargs) -> AgentNode:
        """Add agent to pipeline."""
        position = kwargs.get('position', len(self.pipeline_order))
        
        node = AgentNode(
            agent_id=agent_id,
            agent_name=agent_name,
            role=f'stage_{position}',
            capabilities=kwargs.get('capabilities', []),
            metadata=kwargs.get('metadata', {'position': position})
        )
        
        self.agents[agent_id] = node
        
        # Insert at specified position
        if position >= len(self.pipeline_order):
            self.pipeline_order.append(agent_id)
        else:
            self.pipeline_order.insert(position, agent_id)
        
        self._create_pipeline_routes()
        
        return node
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent from pipeline."""
        if agent_id not in self.agents:
            return False
        
        self.pipeline_order.remove(agent_id)
        del self.agents[agent_id]
        self._create_pipeline_routes()
        
        return True
    
    def get_communication_routes(self, from_agent: str, to_agent: Optional[str] = None) -> List[CommunicationRoute]:
        """Get pipeline routes (to next stage)."""
        routes = []
        
        try:
            current_index = self.pipeline_order.index(from_agent)
            
            # Can send to next stage
            if current_index < len(self.pipeline_order) - 1:
                next_agent = self.pipeline_order[current_index + 1]
                if not to_agent or next_agent == to_agent:
                    routes.append(CommunicationRoute(
                        from_agent=from_agent,
                        to_agent=next_agent,
                        route_type=MessageRouting.DIRECT
                    ))
            
            # Can send back to previous stage (for feedback)
            if current_index > 0:
                prev_agent = self.pipeline_order[current_index - 1]
                if not to_agent or prev_agent == to_agent:
                    routes.append(CommunicationRoute(
                        from_agent=from_agent,
                        to_agent=prev_agent,
                        route_type=MessageRouting.DIRECT
                    ))
        
        except ValueError:
            # Agent not in pipeline
            pass
        
        return routes
    
    def _create_pipeline_routes(self):
        """Create sequential pipeline routes."""
        self.routes.clear()
        
        for i in range(len(self.pipeline_order) - 1):
            current = self.pipeline_order[i]
            next_agent = self.pipeline_order[i + 1]
            
            # Forward route
            route = CommunicationRoute(
                from_agent=current,
                to_agent=next_agent,
                route_type=MessageRouting.DIRECT,
                bidirectional=True  # Allow feedback
            )
            self.routes.append(route)


class MeshTopology(BaseTopology):
    """Partial mesh topology with selective connectivity.
    
    Unlike PeerToPeer (full mesh), this allows selective connections
    based on criteria like capabilities, proximity, or custom rules.
    """
    
    def __init__(self, name: str, max_connections_per_agent: int = 3, 
                 connectivity_strategy: str = "capability_based"):
        super().__init__(name, TopologyType.MESH)
        self.max_connections_per_agent = max_connections_per_agent
        self.connectivity_strategy = connectivity_strategy
        self.connection_matrix: Dict[str, Set[str]] = {}  # agent_id -> connected_agents
        
    def add_agent(self, agent_id: str, agent_name: str, **kwargs) -> AgentNode:
        """Add agent and create selective connections."""
        node = AgentNode(
            agent_id=agent_id,
            agent_name=agent_name,
            capabilities=kwargs.get('capabilities', []),
            role=kwargs.get('role', 'node'),
            metadata=kwargs.get('metadata', {}),
            max_concurrent_messages=kwargs.get('max_concurrent_messages', 10),
            message_queue_size=kwargs.get('message_queue_size', 100),
            timeout_seconds=kwargs.get('timeout_seconds', 30)
        )
        
        self.agents[agent_id] = node
        self.connection_matrix[agent_id] = set()
        
        # Create selective connections based on strategy
        self._create_mesh_connections()
        
        return node
        
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent and update mesh connections."""
        if agent_id not in self.agents:
            return False
        
        # Remove all connections involving this agent
        if agent_id in self.connection_matrix:
            # Remove this agent from other agents' connection sets
            for connected_agent in self.connection_matrix[agent_id]:
                if connected_agent in self.connection_matrix:
                    self.connection_matrix[connected_agent].discard(agent_id)
            
            # Remove this agent's connections
            del self.connection_matrix[agent_id]
        
        del self.agents[agent_id]
        self._create_mesh_connections()
        
        return True
        
    def get_communication_routes(self, from_agent: str, to_agent: Optional[str] = None) -> List[CommunicationRoute]:
        """Get mesh communication routes based on connections."""
        routes = []
        
        if from_agent in self.connection_matrix:
            for connected_agent in self.connection_matrix[from_agent]:
                if not to_agent or connected_agent == to_agent:
                    routes.append(CommunicationRoute(
                        from_agent=from_agent,
                        to_agent=connected_agent,
                        route_type=MessageRouting.DIRECT,
                        bidirectional=True
                    ))
        
        return routes
        
    def _create_mesh_connections(self):
        """Create selective mesh connections based on strategy."""
        self.routes.clear()
        
        if self.connectivity_strategy == "capability_based":
            self._create_capability_based_connections()
        elif self.connectivity_strategy == "round_robin":
            self._create_round_robin_connections()
        elif self.connectivity_strategy == "proximity_based":
            self._create_proximity_based_connections()
        elif self.connectivity_strategy == "random":
            self._create_random_connections()
        else:
            # Default to capability-based
            self._create_capability_based_connections()
        
        # Create routes from connection matrix
        for agent_id, connections in self.connection_matrix.items():
            for connected_agent in connections:
                # Only create route once (avoid duplicates)
                if agent_id < connected_agent:
                    route = CommunicationRoute(
                        from_agent=agent_id,
                        to_agent=connected_agent,
                        route_type=MessageRouting.DIRECT,
                        bidirectional=True
                    )
                    self.routes.append(route)
    
    def _create_capability_based_connections(self):
        """Connect agents with similar or complementary capabilities."""
        agent_ids = list(self.agents.keys())
        
        for agent_id in agent_ids:
            if len(self.connection_matrix[agent_id]) >= self.max_connections_per_agent:
                continue
                
            agent_capabilities = set(self.agents[agent_id].capabilities)
            candidates = []
            
            # Find agents with overlapping capabilities
            for other_id in agent_ids:
                if other_id == agent_id:
                    continue
                if other_id in self.connection_matrix[agent_id]:
                    continue
                if len(self.connection_matrix[other_id]) >= self.max_connections_per_agent:
                    continue
                    
                other_capabilities = set(self.agents[other_id].capabilities)
                overlap = len(agent_capabilities.intersection(other_capabilities))
                candidates.append((other_id, overlap))
            
            # Sort by capability overlap (descending)
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Connect to top candidates
            connections_to_make = min(
                self.max_connections_per_agent - len(self.connection_matrix[agent_id]),
                len(candidates)
            )
            
            for i in range(connections_to_make):
                other_id, _ = candidates[i]
                self.connection_matrix[agent_id].add(other_id)
                self.connection_matrix[other_id].add(agent_id)
    
    def _create_round_robin_connections(self):
        """Connect agents in a round-robin fashion."""
        agent_ids = list(self.agents.keys())
        n = len(agent_ids)
        
        if n < 2:
            return
            
        for i, agent_id in enumerate(agent_ids):
            connections_made = 0
            offset = 1
            
            while connections_made < self.max_connections_per_agent and offset < n:
                other_idx = (i + offset) % n
                other_id = agent_ids[other_idx]
                
                if (other_id not in self.connection_matrix[agent_id] and 
                    len(self.connection_matrix[other_id]) < self.max_connections_per_agent):
                    
                    self.connection_matrix[agent_id].add(other_id)
                    self.connection_matrix[other_id].add(agent_id)
                    connections_made += 1
                
                offset += 1
    
    def _create_proximity_based_connections(self):
        """Connect agents based on metadata proximity (e.g., location, department)."""
        agent_ids = list(self.agents.keys())
        
        for agent_id in agent_ids:
            if len(self.connection_matrix[agent_id]) >= self.max_connections_per_agent:
                continue
                
            agent_metadata = self.agents[agent_id].metadata
            candidates = []
            
            for other_id in agent_ids:
                if other_id == agent_id:
                    continue
                if other_id in self.connection_matrix[agent_id]:
                    continue
                if len(self.connection_matrix[other_id]) >= self.max_connections_per_agent:
                    continue
                    
                other_metadata = self.agents[other_id].metadata
                
                # Calculate "proximity" based on shared metadata keys
                shared_keys = set(agent_metadata.keys()).intersection(set(other_metadata.keys()))
                proximity_score = 0
                
                for key in shared_keys:
                    if agent_metadata[key] == other_metadata[key]:
                        proximity_score += 1
                
                if proximity_score > 0:
                    candidates.append((other_id, proximity_score))
            
            # Sort by proximity score (descending)
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Connect to closest agents
            connections_to_make = min(
                self.max_connections_per_agent - len(self.connection_matrix[agent_id]),
                len(candidates)
            )
            
            for i in range(connections_to_make):
                other_id, _ = candidates[i]
                self.connection_matrix[agent_id].add(other_id)
                self.connection_matrix[other_id].add(agent_id)
    
    def _create_random_connections(self):
        """Connect agents randomly up to max connections."""
        import random
        
        agent_ids = list(self.agents.keys())
        random.shuffle(agent_ids)
        
        for agent_id in agent_ids:
            if len(self.connection_matrix[agent_id]) >= self.max_connections_per_agent:
                continue
                
            # Get available candidates
            candidates = [
                other_id for other_id in agent_ids 
                if (other_id != agent_id and 
                    other_id not in self.connection_matrix[agent_id] and
                    len(self.connection_matrix[other_id]) < self.max_connections_per_agent)
            ]
            
            # Randomly select connections
            connections_to_make = min(
                self.max_connections_per_agent - len(self.connection_matrix[agent_id]),
                len(candidates)
            )
            
            selected = random.sample(candidates, connections_to_make)
            
            for other_id in selected:
                self.connection_matrix[agent_id].add(other_id)
                self.connection_matrix[other_id].add(agent_id)
    
    def add_connection(self, agent1_id: str, agent2_id: str) -> bool:
        """Manually add a connection between two agents."""
        if (agent1_id not in self.agents or agent2_id not in self.agents or
            agent1_id == agent2_id):
            return False
            
        if (len(self.connection_matrix[agent1_id]) >= self.max_connections_per_agent or
            len(self.connection_matrix[agent2_id]) >= self.max_connections_per_agent):
            return False
            
        self.connection_matrix[agent1_id].add(agent2_id)
        self.connection_matrix[agent2_id].add(agent1_id)
        
        # Update routes
        self._create_mesh_connections()
        return True
    
    def remove_connection(self, agent1_id: str, agent2_id: str) -> bool:
        """Manually remove a connection between two agents."""
        if (agent1_id not in self.connection_matrix or 
            agent2_id not in self.connection_matrix[agent1_id]):
            return False
            
        self.connection_matrix[agent1_id].discard(agent2_id)
        self.connection_matrix[agent2_id].discard(agent1_id)
        
        # Update routes
        self._create_mesh_connections()
        return True
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about mesh connectivity."""
        total_connections = sum(len(connections) for connections in self.connection_matrix.values()) // 2
        n = len(self.agents)
        max_possible = (n * (n - 1)) // 2  # Full mesh
        
        connectivity_ratio = total_connections / max_possible if max_possible > 0 else 0.0
        
        # Connection distribution
        connection_counts = [len(connections) for connections in self.connection_matrix.values()]
        avg_connections = sum(connection_counts) / len(connection_counts) if connection_counts else 0
        
        return {
            "total_connections": total_connections,
            "max_possible_connections": max_possible,
            "connectivity_ratio": connectivity_ratio,
            "average_connections_per_agent": avg_connections,
            "max_connections_per_agent": self.max_connections_per_agent,
            "connectivity_strategy": self.connectivity_strategy,
            "agents_count": n
        }


class CustomTopology(BaseTopology):
    """Fully customizable topology for complex patterns."""
    
    def __init__(self, name: str):
        super().__init__(name, TopologyType.CUSTOM)
        self.custom_rules: List[Callable] = []
    
    def add_agent(self, agent_id: str, agent_name: str, **kwargs) -> AgentNode:
        """Add agent with custom configuration."""
        node = AgentNode(
            agent_id=agent_id,
            agent_name=agent_name,
            role=kwargs.get('role', 'custom'),
            capabilities=kwargs.get('capabilities', []),
            metadata=kwargs.get('metadata', {}),
            max_concurrent_messages=kwargs.get('max_concurrent_messages', 10),
            message_queue_size=kwargs.get('message_queue_size', 100),
            timeout_seconds=kwargs.get('timeout_seconds', 30)
        )
        
        self.agents[agent_id] = node
        self._apply_custom_rules()
        
        return node
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent from custom topology."""
        if agent_id not in self.agents:
            return False
        
        # Remove all routes involving this agent
        self.routes = [r for r in self.routes if r.from_agent != agent_id and r.to_agent != agent_id]
        
        del self.agents[agent_id]
        self._apply_custom_rules()
        
        return True
    
    def get_communication_routes(self, from_agent: str, to_agent: Optional[str] = None) -> List[CommunicationRoute]:
        """Get routes based on custom rules."""
        routes = []
        
        for route in self.routes:
            if route.from_agent == from_agent:
                if not to_agent or route.to_agent == to_agent:
                    routes.append(route)
        
        return routes
    
    def add_custom_rule(self, rule: Callable[[Dict[str, AgentNode]], List[CommunicationRoute]]) -> None:
        """Add a custom rule for route generation."""
        self.custom_rules.append(rule)
        self._apply_custom_rules()
    
    def _apply_custom_rules(self):
        """Apply all custom rules to generate routes."""
        # Keep manually added routes
        manual_routes = [r for r in self.routes if hasattr(r, '_manual')]
        
        # Generate routes from rules
        generated_routes = []
        for rule in self.custom_rules:
            try:
                new_routes = rule(self.agents)
                generated_routes.extend(new_routes)
            except Exception as e:
                self.logger.warning(f"Custom rule failed: {e}")
        
        self.routes = manual_routes + generated_routes


# Factory function for creating topologies
def create_topology(topology_type: Union[TopologyType, str], name: str, **kwargs) -> BaseTopology:
    """Factory function to create topology instances."""
    if isinstance(topology_type, str):
        topology_type = TopologyType(topology_type)
    
    if topology_type == TopologyType.STAR:
        return StarTopology(name, **kwargs)
    elif topology_type == TopologyType.PEER_TO_PEER:
        return PeerToPeerTopology(name)
    elif topology_type == TopologyType.HIERARCHICAL:
        return HierarchicalTopology(name)
    elif topology_type == TopologyType.PIPELINE:
        return PipelineTopology(name)
    elif topology_type == TopologyType.MESH:
        return MeshTopology(name, **kwargs)
    elif topology_type == TopologyType.CUSTOM:
        return CustomTopology(name)
    else:
        raise ValueError(f"Unsupported topology type: {topology_type}")


# Convenience functions for common patterns
def create_star_topology(name: str, supervisor_agent: str) -> StarTopology:
    """Create a star topology with specified supervisor."""
    topology = StarTopology(name)
    return topology


def create_pipeline_topology(name: str, agent_stages: List[Tuple[str, str]]) -> PipelineTopology:
    """Create a pipeline topology with specified stages."""
    topology = PipelineTopology(name)
    
    for i, (agent_id, agent_name) in enumerate(agent_stages):
        topology.add_agent(agent_id, agent_name, position=i)
    
    return topology