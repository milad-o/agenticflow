"""
Topology visualizer for multi-agent systems.
"""

from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass
from .mermaid_generator import (
    MermaidGenerator,
    DiagramType,
    FlowDirection,
    NodeShape,
    EdgeType,
    ColorSchemes,
    create_agent_visualization_styles
)


@dataclass
class AgentInfo:
    """Information about an agent for visualization."""
    id: str
    name: str
    role: str
    tools: List[str]
    agent_type: str  # supervisor, worker, specialist, coordinator


class TopologyVisualizer:
    """
    Visualizes multi-agent system topologies using Mermaid diagrams.
    
    Supports all AgenticFlow topology types with tool relationships.
    """
    
    def __init__(self):
        self.generator = MermaidGenerator(DiagramType.FLOWCHART)
        self._setup_default_styles()
        
    def _setup_default_styles(self):
        """Setup default CSS classes for visualization."""
        styles = create_agent_visualization_styles()
        for class_name, style_dict in styles.items():
            self.generator.add_css_class(class_name, style_dict)
            
    def visualize_system(
        self,
        system: Any,  # MultiAgentSystem
        include_tools: bool = True,
        include_tool_relationships: bool = True,
        layout_direction: FlowDirection = FlowDirection.TOP_DOWN
    ) -> str:
        """
        Visualize a complete multi-agent system.
        
        Args:
            system: The MultiAgentSystem to visualize
            include_tools: Whether to show tools as separate nodes
            include_tool_relationships: Whether to show agent-tool relationships
            layout_direction: Layout direction for the diagram
            
        Returns:
            Mermaid diagram as string
        """
        self.generator.clear().set_direction(layout_direction)
        
        # Extract agent information
        agents = self._extract_agent_info(system)
        
        # Add agents based on topology
        topology_name = str(getattr(system, 'topology_type', 'STAR')).upper()
        
        if topology_name == "STAR":
            return self._visualize_star_topology(agents, include_tools, include_tool_relationships)
        elif topology_name == "PEER_TO_PEER":
            return self._visualize_p2p_topology(agents, include_tools, include_tool_relationships)
        elif topology_name == "HIERARCHICAL":
            return self._visualize_hierarchical_topology(agents, include_tools, include_tool_relationships)
        elif topology_name == "PIPELINE":
            return self._visualize_pipeline_topology(agents, include_tools, include_tool_relationships)
        else:
            return self._visualize_custom_topology(agents, include_tools, include_tool_relationships)
            
    def visualize_agents_only(
        self,
        agents: List[Any],  # List[Agent]
        topology_type: str = "PEER_TO_PEER",
        layout_direction: FlowDirection = FlowDirection.TOP_DOWN
    ) -> str:
        """
        Visualize just the agents without a full system.
        
        Args:
            agents: List of agents to visualize
            topology_type: How to arrange the agents
            layout_direction: Layout direction
            
        Returns:
            Mermaid diagram as string
        """
        self.generator.clear().set_direction(layout_direction)
        
        # Create a mock system for visualization
        agent_infos = []
        for i, agent in enumerate(agents):
            agent_infos.append(AgentInfo(
                id=f"agent_{i}",
                name=agent.config.name,
                role=getattr(agent.config, 'role', 'worker'),
                tools=self._get_agent_tools(agent),
                agent_type=self._classify_agent_type(agent)
            ))
            
        topology_name = str(topology_type).upper()
        
        if topology_name == "STAR":
            return self._visualize_star_topology(agent_infos, False, False)
        elif topology_name == "PEER_TO_PEER":
            return self._visualize_p2p_topology(agent_infos, False, False)
        elif topology_name == "HIERARCHICAL":
            return self._visualize_hierarchical_topology(agent_infos, False, False)
        else:
            return self._visualize_pipeline_topology(agent_infos, False, False)
            
    def _extract_agent_info(self, system: Any) -> List[AgentInfo]:
        """Extract agent information from the system."""
        agents = []
        
        # Add supervisor if exists
        if system.supervisor:
            agents.append(AgentInfo(
                id="supervisor",
                name=system.supervisor.config.name,
                role="supervisor",
                tools=self._get_agent_tools(system.supervisor),
                agent_type="supervisor"
            ))
            
        # Add worker agents
        for i, agent in enumerate(system.agents):
            agents.append(AgentInfo(
                id=f"agent_{i}",
                name=agent.config.name,
                role=getattr(agent.config, 'role', 'worker'),
                tools=self._get_agent_tools(agent),
                agent_type=self._classify_agent_type(agent)
            ))
            
        return agents
        
    def _get_agent_tools(self, agent: Any) -> List[str]:
        """Extract tool names from an agent."""
        if hasattr(agent, 'tool_registry') and agent.tool_registry:
            return list(agent.tool_registry.tools.keys())
        return []
        
    def _classify_agent_type(self, agent: Any) -> str:
        """Classify agent type based on its configuration."""
        role = getattr(agent.config, 'role', '').lower()
        if 'supervisor' in role or 'manager' in role:
            return 'supervisor'
        elif 'specialist' in role or 'expert' in role:
            return 'specialist'
        elif 'coordinator' in role:
            return 'coordinator'
        else:
            return 'worker'
            
    def _visualize_star_topology(
        self,
        agents: List[AgentInfo],
        include_tools: bool,
        include_tool_relationships: bool
    ) -> str:
        """Visualize star topology with supervisor at center."""
        
        # Find supervisor
        supervisor = next((a for a in agents if a.agent_type == 'supervisor'), agents[0])
        workers = [a for a in agents if a != supervisor]
        
        # Add supervisor node
        self.generator.add_node(
            supervisor.id,
            f"{supervisor.name}<br/>({supervisor.role})",
            NodeShape.HEXAGON,
            css_class="agent-supervisor"
        )
        
        # Add worker nodes
        for worker in workers:
            self.generator.add_node(
                worker.id,
                f"{worker.name}<br/>({worker.role})",
                NodeShape.ROUNDED,
                css_class=f"agent-{worker.agent_type}"
            )
            
            # Connect to supervisor
            self.generator.add_edge(
                supervisor.id,
                worker.id,
                "manages",
                EdgeType.SOLID
            )
            
        # Add tools if requested
        if include_tools:
            self._add_tools_and_relationships(agents, include_tool_relationships)
            
        return self.generator.generate()
        
    def _visualize_p2p_topology(
        self,
        agents: List[AgentInfo],
        include_tools: bool,
        include_tool_relationships: bool
    ) -> str:
        """Visualize peer-to-peer topology with all agents connected."""
        
        # Add all agent nodes
        for agent in agents:
            self.generator.add_node(
                agent.id,
                f"{agent.name}<br/>({agent.role})",
                NodeShape.ROUNDED,
                css_class=f"agent-{agent.agent_type}"
            )
            
        # Connect all agents to each other
        for i, agent1 in enumerate(agents):
            for j, agent2 in enumerate(agents):
                if i < j:  # Avoid duplicate connections
                    self.generator.add_edge(
                        agent1.id,
                        agent2.id,
                        "communicates",
                        EdgeType.DOTTED
                    )
                    
        # Add tools if requested
        if include_tools:
            self._add_tools_and_relationships(agents, include_tool_relationships)
            
        return self.generator.generate()
        
    def _visualize_hierarchical_topology(
        self,
        agents: List[AgentInfo],
        include_tools: bool,
        include_tool_relationships: bool
    ) -> str:
        """Visualize hierarchical topology with multiple levels."""
        
        # Organize agents by hierarchy level
        supervisors = [a for a in agents if a.agent_type == 'supervisor']
        coordinators = [a for a in agents if a.agent_type == 'coordinator']
        workers = [a for a in agents if a.agent_type in ['worker', 'specialist']]
        
        # Create subgraphs for different levels
        if supervisors:
            self.generator.add_subgraph("management", "Management Layer")
            for supervisor in supervisors:
                self.generator.add_node(
                    supervisor.id,
                    f"{supervisor.name}<br/>({supervisor.role})",
                    NodeShape.HEXAGON,
                    css_class="agent-supervisor"
                )
                self.generator.subgraphs["management"].nodes.append(supervisor.id)
                
        if coordinators:
            self.generator.add_subgraph("coordination", "Coordination Layer")
            for coordinator in coordinators:
                self.generator.add_node(
                    coordinator.id,
                    f"{coordinator.name}<br/>({coordinator.role})",
                    NodeShape.DIAMOND,
                    css_class="agent-coordinator"
                )
                self.generator.subgraphs["coordination"].nodes.append(coordinator.id)
                
        if workers:
            self.generator.add_subgraph("execution", "Execution Layer")
            for worker in workers:
                self.generator.add_node(
                    worker.id,
                    f"{worker.name}<br/>({worker.role})",
                    NodeShape.ROUNDED,
                    css_class=f"agent-{worker.agent_type}"
                )
                self.generator.subgraphs["execution"].nodes.append(worker.id)
                
        # Add hierarchical connections
        for supervisor in supervisors:
            for coordinator in coordinators:
                self.generator.add_edge(supervisor.id, coordinator.id, "delegates", EdgeType.SOLID)
            for worker in workers:
                self.generator.add_edge(supervisor.id, worker.id, "oversees", EdgeType.DOTTED)
                
        for coordinator in coordinators:
            for worker in workers:
                self.generator.add_edge(coordinator.id, worker.id, "coordinates", EdgeType.SOLID)
                
        # Add tools if requested
        if include_tools:
            self._add_tools_and_relationships(agents, include_tool_relationships)
            
        return self.generator.generate()
        
    def _visualize_pipeline_topology(
        self,
        agents: List[AgentInfo],
        include_tools: bool,
        include_tool_relationships: bool
    ) -> str:
        """Visualize pipeline topology with sequential flow."""
        
        # Add agent nodes
        for agent in agents:
            self.generator.add_node(
                agent.id,
                f"{agent.name}<br/>({agent.role})",
                NodeShape.ROUNDED,
                css_class=f"agent-{agent.agent_type}"
            )
            
        # Connect agents in sequence
        for i in range(len(agents) - 1):
            self.generator.add_edge(
                agents[i].id,
                agents[i + 1].id,
                f"step {i + 1}",
                EdgeType.THICK
            )
            
        # Add tools if requested
        if include_tools:
            self._add_tools_and_relationships(agents, include_tool_relationships)
            
        return self.generator.generate()
        
    def _visualize_custom_topology(
        self,
        agents: List[AgentInfo],
        include_tools: bool,
        include_tool_relationships: bool
    ) -> str:
        """Visualize custom topology (fallback to P2P)."""
        return self._visualize_p2p_topology(agents, include_tools, include_tool_relationships)
        
    def _add_tools_and_relationships(
        self,
        agents: List[AgentInfo],
        include_relationships: bool
    ):
        """Add tool nodes and their relationships to agents."""
        
        # Collect all unique tools
        all_tools = set()
        for agent in agents:
            all_tools.update(agent.tools)
            
        if not all_tools:
            return
            
        # Create tools subgraph
        self.generator.add_subgraph("tools", "Available Tools")
        
        # Add tool nodes
        for tool in all_tools:
            tool_id = f"tool_{tool}"
            tool_type = self._classify_tool_type(tool)
            
            self.generator.add_node(
                tool_id,
                tool,
                NodeShape.CYLINDER,
                css_class=f"tool-{tool_type}"
            )
            self.generator.subgraphs["tools"].nodes.append(tool_id)
            
        # Add relationships if requested
        if include_relationships:
            for agent in agents:
                for tool in agent.tools:
                    tool_id = f"tool_{tool}"
                    self.generator.add_edge(
                        agent.id,
                        tool_id,
                        "uses",
                        EdgeType.DOTTED
                    )
                    
    def _classify_tool_type(self, tool_name: str) -> str:
        """Classify tool type based on name."""
        tool_name_lower = tool_name.lower()
        
        if any(keyword in tool_name_lower for keyword in ['llm', 'ai', 'model', 'chat']):
            return 'llm'
        elif any(keyword in tool_name_lower for keyword in ['db', 'database', 'sql', 'mongo']):
            return 'database'
        elif any(keyword in tool_name_lower for keyword in ['api', 'http', 'web', 'external']):
            return 'external'
        else:
            return 'default'
            
    def create_topology_comparison(
        self,
        agents: List[Any],
        topology_types: List[str] = None
    ) -> Dict[str, str]:
        """
        Create comparison diagrams for different topologies.
        
        Args:
            agents: List of agents to visualize
            topology_types: List of topology types to compare
            
        Returns:
            Dictionary mapping topology type to Mermaid diagram
        """
        if topology_types is None:
            topology_types = [
                "STAR",
                "PEER_TO_PEER", 
                "HIERARCHICAL",
                "PIPELINE"
            ]
            
        diagrams = {}
        
        for topology_type in topology_types:
            diagram = self.visualize_agents_only(agents, topology_type)
            diagrams[topology_type] = diagram
            
        return diagrams
        
    def create_system_overview(
        self,
        system: Any,
        include_metrics: bool = False
    ) -> str:
        """
        Create a comprehensive system overview diagram.
        
        Args:
            system: The MultiAgentSystem to visualize
            include_metrics: Whether to include performance metrics
            
        Returns:
            Comprehensive Mermaid diagram
        """
        self.generator.clear().set_direction(FlowDirection.LEFT_RIGHT)
        
        # Create system architecture overview
        agents = self._extract_agent_info(system)
        
        # System info subgraph
        system_name = getattr(system, 'name', 'Multi-Agent System')
        if hasattr(system, 'config') and hasattr(system.config, 'name'):
            system_name = system.config.name or system_name
            
        topology_name = str(getattr(system, 'topology_type', 'UNKNOWN'))
        
        self.generator.add_subgraph("system_info", f"System: {system_name}")
        self.generator.add_node(
            "system_node",
            f"Topology: {topology_name}<br/>Agents: {len(agents)}",
            NodeShape.RECTANGLE,
            css_class="agent-coordinator"
        )
        self.generator.subgraphs["system_info"].nodes.append("system_node")
        
        # Add main visualization
        topology_name = str(getattr(system, 'topology_type', 'STAR')).upper()
        
        if topology_name == "STAR":
            self._visualize_star_topology(agents, True, True)
        elif topology_name == "HIERARCHICAL":
            self._visualize_hierarchical_topology(agents, True, True)
        else:
            self._visualize_p2p_topology(agents, True, True)
            
        return self.generator.generate()
        
    def draw_system(self, system: Any, output_path: Optional[str] = None,
                   format: str = "png", include_tools: bool = True, 
                   include_tool_relationships: bool = True,
                   layout_direction: FlowDirection = FlowDirection.TOP_DOWN,
                   width: int = 1200, height: int = 800) -> bool:
        """Draw a multi-agent system diagram and save/display it.
        
        Args:
            system: The MultiAgentSystem to visualize
            output_path: Path to save the image. If None, uses temporary file
            format: Output format (png, svg, pdf)
            include_tools: Whether to show tools as separate nodes
            include_tool_relationships: Whether to show agent-tool relationships
            layout_direction: Layout direction for the diagram
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            True if successful, False otherwise
        """
        # Generate the diagram
        diagram_code = self.visualize_system(
            system, include_tools, include_tool_relationships, layout_direction
        )
        
        # Use the generator's draw method
        self.generator.clear()
        # We need to recreate the generator with the diagram
        # For now, let's use the export utils directly
        from .export_utils import get_exporter
        exporter = get_exporter()
        
        if not output_path:
            import tempfile
            output_path = tempfile.mktemp(suffix=f".{format}")
            
        if format.lower() == "svg":
            success = exporter.export_to_svg(diagram_code, output_path)
        elif format.lower() == "png":
            success = exporter.export_to_png(diagram_code, output_path, width=width, height=height)
        elif format.lower() == "pdf":
            success = exporter.export_to_pdf(diagram_code, output_path)
        else:
            print(f"Unsupported format: {format}")
            return False
            
        if success:
            print(f"System diagram saved to: {output_path}")
            # Try to open the file on macOS
            if output_path.startswith("/tmp"):
                try:
                    import subprocess
                    subprocess.run(["open", output_path], check=False)
                except Exception:
                    pass
                    
        return success
        
    def show_system(self, system: Any, format: str = "png",
                   include_tools: bool = True, include_tool_relationships: bool = True,
                   layout_direction: FlowDirection = FlowDirection.TOP_DOWN,
                   width: int = 1200, height: int = 800) -> bool:
        """Show a multi-agent system diagram in a viewer.
        
        Args:
            system: The MultiAgentSystem to visualize
            format: Output format (png, svg, pdf)
            include_tools: Whether to show tools as separate nodes
            include_tool_relationships: Whether to show agent-tool relationships
            layout_direction: Layout direction for the diagram
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            True if successful, False otherwise
        """
        return self.draw_system(system, None, format, include_tools, 
                              include_tool_relationships, layout_direction, width, height)
