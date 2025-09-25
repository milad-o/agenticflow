"""Agent Role System for AgenticFlow.

This module defines the role-based system that enables intelligent coordination
between agents in multi-agent workflows. Roles define how agents interact
with the orchestrator and other agents.
"""

from enum import Enum
from typing import Dict, List, Set, Optional
from dataclasses import dataclass


class AgentRole(str, Enum):
    """Standard agent roles for multi-agent coordination.
    
    Each role defines a specific function in the workflow and how the agent
    should interact with the orchestrator and other agents.
    """
    
    # Data and Information Roles
    DATA_COLLECTOR = "data_collector"        # Discovers, reads, and gathers data
    DATA_PROCESSOR = "data_processor"        # Transforms and processes data
    DATA_VALIDATOR = "data_validator"        # Validates data quality and integrity
    
    # Analysis and Intelligence Roles  
    ANALYST = "analyst"                      # Analyzes data and extracts insights
    PATTERN_DETECTOR = "pattern_detector"    # Identifies patterns and anomalies
    COMPARATOR = "comparator"               # Compares and contrasts information
    
    # Content and Communication Roles
    REPORTER = "reporter"                   # Generates reports and documentation
    SUMMARIZER = "summarizer"               # Creates summaries and abstracts
    TRANSLATOR = "translator"               # Converts between formats/languages
    
    # Coordination and Management Roles
    COORDINATOR = "coordinator"             # Coordinates between other agents
    VALIDATOR = "validator"                 # Reviews and validates outputs
    ORCHESTRATOR_ASSISTANT = "orchestrator_assistant"  # Helps orchestrator with complex decisions
    
    # Specialized Domain Roles
    WEB_SCRAPER = "web_scraper"            # Web data extraction
    DATABASE_AGENT = "database_agent"      # Database operations
    FILE_MANAGER = "file_manager"          # File system operations
    API_CLIENT = "api_client"              # External API interactions
    
    # Generic Roles
    GENERALIST = "generalist"              # Multi-purpose agent
    SPECIALIST = "specialist"              # Domain-specific expert


@dataclass
class RoleProfile:
    """Defines the characteristics and behavior patterns of an agent role."""
    
    name: str
    description: str
    primary_capabilities: Set[str]
    interaction_patterns: Dict[str, str]  # How this role interacts with others
    typical_tasks: List[str]
    coordination_preferences: Dict[str, any]  # How to coordinate with this role
    
    
