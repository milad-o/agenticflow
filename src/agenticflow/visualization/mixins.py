"""
Visualization mixins for AgenticFlow core objects.

These mixins add .visualize() and .show() methods directly to agents, workflows, etc.
"""

import tempfile
from typing import Optional, List, Dict, Any, Union
from pathlib import Path


class AgentVisualizationMixin:
    """Add visualization methods to Agent objects."""
    
    def visualize(
        self, 
        show: bool = True,
        save_path: Optional[str] = None,
        format: str = "svg",
        include_tools: bool = True,
        **kwargs
    ) -> Optional[str]:
        """
        Visualize this agent.
        
        Args:
            show: Whether to open visualization automatically
            save_path: Where to save (if None, uses temp file when show=True)
            format: Output format (svg, png, pdf)
            include_tools: Whether to show tools
            
        Returns:
            Path to generated file
            
        Example:
            agent.visualize()  # Shows agent with its tools and state
        """
        from .simple import visualize_agents, SimpleAgent
        
        # Extract agent info
        tools = []
        if hasattr(self, '_tool_registry') and self._tool_registry:
            tools = list(self._tool_registry.list_tools())
        elif hasattr(self, 'tools'):
            tools = getattr(self, 'tools', [])
            
        role = getattr(self, 'role', 'agent')
        if hasattr(self, 'config') and hasattr(self.config, 'role'):
            role = self.config.role or 'agent'
            
        agent_data = SimpleAgent(
            name=getattr(self, 'name', 'Agent'),
            role=role,
            tools=tools if include_tools else []
        )
        
        return visualize_agents(
            [agent_data],
            topology="star",
            title=f"Agent: {agent_data.name}",
            show=show,
            save_path=save_path,
            format=format
        )
    
    def show(self, **kwargs) -> Optional[str]:
        """Quick show - same as visualize() but always shows."""
        kwargs.pop('show', None)
        return self.visualize(show=True, **kwargs)


class WorkflowVisualizationMixin:
    """Add visualization methods to workflow/orchestrator objects."""
    
    def visualize(
        self,
        show: bool = True,
        save_path: Optional[str] = None,
        format: str = "svg",
        **kwargs
    ) -> Optional[str]:
        """
        Visualize this workflow/orchestrator.
        
        Args:
            show: Whether to open visualization automatically
            save_path: Where to save
            format: Output format
            
        Returns:
            Path to generated file
            
        Example:
            orchestrator.visualize()  # Shows current workflow state
        """
        from .simple import visualize_workflow, SimpleTask
        
        # Extract tasks from orchestrator
        tasks = self._extract_tasks_for_visualization()
        
        workflow_name = getattr(self, 'name', 'Workflow')
        if hasattr(self, 'config') and hasattr(self.config, 'name'):
            workflow_name = self.config.name or 'Workflow'
        
        return visualize_workflow(
            tasks,
            workflow_name=workflow_name,
            description=self._get_workflow_description(),
            show=show,
            save_path=save_path,
            format=format
        )
    
    def show(self, **kwargs) -> Optional[str]:
        """Quick show - same as visualize() but always shows."""
        # Remove 'show' from kwargs if it exists to avoid duplicate parameter
        kwargs.pop('show', None)
        return self.visualize(show=True, **kwargs)
    
    def _extract_tasks_for_visualization(self) -> List:
        """Extract tasks from the orchestrator for visualization."""
        from .simple import SimpleTask
        
        tasks = []
        
        # Try different ways to get tasks based on the object type
        task_source = None
        if hasattr(self, 'dag') and hasattr(self.dag, 'tasks'):
            task_source = self.dag.tasks
        elif hasattr(self, 'tasks'):
            task_source = self.tasks
        elif hasattr(self, '_tasks'):
            task_source = self._tasks
        
        if task_source:
            for task_id, task in task_source.items():
                # Convert different task formats
                name = getattr(task, 'name', task_id)
                
                # Determine status
                status = "pending"
                if hasattr(task, 'state'):
                    state = task.state
                    if hasattr(state, 'value'):
                        status = state.value.lower()
                    else:
                        status = str(state).lower()
                elif hasattr(task, 'status'):
                    status = str(task.status).lower()
                
                # Get duration
                duration = None
                if hasattr(task, 'execution_time'):
                    duration = task.execution_time
                elif hasattr(task, 'duration'):
                    duration = task.duration
                
                # Get dependencies
                dependencies = []
                if hasattr(task, 'dependencies'):
                    dependencies = list(task.dependencies) if task.dependencies else []
                elif hasattr(task, 'depends_on'):
                    dependencies = list(task.depends_on) if task.depends_on else []
                
                # Get priority
                priority = "normal"
                if hasattr(task, 'priority'):
                    priority = str(task.priority).lower()
                
                tasks.append(SimpleTask(
                    name=name,
                    status=status,
                    duration=duration,
                    depends_on=dependencies,
                    description=getattr(task, 'description', ''),
                    priority=priority
                ))
        
        # If no tasks found, create a placeholder
        if not tasks:
            tasks.append(SimpleTask(
                name="No Tasks",
                status="pending",
                description="No tasks found in this workflow"
            ))
        
        return tasks
    
    def _get_workflow_description(self) -> str:
        """Get description for the workflow."""
        if hasattr(self, 'description'):
            return self.description
        elif hasattr(self, 'config') and hasattr(self.config, 'description'):
            return self.config.description or "Task orchestration workflow"
        else:
            return "Task orchestration workflow"


