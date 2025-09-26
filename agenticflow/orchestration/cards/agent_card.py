"""
Agent Card

Enhanced metadata layer for agents in multi-agent coordination.
Provides delegation capabilities, workload tracking, and agent discovery.
"""

from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass, field

from .base_card import BaseCard, CardType, CardMetadata, MatchingCriteria


@dataclass
class AgentPerformanceProfile:
    """Performance characteristics of an agent."""
    speed: str = "medium"  # fast, medium, slow
    quality: str = "high"  # excellent, high, medium, low
    resource_usage: str = "medium"  # low, medium, high
    scalability: str = "medium"  # low, medium, high
    specialization_depth: str = "general"  # narrow, focused, general, broad


class AgentCard(BaseCard):
    """
    Enhanced metadata card for agents.
    
    Enables intelligent agent discovery, delegation, and coordination
    in multi-agent systems.
    """
    
    def __init__(
        self,
        agent_name: str,
        description: str,
        agent_type: str,
        specializations: List[str] = None,
        capabilities: List[str] = None,
        supported_tasks: List[str] = None,
        resource_requirements: List[str] = None,
        performance_profile: AgentPerformanceProfile = None,
        delegation_cost: float = 1.0,
        current_load: float = 0.0,
        agent_instance: Optional[Any] = None,
        metadata: CardMetadata = None
    ):
        # Generate card_id from agent name
        card_id = f"agent:{agent_name}"
        
        super().__init__(
            card_id=card_id,
            name=agent_name,
            description=description,
            card_type=CardType.AGENT,
            metadata=metadata
        )
        
        self.agent_type = agent_type
        self.specializations = specializations or []
        self.capabilities = capabilities or []
        self.supported_tasks = supported_tasks or []
        self.resource_requirements = resource_requirements or []
        self.performance_profile = performance_profile or AgentPerformanceProfile()
        self.delegation_cost = delegation_cost
        self.current_load = current_load
        self.agent_instance = agent_instance
        
        # Derived properties
        self.available = current_load < 0.9
        self.capabilities_set = set(self.capabilities)
        self.specializations_set = set(self.specializations)
    
    def calculate_match_score(self, criteria: MatchingCriteria) -> float:
        """Calculate match score based on criteria."""
        score = 0.0
        
        # Required capabilities - must have all
        required = criteria.required_capabilities
        if required and not required.issubset(self.capabilities_set):
            return 0.0  # Missing required capabilities
        
        if required:
            score += 0.5  # High base score for agents
        
        # Preferred capabilities - bonus points
        preferred = criteria.preferred_capabilities
        if preferred:
            overlap = len(preferred.intersection(self.capabilities_set))
            score += 0.3 * (overlap / len(preferred))
        
        # Specialization matching
        if hasattr(criteria, 'specialization'):
            if criteria.specialization in self.specializations_set:
                score += 0.2
        
        # Workload penalty
        load_penalty = self.current_load * 0.1
        score -= load_penalty
        
        # Delegation cost consideration
        cost_penalty = (self.delegation_cost - 1.0) * 0.05
        score -= cost_penalty
        
        return max(0.0, min(1.0, score))
    
    def can_handle_task(self, task_description: str) -> bool:
        """Check if this agent can handle a specific task."""
        task_lower = task_description.lower()
        
        # Check supported task patterns
        for pattern in self.supported_tasks:
            if pattern.lower() in task_lower:
                return True
        
        # Check specializations
        for spec in self.specializations:
            if spec.lower() in task_lower:
                return True
        
        # Check capabilities
        for cap in self.capabilities:
            if cap.lower() in task_lower:
                return True
        
        return False
    
    def get_capabilities(self) -> Set[str]:
        """Get all capabilities provided by this agent."""
        return self.capabilities_set.copy()
    
    def get_specializations(self) -> Set[str]:
        """Get all specializations of this agent."""
        return self.specializations_set.copy()
    
    def estimate_execution_time(self, task_complexity: str = "medium") -> float:
        """Estimate execution time based on agent performance and current load."""
        base_time = {
            "simple": 5.0,
            "medium": 15.0,
            "complex": 45.0
        }.get(task_complexity, 15.0)
        
        # Adjust for agent speed
        speed_multiplier = {
            "fast": 0.7,
            "medium": 1.0,
            "slow": 1.5
        }.get(self.performance_profile.speed, 1.0)
        
        # Adjust for current load
        load_multiplier = 1.0 + (self.current_load * 0.5)
        
        return base_time * speed_multiplier * load_multiplier
    
    def is_available_for_delegation(self) -> bool:
        """Check if agent is available for delegation."""
        return self.available and self.current_load < 0.8
    
    def update_load(self, load_delta: float):
        """Update the current workload of the agent."""
        self.current_load = max(0.0, min(1.0, self.current_load + load_delta))
        self.available = self.current_load < 0.9
    
    def get_delegation_context(self) -> Dict[str, Any]:
        """Get context information for delegation."""
        return {
            "agent_name": self.name,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "specializations": self.specializations,
            "current_load": self.current_load,
            "delegation_cost": self.delegation_cost,
            "performance_profile": {
                "speed": self.performance_profile.speed,
                "quality": self.performance_profile.quality,
                "resource_usage": self.performance_profile.resource_usage
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with agent-specific information."""
        base_dict = super().to_dict()
        base_dict.update({
            "agent_type": self.agent_type,
            "specializations": self.specializations,
            "capabilities": self.capabilities,
            "supported_tasks": self.supported_tasks,
            "resource_requirements": self.resource_requirements,
            "performance_profile": {
                "speed": self.performance_profile.speed,
                "quality": self.performance_profile.quality,
                "resource_usage": self.performance_profile.resource_usage,
                "scalability": self.performance_profile.scalability,
                "specialization_depth": self.performance_profile.specialization_depth
            },
            "delegation_cost": self.delegation_cost,
            "current_load": self.current_load,
            "available": self.available,
            "estimated_execution_time": self.estimate_execution_time(),
            "delegation_context": self.get_delegation_context()
        })
        return base_dict
    
    @classmethod
    def create_from_agent(
        cls,
        agent: Any,
        agent_name: Optional[str] = None
    ) -> 'AgentCard':
        """
        Create an AgentCard from an existing agent instance.
        
        Args:
            agent: The agent instance to create a card for
            agent_name: Optional custom name (defaults to agent.name)
            
        Returns:
            AgentCard instance
        """
        name = agent_name or getattr(agent, 'name', 'unknown_agent')
        description = getattr(agent, 'description', f"Agent for {name} operations")
        
        # Analyze agent to extract metadata
        analyzer = AgentAnalyzer()
        agent_type = analyzer.infer_agent_type(agent)
        specializations = analyzer.extract_specializations(agent)
        capabilities = analyzer.extract_capabilities(agent)
        supported_tasks = analyzer.extract_supported_tasks(agent)
        resource_requirements = analyzer.extract_resource_requirements(agent)
        performance_profile = analyzer.create_performance_profile(agent)
        delegation_cost = analyzer.calculate_delegation_cost(agent)
        
        # Create metadata
        metadata = CardMetadata(
            source="agent_instance",
            confidence=0.95,
            tags={"auto_generated", "agent_registry"}
        )
        
        return cls(
            agent_name=name,
            description=description,
            agent_type=agent_type,
            specializations=specializations,
            capabilities=capabilities,
            supported_tasks=supported_tasks,
            resource_requirements=resource_requirements,
            performance_profile=performance_profile,
            delegation_cost=delegation_cost,
            agent_instance=agent,
            metadata=metadata
        )


class AgentAnalyzer:
    """Helper class for analyzing agents and extracting metadata."""
    
    def infer_agent_type(self, agent: Any) -> str:
        """Infer the type of agent based on its properties."""
        # Check for role-based typing
        if hasattr(agent, 'config') and hasattr(agent.config, 'role'):
            return str(agent.config.role)
        
        # Check class name patterns
        class_name = agent.__class__.__name__.lower()
        if 'filesystem' in class_name:
            return 'filesystem'
        elif 'report' in class_name:
            return 'reporting'
        elif 'analysis' in class_name:
            return 'analysis'
        elif 'rpavh' in class_name:
            return 'rpavh'
        
        return 'general'
    
    def extract_specializations(self, agent: Any) -> List[str]:
        """Extract specializations from agent properties."""
        specializations = []
        
        # From agent type
        agent_type = self.infer_agent_type(agent)
        specializations.append(agent_type)
        
        # From tools
        if hasattr(agent, 'tools'):
            for tool in agent.tools:
                tool_name = getattr(tool, 'name', '').lower()
                if 'file' in tool_name:
                    specializations.append('file_operations')
                elif 'csv' in tool_name:
                    specializations.append('data_processing')
                elif 'report' in tool_name:
                    specializations.append('reporting')
        
        return list(set(specializations))
    
    def extract_capabilities(self, agent: Any) -> List[str]:
        """Extract capabilities from agent properties."""
        capabilities = []
        
        # Base capabilities
        capabilities.extend(['task_execution', 'llm_interaction'])
        
        # Tool-based capabilities
        if hasattr(agent, 'tools'):
            for tool in agent.tools:
                tool_name = getattr(tool, 'name', '').lower()
                if 'read' in tool_name:
                    capabilities.append('data_reading')
                if 'write' in tool_name:
                    capabilities.append('data_writing')
                if 'find' in tool_name:
                    capabilities.append('discovery')
                if 'stat' in tool_name:
                    capabilities.append('analysis')
        
        # Strategy-based capabilities
        if hasattr(agent, '__class__'):
            class_name = agent.__class__.__name__.lower()
            if 'rpavh' in class_name:
                capabilities.extend(['reflection', 'planning', 'verification'])
            if 'enhanced' in class_name:
                capabilities.extend(['dag_execution', 'smart_verification'])
        
        return list(set(capabilities))
    
    def extract_supported_tasks(self, agent: Any) -> List[str]:
        """Extract supported task patterns."""
        tasks = []
        
        agent_type = self.infer_agent_type(agent)
        
        type_tasks = {
            'filesystem': ['file operations', 'directory scanning', 'file analysis'],
            'reporting': ['report generation', 'document creation', 'data summarization'],
            'analysis': ['data analysis', 'pattern recognition', 'insight extraction'],
            'rpavh': ['complex task execution', 'multi-step workflows', 'verification']
        }
        
        tasks.extend(type_tasks.get(agent_type, ['general tasks']))
        
        return tasks
    
    def extract_resource_requirements(self, agent: Any) -> List[str]:
        """Extract resource requirements."""
        requirements = ['llm_access']
        
        if hasattr(agent, 'tools'):
            for tool in agent.tools:
                tool_name = getattr(tool, 'name', '').lower()
                if 'file' in tool_name:
                    requirements.append('filesystem_access')
                if 'network' in tool_name or 'http' in tool_name:
                    requirements.append('network_access')
        
        return list(set(requirements))
    
    def create_performance_profile(self, agent: Any) -> AgentPerformanceProfile:
        """Create performance profile based on agent characteristics."""
        # Analyze complexity
        tool_count = len(getattr(agent, 'tools', []))
        
        if tool_count > 10:
            return AgentPerformanceProfile(
                speed="medium",
                quality="high",
                resource_usage="high",
                scalability="high",
                specialization_depth="broad"
            )
        elif tool_count > 5:
            return AgentPerformanceProfile(
                speed="medium",
                quality="high",
                resource_usage="medium",
                scalability="medium",
                specialization_depth="focused"
            )
        else:
            return AgentPerformanceProfile(
                speed="fast",
                quality="medium",
                resource_usage="low",
                scalability="low",
                specialization_depth="narrow"
            )
    
    def calculate_delegation_cost(self, agent: Any) -> float:
        """Calculate delegation cost based on agent complexity."""
        base_cost = 1.0
        
        # Cost increases with complexity
        tool_count = len(getattr(agent, 'tools', []))
        tool_cost = tool_count * 0.1
        
        # RPAVH agents have higher setup cost
        if hasattr(agent, '__class__') and 'rpavh' in agent.__class__.__name__.lower():
            base_cost += 0.5
        
        return base_cost + tool_cost