class RoleRegistry:
    """Registry of agent role profiles and their characteristics."""
    
    _profiles: Dict[AgentRole, RoleProfile] = {
        
        AgentRole.DATA_COLLECTOR: RoleProfile(
            name="Data Collector",
            description="Specializes in discovering, reading, and gathering data from various sources",
            primary_capabilities={"file_read", "dir_walk", "search", "file_meta", "data_discovery"},
            interaction_patterns={
                "orchestrator": "receives_data_requests",
                "analyst": "provides_raw_data",
                "reporter": "provides_source_materials",
                "coordinator": "reports_collection_status"
            },
            typical_tasks=[
                "Find and list files matching patterns",
                "Read file contents and metadata", 
                "Discover directory structures",
                "Extract data from various sources",
                "Validate file accessibility and permissions"
            ],
            coordination_preferences={
                "prefers_parallel": False,  # Often needs sequential access
                "provides_context": True,   # Provides data context to others
                "dependencies": [],         # Usually first in pipeline
                "outputs_to": ["analyst", "reporter", "data_processor"]
            }
        ),
        
        AgentRole.ANALYST: RoleProfile(
            name="Analyst",
            description="Analyzes data to extract insights, patterns, and relationships",
            primary_capabilities={"analysis", "pattern_recognition", "data_interpretation", "comparison"},
            interaction_patterns={
                "orchestrator": "receives_analysis_requests",
                "data_collector": "consumes_raw_data",
                "reporter": "provides_insights",
                "coordinator": "reports_analysis_findings"
            },
            typical_tasks=[
                "Analyze data for patterns and trends",
                "Compare and contrast different data sources",
                "Extract meaningful insights and relationships",
                "Identify dependencies and correlations",
                "Perform statistical or qualitative analysis"
            ],
            coordination_preferences={
                "prefers_parallel": True,   # Can analyze multiple datasets
                "provides_context": True,   # Provides analytical context
                "dependencies": ["data_collector"],
                "outputs_to": ["reporter", "coordinator"]
            }
        ),
        
        AgentRole.REPORTER: RoleProfile(
            name="Reporter",
            description="Generates structured reports, summaries, and documentation",
            primary_capabilities={"content_creation", "summarization", "markdown", "reporting", "documentation"},
            interaction_patterns={
                "orchestrator": "receives_reporting_requests",
                "data_collector": "consumes_source_data",
                "analyst": "consumes_insights",
                "coordinator": "provides_final_deliverables"
            },
            typical_tasks=[
                "Generate structured markdown reports",
                "Create executive summaries",
                "Synthesize information from multiple sources",
                "Format and organize content for readability",
                "Produce final documentation deliverables"
            ],
            coordination_preferences={
                "prefers_parallel": False,  # Usually final step in pipeline
                "provides_context": False,  # Consumer of context
                "dependencies": ["data_collector", "analyst"],
                "outputs_to": ["coordinator"]
            }
        ),
        
        AgentRole.FILE_MANAGER: RoleProfile(
            name="File Manager", 
            description="Manages file system operations, organization, and maintenance",
            primary_capabilities={"file_read", "file_write", "dir_walk", "file_meta", "file_ops"},
            interaction_patterns={
                "orchestrator": "receives_file_operation_requests",
                "data_collector": "collaborates_on_data_access",
                "reporter": "manages_output_files",
                "coordinator": "reports_file_operations"
            },
            typical_tasks=[
                "Create and manage files and directories",
                "Organize and structure file systems",
                "Handle file permissions and metadata",
                "Backup and archive operations",
                "File cleanup and maintenance"
            ],
            coordination_preferences={
                "prefers_parallel": True,   # Can handle multiple file ops
                "provides_context": True,   # Provides file system context
                "dependencies": [],
                "outputs_to": ["data_collector", "reporter"]
            }
        ),
        
        AgentRole.COORDINATOR: RoleProfile(
            name="Coordinator",
            description="Coordinates workflow between multiple agents and manages dependencies",
            primary_capabilities={"coordination", "workflow_management", "communication", "validation"},
            interaction_patterns={
                "orchestrator": "assists_with_coordination",
                "all_agents": "coordinates_activities",
            },
            typical_tasks=[
                "Coordinate multi-agent workflows",
                "Manage dependencies between agents",
                "Validate workflow completion",
                "Handle inter-agent communication",
                "Resolve conflicts and bottlenecks"
            ],
            coordination_preferences={
                "prefers_parallel": True,   # Coordinates multiple agents
                "provides_context": True,   # Provides workflow context
                "dependencies": [],         # Meta-level role
                "outputs_to": ["orchestrator"]
            }
        ),
        
        AgentRole.GENERALIST: RoleProfile(
            name="Generalist",
            description="Multi-purpose agent capable of handling various types of tasks",
            primary_capabilities={"general", "adaptable", "multi_domain"},
            interaction_patterns={
                "orchestrator": "receives_general_requests",
                "all_agents": "can_collaborate_with_any",
            },
            typical_tasks=[
                "Handle miscellaneous tasks",
                "Fill gaps in specialized workflows",
                "Provide general-purpose problem solving",
                "Adapt to various domain requirements"
            ],
            coordination_preferences={
                "prefers_parallel": True,   # Flexible coordination
                "provides_context": True,   # Adaptable context provision
                "dependencies": [],         # No specific dependencies
                "outputs_to": ["any"]      # Can output to any role
            }
        )
    }
    
    @classmethod
    def get_profile(cls, role: AgentRole) -> Optional[RoleProfile]:
        """Get the profile for a specific role."""
        return cls._profiles.get(role)
    
    @classmethod
    def get_all_profiles(cls) -> Dict[AgentRole, RoleProfile]:
        """Get all role profiles."""
        return cls._profiles.copy()
    
    @classmethod
    def get_roles_by_capability(cls, capability: str) -> List[AgentRole]:
        """Get all roles that have a specific capability."""
        matching_roles = []
        for role, profile in cls._profiles.items():
            if capability in profile.primary_capabilities:
                matching_roles.append(role)
        return matching_roles
    
    @classmethod
    def get_coordination_pattern(cls, source_role: AgentRole, target_role: AgentRole) -> Optional[str]:
        """Get the interaction pattern between two roles."""
        source_profile = cls.get_profile(source_role)
        if source_profile:
            # Check for specific target role pattern
            if target_role.value in source_profile.interaction_patterns:
                return source_profile.interaction_patterns[target_role.value]
            # Check for generic patterns
            if "all_agents" in source_profile.interaction_patterns:
                return source_profile.interaction_patterns["all_agents"]
        return None
    
    @classmethod
    def suggest_workflow_order(cls, roles: List[AgentRole]) -> List[AgentRole]:
        """Suggest an optimal order for agents based on their role dependencies."""
        # Simple topological sort based on role dependencies
        remaining = set(roles)
        ordered = []
        
        while remaining:
            # Find roles with no unmet dependencies
            ready = []
            for role in remaining:
                profile = cls.get_profile(role)
                if profile:
                    deps = profile.coordination_preferences.get("dependencies", [])
                    # Check if all dependencies are already in ordered list
                    deps_met = all(
                        any(ordered_role.value == dep for ordered_role in ordered) 
                        for dep in deps
                    )
                    if deps_met:
                        ready.append(role)
                else:
                    ready.append(role)  # Unknown roles go first
            
            if not ready:
                # Break cycles by adding remaining roles
                ready = list(remaining)
            
            # Sort ready roles by preference (data collectors first, reporters last)
            ready.sort(key=lambda r: {
                AgentRole.DATA_COLLECTOR: 0,
                AgentRole.FILE_MANAGER: 1,
                AgentRole.ANALYST: 2,
                AgentRole.COORDINATOR: 3,
                AgentRole.REPORTER: 4,
                AgentRole.GENERALIST: 5
            }.get(r, 3))
            
            # Add first ready role to ordered list
            next_role = ready[0]
            ordered.append(next_role)
            remaining.remove(next_role)
        
        return ordered