class MultiAgentSystemVisualizationMixin:
    """Add visualization methods to MultiAgentSystem objects."""
    
    def visualize(
        self,
        show: bool = True,
        save_path: Optional[str] = None,
        format: str = "svg",
        include_tools: bool = True,
        **kwargs
    ) -> Optional[str]:
        """
        Visualize this multi-agent system.
        
        Args:
            show: Whether to open visualization automatically
            save_path: Where to save
            format: Output format
            include_tools: Whether to show agent tools
            
        Returns:
            Path to generated file
            
        Example:
            system.visualize()  # Shows system topology
        """
        from .simple import visualize_agents, SimpleAgent
        
        # Extract agents
        agents_data = []
        
        # Get agents from different possible locations
        agents_source = getattr(self, '_agents', {})
        if not agents_source and hasattr(self, 'agents'):
            agents_source = self.agents
        
        for agent_id, agent in agents_source.items():
            # Extract agent info
            name = getattr(agent, 'name', agent_id)
            role = self._determine_agent_role(agent)
            tools = self._extract_agent_tools(agent) if include_tools else []
            
            agents_data.append(SimpleAgent(
                name=name,
                role=role,
                tools=tools
            ))
        
        # Add supervisor if exists
        if hasattr(self, '_supervisor') and self._supervisor:
            supervisor = self._supervisor
            agents_data.insert(0, SimpleAgent(
                name=getattr(supervisor, 'name', 'Supervisor'),
                role='supervisor',
                tools=self._extract_agent_tools(supervisor) if include_tools else []
            ))
        
        # Determine topology
        topology_type = "star"  # default
        if hasattr(self, 'topology') and hasattr(self.topology, 'topology_type'):
            topology_map = {
                'STAR': 'star',
                'HIERARCHICAL': 'hierarchy', 
                'PEER_TO_PEER': 'mesh',
                'PIPELINE': 'pipeline'
            }
            topology_type = topology_map.get(
                str(self.topology.topology_type).upper(),
                'star'
            )
        
        system_name = "Multi-Agent System"
        if hasattr(self, 'name'):
            system_name = self.name
        elif hasattr(self, 'config') and hasattr(self.config, 'name'):
            system_name = self.config.name or system_name
        
        return visualize_agents(
            agents_data,
            topology=topology_type,
            title=system_name,
            show=show,
            save_path=save_path,
            format=format
        )
    
    def show(self, **kwargs) -> Optional[str]:
        """Quick show - same as visualize() but always shows.""" 
        kwargs.pop('show', None)
        return self.visualize(show=True, **kwargs)
    
    def _determine_agent_role(self, agent) -> str:
        """Determine the role of an agent."""
        # Try different ways to get role
        if hasattr(agent, 'role'):
            return agent.role
        elif hasattr(agent, 'config') and hasattr(agent.config, 'role'):
            return agent.config.role or 'worker'
        elif 'supervisor' in getattr(agent, 'name', '').lower():
            return 'supervisor'
        else:
            return 'worker'
    
    def _extract_agent_tools(self, agent) -> List[str]:
        """Extract tools from an agent."""
        tools = []
        
        # Try different ways to get tools
        if hasattr(agent, '_tool_registry') and agent._tool_registry:
            tools = list(agent._tool_registry.list_tools())
        elif hasattr(agent, 'tools'):
            tools_attr = getattr(agent, 'tools')
            if isinstance(tools_attr, list):
                tools = tools_attr
            elif hasattr(tools_attr, 'keys'):
                tools = list(tools_attr.keys())
        
        return tools


class JupyterVisualizationMixin:
    """Add Jupyter notebook display methods to objects."""
    
    def _repr_html_(self) -> str:
        """Display visualization inline in Jupyter notebooks."""
        try:
            # Generate the visualization
            if hasattr(self, '_extract_tasks_for_visualization'):
                # This is a workflow/orchestrator
                from .simple import show_workflow
                tasks = self._extract_tasks_for_visualization()
                viz = show_workflow(tasks)
                return viz._repr_html_()
            
            elif hasattr(self, '_agents') or hasattr(self, 'agents'):
                # This is a multi-agent system
                from .simple import show_agents, SimpleAgent
                
                agents_data = []
                agents_source = getattr(self, '_agents', {}) or getattr(self, 'agents', {})
                
                for agent_id, agent in agents_source.items():
                    agents_data.append(SimpleAgent(
                        name=getattr(agent, 'name', agent_id),
                        role=self._determine_agent_role(agent) if hasattr(self, '_determine_agent_role') else 'worker'
                    ))
                
                viz = show_agents(agents_data)
                return viz._repr_html_()
            
            else:
                # This is likely a single agent
                from .simple import show_agents, SimpleAgent
                
                name = getattr(self, 'name', 'Agent')
                role = 'agent'
                if hasattr(self, 'config') and hasattr(self.config, 'role'):
                    role = self.config.role or 'agent'
                
                agent_data = SimpleAgent(name=name, role=role)
                viz = show_agents([agent_data])
                return viz._repr_html_()
                
        except Exception as e:
            return f"""
            <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 10px; color: #c62828;">
                <h4>Visualization Error</h4>
                <p>Failed to render visualization: {str(e)}</p>
                <p><em>Try calling .visualize() or .show() methods instead</em></p>
            </div>
            """


# Combined mixin for objects that might be any of the above
class FullVisualizationMixin(
    AgentVisualizationMixin, 
    WorkflowVisualizationMixin, 
    MultiAgentSystemVisualizationMixin,
    JupyterVisualizationMixin
):
    """Complete visualization mixin with all capabilities.""" 
    pass